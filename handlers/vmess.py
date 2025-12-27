import threading
import datetime
import telebot
import subprocess
import requests
import math
import os
from bot_init import bot
from config import ADMIN_ID, DOMAIN_HOST
from database import get_user_data, add_balance, increment_reseller_trx
from utils_helper import get_price, get_back_markup
from constants import PATH_KYT
from vmess_service import create_vmess_user

# === BAGIAN BELI VMESS ===
@bot.callback_query_handler(func=lambda call: call.data == "buy_vmess")
def buy_vmess(call):
    uid = call.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price:
        return bot.send_message(call.message.chat.id, f"⚠️ <b>SALDO KURANG</b>\nHarga: Rp {price:,}", parse_mode='HTML')
    
    m = telebot.types.InlineKeyboardMarkup()
    m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="menu_back"))
    
    msg = bot.send_message(call.message.chat.id, 
        f"<b>⚡ BELI VMESS (Rp {price:,})</b>\n\nMasukkan <b>Username</b> yang diinginkan:", 
        parse_mode='HTML', reply_markup=m)
    
    bot.register_next_step_handler(msg, vmess_process)

def vmess_process(m):
    u = m.text.strip()
    if not u.isalnum() or len(u) < 3: 
        return bot.reply_to(m, "❌ Invalid Username (Min 3 karakter, huruf/angka saja).")
    
    uid = m.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price: 
        return bot.reply_to(m, "❌ Saldo Kurang saat diproses.")

    status = bot.reply_to(m, "⏳ <b>Memproses Akun Vmess Premium...</b>", parse_mode='HTML')
    threading.Thread(target=vmess_execution, args=(m, u, uid, price, status)).start()

def vmess_execution(m, u, uid, price, status_msg):
    try:
        quota_gb = "100"      
        masa_aktif = "30"     
        limit_ip = 2          

        succ, info, res = create_vmess_user(u, quota_gb, masa_aktif)
        
        if succ:
            if str(uid) != str(ADMIN_ID): 
                try:
                    add_balance(uid, -price, f"Beli Vmess {u}")
                    try:
                        if get_user_data(uid)['role'] == 'reseller': 
                            increment_reseller_trx(uid)
                    except: pass
                except Exception as e:
                    print(f"Error Potong Saldo: {e}")

            try: bot.delete_message(m.chat.id, status_msg.message_id)
            except: pass
            
            uuid = res.get('uuid', '-')
            link_tls = res.get('link_tls', '-')
            link_ntls = res.get('link_ntls', '-')
            link_grpc = res.get('link_grpc', '-')
            domain = res.get('domain', DOMAIN_HOST)

            try:
                ip_pub = subprocess.check_output("curl -s ipv4.icanhazip.com", shell=True).decode().strip()
                r_isp = requests.get(f"http://ip-api.com/json/{ip_pub}", timeout=5).json()
                isp_name = r_isp.get('isp', 'Datacenter')
                city_name = r_isp.get('city', 'Unknown')
            except:
                isp_name = "Server ISP"
                city_name = "Server Location"

            now = datetime.datetime.now()
            exp_date = now + datetime.timedelta(days=int(masa_aktif))
            tgl_buat = now.strftime("%d %b, %Y")   
            tgl_exp = exp_date.strftime("%d %b, %Y") 

            txt = f"""<code>☉——————————————————————————☉</code>
<code> ☘️Xray/Vmess Account☘️</code>
<code>☉——————————————————————————☉</code>
<code>Remarks     : {u}
Domain      : {domain}
Limit Quota : {quota_gb} GB
Limit Ip    : {limit_ip} (Device)
ISP         : {isp_name}
Location    : {city_name}
Port TLS    : 443
Port NTLS   : 80, 8080, 8880
id          : {uuid}
alterId     : 0
Security    : auto
network     : ws or grpc
Path        : /vmess
Dynamic     : https://bugmu.com/path
Name        : vmess-grpc</code>
<code>☉——————————————————————————☉</code>
<code> VMESS WS TLS</code>
<code>☉——————————————————————————☉</code>
<code>{link_tls}</code>
<code>☉——————————————————————————☉</code>
<code> VMESS WS NO TLS</code>
<code>☉——————————————————————————☉</code>
<code>{link_ntls}</code>
<code>☉——————————————————————————☉</code>
<code> VMESS gRPC</code>
<code>☉——————————————————————————☉</code>
<code>{link_grpc}</code>
<code>☉——————————————————————————☉</code>
Format OpenClash : https://{domain}:81/vmess-{u}.txt
<code>☉——————————————————————————☉</code>
Aktif Selama   : {masa_aktif} Hari
Dibuat Pada    : {tgl_buat}
Berakhir Pada  : {tgl_exp}
<code>☉——————————————————————————☉</code>"""

            bot.send_message(m.chat.id, txt, parse_mode='HTML', reply_markup=get_back_markup())
            
        else:
            try: bot.delete_message(m.chat.id, status_msg.message_id)
            except: pass
            bot.reply_to(m, f"❌ <b>GAGAL:</b> {info}", parse_mode='HTML')

    except Exception as e:
        print(f"CRITICAL ERROR VMESS: {e}")
        try: bot.delete_message(m.chat.id, status_msg.message_id)
        except: pass
        bot.reply_to(m, "❌ Terjadi Kesalahan Sistem (Cek Log).")

# === BAGIAN CEK & HAPUS VPS VMESS ===
def render_vmess_page(chat_id, message_id, page=0):
    try:
        cmd = f"{PATH_KYT}/bot-cek-vmess"
        if not os.path.exists(cmd): return
        raw = subprocess.check_output(cmd, shell=True).decode("utf-8")
        users = []
        for line in raw.splitlines():
            if "|" in line:
                p = line.split("|")
                users.append({"u": p[0], "us": p[1], "lim": p[2], "ip": p[3], "ex": p[4]})
    except: users = []

    per_page = 5
    total = math.ceil(len(users)/per_page)
    if page < 0: page = 0
    if total > 0 and page >= total: page = total - 1
    
    cur = users[page*per_page:(page+1)*per_page]
    msg = f"<b>⚡ LIST VMESS</b>\nHal: {page+1}/{total} | Total: {len(users)}\n━━━━━━━━━━\n"
    m = telebot.types.InlineKeyboardMarkup()
    for u in cur:
        ic = "🟢" if int(u['ip']) > 0 else "⚪"
        msg += f"👤 <b>{u['u']}</b>\n📊 {u['us']} / {u['lim']}\n🔌 {ic} Login: {u['ip']}\n📅 {u['ex']}\n➖➖➖➖\n"
        m.add(telebot.types.InlineKeyboardButton(f"🗑️ Hapus {u['u']}", callback_data=f"vms_del_{u['u']}_{page}"))
    
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"vms_nav_{page-1}"))
    if page < total - 1: nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"vms_nav_{page+1}"))
    if nav: m.row(*nav)
    m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu"))
    
    try: bot.edit_message_text(msg, chat_id, message_id, parse_mode='HTML', reply_markup=m)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "check_vmess_vps")
def start_cek_vmess(call): 
    if str(call.from_user.id) == str(ADMIN_ID): 
        bot.answer_callback_query(call.id, "Loading...")
        render_vmess_page(call.message.chat.id, call.message.message_id, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vms_nav_"))
def nav_vmess(call):
    if str(call.from_user.id) == str(ADMIN_ID): render_vmess_page(call.message.chat.id, call.message.message_id, int(call.data.split("_")[2]))

@bot.callback_query_handler(func=lambda call: call.data.startswith("vms_del_"))
def del_vmess(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    try:
        p = call.data.split("_")
        user_to_delete = p[2]
        page = int(p[3])
        
        config_path = "/etc/xray/config.json"
        cmd_hapus = f"sed -i '/^### {user_to_delete} /,+1d' {config_path}"
        subprocess.run(cmd_hapus, shell=True)
        subprocess.run(f"sed -i '/^$/d' {config_path}", shell=True)
        subprocess.run(f"rm -f /etc/xray/limit/vmess/{user_to_delete}", shell=True)
        subprocess.run("systemctl restart xray", shell=True)
        
        bot.answer_callback_query(call.id, f"✅ {user_to_delete} tewas!", show_alert=True)
        render_vmess_page(call.message.chat.id, call.message.message_id, page)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)