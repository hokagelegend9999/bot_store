import threading
import datetime
import telebot
import subprocess
import math
import os
from bot_init import bot
from config import ADMIN_ID, DOMAIN_HOST
from database import get_user_data, add_balance, increment_reseller_trx
from utils_helper import get_price, get_back_markup
from constants import PATH_KYT
from ssh_service import create_linux_user

# === BAGIAN BELI SSH ===
@bot.callback_query_handler(func=lambda call: call.data == "buy_ssh")
def buy_ssh(call):
    uid = call.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price:
        return bot.send_message(call.message.chat.id, f"⚠️ <b>SALDO KURANG</b>\nHarga: Rp {price:,}", parse_mode='HTML')
    
    m = telebot.types.InlineKeyboardMarkup()
    m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="menu_back"))
    
    msg = bot.send_message(call.message.chat.id, 
        f"<b>🚀 BELI SSH (Rp {price:,})</b>\n\n1️⃣ Masukkan <b>Username</b> yang diinginkan:", 
        parse_mode='HTML', reply_markup=m)
    
    bot.register_next_step_handler(msg, ssh_input_username)

def ssh_input_username(m):
    u = m.text.strip()
    if not u.isalnum() or len(u) < 3: 
        return bot.reply_to(m, "❌ Invalid Username (Min 3 karakter, huruf/angka saja). Silakan ulangi pembelian.")
    
    msg = bot.reply_to(m, f"✅ Username: <b>{u}</b>\n\n2️⃣ Sekarang masukkan <b>Password</b> yang diinginkan:", parse_mode='HTML')
    bot.register_next_step_handler(msg, ssh_input_password, u)

def ssh_input_password(m, username):
    password = m.text.strip()
    if len(password) < 1:
        return bot.reply_to(m, "❌ Password tidak boleh kosong.")

    uid = m.from_user.id
    price = get_price(uid)
    
    if str(uid) != str(ADMIN_ID) and get_user_data(uid)['balance'] < price: 
        return bot.reply_to(m, "❌ Saldo Kurang saat diproses.")

    status = bot.reply_to(m, "⏳ <b>Memproses Akun SSH Premium...</b>", parse_mode='HTML')
    threading.Thread(target=ssh_execution, args=(m, username, password, uid, price, status)).start()

def ssh_execution(m, u, password, uid, price, status_msg):
    try:
        limit_ip = 2
        masa_aktif = 30
        quota_display = "200 GB" 

        succ, info, exp = create_linux_user(u, password, days=masa_aktif, limit=limit_ip)
        
        if succ:
            if str(uid) != str(ADMIN_ID): 
                try:
                    add_balance(uid, -price, f"Beli SSH {u}")
                    if get_user_data(uid)['role'] == 'reseller': 
                        increment_reseller_trx(uid)
                except Exception as e:
                    print(f"Error Potong Saldo: {e}")

            try: bot.delete_message(m.chat.id, status_msg.message_id)
            except: pass
            
            now = datetime.datetime.now().strftime("%d/%m/%Y")
            res = f"""
========================================
🌟 <b>AKUN SSH PREMIUM</b>
========================================

🔹 <b>INFORMASI AKUN SSH</b>
Username: <code>{u}</code>
Domain: <code>{DOMAIN_HOST}</code>
Password: <code>{password}</code>
SSH WS: 80
SSH SSL WS: 443

🔗 <b>FORMAT KONEKSI</b>
WS Format: 
<code>{DOMAIN_HOST}:80@{u}:{password}</code>
TLS Format: 
<code>{DOMAIN_HOST}:443@{u}:{password}</code>
UDP Format: 
<code>{DOMAIN_HOST}:1-65535@{u}:{password}</code>

📋 <b>INFORMASI TAMBAHAN</b>
Expired: {exp}
IP Limit: {limit_ip} Device
Quota: {quota_display}

========================================
♨ᵗᵉʳⁱᵐᵃᵏᵃˢⁱʰ ᵗᵉˡᵃʰ ᵐᵉⁿᵍᵍᵘⁿᵃᵏᵃⁿ ˡᵃʸᵃⁿᵃⁿ ᵏᵃᵐⁱ♨
Generated on {now}
========================================
"""
            bot.send_message(m.chat.id, res, parse_mode='HTML', reply_markup=get_back_markup())
            
        else:
            try: bot.delete_message(m.chat.id, status_msg.message_id)
            except: pass
            bot.reply_to(m, f"❌ <b>GAGAL:</b> {info}", parse_mode='HTML')

    except Exception as e:
        print(f"CRITICAL ERROR SSH: {e}")
        try: bot.delete_message(m.chat.id, status_msg.message_id)
        except: pass
        bot.reply_to(m, "❌ Terjadi Kesalahan Sistem.")

# === BAGIAN CEK & HAPUS VPS SSH ===
def render_ssh_page(chat_id, message_id, page=0):
    try:
        cmd = f"{PATH_KYT}/bot-member-ssh"
        if not os.path.exists(cmd):
            cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd"
        
        raw = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
        all_users = []
        for line in raw.splitlines():
            if "|" in line: 
                p = line.split("|")
                if len(p) >= 3:
                    all_users.append({"u": p[0], "e": p[1], "s": p[2].strip()})
            elif line.strip() and " " not in line: 
                all_users.append({"u": line.strip(), "e": "-", "s": "?"})
                
    except Exception as e:
        print(f"Error baca SSH: {e}") 
        all_users = []

    per_page = 5
    total = math.ceil(len(all_users)/per_page)
    if page < 0: page = 0
    if total > 0 and page >= total: page = total - 1
    
    cur = all_users[page*per_page:(page+1)*per_page]
    msg = f"<b>🚀 LIST SSH</b>\nHal: {page+1}/{total} | Total: {len(all_users)}\n━━━━━━━━━━\n"
    m = telebot.types.InlineKeyboardMarkup()
    for u in cur:
        ic = "🟢" if "UNLOCKED" in u['s'] else "🔴"
        msg += f"👤 <b>{u['u']}</b> | {ic}\n📅 {u['e']}\n➖➖➖➖\n"
        m.add(telebot.types.InlineKeyboardButton(f"🗑️ Hapus {u['u']}", callback_data=f"ssh_del_{u['u']}_{page}"))
    
    nav = []
    if page > 0: nav.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"ssh_nav_{page-1}"))
    if page < total - 1: nav.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"ssh_nav_{page+1}"))
    if nav: m.row(*nav)
    m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu"))
    
    try: bot.edit_message_text(msg, chat_id, message_id, parse_mode='HTML', reply_markup=m)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "check_ssh_vps")
def start_cek_ssh(call): 
    if str(call.from_user.id) == str(ADMIN_ID): render_ssh_page(call.message.chat.id, call.message.message_id, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ssh_nav_"))
def nav_ssh(call):
    if str(call.from_user.id) == str(ADMIN_ID): render_ssh_page(call.message.chat.id, call.message.message_id, int(call.data.split("_")[2]))

@bot.callback_query_handler(func=lambda call: call.data.startswith("ssh_del_"))
def del_ssh(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    try:
        p = call.data.split("_")
        subprocess.run(f"userdel -f {p[2]}", shell=True)
        bot.answer_callback_query(call.id, "Deleted!")
        render_ssh_page(call.message.chat.id, call.message.message_id, int(p[3]))
    except: pass