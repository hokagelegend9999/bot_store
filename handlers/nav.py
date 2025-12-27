import telebot
from bot_init import bot, TEMP_VIEW
from config import ADMIN_ID
from database import add_user, get_user_data, get_user_transaction_history

# Import Menu
from menus import menu_user, menu_owner, menu_reseller
from utils_helper import get_back_markup

# ==========================================
#  FUNGSI BANTUAN: GENERATE KONTEN MENU
# ==========================================
def generate_menu_content(uid, first_name, username):
    """
    Fungsi pintar untuk menentukan Teks & Tombol berdasarkan Role & View Mode.
    """
    # 1. Ambil Data User Real dari Database
    user = get_user_data(uid)
    if not user:
        saldo = 0
        role = 'user'
    else:
        try:
            saldo = int(user.get('balance', 0))
            role = str(user.get('role', 'user')).lower()
        except:
            saldo = 0
            role = 'user'

    # 2. Cek Apakah User ini OWNER ASLI?
    is_real_owner = (str(uid) == str(ADMIN_ID)) or ('owner' in role)

    # 3. Tentukan Mode Tampilan (View Mode)
    if uid in TEMP_VIEW:
        view_mode = TEMP_VIEW[uid] # 'user', 'reseller', 'owner'
    else:
        view_mode = 'owner' if is_real_owner else role

    # 4. LOGIKA PEMBUATAN PESAN & TOMBOL
    
    # --- KASUS A: TAMPILAN OWNER (GOD MODE) ---
    if is_real_owner and (view_mode == 'owner' or 'owner' in view_mode):
        saldo_display = "♾️ UNLIMITED (Owner)"
        text = (
            f"👑 <b>PANEL OWNER (GOD MODE)</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👋 Halo, Bos <b>{first_name}</b>!\n"
            f"🆔 ID Akun: <code>{uid}</code>\n"
            f"👤 Username: @{username}\n"
            f"💰 <b>Saldo: {saldo_display}</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"🛡️ <i>Sebagai Owner, Anda memiliki akses penuh dan saldo tak terbatas.\n"
            f"Gunakan panel di bawah untuk mengelola bot.</i>"
        )
        markup = menu_owner(uid)

    # --- KASUS B: PREVIEW MODE (Owner melihat tampilan User) ---
    elif is_real_owner and view_mode == 'user':
        saldo_display = "♾️ UNLIMITED (Preview)"
        text = (
            f"👑 <b>PREVIEW MODE (OWNER)</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👋 Halo Bos <b>{first_name}</b>\n"
            f"💰 <b>Saldo: {saldo_display}</b>\n\n"
            f"<i>(Ini adalah tampilan menu yang dilihat Member biasa.)</i>\n"
            f"<i>(Tombol 'Daftar Reseller' aman, tidak akan memotong saldo Anda.)</i>"
        )
        markup = menu_user('user', is_owner_preview=True)

    # --- KASUS C: PREVIEW MODE (Owner melihat tampilan Reseller) ---
    elif is_real_owner and view_mode == 'reseller':
        saldo_display = "♾️ UNLIMITED (Preview)"
        
        # Teks Benefit untuk Preview
        benefit_msg = (
            "<b>💎 KEUNTUNGAN RESELLER:</b>\n"
            "• 🚀 <b>SSH/VPN:</b> Rp 10.000 ➔ <b>Rp 7.000</b>\n"
            "• 📱 <b>PULSA:</b> Lebih Murah (Cth: 13k ➔ 12k)\n\n"
            "⚠️ <i>Pertahankan saldo Anda agar status Reseller tetap aktif dan dapatkan profit menarik lainnya!</i>"
        )
        
        text = (
            f"👑 <b>PREVIEW MODE (OWNER)</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👋 Halo Bos <b>{first_name}</b>\n"
            f"⚡ <b>Status: RESELLER VIEW</b>\n"
            f"💰 <b>Saldo: {saldo_display}</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"{benefit_msg}"
        )
        markup = menu_reseller(is_owner_preview=True)

    # --- KASUS D: USER ASLI / RESELLER ASLI ---
    else:
        saldo_display = f"Rp {saldo:,}".replace(",", ".")
        
        # Header Teks & Pesan Tambahan
        if 'reseller' in view_mode:
            title = "⚡ RESELLER AREA"
            # [UPDATE DISINI] Menambahkan Informasi Benefit
            extra_msg = (
                "<b>💎 BENEFIT EKSKLUSIF ANDA:</b>\n"
                "• 🚀 <b>SSH/VPN:</b> <s>Rp 10.000</s> ➔ <b>Rp 7.000</b>\n"
                "• 📱 <b>PULSA:</b> Harga Spesial (Cth: 13k ➔ 12k)\n\n"
                "⚠️ <i>Mohon pertahankan saldo Anda agar status Reseller tetap aktif. "
                "Nantikan profit dan fitur menarik lainnya segera!</i>"
            )
        else:
            title = "👤 MEMBER AREA"
            extra_msg = (
                "🚀 <b>TINGKATKAN TRANSAKSI ANDA!</b>\n"
                "Segera lakukan ISI SALDO (Topup) agar bisa bertransaksi.\n"
                "<i>Semakin sering bertransaksi, semakin dekat kesempatan mendapatkan benefit eksklusif!</i>"
            )

        text = (
            f"<b>{title}</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👋 Selamat Datang, <b>{first_name}</b>!\n"
            f"🆔 ID Akun: <code>{uid}</code>\n"
            f"👤 Username: @{username}\n"
            f"💰 <b>Saldo Aktif: {saldo_display}</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"{extra_msg}"
        )

        # Markup Logic
        if 'reseller' in role: 
             if view_mode == 'user':
                 markup = menu_user(role, is_reseller_preview=True)
             else:
                 markup = menu_reseller()
        else:
            markup = menu_user(role)

    return text, markup


# ==========================================
#  HANDLERS UTAMA
# ==========================================

# --- 1. MENU UTAMA (/start atau /menu) ---
@bot.message_handler(commands=['start', 'menu'])
def start(m):
    add_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
    
    # Reset tampilan ke mode asli saat /start
    if m.from_user.id in TEMP_VIEW: 
        del TEMP_VIEW[m.from_user.id]
        
    txt, mark = generate_menu_content(m.from_user.id, m.from_user.first_name, m.from_user.username)
    bot.send_message(m.chat.id, txt, parse_mode='HTML', reply_markup=mark)

# --- 2. SWITCH ROLE (Lihat Sebagai...) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('switch_'))
def switch(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    
    uid = call.from_user.id
    user_data = get_user_data(uid)
    role = user_data.get('role', 'user')
    
    # Logika Switching
    if str(uid) == str(ADMIN_ID) or 'owner' in role:
        if "reseller" in call.data and "back" not in call.data: 
            TEMP_VIEW[uid] = "reseller"
        elif "user" in call.data: 
            TEMP_VIEW[uid] = "user"
        else: # switch_owner
            if uid in TEMP_VIEW: del TEMP_VIEW[uid]

    elif role == 'reseller':
        if "user" in call.data:
            TEMP_VIEW[uid] = "user"
        elif "reseller" in call.data: # switch_reseller_back
            if uid in TEMP_VIEW: del TEMP_VIEW[uid]
            
    # Generate Tampilan Baru
    txt, mark = generate_menu_content(uid, call.from_user.first_name, call.from_user.username)
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, 
                              parse_mode='HTML', reply_markup=mark)
    except:
        bot.send_message(call.message.chat.id, txt, parse_mode='HTML', reply_markup=mark)

# --- 3. TOMBOL KEMBALI (Global Back) ---
@bot.callback_query_handler(func=lambda call: call.data == "menu_back")
def back(call):
    try: bot.answer_callback_query(call.id)
    except: pass
    
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    
    txt, mark = generate_menu_content(call.from_user.id, call.from_user.first_name, call.from_user.username)
    
    try: 
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: 
        pass
        
    bot.send_message(call.message.chat.id, txt, parse_mode='HTML', reply_markup=mark)

# --- 4. RIWAYAT TRANSAKSI USER ---
@bot.callback_query_handler(func=lambda call: call.data == "history_user")
def user_hist(call):
    try: bot.answer_callback_query(call.id)
    except: pass

    hs = get_user_transaction_history(call.from_user.id)
    msg = "<b>📜 RIWAYAT TRANSAKSI ANDA</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    if not hs:
        msg += "Belum ada transaksi."
    else:
        for h in hs[:10]:
            msg += f"✅ {h[1]} | Rp {h[2]:,} | {h[0]}\n"
            
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                          parse_mode='HTML', reply_markup=get_back_markup())