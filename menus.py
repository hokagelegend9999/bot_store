# menus.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# 1. MENU OWNER (Panel Admin Tertinggi)
# ==========================================
def menu_owner(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # --- Baris 1: Panel Utama & Saldo ---
    markup.add(
        InlineKeyboardButton("👑 PANEL UTAMA", callback_data="admin_panel"),
        InlineKeyboardButton("💰 SALDO", callback_data="manage_saldo")
    ) 
    
    # --- Baris 2: Fitur Keuangan ---
    markup.add(InlineKeyboardButton("💸 TRANSFER / WD", callback_data="owner_wd_menu")),
    markup.add(InlineKeyboardButton("📂 BACKUP DATABASE (ZIP/EXCEL)", callback_data="backup_db"))
    
    # --- Baris 3: Manajemen Member & Riwayat ---
    markup.add(
        InlineKeyboardButton("👥 List Member", callback_data="list_member|1"),
        InlineKeyboardButton("🆔 CEK USER (DETAIL)", callback_data="check_user_by_id_menu"),
        InlineKeyboardButton("🔎 Cek Riwayat User", callback_data="check_user_history")
    ) 

    # --- Baris 4: Monitoring VPS ---
    markup.add(InlineKeyboardButton("🔍 CEK USER VPS", callback_data="check_vps_menu"))

    # --- Baris 5: Manajemen Reseller ---
    markup.add(InlineKeyboardButton("💼 List Reseller", callback_data="list_reseller|1"))
    
    # --- Baris 6: Pengaturan System ---
    markup.add(
        InlineKeyboardButton("➕ Angkat Reseller", callback_data="manual_add_reseller"),
        InlineKeyboardButton("⚙️ SETTING SERVER", callback_data="setting_menu")
    )
    
    # --- Baris 7: Fitur Preview (Switch Role) ---
    markup.add(InlineKeyboardButton("👁️ Lihat sbg RESELLER", callback_data="switch_reseller"))
    markup.add(InlineKeyboardButton("👁️ Lihat sbg USER", callback_data="switch_user"))
    
    return markup

# ==========================================
# 2. MENU RESELLER
# ==========================================
def menu_reseller(is_owner_preview=False):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # --- Fitur Jualan VPN ---
    markup.add(InlineKeyboardButton("🏪 BELI GROSIR SSH", callback_data="buy_ssh_bulk"))
    markup.add(
        InlineKeyboardButton("👥 Buat User Baru", callback_data="create_user"),
        InlineKeyboardButton("📊 Laporan", callback_data="report")
    )
    
    # --- Fitur PPOB (Dua Jalur Provider) ---
    markup.add(
        InlineKeyboardButton("📱 PULSA/DATA MURAH (OK)", callback_data="ppob_menu"),
        InlineKeyboardButton("📱 PULSA/DATA LENGKAP (ATL)", callback_data="ppob_atlantic")
    )
    
    # --- Navigasi Preview ---
    markup.add(InlineKeyboardButton("👁️ Lihat sbg USER", callback_data="switch_user"))
    
    # Jika diakses oleh Owner (Mode Preview)
    if is_owner_preview:
        markup.add(InlineKeyboardButton("🔙 KEMBALI OWNER", callback_data="switch_owner"))
        
    return markup

# ==========================================
# 3. MENU USER (Tampilan Member Biasa)
# ==========================================
def menu_user(role, is_owner_preview=False, is_reseller_preview=False):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Tentukan Label Harga Berdasarkan Role
    tag = "7k" if role == 'reseller' else "10k"

    # --- Produk VPN (SSH & XRAY) ---
    markup.add(
        InlineKeyboardButton(f"🚀 SSH ({tag})", callback_data="buy_ssh"),
        InlineKeyboardButton(f"⚡ VMESS ({tag})", callback_data="buy_vmess")
    )
    markup.add(
        InlineKeyboardButton(f"🛡️ VLESS ({tag})", callback_data="buy_vless"),
        InlineKeyboardButton(f"🐎 TROJAN ({tag})", callback_data="buy_trojan")
    )
    
    # --- Layanan PPOB (Dua Jalur Provider) ---
    # ppob_menu diarahkan ke handler OkeConnect (Murah)
    # ppob_atlantic diarahkan ke handler Atlantic (Lengkap)
    markup.add(
        InlineKeyboardButton("📱 PULSA DATA MURAH", callback_data="ppob_menu"),
        InlineKeyboardButton("📱 PULSA DATA LENGKAP", callback_data="ppob_atlantic")
    )
    
    # --- Akun & Saldo ---
    # Tombol pendaftaran reseller hanya muncul jika role masih 'user'
    if role != 'reseller':
        markup.add(InlineKeyboardButton("💼 DAFTAR RESELLER (50k)", callback_data="register_reseller"))
    
    markup.add(
        InlineKeyboardButton("➕ ISI SALDO", callback_data="topup"),
        InlineKeyboardButton("📜 RIWAYAT", callback_data="history_user")
    )
    
    # --- Navigasi Back (Jika dalam Mode Intip/Preview) ---
    if is_owner_preview:
        markup.add(InlineKeyboardButton("👁️ Lihat sbg RESELLER", callback_data="switch_reseller"))
        markup.add(InlineKeyboardButton("🔙 KEMBALI OWNER", callback_data="switch_owner"))
    elif is_reseller_preview:
        markup.add(InlineKeyboardButton("🔙 KEMBALI KE RESELLER", callback_data="switch_reseller_back"))
        
    return markup