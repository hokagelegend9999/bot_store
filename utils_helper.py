import telebot
from database import get_user_data
from menus import menu_owner, menu_reseller, menu_user
from config import ADMIN_ID
from bot_init import TEMP_VIEW
from constants import HARGA_RESELLER, HARGA_USER, TARGET_RESELLER

def get_back_markup():
    """Markup standar untuk tombol kembali"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="menu_back"))
    return markup

def get_price(user_id):
    """Mengambil harga sesuai role user (reseller atau user biasa)"""
    try:
        data = get_user_data(user_id)
        if data['role'] == 'reseller': return HARGA_RESELLER
    except: pass
    return HARGA_USER

def get_menu_content(user_id, first_name, username):
    """Menyusun teks dan keyboard menu berdasarkan Role dan Status View"""
    data = get_user_data(user_id)
    
    # Tentukan Role asli
    real_role = "owner" if str(user_id) == str(ADMIN_ID) else data['role']
    saldo = data['balance']
    uname_text = f"@{username}" if username else "No Username"
    
    # Ambil tampilan role saat ini (fitur switch view)
    current_role = TEMP_VIEW.get(user_id, real_role)
    
    # Indikator Preview
    is_owner_preview = (str(user_id) == str(ADMIN_ID))
    is_reseller_preview = (real_role == 'reseller' and current_role == 'user')

    text = ""
    markup = None

    # 1. TAMPILAN OWNER
    if current_role == 'owner':
        text = f"👑 <b>OWNER PANEL</b>\nHalo <b>{first_name}</b>\nSaldo Server: Unlimited"
        markup = menu_owner(user_id)
        
    # 2. TAMPILAN RESELLER
    elif current_role == 'reseller':
        text = (
            f"💼 <b>RESELLER DASHBOARD</b>\n"
            f"👤 <b>{first_name}</b> ({uname_text})\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"💰 Saldo: <b>Rp {saldo:,}</b>\n"
            f"🎯 <i>Target: Min {TARGET_RESELLER} Trx/Bulan</i>"
        )
        if is_owner_preview: text += "\n<i>(Mode Preview Owner)</i>"
        markup = menu_reseller(is_owner_preview)
        
    # 3. TAMPILAN USER BIASA / MEMBER
    else: 
        display_role = real_role
        if is_reseller_preview: display_role = 'reseller' 
        if is_owner_preview: display_role = 'user' 
        
        text = (
            f"👤 <b>MEMBER AREA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 <b>Selamat Datang, {first_name}!</b>\n"
            f"🆔 ID Akun: <code>{user_id}</code>\n"
            f"👤 Username: {uname_text}\n"
            f"💰 Saldo Aktif: <b>Rp {saldo:,}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚀 <b>TINGKATKAN TRANSAKSI ANDA!</b>\n"
            f"Segera lakukan <b>ISI SALDO (Topup)</b> dan gunakan layanan kami sesering mungkin.\n\n"
            f"<i>💡 Semakin sering bertransaksi, semakin dekat kesempatan Anda mendapatkan benefit eksklusif dan harga yang lebih hemat!</i>"
        )
        
        if is_owner_preview: text += "\n\n<i>(Mode Preview Owner)</i>"
        if is_reseller_preview: text += "\n\n<i>(Mode Preview Reseller)</i>"
        
        # Mengirim display_role agar harga (10k/7k) di tombol otomatis berubah
        markup = menu_user(display_role, is_owner_preview, is_reseller_preview)

    return text, markup