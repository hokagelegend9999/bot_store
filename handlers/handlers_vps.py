import telebot
import subprocess
import os
import zipfile
import json
import smtplib
import math
import requests
import time
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import base64

from bot_init import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException
from config import (
    ADMIN_ID, DOMAIN_HOST, ATLANTIC_API_KEY, ATLANTIC_PROFILE_URL, 
    SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, RECIPIENT_EMAIL
)
from database import add_balance, get_user_data, increment_reseller_trx
from utils_helper import get_back_markup, get_price
from ssh_service import create_linux_user

# Coba import OkeConnect
try:
    from orderkuota_service import get_okeconnect_profile
except ImportError:
    get_okeconnect_profile = None

# ==========================================
#  1. FITUR BELI SSH & ZIVPN
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "buy_ssh")
def buy_ssh_start(call):
    uid = call.from_user.id
    try: price = get_price(uid) 
    except: price = 5000
    
    if str(uid) != str(ADMIN_ID):
        user_data = get_user_data(uid)
        if not user_data or user_data['balance'] < price:
            return bot.send_message(call.message.chat.id, f"⚠️ <b>SALDO KURANG</b>\nHarga: Rp {price:,}\nSaldo Anda: Rp {user_data['balance']:,}", parse_mode='HTML')
    
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("❌ BATAL", callback_data="menu_back"))
    msg = bot.send_message(call.message.chat.id, f"<b>🚀 BELI SSH & ZIVPN (Rp {price:,})</b>\n\n1️⃣ Masukkan <b>Username</b>:", parse_mode='HTML', reply_markup=m)
    bot.register_next_step_handler(msg, ssh_input_username, price)

def ssh_input_username(message, price):
    username = message.text.strip()
    if not username.isalnum() or len(username) < 3:
        return bot.reply_to(message, "❌ Username invalid.")
    msg = bot.reply_to(message, f"✅ User: <b>{username}</b>\n\n2️⃣ Masukkan <b>Password</b>:", parse_mode='HTML')
    bot.register_next_step_handler(msg, ssh_input_password, username, price)

def ssh_input_password(message, username, price):
    password = message.text.strip()
    uid = message.from_user.id
    if str(uid) != str(ADMIN_ID):
        if get_user_data(uid)['balance'] < price:
            return bot.reply_to(message, "❌ Saldo tidak cukup.")

    status_msg = bot.reply_to(message, "⏳ <b>Proses...</b>", parse_mode='HTML')
    threading.Thread(target=ssh_execution, args=(message, username, password, uid, price, status_msg)).start()

def ssh_execution(message, u, p, uid, price, status_msg):
    try:
        success, info, exp = create_linux_user(u, p, days=30, limit=2)
        if success:
            if str(uid) != str(ADMIN_ID):
                add_balance(uid, -price, f"Beli SSH {u}")
                udata = get_user_data(uid)
                if udata and str(udata.get('role')).lower() == 'reseller':
                    increment_reseller_trx(uid)
            
            try: bot.delete_message(message.chat.id, status_msg.message_id)
            except: pass
            
            res = f"""
<b>✅ SSH & ZIVPN PREMIUM</b>
━━━━━━━━━━━━━━━
👤 User : <code>{u}</code>
🔑 Pass : <code>{p}</code>
📅 Exp  : {exp}
━━━━━━━━━━━━━━━
🔌 <b>SSH WS</b>  : 80
🔌 <b>SSH SSL</b> : 443
🎮 <b>ZIVPN</b>   : 5667 (UDP)
━━━━━━━━━━━━━━━
"""
            bot.send_message(message.chat.id, res, parse_mode='HTML', reply_markup=get_back_markup())
        else:
            bot.reply_to(message, f"❌ Gagal: {info}")
    except Exception as e:
        bot.reply_to(message, "❌ Error System")

# ==========================================
#  2. HELPER UTILS (SSH, XRAY, SERVICE CHECK)
# ==========================================
def get_content(path):
    try: return subprocess.check_output(f"cat {path}", shell=True).decode('utf-8').strip()
    except: return "-"

def get_service_status(service_name):
    """
    [BARU] Mengecek status service via systemctl
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            timeout=3
        )
        status = result.stdout.strip()
        if status == "active" or status == "running":
            return "🟢 Online"
        else:
            return "🔴 Offline"
    except:
        return "🔴 Error"

def get_linux_user_detail(username):
    try:
        cmd_exp = f"chage -l {username} | grep 'Account expires' | cut -d: -f2"
        exp_date = subprocess.check_output(cmd_exp, shell=True).decode('utf-8').strip()
        cmd_status = f"passwd -S {username} | awk '{{print $2}}'"
        status_code = subprocess.check_output(cmd_status, shell=True).decode('utf-8').strip()
        if status_code == "L": status_text, is_locked = "🔴 LOCKED", True
        else: status_text, is_locked = "🟢 ACTIVE", False
        return {'username': username, 'exp': exp_date, 'status': status_text, 'is_locked': is_locked}
    except: return None

def delete_zivpn_user(username):
    try:
        subprocess.run(f"jq --arg u '{username}' '.auth.config -= [$u]' /etc/zivpn/config.json > /etc/zivpn/config.json.tmp && mv /etc/zivpn/config.json.tmp /etc/zivpn/config.json", shell=True)
        subprocess.run(f"jq --arg u '{username}' 'del(.[$u])' /etc/zivpn/user-db.json > /etc/zivpn/user-db.json.tmp && mv /etc/zivpn/user-db.json.tmp /etc/zivpn/user-db.json", shell=True)
        subprocess.run("systemctl restart zivpn", shell=True)
    except: pass

def get_xray_detail(user, proto):
    try:
        domain = get_content("/etc/xray/domain")
        if proto == 'vmess': header = "###"
        elif proto == 'vless': header = "#&"
        elif proto == 'trojan': header = "#!"
        else: return "Unknown Proto"

        cmd = f"grep -A 1 '^{header} {user} ' /etc/xray/config.json"
        raw = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        info = f"👤 <b>{proto.upper()} USER</b>\nDomain: {domain}\nUser: {user}\n"
        if proto == 'trojan': info += "<i>Cek config manual untuk pass/uuid detail</i>"
        else: info += "<i>UUID hidden (security)</i>"
        return info
    except: return f"Gagal mengambil detail {user}"

def count_unique_users(proto):
    try:
        if proto == 'ssh':
            cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd"
        else:
            header = "^### " if proto == 'vmess' else "^#& " if proto == 'vless' else "^#! "
            cmd = f"grep '{header}' /etc/xray/config.json | cut -d ' ' -f 2"
        
        output = subprocess.check_output(cmd, shell=True).decode("utf-8")
        unique_users = set([u.strip() for u in output.split("\n") if u.strip()])
        return len(unique_users)
    except:
        return 0

# ==========================================
#  3. MONITORING SERVER (DASHBOARD & DETAIL SERVICE)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "check_vps_menu")
def vps_check_menu(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🖥️ DASHBOARD VPS (FULL)", callback_data="vps_dashboard_full"))
    m.row(InlineKeyboardButton("👤 Cek User Login", callback_data="vps_monitor_login"), 
          InlineKeyboardButton("🔒 Detail Service", callback_data="vps_service_detail"))
    m.add(InlineKeyboardButton("📂 LIST SSH MEMBER", callback_data="vps_list_view|ssh|1"))
    m.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_owner"))
    bot.edit_message_text("<b>🔍 MENU MONITORING VPS</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "vps_dashboard_full")
def vps_dashboard_full(call):
    bot.answer_callback_query(call.id, "🔄 Loading Data...")
    try:
        ipvps = subprocess.check_output("curl -s ipv4.icanhazip.com", shell=True).decode("utf-8").strip()
        uptime = subprocess.check_output("uptime -p", shell=True).decode("utf-8").strip().replace("up ", "")
        
        acc_ssh = count_unique_users('ssh')
        acc_vmess = count_unique_users('vmess')
        acc_vless = count_unique_users('vless')
        acc_trojan = count_unique_users('trojan')

        msg = (f"💻 <b>VPS DASHBOARD</b>\n"
               f"IP: <code>{ipvps}</code>\n"
               f"Uptime: {uptime}\n\n"
               f"📊 <b>STATISTIK USER (UNIK):</b>\n"
               f"• SSH/ZIVPN : {acc_ssh}\n"
               f"• VMESS     : {acc_vmess}\n"
               f"• VLESS     : {acc_vless}\n"
               f"• TROJAN    : {acc_trojan}")
        
        m = InlineKeyboardMarkup(row_width=2)
        m.add(InlineKeyboardButton(f"📂 SSH ({acc_ssh})", callback_data="vps_list_view|ssh|1"))
        m.row(
            InlineKeyboardButton(f"📂 VMESS ({acc_vmess})", callback_data="vps_list_view|vmess|1"),
            InlineKeyboardButton(f"📂 VLESS ({acc_vless})", callback_data="vps_list_view|vless|1")
        )
        m.add(InlineKeyboardButton(f"📂 TROJAN ({acc_trojan})", callback_data="vps_list_view|trojan|1"))
        m.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
    except Exception as e: bot.send_message(call.message.chat.id, f"Error: {e}")

# ==========================================
#  [UPDATE] HANDLER DETAIL SERVICE (+ZIVPN)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "vps_service_detail")
def show_vps_service_detail(call):
    if str(call.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(call.id, "❌ Akses Ditolak")

    bot.answer_callback_query(call.id, "🔄 Memeriksa service...")
    bot.edit_message_text(
        "⏳ <b>Sedang memeriksa status service VPS...</b>\nMohon tunggu sejenak.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML'
    )

    # 1. Ambil Info System
    try:
        os_name = subprocess.check_output("cat /etc/os-release | grep -w PRETTY_NAME | cut -d= -f2 | tr -d '\"'", shell=True).decode().strip()
    except: os_name = "Unknown"
    
    try: ip_vps = subprocess.check_output("curl -s ipv4.icanhazip.com", shell=True).decode().strip()
    except: ip_vps = "Unknown"
    
    domain = get_content("/etc/xray/domain")

    # 2. Cek Semua Service
    ssh_stat = get_service_status("ssh")
    dropbear_stat = get_service_status("dropbear")
    haproxy_stat = get_service_status("haproxy")
    xray_stat = get_service_status("xray") 
    nginx_stat = get_service_status("nginx")
    cron_stat = get_service_status("cron")
    fail2ban_stat = get_service_status("fail2ban")
    openvpn_stat = get_service_status("openvpn")
    
    # [NEW] Cek ZIVPN
    zivpn_stat = get_service_status("zivpn")

    udp1 = get_service_status("udp-mini-1")
    udp2 = get_service_status("udp-mini-2")
    udp3 = get_service_status("udp-mini-3")
    ws_stat = get_service_status("ws") 
    udp_custom = get_service_status("udp-custom")

    # 3. Susun Pesan
    msg = (
        f"<b>🖥 SYSTEM INFORMATION</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"💻 <b>OS     :</b> <code>{os_name}</code>\n"
        f"🌐 <b>IP     :</b> <code>{ip_vps}</code>\n"
        f"🎯 <b>Domain :</b> <code>{domain}</code>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"<b>⚙️ SERVICE STATUS</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🟢 <b>SSH / OVPN</b>\n"
        f"├ SSH Service    : {ssh_stat}\n"
        f"├ Dropbear       : {dropbear_stat}\n"
        f"├ OpenVPN        : {openvpn_stat}\n"
        f"├ ZIVPN Tunnel   : {zivpn_stat}\n"
        f"└ Haproxy        : {haproxy_stat}\n\n"
        
        f"🔵 <b>XRAY / TUNNEL</b>\n"
        f"├ Xray Core      : {xray_stat}\n"
        f"├ (Vmess/Vless/Trojan)\n"
        f"└ Websocket      : {ws_stat}\n\n"
        
        f"🟠 <b>UDP & LAINNYA</b>\n"
        f"├ Nginx Web      : {nginx_stat}\n"
        f"├ UDP Custom     : {udp_custom}\n"
        f"├ BadVPN 7100    : {udp1}\n"
        f"├ BadVPN 7200    : {udp2}\n"
        f"├ BadVPN 7300    : {udp3}\n"
        f"├ Crontab        : {cron_stat}\n"
        f"└ Fail2Ban       : {fail2ban_stat}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Refresh Status", callback_data="vps_service_detail"))
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu"))

    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

# ==========================================
#  4. LIST USER (FIXED DUPLICATE & SORTED)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("vps_list_view"))
def vps_show_list(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    parts = call.data.split("|")
    proto = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1
    
    all_users = []
    try:
        if proto == 'ssh':
            cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd"
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")
            raw_list = [u.strip() for u in output.split("\n") if u.strip()]
            all_users = sorted(list(set(raw_list)))
            
        elif proto in ['vmess', 'vless', 'trojan']:
            header = "^### " if proto == 'vmess' else "^#& " if proto == 'vless' else "^#! "
            cmd = f"grep '{header}' /etc/xray/config.json | cut -d ' ' -f 2"
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")
            raw_list = [u.strip() for u in output.split("\n") if u.strip()]
            all_users = sorted(list(set(raw_list)))
    except: 
        all_users = []
    
    LIMIT = 10
    total_items = len(all_users)
    total_pages = math.ceil(total_items / LIMIT)
    
    if total_pages == 0: total_pages = 1
    if page > total_pages: page = total_pages
    if page < 1: page = 1
    
    offset = (page - 1) * LIMIT
    current_users = all_users[offset : offset + LIMIT]
    
    msg = f"📂 <b>LIST {proto.upper()}</b>\n"
    msg += f"📄 Halaman {page} dari {total_pages}\n"
    msg += f"👥 Total: {total_items} User (Unik)\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    
    markup = InlineKeyboardMarkup(row_width=5)
    btn_numbers = []
    
    if not current_users:
        msg += "<i>Belum ada user.</i>"
    else:
        for i, user in enumerate(current_users, 1):
            msg += f"<b>[{offset + i}]</b> {user}\n"
            btn_numbers.append(InlineKeyboardButton(str(offset + i), callback_data=f"vps_det|{proto}|{user}|{page}"))
        
        msg += "\n<i>👇 Klik nomor untuk Hapus/Detail:</i>"
        markup.add(*btn_numbers)
    
    nav_btns = []
    if page > 1:
        nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"vps_list_view|{proto}|{page-1}"))
    nav_btns.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"vps_list_view|{proto}|{page+1}"))
        
    markup.row(*nav_btns)
    markup.add(InlineKeyboardButton("🔙 KEMBALI DASHBOARD", callback_data="vps_dashboard_full"))
    
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except ApiTelegramException: pass

# ==========================================
#  5. DETAIL USER & ACTION
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("vps_det|"))
def vps_user_detail(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    _, proto, username, page = call.data.split("|")
    
    msg = f"👤 <b>DETAIL USER {proto.upper()}</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    
    if proto == 'ssh':
        info = get_linux_user_detail(username)
        if info:
            msg += f"🆔 User : <b>{info['username']}</b>\n📅 Exp  : {info['exp']}\n🔌 Status: {info['status']}"
        else: msg += "User tidak ditemukan."
    else:
        info = get_xray_detail(username, proto)
        msg += info
    
    msg += "\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n<i>Pilih tindakan:</i>"
    
    m = InlineKeyboardMarkup()
    if proto == 'ssh':
        m.row(InlineKeyboardButton("🔐 LOCK", callback_data=f"ssh_act|lock|{username}|{page}"),
              InlineKeyboardButton("🔓 UNLOCK", callback_data=f"ssh_act|unlock|{username}|{page}"))
        
    m.add(InlineKeyboardButton("🗑️ HAPUS USER", callback_data=f"vps_del_conf|{proto}|{username}|{page}"))
    m.add(InlineKeyboardButton("🔙 KEMBALI", callback_data=f"vps_list_view|{proto}|{page}"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ssh_act|"))
def ssh_action(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    _, action, username, page = call.data.split("|")
    
    if action == "lock": subprocess.run(["passwd", "-l", username])
    elif action == "unlock": subprocess.run(["passwd", "-u", username])
    
    bot.answer_callback_query(call.id, f"Sukses {action} {username}")
    call.data = f"vps_det|ssh|{username}|{page}"
    vps_user_detail(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vps_del_conf|"))
def vps_confirm_delete(call):
    _, proto, username, page = call.data.split("|")
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("✅ YA, HAPUS", callback_data=f"vps_exec_del|{proto}|{username}|{page}"),
          InlineKeyboardButton("❌ BATAL", callback_data=f"vps_det|{proto}|{username}|{page}"))
    bot.edit_message_text(f"⚠️ <b>HAPUS USER?</b>\n\nYakin hapus <b>{username}</b> ({proto})?", 
                          call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vps_exec_del|"))
def vps_execute_delete(call):
    _, proto, username, page = call.data.split("|")
    
    if proto == 'ssh':
        subprocess.run(["userdel", "-f", username])
        delete_zivpn_user(username)
    else:
        try:
            bot.answer_callback_query(call.id, "Untuk Xray, hapus via menu VPS demi keamanan.")
            return
        except: pass

    bot.answer_callback_query(call.id, "User Deleted!")
    call.data = f"vps_list_view|{proto}|{page}"
    vps_show_list(call)

# ==========================================
#  6. BACKUP & SETTING MENU
# ==========================================
def send_email_backup(zip_filename):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = SMTP_EMAIL, RECIPIENT_EMAIL, f"Backup {datetime.now()}"
        attachment = open(zip_filename, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {zip_filename}")
        msg.attach(part)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e: return False

@bot.callback_query_handler(func=lambda call: call.data == "setting_menu")
def setting_menu(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    # Ambil data saldo
    saldo_oke = "Modul Off"
    if get_okeconnect_profile:
        try: saldo_oke = get_okeconnect_profile()
        except: pass

    saldo_atl = "Rp -"
    try:
        res = requests.post(ATLANTIC_PROFILE_URL, data={'api_key': ATLANTIC_API_KEY}, timeout=15).json()
        if str(res.get('status')).lower() in ['true', '1', 'success']:
            saldo_atl = f"Rp {int(res['data']['balance']):,}".replace(",", ".")
    except: pass

    msg = (f"🎛 <b>CONTROL PANEL ADMIN</b>\n"
           f"🖥 IP: <code>{DOMAIN_HOST}</code>\n"
           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
           f"🏦 OkeConnect: {saldo_oke}\n"
           f"🌊 Atlantic: <b>{saldo_atl}</b>\n"
           f"🕒 <i>Updated: {datetime.now().strftime('%H:%M:%S')}</i>")
    
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton("🔄 REFRESH DATA", callback_data="setting_menu"))
    m.row(InlineKeyboardButton("🔌 REBOOT", callback_data="srv_reboot"), InlineKeyboardButton("🔁 RESTART", callback_data="srv_restart"))
    m.row(InlineKeyboardButton("💾 BACKUP", callback_data="srv_backup_menu"), InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast_menu"))
    m.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_owner"))
    
    try:
        if call.message.content_type == 'document':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, msg, parse_mode='HTML', reply_markup=m)
        else:
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
    except Exception as e:
        bot.send_message(call.message.chat.id, msg, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "srv_backup_menu")
def backup_handler(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    chat_id = call.message.chat.id
    wait = bot.send_message(chat_id, "⏳ <b>Sedang memproses backup data...</b>", parse_mode='HTML')
    
    try:
        now = datetime.now()
        zname = f"Backup_{now.strftime('%Y%m%d_%H%M')}.zip"
        
        with zipfile.ZipFile(zname, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.py', '.db', '.json')) and not file.startswith('Backup_'):
                        zipf.write(os.path.join(root, file))
        
        is_email_sent = send_email_backup(zname)
        status_email = "✅ <b>Email Terkirim</b>" if is_email_sent else "❌ <b>Email Gagal</b>"
        
        caption_msg = (
            f"📦 <b>BACKUP SUCCESSFUL</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"{status_email}\n\n"
            f"📝 <b>Rincian Data:</b>\n"
            f"├ 📄 <code>Source Code (.py)</code>\n"
            f"├ 🗄 <code>Database User (.db)</code>\n"
            f"├ ⚙️ <code>Konfigurasi (.json)</code>\n"
            f"└ 🕒 {now.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"⚠️ <i>Simpan file ini di tempat aman.</i>"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 KEMBALI KE PENGATURAN", callback_data="setting_menu"))
        
        with open(zname, 'rb') as f:
            bot.send_document(
                chat_id, 
                f, 
                caption=caption_msg, 
                parse_mode='HTML', 
                reply_markup=markup
            )
        
        if os.path.exists(zname): os.remove(zname) 
        bot.delete_message(chat_id, wait.message_id) 
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        
    except Exception as e:
        err_markup = InlineKeyboardMarkup()
        err_markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="setting_menu"))
        bot.edit_message_text(f"❌ <b>Backup Gagal:</b>\n<code>{e}</code>", 
                              chat_id, wait.message_id, 
                              parse_mode='HTML', reply_markup=err_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("srv_"))
def srv_act(call):
    if "reboot" in call.data: subprocess.Popen(["reboot"])
    elif "restart" in call.data: subprocess.Popen(["systemctl", "restart", "bot-store"])
    bot.answer_callback_query(call.id, "Processing...")