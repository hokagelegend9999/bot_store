# handlers/handlers_users.py
import telebot
import math
import time
from bot_init import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from constants import HARGA_DAFTAR_RESELLER
from database import add_downline_user
# --- PERBAIKAN IMPORT (MENGGUNAKAN KURUNG AGAR RAPI) ---
from database import (
    find_user, add_balance, get_user_data, set_role,
    set_reseller_start, get_all_users_list,
    get_user_transaction_history, get_all_ids,
    get_reseller_downline_transactions
)
from utils_helper import get_back_markup
from telebot.apihelper import ApiTelegramException 
from activity_tracker import get_online_icon

# Konfigurasi Auto Upgrade
MIN_TOPUP_AUTO_RESELLER = 50000
BIAYA_DAFTAR_RESELLER = 50000  # Konfigurasi Biaya Daftar Manual

# ==========================================
#  1. MANAJEMEN SALDO (ADMIN) & AUTO UPGRADE
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "manage_saldo")
def saldo_menu_handler(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    m = InlineKeyboardMarkup(row_width=2)
    m.add(InlineKeyboardButton("🔍 CEK SALDO USER", callback_data="saldo_check"), 
          InlineKeyboardButton("➕ TAMBAH SALDO", callback_data="saldo_add"))
    m.add(InlineKeyboardButton("➖ POTONG SALDO", callback_data="saldo_deduct"), 
          InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_owner"))
    bot.edit_message_text("<b>💰 MANAJEMEN KEUANGAN USER</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "saldo_check")
def saldo_check_start(call):
    msg = bot.send_message(call.message.chat.id, "🔍 Kirim <b>ID</b> atau <b>Username</b> user yang ingin dicek:", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_saldo_check)

def process_saldo_check(message):
    user = find_user(message.text.strip())
    if not user: return bot.reply_to(message, "❌ User tidak ditemukan.")
    bot.reply_to(message, f"👤 <b>{user[1]}</b>\n💰 Saldo: Rp {user[2]:,}", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "saldo_add")
def saldo_add_start(call):
    msg = bot.send_message(call.message.chat.id, "➕ Kirim <b>ID</b> atau <b>Username</b> target:", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_saldo_add_step1)

def process_saldo_add_step1(message):
    user = find_user(message.text.strip())
    if not user: return bot.reply_to(message, "❌ User tidak ditemukan.")
    msg = bot.reply_to(message, f"Target: <b>{user[1]}</b>\n🆔 ID: <code>{user[0]}</code>\n\n💸 Masukkan Nominal Tambah (Contoh: 50000):", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_saldo_add_step2, user[0])

def process_saldo_add_step2(message, target_id):
    try:
        amount = int(message.text.replace(".","").replace(",",""))
        
        # 1. Tambah Saldo
        add_balance(target_id, amount, "Deposit via Admin")
        reply_msg = f"✅ Sukses menambah <b>Rp {amount:,}</b> ke ID {target_id}"

        # 2. Cek Auto Upgrade Reseller (Jika Topup >= 50.000)
        if amount >= MIN_TOPUP_AUTO_RESELLER:
            user_data = get_user_data(target_id)
            # Cek jika user belum reseller
            if user_data and 'reseller' not in str(user_data.get('role')).lower():
                set_role(target_id, 'reseller')
                set_reseller_start(target_id)
                
                reply_msg += "\n🎉 <b>AUTO UPGRADE:</b> User otomatis naik jadi RESELLER!"
                
                # Notif ke User
                try:
                    bot.send_message(
                        target_id,
                        f"🎉 <b>SELAMAT!</b>\n\nKarena Anda melakukan Topup sebesar Rp {amount:,} (Minimal Rp {MIN_TOPUP_AUTO_RESELLER:,}),\n"
                        f"Status akun Anda otomatis naik menjadi ⚡ <b>RESELLER</b>.\n\n"
                        f"<i>Nikmati harga produk yang lebih murah!</i>",
                        parse_mode='HTML'
                    )
                except: pass

        bot.reply_to(message, reply_msg, parse_mode='HTML')
        
    except ValueError:
        bot.reply_to(message, "❌ Nominal harus angka.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ==========================================
#  2. LIST MEMBER & RESELLER
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "list_member" or call.data.startswith("list_member|"))
def list_member_pagination(call):
    if str(call.from_user.id) != str(ADMIN_ID): 
        return bot.answer_callback_query(call.id, "Akses Ditolak")
    
    if "|" in call.data: page = int(call.data.split("|")[1])
    else: page = 1 

    all_users = get_all_users_list()
    LIMIT = 10
    total_items = len(all_users)
    total_pages = math.ceil(total_items / LIMIT)

    if page > total_pages: page = total_pages
    if page < 1: page = 1

    offset = (page - 1) * LIMIT
    current_users = all_users[offset : offset + LIMIT]

    msg = f"👥 <b>DAFTAR SEMUA MEMBER ({total_items})</b>\n"
    msg += f"📄 Halaman {page} dari {total_pages}\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"

    for i, user in enumerate(current_users, 1):
        uid = user[0]
        try: saldo = int(user[1])
        except: saldo = 0
        try: role = str(user[2]).upper()
        except: role = "USER"
        
        # Ambil Nama & Username (Asumsi index 3=Nama, 4=Username)
        try: nama = user[3] if user[3] else "Unknown"
        except: nama = "Unknown"
        
        try: username = user[4]
        except: username = None

        saldo_fmt = f"Rp {saldo:,}".replace(",", ".")
        online_stat = get_online_icon(uid)
        role_icon = "⚡" if "RESELLER" in role else "👤"
        
        # --- LOGIKA PENGECEKAN USERNAME ---
        # Jika Nama Unknown atau Username Kosong -> Kirim Peringatan
        if nama == "Unknown" or not username:
            warning_sign = "⚠️"
            nama_display = "Unknown (No Username)"
            
            # Kirim Notifikasi ke User (Silent agar tidak spam log admin)
            try:
                pesan_peringatan = (
                    "⚠️ <b>PERINGATAN SISTEM</b>\n\n"
                    "Halo! Kami mendeteksi akun Telegram Anda <b>belum memiliki Username</b> atau nama tidak terbaca.\n\n"
                    "Mohon segera:\n"
                    "1. Buka Pengaturan Telegram\n"
                    "2. Buat/Set <b>Username</b> (contoh: @nama_anda)\n"
                    "3. Ketik /start lagi di bot ini.\n\n"
                    "<i>Hal ini diperlukan agar akun Anda terdata dengan benar di sistem kami. Terima kasih!</i>"
                )
                bot.send_message(uid, pesan_peringatan, parse_mode='HTML')
            except:
                pass # Abaikan jika bot diblokir user
        else:
            warning_sign = ""
            nama_display = nama

        msg += f"<b>{offset + i}. {online_stat} {nama_display} {role_icon} {warning_sign}</b>\n"
        msg += f"   🆔 <code>{uid}</code> | 💰 {saldo_fmt}\n"
        msg += f"   ────────────────\n"

    markup = InlineKeyboardMarkup()
    nav_btns = []
    if page > 1: nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"list_member|{page-1}"))
    nav_btns.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages: nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"list_member|{page+1}"))

    markup.row(*nav_btns)
    markup.add(InlineKeyboardButton("🔙 KEMBALI MENU", callback_data="switch_owner"))

    try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except ApiTelegramException: pass

@bot.callback_query_handler(func=lambda call: call.data == "list_reseller" or call.data.startswith("list_reseller|"))
def list_reseller_pagination(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    if "|" in call.data: page = int(call.data.split("|")[1])
    else: page = 1 

    all_users = get_all_users_list()
    resellers = [u for u in all_users if 'reseller' in str(u[2]).lower()]
    
    LIMIT = 10
    total_items = len(resellers)
    total_pages = math.ceil(total_items / LIMIT)

    if page > total_pages: page = total_pages
    if page < 1: page = 1
    offset = (page - 1) * LIMIT
    current_users = resellers[offset : offset + LIMIT]

    msg = f"⚡ <b>DAFTAR RESELLER ({total_items})</b>\n"
    msg += f"📄 Halaman {page} dari {total_pages}\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    if not resellers: msg += "\n<i>Belum ada Reseller terdaftar.</i>"

    for i, user in enumerate(current_users, 1):
        uid = user[0]
        try: saldo = int(user[1])
        except: saldo = 0
        try: nama = user[3]
        except: nama = "Unknown"
        saldo_fmt = f"Rp {saldo:,}".replace(",", ".")
        msg += f"<b>{offset + i}. ⚡ {nama}</b>\n"
        msg += f"   🆔 <code>{uid}</code> | 💰 {saldo_fmt}\n"
        msg += f"   ────────────────\n"

    markup = InlineKeyboardMarkup()
    nav_btns = []
    if page > 1: nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"list_reseller|{page-1}"))
    nav_btns.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages: nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"list_reseller|{page+1}"))

    markup.row(*nav_btns)
    markup.add(InlineKeyboardButton("🔙 KEMBALI MENU", callback_data="switch_owner"))
    try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except ApiTelegramException: pass

# ==========================================
#  3. CEK RIWAYAT & DETAIL USER
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "check_user_history" or call.data.startswith("hist_page|"))
def check_user_history_pagination(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    if "hist_page|" in call.data: page = int(call.data.split("|")[1])
    else: page = 1 

    all_users = get_all_users_list()
    LIMIT = 10
    total_items = len(all_users)
    total_pages = math.ceil(total_items / LIMIT)

    if page > total_pages: page = total_pages
    if page < 1: page = 1
    offset = (page - 1) * LIMIT
    current_users = all_users[offset : offset + LIMIT]

    msg = f"🔎 <b>CARI USER & RIWAYAT ({total_items})</b>\n"
    msg += f"📄 Halaman {page} dari {total_pages}\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"

    markup = InlineKeyboardMarkup(row_width=5) 
    btn_numbers = []

    for i, user in enumerate(current_users, 1):
        uid = user[0]
        try: nama = user[3]
        except: nama = "Unknown"
        msg += f"<b>[{i}] {nama}</b> (ID: {uid})\n"
        btn_numbers.append(InlineKeyboardButton(str(i), callback_data=f"hist_{uid}"))

    msg += "\n<i>👇 Klik nomor user untuk melihat detail:</i>"
    markup.add(*btn_numbers)

    nav_btns = []
    if page > 1: nav_btns.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"hist_page|{page-1}"))
    nav_btns.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages: nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"hist_page|{page+1}"))

    markup.row(*nav_btns)
    markup.add(InlineKeyboardButton("🔙 KEMBALI MENU", callback_data="switch_owner"))
    try: bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except ApiTelegramException: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("hist_"))
def detail_user_history(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    if "page" in call.data: return
    
    uid = call.data.split("_")[1]
    user = find_user(uid) 
    if not user: return bot.answer_callback_query(call.id, "❌ Data user tidak ditemukan", show_alert=True)
    
    try:
        u_id = user[0]
        if isinstance(user[1], int) or isinstance(user[1], float):
             u_saldo, u_role, u_nama = user[1], user[2], user[3]
        else:
             u_nama, u_saldo, u_role = user[1], user[2], user[3]
    except:
        u_id, u_nama, u_saldo, u_role = uid, "Unknown", 0, "User"

    raw_hist = get_user_transaction_history(uid)
    hist_txt = ""
    if raw_hist:
        for trx in raw_hist[:5]:
            hist_txt += f"• <code>{trx[0]}</code> | {trx[1]}\n"
    else: hist_txt = "<i>Belum ada riwayat transaksi.</i>"
    
    full_msg = (
        f"🔎 <b>DETAIL PENGGUNA</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Nama  : <b>{u_nama}</b>\n🆔 ID    : <code>{u_id}</code>\n"
        f"🔰 Role  : {str(u_role).upper()}\n💰 Saldo : <b>Rp {u_saldo:,}</b>\n\n"
        f"📜 <b>5 RIWAYAT TERAKHIR:</b>\n{hist_txt}"
    )
    
    m = InlineKeyboardMarkup()
    m.row(InlineKeyboardButton("➕ Isi Saldo", callback_data=f"saldo_add_shortcut|{u_id}"), 
          InlineKeyboardButton("➖ Potong", callback_data=f"saldo_min_shortcut|{u_id}"))
          
    if 'reseller' not in str(u_role).lower():
        m.add(InlineKeyboardButton("⚡ Angkat Jadi Reseller", callback_data=f"set_reseller|{u_id}"))
        
    m.add(InlineKeyboardButton("🔙 KEMBALI KE LIST", callback_data="check_user_history"))
    bot.edit_message_text(full_msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

# ==========================================
#  4. FITUR ANGKAT RESELLER (MANUAL BY ADMIN)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "manual_add_reseller")
def manual_add_reseller_start(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ BATAL", callback_data="switch_owner"))
    msg = bot.send_message(call.message.chat.id, "<b>⚡ ANGKAT RESELLER MANUAL</b>\n\nSilakan kirim <b>ID Telegram</b> user yang ingin dijadikan Reseller:", parse_mode='HTML', reply_markup=markup)
    bot.register_next_step_handler(msg, process_manual_upgrade_reseller)

def process_manual_upgrade_reseller(message):
    target_id = message.text.strip()
    if not target_id.isdigit(): return bot.reply_to(message, "❌ ID harus angka.")
    user = find_user(target_id)
    if not user: return bot.reply_to(message, f"❌ User ID {target_id} tidak ditemukan.")
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✅ YA, ANGKAT", callback_data=f"set_reseller|{target_id}"),
               InlineKeyboardButton("❌ BATAL", callback_data="switch_owner"))
    bot.send_message(message.chat.id, f"Konfirmasi angkat Reseller untuk ID <code>{target_id}</code>?", parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_reseller|"))
def execute_upgrade_reseller_manual(call):
    target_id = call.data.split("|")[1]
    set_role(target_id, 'reseller')
    set_reseller_start(target_id)
    bot.answer_callback_query(call.id, "✅ Sukses Upgrade Reseller!", show_alert=True)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="switch_owner"))
    bot.send_message(call.message.chat.id, f"✅ <b>BERHASIL!</b>\nUser <code>{target_id}</code> telah resmi diangkat menjadi <b>RESELLER</b>.", parse_mode='HTML', reply_markup=markup)
    
    try: bot.send_message(target_id, "🎉 <b>SELAMAT!</b>\nAkun Anda telah diupgrade menjadi <b>RESELLER</b>.")
    except: pass

# ==========================================
#  5. BROADCAST SYSTEM
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "broadcast_menu")
def broadcast_ask(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    
    msg_text = (
        "<b>📢 BROADCAST MESSAGE</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Silakan kirim pesan yang ingin disebarkan ke seluruh member.\n\n"
        "<b>Support Format:</b>\n"
        "📝 Teks (HTML/Markdown)\n"
        "📸 Gambar / Foto / Video\n"
        "📂 File / Dokumen / Apk\n"
        "🤡 Sticker / GIF\n"
        "🎙 Audio / Voice Note\n\n"
        "<i>👇 Kirim pesan Anda sekarang atau tekan Batal.</i>"
    )
    
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("❌ BATAL KEMBALI", callback_data="broadcast_cancel"))
    
    try: sent_msg = bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
    except: sent_msg = bot.send_message(call.message.chat.id, msg_text, parse_mode='HTML', reply_markup=m)
        
    bot.register_next_step_handler(sent_msg, broadcast_process)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_cancel")
def broadcast_cancel_handler(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.answer_callback_query(call.id, "Broadcast dibatalkan")
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="setting_menu"))
    bot.edit_message_text("❌ <b>Broadcast Dibatalkan.</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

def broadcast_process(message):
    if message.content_type == 'text' and message.text.startswith('/'):
        bot.reply_to(message, "❌ Broadcast dibatalkan karena Anda mengirim command.")
        return
        
    all_users = get_all_ids() 
    total_users = len(all_users)
    
    status_msg = bot.reply_to(message, f"⏳ <b>Memulai Broadcast...</b>\nTarget: {total_users} User\n<i>Mohon tunggu...</i>", parse_mode='HTML')
    
    success = 0
    failed = 0
    start_time = time.time()
    
    for i, uid in enumerate(all_users, 1):
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            failed += 1
            
        if i % 20 == 0 or i == total_users:
            try:
                bot.edit_message_text(
                    f"🚀 <b>Sedang Mengirim...</b>\n"
                    f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"✅ Sukses : {success}\n"
                    f"❌ Gagal  : {failed}\n"
                    f"📊 Progress: {i}/{total_users}",
                    chat_id=message.chat.id, 
                    message_id=status_msg.message_id,
                    parse_mode='HTML'
                )
            except: pass
        time.sleep(0.05) 
        
    duration = round(time.time() - start_time, 2)
    
    report_text = (
        f"✅ <b>BROADCAST SELESAI</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👥 Total Target : {total_users}\n"
        f"✅ Terkirim      : <b>{success}</b>\n"
        f"❌ Gagal         : <b>{failed}</b>\n"
        f"⏱ Durasi        : {duration} detik\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="setting_menu"))
    
    try: bot.delete_message(message.chat.id, status_msg.message_id)
    except: pass
    
    bot.reply_to(message, report_text, parse_mode='HTML', reply_markup=m)

# ==========================================
#  6. SHORTCUT ACTIONS & SELF REGISTER RESELLER
# ==========================================
@bot.callback_query_handler(func=lambda call: "saldo_add_shortcut" in call.data)
def shortcut_add_saldo(call):
    target_id = call.data.split("|")[1]
    msg = bot.send_message(call.message.chat.id, f"➕ <b>ISI SALDO MANUAL</b>\nTarget ID: <code>{target_id}</code>\n\nMasukkan Nominal (Tanpa Titik):", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_saldo_add_step2, target_id)

@bot.callback_query_handler(func=lambda call: "saldo_min_shortcut" in call.data)
def shortcut_deduct_saldo(call):
    target_id = call.data.split("|")[1]
    msg = bot.send_message(call.message.chat.id, f"➖ <b>POTONG SALDO MANUAL</b>\nTarget ID: <code>{target_id}</code>\n\nMasukkan Nominal Potongan:", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_saldo_deduct_shortcut, target_id)

def process_saldo_deduct_shortcut(message, target_id):
    try:
        amount = int(message.text.replace(".","").replace(",",""))
        add_balance(target_id, -amount, "Potong Saldo Admin")
        bot.reply_to(message, f"✅ Berhasil memotong <b>Rp {amount:,}</b> dari user {target_id}", parse_mode='HTML')
    except: bot.reply_to(message, "❌ Gagal. Pastikan nominal angka.")

# ----------------------------------------------
#  FITUR SELF-REGISTER RESELLER (VERSI FINAL)
# ----------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == "register_reseller")
def register_reseller_prompt(call):
    uid = call.from_user.id
    user = get_user_data(uid)
    
    if not user: 
        return bot.answer_callback_query(call.id, "❌ Error: Data user tidak ditemukan.")
    
    current_role = str(user.get('role', 'user')).lower()
    saldo = int(user.get('balance', 0))

    # --- LOGIKA PENGECEKAN STATUS ---
    is_owner = (str(uid) == str(ADMIN_ID)) or ('owner' in current_role)
    is_reseller = 'reseller' in current_role

    # Jika OWNER atau RESELLER -> Tampilkan pesan spesial (Tanpa Cek Saldo)
    if is_owner or is_reseller:
        status_label = "OWNER (BOS BESAR)" if is_owner else "RESELLER"
        
        pesan_kocak = (
            f"✅ <b>STATUS: {status_label}</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"<i>Halo Bos! Status Anda saat ini sudah <b>{status_label}</b>, yang mencakup akses Owner, Reseller, dan Member sekaligus.\n\n"
            "Jadi tidak perlu daftar lagi ya... Ayo transaksi sebanyak-banyaknya "
            "untuk mendapatkan bonus menarik dari diri sendiri yang baik hati... wkwkwk 🤣</i>"
        )
        
        markup = InlineKeyboardMarkup()
        # Jika Owner, kembali ke Owner Menu
        back_data = "switch_owner" if is_owner else "switch_user"
        markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data=back_data))
        
        bot.edit_message_text(pesan_kocak, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        return

    # --- KONDISI 2: MEMBER BIASA, CEK SALDO ---
    if saldo < BIAYA_DAFTAR_RESELLER:
        kurang = BIAYA_DAFTAR_RESELLER - saldo
        msg = (
            f"⚠️ <b>SALDO TIDAK CUKUP</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"💸 Biaya Daftar: Rp {BIAYA_DAFTAR_RESELLER:,}\n"
            f"💰 Saldo Anda : Rp {saldo:,}\n"
            f"❌ Kekurangan : <b>Rp {kurang:,}</b>\n\n"
            f"<i>Silakan isi saldo dulu minimal Rp {BIAYA_DAFTAR_RESELLER:,} biar bisa gabung jadi Reseller.</i>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ ISI SALDO SEKARANG", callback_data="topup"))
        markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_user"))
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        return

    # --- KONDISI 3: SALDO CUKUP, KONFIRMASI PEMBAYARAN ---
    msg = (
        f"⚡ <b>KONFIRMASI UPGRADE RESELLER</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"Saldo kamu cukup nih! Yakin mau upgrade jadi RESELLER?\n\n"
        f"💸 Biaya: <b>Rp {BIAYA_DAFTAR_RESELLER:,}</b>\n"
        f"✅ <i>Saldo otomatis terpotong.</i>"
    )
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ GAS BAYAR!", callback_data="fix_reg_reseller"),
        InlineKeyboardButton("❌ GAK JADI", callback_data="switch_user")
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "fix_reg_reseller")
def register_reseller_execute(call):
    uid = call.from_user.id
    user = get_user_data(uid)
    saldo = int(user.get('balance', 0))

    # Double check saldo
    if saldo < BIAYA_DAFTAR_RESELLER:
        return bot.answer_callback_query(call.id, "❌ Saldo tidak cukup.", show_alert=True)

    try:
        add_balance(uid, -BIAYA_DAFTAR_RESELLER, "Daftar Reseller Mandiri")
        set_role(uid, 'reseller')
        set_reseller_start(uid)

        pesan_sukses = (
            "🎉 <b>SELAMAT! UPGRADE BERHASIL</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "✅ Status: ⚡ <b>RESELLER</b>\n\n"
            "<i>Kamu sudah menjadi reseller ...ayo transaksi sebanyak banyak nya "
            "untuk mendapat kan bonus menarik dari admin yang baik hati dan sedikit kikir ...wkakaka 🤣</i>"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 MENU RESELLER", callback_data="switch_reseller"))
        
        bot.edit_message_text(pesan_sukses, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        print(f"DEBUG: User {uid} Sukses Upgrade Reseller")

    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {e}")
        
@bot.callback_query_handler(func=lambda call: call.data == "check_user_by_id_menu")
def ask_user_id_detail(call):
    # Validasi Admin
    if str(call.from_user.id) != str(ADMIN_ID): 
        return bot.answer_callback_query(call.id, "Akses Ditolak")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ BATAL", callback_data="switch_owner"))
    
    msg = bot.send_message(
        call.message.chat.id, 
        "<b>🔎 CEK DETAIL USER</b>\n\nSilakan kirim <b>ID Telegram</b> user yang ingin Anda cek profil lengkapnya:", 
        parse_mode='HTML', 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_check_user_detail)

def process_check_user_detail(message):
    target_id = message.text.strip()
    
    # Validasi Input Angka
    if not target_id.isdigit():
        return bot.reply_to(message, "❌ ID harus berupa angka.")

    # Ambil Data User
    user = find_user(target_id) # Mengembalikan (id, saldo, role, nama, username)
    user_data = get_user_data(target_id) # Mengembalikan dict lengkap

    if not user and not user_data:
        return bot.reply_to(message, f"❌ User dengan ID <code>{target_id}</code> tidak ditemukan di database.", parse_mode='HTML')

    # Parsing Data (Menggabungkan data dari find_user dan get_user_data untuk kelengkapan)
    try:
        # Jika find_user mengembalikan tuple
        if user and isinstance(user, tuple):
             u_id = user[0]
             # Cek urutan index database Anda (biasanya ID, Saldo, Role, Nama)
             # Sesuaikan jika urutan DB Anda berbeda
             try:
                 u_saldo = int(user[1])
                 u_role = str(user[2]).upper()
                 u_nama = user[3]
             except:
                 # Fallback
                 u_saldo = int(user_data.get('balance', 0))
                 u_role = str(user_data.get('role', 'user')).upper()
                 u_nama = user_data.get('username', 'Unknown')
        else:
             u_id = target_id
             u_saldo = int(user_data.get('balance', 0))
             u_role = str(user_data.get('role', 'user')).upper()
             u_nama = user_data.get('username', 'Unknown')
    except Exception as e:
        print(f"Error parsing user data: {e}")
        return bot.reply_to(message, "❌ Terjadi kesalahan saat membaca data user.")

    # Ambil Status Online
    status_icon = get_online_icon(target_id)
    status_text = "ONLINE" if status_icon == "🟢" else "OFFLINE"

    # Ambil Riwayat Transaksi Terakhir
    history = get_user_transaction_history(target_id)
    hist_text = ""
    if history:
        for trx in history[:5]: # Ambil 5 terakhir
            # Asumsi format trx: (Date, Desc, Amount)
            hist_text += f"• {trx[0]} | {trx[1]}\n"
    else:
        hist_text = "<i>Belum ada riwayat transaksi.</i>"

    # Susun Pesan Laporan Lengkap
    report_msg = (
        f"<b>👤 PROFIL LENGKAP USER</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"🆔 <b>ID:</b> <code>{u_id}</code>\n"
        f"👤 <b>Nama:</b> {u_nama}\n"
        f"🔰 <b>Role:</b> {u_role}\n"
        f"💰 <b>Saldo:</b> Rp {u_saldo:,}\n"
        f"📡 <b>Status:</b> {status_icon} {status_text}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📜 <b>5 TRANSAKSI TERAKHIR:</b>\n"
        f"{hist_text}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"<i>👇 Pilih tindakan untuk user ini:</i>"
    )

    # Tombol Aksi Cepat
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Tambah Saldo", callback_data=f"saldo_add_shortcut|{u_id}"),
        InlineKeyboardButton("➖ Potong Saldo", callback_data=f"saldo_min_shortcut|{u_id}")
    )
    
    # Logika Tombol Role (Jika User biasa -> Tawarkan jadi Reseller, Jika Reseller -> Turunkan)
    if 'RESELLER' not in u_role and 'OWNER' not in u_role:
        markup.add(InlineKeyboardButton("⚡ Jadikan Reseller", callback_data=f"set_reseller|{u_id}"))
    
    markup.add(InlineKeyboardButton("🔙 KEMBALI KE PANEL", callback_data="switch_owner"))

    bot.reply_to(message, report_msg, parse_mode='HTML', reply_markup=markup)
    
# ==========================================
#  HANDLER LAPORAN RESELLER
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "report")
def reseller_report_menu(call):
    """
    Menampilkan menu pilihan laporan untuk Reseller.
    """
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📜 Riwayat Transaksi Saya", callback_data="report_my_trx"))
    markup.add(InlineKeyboardButton("👥 Riwayat Transaksi Downline", callback_data="report_downline_trx"))
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_reseller"))
    
    bot.edit_message_text(
        "📊 <b>MENU LAPORAN RESELLER</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Silakan pilih jenis laporan yang ingin ditampilkan:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "report_my_trx")
def reseller_my_report(call):
    """
    Menampilkan 10 transaksi terakhir milik Reseller itu sendiri.
    """
    uid = call.from_user.id
    history = get_user_transaction_history(uid) # Fungsi yg sudah ada
    
    msg = "<b>📜 RIWAYAT TRANSAKSI SAYA</b>\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    
    if not history:
        msg += "<i>Belum ada transaksi.</i>"
    else:
        for trx in history[:10]:
            # Format: Tanggal | Keterangan | Nominal
            msg += f"✅ {trx[0]} | {trx[1]} | <b>Rp {trx[2]:,}</b>\n"
            msg += "────────────────\n"
            
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="report"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "report_downline_trx")
def reseller_downline_report(call):
    """
    Menampilkan transaksi yang dilakukan oleh User bawahan Reseller.
    Perlu fungsi database khusus: get_reseller_downline_transactions(reseller_id)
    """
    uid = call.from_user.id
    
    # Ambil data dari database (Lihat langkah 3 untuk membuat fungsinya)
    try:
        downline_trx = get_reseller_downline_transactions(uid)
    except:
        downline_trx = []

    msg = "<b>👥 LAPORAN TRANSAKSI DOWNLINE</b>\n"
    msg += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    
    if not downline_trx:
        msg += "<i>Belum ada aktivitas transaksi dari user Anda.</i>"
    else:
        total_omset = 0
        for trx in downline_trx[:15]: # Tampilkan 15 terakhir
            # Asumsi format: (Tanggal, Username Pembeli, Produk, Harga)
            tgl, user_name, produk, harga = trx
            msg += f"👤 <b>{user_name}</b> beli {produk}\n"
            msg += f"🕒 {tgl} | 💰 Rp {harga:,}\n"
            msg += "────────────────\n"
            total_omset += harga
            
        msg += f"\n💰 <b>Total Omset (Halaman ini): Rp {total_omset:,}</b>"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="report"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    
# ==========================================
#  HANDLER BUAT USER BARU (UNTUK RESELLER)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "create_user")
def create_user_start(call):
    """
    Langkah 1: Reseller klik tombol Buat User Baru.
    Bot meminta ID Telegram user yang akan didaftarkan.
    """
    # 1. Validasi Akses (Hanya Reseller & Owner)
    uid = call.from_user.id
    user = get_user_data(uid)
    role = str(user.get('role', 'user')).lower()
    
    if 'reseller' not in role and str(uid) != str(ADMIN_ID):
        return bot.answer_callback_query(call.id, "⛔ Akses Ditolak! Hanya untuk Reseller.", show_alert=True)

    # 2. Kirim Form Input
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ BATAL", callback_data="switch_reseller"))
    
    msg = bot.send_message(
        call.message.chat.id,
        "<b>➕ TAMBAH DOWNLINE BARU</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Silakan kirim <b>ID Telegram</b> calon user yang ingin didaftarkan:\n\n"
        "<i>Tips: Minta user tersebut cek ID mereka di bot atau forward pesan mereka ke sini.</i>",
        parse_mode='HTML',
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_input_new_user_id)

def process_input_new_user_id(message):
    """
    Langkah 2: Memproses ID yang dikirim Reseller.
    """
    try:
        target_id = message.text.strip()
        
        # Validasi Angka
        if not target_id.isdigit():
            msg = bot.reply_to(message, "❌ <b>ID Tidak Valid!</b>\nID Telegram harus berupa angka. Silakan kirim ulang ID yang benar:", parse_mode='HTML')
            bot.register_next_step_handler(msg, process_input_new_user_id)
            return

        # Validasi Panjang ID (Telegram ID biasanya 9-10 digit atau lebih)
        if len(target_id) < 5:
            msg = bot.reply_to(message, "❌ <b>ID Terlalu Pendek!</b> Silakan kirim ID yang valid:", parse_mode='HTML')
            bot.register_next_step_handler(msg, process_input_new_user_id)
            return

        # Lanjut Minta Nama
        msg = bot.reply_to(
            message, 
            f"✅ ID Diterima: <code>{target_id}</code>\n\n"
            "Sekarang kirim <b>NAMA PANGGILAN</b> untuk user ini (Bebas):", 
            parse_mode='HTML'
        )
        bot.register_next_step_handler(msg, process_input_new_user_name, target_id)
        
    except Exception as e:
        bot.reply_to(message, "❌ Terjadi kesalahan. Silakan ulangi dari menu.")

def process_input_new_user_name(message, target_id):
    """
    Langkah 3: Memproses Nama dan Menyimpan ke Database.
    """
    name = message.text.strip()
    reseller_id = message.from_user.id
    
    # Simpan ke Database
    success, info = add_downline_user(target_id, name, reseller_id)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="switch_reseller"))

    if success:
        pesan_sukses = (
            "✅ <b>USER BARU BERHASIL DIBUAT!</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👤 Nama: <b>{name}</b>\n"
            f"🆔 ID: <code>{target_id}</code>\n"
            f"💰 Saldo Awal: Rp 0\n"
            f"⚡ Upline: {message.from_user.first_name}\n\n"
            "<i>User kini sudah terdaftar di bawah jaringan Anda.</i>\n"
            "⚠️ <b>PENTING:</b> Pastikan user tersebut sudah klik <b>/start</b> di bot ini agar bisa bertransaksi."
        )
        bot.reply_to(message, pesan_sukses, parse_mode='HTML', reply_markup=markup)
        
        # Coba kirim notifikasi ke User Baru (Hanya berhasil jika user sudah pernah start bot)
        try:
            bot.send_message(
                target_id,
                f"🎉 <b>SELAMAT DATANG!</b>\n\n"
                f"Akun Anda telah didaftarkan oleh Reseller <b>{message.from_user.first_name}</b>.\n"
                "Silakan ketik /start untuk memuat ulang menu Anda."
            )
        except:
            pass # User mungkin belum pernah start bot (wajar)

    else:
        # Jika Gagal (Misal ID sudah terdaftar)
        bot.reply_to(
            message, 
            f"❌ <b>GAGAL MENAMBAHKAN USER</b>\n\nAlasan: {info}", 
            parse_mode='HTML', 
            reply_markup=markup
        )