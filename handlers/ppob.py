import telebot
import math
import logging
import time
from bot_init import bot
from config import ADMIN_ID
from database import get_user_data, add_balance, increment_reseller_trx
from utils_helper import get_back_markup
import random
import re
# Import service 
try:
    from orderkuota_service import request_orderkuota_trx, get_okeconnect_price, check_orderkuota_status
except ImportError:
    from orderkuota_service import request_orderkuota_trx, get_okeconnect_price
    check_orderkuota_status = None 

# --- KONFIGURASI ---
logger = logging.getLogger(__name__)
MARKUP_PPOB = 3000      
ITEMS_PER_PAGE = 10     

# ==========================================
# 1. MENU KATEGORI
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "ppob_orderkuota")
def ppob_orderkuota_categories(call):
    try:
        bot.answer_callback_query(call.id)
        
        uid = call.from_user.id
        user = get_user_data(uid)
        balance = user['balance'] if user else 0
        user_label = "👑 OWNER" if str(uid) == str(ADMIN_ID) else f"👤 {call.from_user.first_name}"
        
        m = telebot.types.InlineKeyboardMarkup(row_width=2)
        
        btn_pulsa = telebot.types.InlineKeyboardButton("📱 ISI PULSA (ALL OP)", callback_data="show_list|PULSA|1")
        btn_pln   = telebot.types.InlineKeyboardButton("⚡ TOKEN LISTRIK PLN", callback_data="show_list|PLN|1")
        m.add(btn_pulsa)
        m.add(btn_pln)
        
        m.add(telebot.types.InlineKeyboardButton("⬇️  PAKET DATA INTERNET  ⬇️", callback_data="ignore"))

        providers = [
            ("🔴 TELKOMSEL", "TELKOMSEL"), 
            ("🟡 INDOSAT", "INDOSAT"),
            ("🔵 XL AXIATA", "KUOTA XL"), 
            ("🟣 AXIS", "AXIS"),
            ("⚫ TRI (3)", "KUOTA TRI"),      
            ("⚪ SMARTFREN", "SMARTFREN")
        ]
        
        prov_buttons = []
        for label, keyword in providers:
            prov_buttons.append(telebot.types.InlineKeyboardButton(label, callback_data=f"show_list|{keyword}|1"))
        
        m.add(*prov_buttons)
        m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI KE MENU UTAMA", callback_data="menu_back"))
        
        msg_text = (
            "<b>🏪 PPOB STORE & TOPUP CENTER</b>\n"
            "<i>Termurah • Cepat • Otomatis 24 Jam</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"{user_label}\n"
            f"💰 <b>Saldo:</b> <code>Rp {balance:,}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <i>Silakan pilih kategori layanan:</i>"
        )
        
        if call.message.content_type != 'text':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, msg_text, parse_mode='HTML', reply_markup=m)
        else:
            bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)
            
    except Exception as e:
        logger.error(f"Error Menu PPOB: {e}")

# ==========================================
# 2. LIST PRODUK
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("show_list|"))
def ppob_show_pricelist(call):
    try:
        parts = call.data.split("|")
        keyword = parts[1].upper()
        page = int(parts[2])
        
        if page == 1:
            bot.edit_message_text(f"⏳ <b>Sedang mengambil data {keyword}...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        data_harga = get_okeconnect_price()
        
        if not data_harga:
            return bot.edit_message_text("❌ Gagal terhubung ke server pusat.", call.message.chat.id, call.message.message_id, reply_markup=get_back_markup())

        filtered_items = []
        for item in data_harga:
            full_text = (
                str(item.get('kategori', '')) + 
                str(item.get('produk', '')) + 
                str(item.get('keterangan', ''))
            ).upper()
            
            if keyword in full_text:
                if keyword == "KUOTA TRI" and ("LISTRIK" in full_text or "PLN" in full_text):
                    continue
                filtered_items.append(item)
        
        filtered_items.sort(key=lambda x: int(x.get('harga', 0)))

        total_items = len(filtered_items)
        if total_items == 0:
            m_fail = telebot.types.InlineKeyboardMarkup()
            m_fail.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_orderkuota"))
            return bot.edit_message_text(f"❌ Produk <b>{keyword}</b> tidak ditemukan / gangguan.", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m_fail)

        max_page = math.ceil(total_items / ITEMS_PER_PAGE)
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_items = filtered_items[start_idx:end_idx]

        msg_display = f"<b>📋 LIST HARGA: {keyword}</b>\n"
        msg_display += f"<i>Halaman {page} dari {max_page}</i>\n"
        msg_display += "━━━━━━━━━━━━━━━━━━━━━\n\n"

        m = telebot.types.InlineKeyboardMarkup(row_width=5)
        number_buttons = []

        for i, item in enumerate(current_items):
            btn_label = str(i + 1) 
            kode = item.get('kode', 'CODE')
            nama = item.get('keterangan', 'Produk')
            harga_pusat = int(item.get('harga', 0))
            harga_jual = harga_pusat + MARKUP_PPOB
            status_code = str(item.get('status', '0'))
            
            if status_code == '1':
                status_txt = "✅ Ready"
                cb_data = f"ask_num|{kode}|{harga_jual}"
            else:
                status_txt = "🔴 Gangguan"
                cb_data = "prod_empty"

            msg_display += f"<b>[{btn_label}] {nama}</b>\n"
            msg_display += f"💰 Rp {harga_jual:,}\n"
            msg_display += f"📦 Kode: <code>{kode}</code>\n"
            msg_display += f"🔔 Status: {status_txt}\n"
            msg_display += "➖➖➖➖➖➖➖➖➖➖\n"

            number_buttons.append(
                telebot.types.InlineKeyboardButton(btn_label, callback_data=cb_data)
            )

        msg_display += "\n<i>Klik nomor produk di bawah untuk membeli 👇</i>"

        m.add(*number_buttons) 

        nav_btns = []
        if page > 1:
            nav_btns.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"show_list|{keyword}|{page-1}"))
        else:
            nav_btns.append(telebot.types.InlineKeyboardButton("⏹️", callback_data="ignore"))
            
        nav_btns.append(telebot.types.InlineKeyboardButton(f"📄 {page}/{max_page}", callback_data="ignore"))
        
        if page < max_page:
            nav_btns.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"show_list|{keyword}|{page+1}"))
        else:
            nav_btns.append(telebot.types.InlineKeyboardButton("⏹️", callback_data="ignore"))

        m.row(*nav_btns)
        m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI KE KATEGORI", callback_data="ppob_orderkuota"))

        bot.edit_message_text(
            msg_display,
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode='HTML', 
            reply_markup=m
        )

    except Exception as e:
        logger.error(f"Error Pagination: {e}")
        bot.answer_callback_query(call.id, "Terjadi kesalahan sistem.")

# ==========================================
# 3. INTERAKSI INPUT & KONFIRMASI
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore_callback(call):
    bot.answer_callback_query(call.id) 

@bot.callback_query_handler(func=lambda call: call.data == "prod_empty")
def product_empty_alert(call):
    bot.answer_callback_query(call.id, "❌ Maaf, produk ini sedang gangguan/stok habis!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ask_num|"))
def ppob_ask_number(call):
    try:
        bot.answer_callback_query(call.id)
        _, kode, harga = call.data.split("|")
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        is_pln = "PLN" in kode.upper() or "TOKEN" in kode.upper()
        
        if is_pln:
            title_input = "⚡ INPUT ID PELANGGAN (PLN)"
            instruction = "⚠️ <i>Silakan ketik ID PELANGGAN / NO METER:</i>\n(Contoh: 14123456789)"
        else:
            title_input = "📲 INPUT NOMOR HP"
            instruction = "⚠️ <i>Silakan ketik NOMOR HP tujuan:</i>\n(Contoh: 08123456789)"
        
        msg_text = (
            f"<b>{title_input}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Produk:</b> <code>{kode}</code>\n"
            f"💰 <b>Harga:</b> Rp {int(harga):,}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"{instruction}"
        )
        
        msg = bot.send_message(call.message.chat.id, msg_text, parse_mode='HTML')
        bot.register_next_step_handler(msg, ppob_confirmation, kode, harga)
    except Exception as e:
        logger.error(f"Error Ask Num: {e}")

def ppob_confirmation(message, kode, harga):
    try:
        phone = message.text.strip()
        is_pln = "PLN" in kode.upper() or "TOKEN" in kode.upper()

        if not phone.isdigit():
            return bot.reply_to(message, "❌ <b>Format Salah!</b>\nHarap masukkan angka saja.", parse_mode='HTML', reply_markup=get_back_markup())

        if is_pln:
            if len(phone) < 11 or len(phone) > 12:
                return bot.reply_to(message, "❌ <b>ID PLN Tidak Valid!</b>\nPanjang ID PLN harus 11-12 digit.", parse_mode='HTML', reply_markup=get_back_markup())
        else:
            if not phone.startswith("08"):
                return bot.reply_to(message, "❌ <b>Nomor HP Salah!</b>\nHarus diawali '08'.", parse_mode='HTML', reply_markup=get_back_markup())
            if len(phone) < 10 or len(phone) > 14:
                return bot.reply_to(message, "❌ <b>Nomor HP Tidak Valid!</b>\nPeriksa jumlah digit (10-14 angka).", parse_mode='HTML', reply_markup=get_back_markup())
           
        uid = message.from_user.id
        user = get_user_data(uid)
        price_int = int(harga)
        balance = user['balance']
        is_owner = str(uid) == str(ADMIN_ID)
        
        if not is_owner and balance < price_int:
            deficit = price_int - balance
            msg_fail = (
                "⛔ <b>TRANSAKSI DITOLAK</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Maaf, saldo akun Anda tidak mencukupi.</i>\n\n"
                f"💰 <b>Saldo:</b> Rp {balance:,}\n"
                f"🏷 <b>Harga:</b> Rp {price_int:,}\n"
                f"📉 <b>Kurang:</b> <code>Rp {deficit:,}</code>\n\n"
                "💡 <i>Silakan isi saldo terlebih dahulu.</i>"
            )
            m_fail = telebot.types.InlineKeyboardMarkup()
            m_fail.add(telebot.types.InlineKeyboardButton("➕ ISI SALDO SEKARANG", callback_data="topup"))
            m_fail.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_orderkuota"))
            return bot.reply_to(message, msg_fail, parse_mode='HTML', reply_markup=m_fail)
            
        m = telebot.types.InlineKeyboardMarkup()
        m.add(telebot.types.InlineKeyboardButton("✅ BELI SEKARANG", callback_data=f"exec_buy|{kode}|{phone}|{price_int}"))
        m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="menu_back"))
        
        label_tujuan = "ID Pelanggan" if is_pln else "Nomor HP"
        msg_confirm = (
            "<b>🧐 KONFIRMASI TRANSAKSI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Produk:</b> <code>{kode}</code>\n"
            f"⚡ <b>{label_tujuan}:</b> <code>{phone}</code>\n"
            f"💰 <b>Harga:</b> Rp {price_int:,}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Pastikan {label_tujuan.lower()} sudah benar!</i>"
        )
        bot.send_message(message.chat.id, msg_confirm, parse_mode='HTML', reply_markup=m)
        
    except Exception as e:
        logger.error(f"Error Konfirmasi: {e}")

# ==========================================
# 4. EKSEKUSI TRANSAKSI (UPDATED: BAWA DATA HP UNTUK CEK STATUS)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("exec_buy|"))
def ppob_execute_final(call):
    try:
        # Hapus tombol agar tidak double click
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        
        _, kode, phone, price = call.data.split("|")
        price = int(price)
        uid = call.from_user.id
        
        user = get_user_data(uid)
        is_owner = str(uid) == str(ADMIN_ID)
        
        if not is_owner and user['balance'] < price:
             return bot.send_message(call.message.chat.id, "❌ Saldo tidak cukup.")

        add_balance(uid, -price, f"Beli {kode}")
        msg_wait = bot.send_message(call.message.chat.id, "🚀 <b>Sedang Diproses ke Server...</b>", parse_mode='HTML')
        
        ref_id = f"TRX{str(int(time.time()))[-8:]}{random.randint(100,999)}"
        trx_result = request_orderkuota_trx(kode, phone, ref_id)
        
        is_success = trx_result['success']
        pesan_server = trx_result['msg']
        server_id = trx_result.get('server_id') 

        # --- TAMPILAN HASIL (DENGAN TOMBOL KEMBALI) ---
        m_result = telebot.types.InlineKeyboardMarkup()
        if is_success:
            cb_data = f"cs|{server_id if server_id else ''}|{ref_id}|{phone}|{kode}"
            m_result.add(telebot.types.InlineKeyboardButton("🔄 Refresh Status", callback_data=cb_data))
        
        # Tombol Kembali ke Menu PPOB agar tidak macet
        m_result.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI KE MENU PPOB", callback_data="ppob_orderkuota"))

        if not is_success:
            add_balance(uid, price, f"REFUND {kode}")
            bot.edit_message_text(
                f"❌ <b>TRANSAKSI GAGAL</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Ket: {pesan_server}\n\n"
                f"<i>Saldo telah dikembalikan otomatis.</i>",
                call.message.chat.id, msg_wait.message_id, parse_mode='HTML',
                reply_markup=m_result
            )
        else:
            increment_reseller_trx(uid)
            status_emoji = "⏳" if "proses" in pesan_server.lower() else "✅"
            status_header = "TRANSAKSI DIPROSES" if "proses" in pesan_server.lower() else "TRANSAKSI BERHASIL"

            bot.edit_message_text(
                f"{status_emoji} <b>{status_header}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 Produk: {kode}\n"
                f"📱 Tujuan: {phone}\n"
                f"🔑 Server ID: <code>{server_id if server_id else '-'}</code>\n"
                f"🔑 Ref ID: <code>{ref_id}</code>\n\n"
                f"📝 <b>Respon Server:</b>\n{pesan_server}",
                call.message.chat.id, msg_wait.message_id, parse_mode='HTML',
                reply_markup=m_result
            )
            
    except Exception as e:
        logger.error(f"Error Exec: {e}")


# ==========================================
# 5. HANDLER CEK STATUS (UPDATED: SUPPORT SERVER ID)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("cs|"))
def ppob_check_realtime_status(call):
    try:
        parts = call.data.split("|")
        _, srv_val, ref_val, phone_val, kode_val = parts
        
        bot.answer_callback_query(call.id, "🔄 Cek Status...")
        
        # Panggil API Cek Status
        status_server = check_orderkuota_status(
            ref_id=ref_val, 
            server_id=srv_val if srv_val else None, 
            nomor_tujuan=phone_val, 
            kode_produk=kode_val
        )
        
        # Bersihkan pesan
        clean_msg = re.sub(r"Saldo\s*[:=]?\s*[\d\.,]+.*", "", status_server, flags=re.IGNORECASE).strip()
        
        # Logika Parsing (Header & Status)
        resp_lower = status_server.lower()
        if "sukses" in resp_lower or "berhasil" in resp_lower:
            header = "✅ <b>TRANSAKSI SUKSES</b>"
        elif "gagal" in resp_lower or "error" in resp_lower:
            header = "❌ <b>TRANSAKSI GAGAL</b>"
        else:
            header = "⏳ <b>SEDANG DIPROSES</b>"

        msg_update = (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Produk :</b> {kode_val}\n"
            f"📱 <b>Tujuan :</b> {phone_val}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Info Lengkap:</b>\n"
            f"<i>{clean_msg}</i>\n\n"
            f"🕒 <i>Last Check: {time.strftime('%H:%M:%S')}</i>"
        )
        
        m_status = telebot.types.InlineKeyboardMarkup()
        m_status.add(telebot.types.InlineKeyboardButton("🔄 Refresh Status", callback_data=call.data))
        # Tombol Kembali wajib ada di sini
        m_status.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI KE MENU PPOB", callback_data="ppob_orderkuota"))
        
        bot.edit_message_text(msg_update, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m_status)
            
    except Exception as e:
        logger.error(f"Error Cek Status: {e}")