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
from vless_service import create_vless_user

# === BAGIAN BELI VLESS ===
@bot.callback_query_handler(func=lambda call: call.data == "buy_vless")
def buy_vless(call):
    uid = call.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price:
        return bot.send_message(call.message.chat.id, f"⚠️ <b>SALDO KURANG</b>\nHarga: Rp {price:,}", parse_mode='HTML')
    
    m = telebot.types.InlineKeyboardMarkup()
    m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="menu_back"))
    
    msg = bot.send_message(call.message.chat.id, 
        f"<b>🔮 BELI VLESS (Rp {price:,})</b>\n\nMasukkan <b>Username</b> yang diinginkan:", 
        parse_mode='HTML', reply_markup=m)
    
    bot.register_next_step_handler(msg, vless_process)

def vless_process(m):
    u = m.text.strip()
    if not u.isalnum() or len(u) < 3: 
        return bot.reply_to(m, "❌ Invalid Username (Min 3 karakter, huruf/angka saja).")
    
    uid = m.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price: 
        return bot.reply_to(m, "❌ Saldo Kurang saat diproses.")

    status = bot.reply_to(m, "⏳ <b>Memproses Akun Vless Premium...</b>", parse_mode='HTML')
    threading.Thread(target=vless_execution, args=(m, u, uid, price, status)).start()

def vless_execution(m, u, uid, price, status_msg):
    try:
        quota_gb = "100"      
        masa_aktif = "30"     
        limit_ip = 2          

        succ, info, res = create_vless_user(u, quota_gb, masa_aktif)
        
        if succ:
            if str(uid) != str(ADMIN_ID): 
                try:
                    add_balance(uid, -price, f"Beli Vless {u}")
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
<code> 🔮Xray/Vless Account🔮</code>
<code>☉——————————————————————————☉</code>
<code>Remarks     : {u}
Domain      : {domain}
User Quota  : {quota_gb} GB
Limit Ip    : {limit_ip} (Device)
ISP         : {isp_name}
City        : {city_name}
port TLS    : 443
Port NTLS   : 80, 8080, 8880
User ID     : {uuid}
Encryption  : none
Path TLS    : /vless 
ServiceName : vless-grpc</code>
<code>☉——————————————————————————☉</code>
<code> VLESS WS TLS</code>
<code>☉——————————————————————————☉</code>
<code>{link_tls}</code>
<code>☉——————————————————————————☉</code>
<code> VLESS WS NO TLS</code>
<code>☉——————————————————————————☉</code>
<code>{link_ntls}</code>
<code>☉——————————————————————————☉</code>
<code> VLESS gRPC</code>
<code>☉——————————————————————————☉</code>
<code>{link_grpc}</code>
<code>☉——————————————————————————☉</code>
Format OpenClash : https://{domain}:81/vless-{u}.txt
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
        print(f"CRITICAL ERROR VLESS: {e}")
        try: bot.delete_message(m.chat.id, status_msg.message_id)
        except: pass
        bot.reply_to(m, "❌ Terjadi Kesalahan Sistem.")

# === BAGIAN CEK & HAPUS VPS VLESS ===
def render_vless_page(chat_id, message_id, page=0):
    try:
        cmd = f"{PATH_KYT}/bot-cek-vless" 
        if not os.path.exists(cmd): 
            bot.send_message(chat_id, "⚠️ Script bot-cek-vless tidak ditemukan!")
            return

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
    msg = f"<b>🔮 LIST VLESS</b>\nHal: {page+1}/{total} | Total: {len(users)}\n━━━━━━━━━━\n"
    m = telebot.types.InlineKeyboardMarkup()
    
    for u in cur:
        ic = "🟢" if int(u['ip']) > 0 else "⚪"
        msg += f"👤 <b>{u['u']}</b>\n📊 {u['us']} / {u['lim']}\n🔌 {ic} Login: {u['ip']}\n📅 {u['ex']}\n➖➖➖➖\n"
        m.add(telebot.types.InlineKeyboardButton(f"🗑️ Hapus {u['u']}", callback_data=f"vls_del_{u['u']}_{page}"))
    
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"vls_nav_{page-1}"))
    if page < total - 1: nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"vls_nav_{page+1}"))
    if nav: m.row(*nav)
    m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu"))
    
    try: bot.edit_message_text(msg, chat_id, message_id, parse_mode='HTML', reply_markup=m)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "check_vless_vps")
def start_cek_vless(call): 
    if str(call.from_user.id) == str(ADMIN_ID): 
        bot.answer_callback_query(call.id, "Loading Vless...")
        render_vless_page(call.message.chat.id, call.message.message_id, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vls_nav_"))
def nav_vless(call):
    if str(call.from_user.id) == str(ADMIN_ID): 
        render_vless_page(call.message.chat.id, call.message.message_id, int(call.data.split("_")[2]))

@bot.callback_query_handler(func=lambda call: call.data.startswith("vls_del_"))
def del_vless(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    try:
        p = call.data.split("_")
        user_to_delete = p[2]
        page = int(p[3])
        
        config_path = "/etc/xray/config.json"
        db_path = "/etc/vless/.vless.db"

        subprocess.run(f"sed -i '/^#& {user_to_delete} /,+1d' {config_path}", shell=True)
        
        if os.path.exists(db_path):
            subprocess.run(f"sed -i '/^### {user_to_delete} /d' {db_path}", shell=True)
            subprocess.run(f"sed -i '/^#& {user_to_delete} /d' {db_path}", shell=True)
            
        subprocess.run(f"sed -i '/^$/d' {config_path}", shell=True)
        subprocess.run(f"rm -f /etc/xray/limit/vless/{user_to_delete}", shell=True)
        subprocess.run(f"rm -f /etc/vless/{user_to_delete}", shell=True) 

        subprocess.run("systemctl restart xray", shell=True)
        
        bot.answer_callback_query(call.id, f"✅ User {user_to_delete} BERHASIL DIHAPUS!", show_alert=True)
        render_vless_page(call.message.chat.id, call.message.message_id, page)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)