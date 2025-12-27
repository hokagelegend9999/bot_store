# admin.py
import telebot
from bot_init import bot
import sqlite3
import pandas as pd
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# --- IMPORT SEMUA MODULE HANDLER ---
# Dengan mengimport ini, semua dekorator @bot... akan teregistrasi otomatis
from handlers import handlers_vps
from handlers import handlers_users
from handlers import handlers_ppob
from handlers import handlers_payment
from config import ADMIN_ID
from datetime import datetime
DB_NAME = "store_data.db"
# --- DEFAULT HANDLER (OPSIONAL) ---
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_default(call):
    bot.answer_callback_query(call.id, "Panel Utama Aktif")
# ==========================================
#  HANDLER BACKUP DATABASE
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "backup_db")
def export_database_handler(call):
    # 1. Validasi Owner
    if str(call.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(call.id, "❌ Akses Ditolak!", show_alert=True)

    # Siapkan Tombol Kembali
    markup_back = InlineKeyboardMarkup()
    markup_back.add(InlineKeyboardButton("🔙 KEMBALI KE PANEL", callback_data="switch_owner"))

    try:
        # Notif sedang proses
        msg = bot.send_message(call.message.chat.id, "⏳ <b>Sedang memproses backup data...</b>\nMohon tunggu sebentar.", parse_mode='HTML')
        
        # Tanggal hari ini
        today = datetime.now().strftime("%Y-%m-%d_%H-%M")
        excel_filename = f"Backup_Store_{today}.xlsx"

        # A. KIRIM FILE DATABASE ASLI (.DB)
        if os.path.exists(DB_NAME):
            with open(DB_NAME, 'rb') as f:
                bot.send_document(
                    call.message.chat.id, 
                    f, 
                    caption=f"🗄 <b>DATABASE RAW ({today})</b>\nFile ini untuk restore jika bot error.",
                    parse_mode='HTML'
                )
        else:
            bot.send_message(call.message.chat.id, "❌ File database asli tidak ditemukan!")

        # B. EXPORT KE EXCEL (.XLSX)
        conn = sqlite3.connect(DB_NAME)
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            try:
                df_users = pd.read_sql_query("SELECT * FROM users", conn)
                df_users.to_excel(writer, sheet_name='Users', index=False)
            except: pass

            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
                if cursor.fetchone():
                    df_trx = pd.read_sql_query("SELECT * FROM transactions", conn)
                    df_trx.to_excel(writer, sheet_name='Transaksi', index=False)
            except: pass
        conn.close()

        # C. KIRIM FILE EXCEL
        with open(excel_filename, 'rb') as f:
            bot.send_document(
                call.message.chat.id, 
                f, 
                caption=f"📊 <b>LAPORAN EXCEL ({today})</b>\nData user dan transaksi agar mudah dibaca.",
                parse_mode='HTML'
            )

        # Cleanup
        os.remove(excel_filename)
        try: bot.delete_message(call.message.chat.id, msg.message_id)
        except: pass

        # [UPDATE] Kirim Pesan Konfirmasi Akhir dengan Tombol Kembali
        bot.send_message(
            call.message.chat.id, 
            "✅ <b>BACKUP SELESAI!</b>\nSilakan simpan file di atas dengan aman.", 
            parse_mode='HTML', 
            reply_markup=markup_back
        )

    except Exception as e:
        try: bot.delete_message(call.message.chat.id, msg.message_id)
        except: pass
        
        # [UPDATE] Tampilkan tombol kembali saat Error
        bot.reply_to(call.message, f"❌ Gagal Backup: {e}", reply_markup=markup_back)
        print(f"Error Backup: {e}")
        
@bot.callback_query_handler(func=lambda call: True)
def default_callback(call):
    # Daftar prefix yang sudah ditangani di file lain agar tidak dianggap unhandled
    handled_prefixes = [
        'ppob_', 'atl_', 'atlbeli', 'atlfix', # PPOB
        'vps_', 'srv_', # VPS
        'list_', 'hist_', 'saldo_', 'manual_', 'broadcast', 'deal_', # Users
        'wd_', 'check_atlantic', 'cek_profil' # Payment
    ]
    
    if any(call.data.startswith(p) for p in handled_prefixes): return
    
    # Jika benar-benar tidak ada handler
    bot.answer_callback_query(call.id, "⚠️ Fitur belum tersedia / Maintenance")

# Jalankan bot (Biasanya main.py yang menjalankan polling, tapi jika admin.py adalah entry point):
if __name__ == "__main__":
    print("Bot Admin Modules Loaded...")
    # bot.infinity_polling() # Aktifkan ini jika Anda menjalankan bot dari file ini langsung
    
def get_service_status(service_name):
    """
    Mengecek apakah service berjalan menggunakan systemctl.
    Return: Icon (🟢/🔴) dan Teks Status.
    """
    try:
        # Cek status menggunakan systemctl is-active
        result = subprocess.run(
            ["systemctl", "is-active", service_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        status = result.stdout.strip()
        
        if status == "active" or status == "running":
            return "🟢 Online"
        else:
            return "🔴 Offline"
    except:
        return "🔴 Error"

def get_system_info():
    """Mengambil OS, IP, dan Domain"""
    # 1. Ambil OS
    try:
        os_name = subprocess.check_output("cat /etc/os-release | grep -w PRETTY_NAME | cut -d= -f2 | tr -d '\"'", shell=True).decode().strip()
    except:
        os_name = "Unknown Linux"

    # 2. Ambil IP
    try:
        ip_vps = subprocess.check_output("curl -s ipv4.icanhazip.com", shell=True).decode().strip()
    except:
        ip_vps = "Unknown IP"

    # 3. Ambil Domain (Sesuai path script bash Anda)
    try:
        if os.path.exists("/etc/xray/domain"):
            with open("/etc/xray/domain", "r") as f:
                domain = f.read().strip()
        else:
            domain = "-"
    except:
        domain = "-"
        
    return os_name, ip_vps, domain

# ==========================================
#  HANDLER TOMBOL DETAIL SERVICE
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "vps_service_detail")
def show_vps_service_detail(call):
    # Validasi Admin
    if str(call.from_user.id) != str(ADMIN_ID):
        return bot.answer_callback_query(call.id, "❌ Akses Ditolak")

    bot.answer_callback_query(call.id, "🔄 Memeriksa service...")
    bot.send_chat_action(call.message.chat.id, 'typing')

    # 1. Ambil Info System
    os_name, ip_vps, domain = get_system_info()

    # 2. Cek Semua Service (Sesuai Script Bash Anda)
    # Nama service disesuaikan dengan yang umum dipakai di script tunneling
    ssh_stat = get_service_status("ssh")
    dropbear_stat = get_service_status("dropbear")
    haproxy_stat = get_service_status("haproxy")
    xray_stat = get_service_status("xray") # Mewakili Vmess, Vless, Trojan
    nginx_stat = get_service_status("nginx")
    cron_stat = get_service_status("cron")
    fail2ban_stat = get_service_status("fail2ban")
    openvpn_stat = get_service_status("openvpn")
    
    # UDP Mini / BadVPN (Cek 3 port umum)
    udp1 = get_service_status("udp-mini-1")
    udp2 = get_service_status("udp-mini-2")
    udp3 = get_service_status("udp-mini-3")
    
    # WebSocket & UDP Custom
    ws_stat = get_service_status("ws") # Service websocket
    udp_custom = get_service_status("udp-custom")

    # 3. Susun Pesan (Format Rapi)
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
        f"└ Haproxy        : {haproxy_stat}\n\n"
        
        f"🔵 <b>XRAY / TUNNEL</b>\n"
        f"├ Xray Core      : {xray_stat}\n"
        f"├ (Vmess/Vless/Trojan/Shadowsocks)\n"
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
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="check_vps_menu")) # Sesuaikan callback menu VPS anda

    # Edit pesan yang ada
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)