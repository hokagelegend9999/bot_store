import time
import requests
import threading
import qrcode
import urllib.parse
import os
import telebot
from io import BytesIO
from bot_init import bot
from config import ADMIN_ID, ATLANTIC_API_KEY
from constants import ATLANTIC_INSTANT_URL, ATLANTIC_TRANSFER_URL, WA_ADMIN, TG_ADMIN
from database import add_balance
from utils_helper import get_back_markup
from atlantic import create_deposit_qris, check_deposit_status, cancel_deposit

# --- HELPER API ---
def claim_instant_deposit(deposit_id):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'api_key': ATLANTIC_API_KEY, 'id': str(deposit_id), 'action': 'true'}
    try:
        response = requests.post(ATLANTIC_INSTANT_URL, data=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error Instant Depo: {e}")
        return None

# --- TOPUP MENU ---
@bot.callback_query_handler(func=lambda call: call.data == "topup")
def topup_menu(call):
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    
    msg = (
        "<b>💸 PILIH METODE DEPOSIT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Silakan pilih cara pembayaran yang Anda inginkan:\n\n"
        "🤖 <b>OTOMATIS (QRIS / E-Wallet)</b>\n"
        "• Proses Instan (1-5 Menit)\n"
        "• Aktif 24 Jam Non-Stop\n"
        "• Ada Biaya Admin Kecil\n\n"
        "👤 <b>MANUAL (Transfer Admin)</b>\n"
        "• Chat Admin & Kirim Bukti\n"
        "• Proses Tergantung Admin Online\n"
        "• Tanpa Biaya Admin"
    )
    
    m = telebot.types.InlineKeyboardMarkup(row_width=1)
    m.add(telebot.types.InlineKeyboardButton("🤖 OTOMATIS (QRIS)", callback_data="topup_auto"))
    m.add(telebot.types.InlineKeyboardButton("👤 MANUAL (CHAT ADMIN)", callback_data="topup_manual"))
    m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_back"))
    
    bot.send_message(call.message.chat.id, msg, parse_mode='HTML', reply_markup=m)

# --- AUTO DEPOSIT ---
@bot.callback_query_handler(func=lambda call: call.data == "topup_auto")
def topup_auto_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    m = telebot.types.InlineKeyboardMarkup()
    m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="topup"))
    msg = bot.send_message(call.message.chat.id, 
        "<b>🤖 DEPOSIT OTOMATIS (QRIS)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <i>Support DANA, OVO, Shopee, LinkAja, Mobile Banking</i>\n"
        "🔹 Min: Rp 1.000\n"
        "🔹 Max: Rp 5.000.000\n\n"
        "✍️ <b>Masukkan Nominal Deposit:</b>\n"
        "Contoh: <code>20000</code>", 
        parse_mode='HTML', reply_markup=m)
    bot.register_next_step_handler(msg, process_topup_atlantic)

def process_topup_atlantic(message):
    try:
        input_text = message.text.replace('.', '').replace(',', '').strip()
        if input_text.startswith('/'): return 
        if not input_text.isdigit(): return bot.reply_to(message, "❌ Nominal harus angka.")
            
        nominal = int(input_text)
        if nominal < 1000: return bot.reply_to(message, "❌ Minimal Deposit Rp 1.000")
            
        uid = message.from_user.id
        msg_wait = bot.reply_to(message, "⏳ <b>Menghubungkan ke Payment Gateway...</b>", parse_mode='HTML')

        result = create_deposit_qris(nominal, uid)
        try: bot.delete_message(message.chat.id, msg_wait.message_id)
        except: pass

        if result.get('status') == True:
            data = result.get('data', {})
            trx_id = data.get('id')
            qr_string = data.get('qr_string')
            amount = data.get('nominal')
            fee = data.get('fee', 0)
            total_bayar = amount + int(fee)
            expired_at = data.get('expired_at')
            
            qr = qrcode.make(qr_string)
            bio = BytesIO()
            qr.save(bio, 'PNG')
            bio.seek(0)
            
            caption = (
                f"<b>TAGIHAN DEPOSIT QRIS</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 Nominal : <b>Rp {amount:,}</b>\n"
                f"💸 Admin    : <b>Rp {fee}</b>\n"
                f"💵 <b>TOTAL  : Rp {total_bayar:,}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 Reff ID : <code>{trx_id}</code>\n"
                f"⏳ Expired : {expired_at}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<i>Scan QR Code di atas menggunakan E-Wallet atau M-Banking.</i>\n\n"
                f"🔄 <b>Status: Menunggu Pembayaran...</b>"
            )
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🔄 CEK STATUS", callback_data=f"chk_dep_{trx_id}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ BATALKAN", callback_data=f"cancel_dep_{trx_id}"))
            
            sent_msg = bot.send_photo(message.chat.id, bio, caption=caption, parse_mode='HTML', reply_markup=markup)
            
            t = threading.Thread(target=monitor_deposit_loop, args=(message.chat.id, uid, trx_id, sent_msg.message_id))
            t.daemon = True
            t.start()
        else:
            bot.reply_to(message, f"❌ Gagal: {result.get('message')}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error System: {e}")

# --- MONITORING LOOP (UPDATED) ---
def monitor_deposit_loop(chat_id, user_id, trx_id, message_id):
    start_time = time.time()
    paid = False
    
    while time.time() - start_time < 600: 
        result = check_deposit_status(trx_id)
        
        if result.get('status') == True:
            data = result.get('data', {})
            status_trx = data.get('status')
            
            # --- [UPDATE PENTING DISINI] ---
            # Kita ambil 'nominal' (input user), BUKAN 'get_balance' (bersih admin)
            # Agar saldo masuk full sesuai input user.
            amount_to_add = int(data.get('nominal', 0)) 
            
            if status_trx == 'success':
                add_balance(user_id, amount_to_add, f"Deposit QRIS {trx_id}")
                try:
                    bot.edit_message_caption(
                        chat_id=chat_id, message_id=message_id,
                        caption=f"✅ <b>PEMBAYARAN DITERIMA!</b>\n━━━━━━━━━━━━━━━━━━\n💰 Saldo Masuk: <b>Rp {amount_to_add:,}</b>\n📅 {data.get('created_at')}\n━━━━━━━━━━━━━━━━━━\nTerima kasih telah topup.",
                        parse_mode='HTML', reply_markup=get_back_markup()
                    )
                except: pass
                bot.send_message(chat_id, f"🎉 <b>DEPOSIT SUKSES!</b>\nSaldo Rp {amount_to_add:,} telah ditambahkan ke akun Anda.", parse_mode='HTML', reply_markup=get_back_markup())
                paid = True
                break 
                
            elif status_trx == 'expired' or status_trx == 'failed':
                try:
                    bot.edit_message_caption(
                        chat_id=chat_id, message_id=message_id,
                        caption=f"❌ <b>TAGIHAN EXPIRED/GAGAL</b>\nSilakan buat request baru.",
                        parse_mode='HTML', reply_markup=get_back_markup()
                    )
                except: pass
                break 
                
        time.sleep(10) 

# --- MANUAL CHECK (UPDATED) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('chk_dep_'))
def manual_check_deposit(call):
    trx_id = call.data.split("_")[2]
    result = check_deposit_status(trx_id)
    
    if result.get('status') == True:
        status = result['data']['status']
        if status == 'processing':
            bot.answer_callback_query(call.id, "🔄 Mengklaim Pembayaran Instant...", show_alert=False)
            instant_res = claim_instant_deposit(trx_id)
            if instant_res and instant_res.get('status') == True:
                result = instant_res
                status = result['data']['status'] 
        
        if status == 'success':
            # --- [UPDATE PENTING DISINI] ---
            # Sama seperti di atas, pakai 'nominal' agar saldo full
            amount_to_add = int(result['data'].get('nominal', 0))
            
            # Fallback jika nominal 0 (jarang terjadi)
            if amount_to_add == 0: amount_to_add = int(result['data'].get('total_diterima', 0))

            add_balance(call.from_user.id, amount_to_add, f"Deposit QRIS {trx_id}")
            bot.answer_callback_query(call.id, "✅ SUKSES! Saldo Masuk.", show_alert=True)
            try:
                 bot.send_message(call.message.chat.id, f"✅ <b>DEPOSIT BERHASIL</b>\nSaldo Rp {amount_to_add:,} masuk.", parse_mode='HTML', reply_markup=get_back_markup())
            except: pass
            
        elif status == 'pending':
            bot.answer_callback_query(call.id, "⏳ MENUNGGU PEMBAYARAN", show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"Status: {status.upper()}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Gagal koneksi ke Atlantic", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_dep_'))
def manual_cancel_deposit(call):
    trx_id = call.data.split("_")[2]
    check = check_deposit_status(trx_id)
    if check.get('status') == True and (check['data']['status'] == 'success' or check['data']['status'] == 'processing'):
        return bot.answer_callback_query(call.id, "❌ Tidak bisa cancel, Transaksi sedang diproses/sukses!", show_alert=True)
        
    res = cancel_deposit(trx_id)
    if res.get('status') == True:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅ Tagihan Dibatalkan", show_alert=True)
        bot.send_message(call.message.chat.id, "🗑️ Tagihan deposit telah dibatalkan.", reply_markup=get_back_markup())
    else:
        bot.answer_callback_query(call.id, f"Gagal Cancel: {res.get('message')}", show_alert=True)

# --- MANUAL MANUAL ---
@bot.callback_query_handler(func=lambda call: call.data == "topup_manual")
def topup_manual_start(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    m = telebot.types.InlineKeyboardMarkup()
    m.add(telebot.types.InlineKeyboardButton("❌ BATAL", callback_data="topup"))
    msg = bot.send_message(call.message.chat.id, 
        "<b>👤 DEPOSIT MANUAL (ADMIN)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <i>Metode ini membutuhkan konfirmasi manual dari Admin.</i>\n\n"
        "✍️ <b>Masukkan Nominal Deposit:</b>\n"
        "Contoh: <code>50000</code>", 
        parse_mode='HTML', reply_markup=m)
    bot.register_next_step_handler(msg, process_topup_manual)

def process_topup_manual(message):
    try:
        input_text = message.text.replace('.', '').replace(',', '').strip()
        if not input_text.isdigit(): return bot.reply_to(message, "❌ Nominal harus angka.")
        
        amt = int(input_text)
        if amt < 1000: return bot.reply_to(message, "❌ Min Rp 1.000")
        
        uid = message.from_user.id
        pesan_konfirmasi = f"Halo Admin, saya mau deposit Manual.\n🆔 ID: {uid}\n💰 Nominal: Rp {amt:,}"
        wa_link = f"https://wa.me/{WA_ADMIN}?text={urllib.parse.quote(pesan_konfirmasi)}"
        tg_link = f"https://t.me/{TG_ADMIN}"
        
        m = telebot.types.InlineKeyboardMarkup()
        m.add(telebot.types.InlineKeyboardButton("✅ KONFIRMASI WA", url=wa_link))
        m.add(telebot.types.InlineKeyboardButton("✅ KONFIRMASI TG", url=tg_link))
        m.add(telebot.types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_back"))
        
        qris_path = "/root/bot_store/bayar/qris.jpg"
        caption = (
            f"<b>💳 PEMBAYARAN MANUAL</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Nominal: <b>Rp {amt:,}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"1. Scan QRIS di atas / Transfer ke Admin.\n"
            f"2. Klik Tombol Konfirmasi di bawah.\n"
            f"3. Kirim bukti transfer ke Admin."
        )
        
        if os.path.exists(qris_path): 
            with open(qris_path, 'rb') as f: 
                bot.send_photo(message.chat.id, f, caption=caption, parse_mode='HTML', reply_markup=m)
        else: 
            bot.send_message(message.chat.id, "⚠️ QRIS Admin Belum Diupload.\n" + caption, parse_mode='HTML', reply_markup=m)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")