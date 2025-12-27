# handlers_payment.py
import telebot
import requests
import time
from bot_init import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID, ATLANTIC_API_KEY, ATLANTIC_PROFILE_URL, ATLANTIC_TRANSFER_URL
from utils_helper import get_back_markup

# --- API HELPERS ---
def request_atlantic_profile_data():
    try:
        return requests.post(ATLANTIC_PROFILE_URL, data={'api_key': ATLANTIC_API_KEY}, headers={'Content-Type': 'application/x-www-form-urlencoded'}).json()
    except Exception as e: return None

def request_atlantic_transfer(bank, akun, nominal, nama):
    try:
        payload = {'api_key': ATLANTIC_API_KEY, 'ref_id': f"TRF-{int(time.time())}", 'kode_bank': bank, 'nomor_akun': akun, 'nama_pemilik': nama, 'nominal': nominal}
        return requests.post(ATLANTIC_TRANSFER_URL, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'}).json()
    except: return None

# --- HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data == "check_atlantic_profile")
def atlantic_profile_handler(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    res = request_atlantic_profile_data()
    if res and (res.get('status') is True or str(res.get('status')).lower() == 'true'):
        d = res.get('data', {})
        msg = f"<b>🌊 ATLANTIC PROFILE</b>\nName: {d.get('name')}\nSaldo: Rp {d.get('balance'):,}\nStatus: {d.get('status')}"
    else:
        msg = "❌ Gagal mengambil data."
    
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🔄 Refresh", callback_data="check_atlantic_profile"), InlineKeyboardButton("🔙 Kembali", callback_data="setting_menu"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

# --- WITHDRAW / TRANSFER MENU ---
@bot.callback_query_handler(func=lambda call: call.data == "owner_wd_menu")
def wd_menu_start(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🚀 MULAI TRANSFER", callback_data="wd_input_bank"), InlineKeyboardButton("🔙 KEMBALI", callback_data="switch_owner"))
    bot.edit_message_text("<b>💸 TRANSFER DANA</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data == "wd_input_bank")
def wd_step1_bank(call):
    msg = bot.send_message(call.message.chat.id, "1️⃣ Masukkan KODE BANK:", parse_mode='HTML')
    bot.register_next_step_handler(msg, wd_step2_number)

def wd_step2_number(message):
    kode = message.text.strip().upper()
    msg = bot.reply_to(message, f"Bank: {kode}\n2️⃣ Masukkan NO REKENING:")
    bot.register_next_step_handler(msg, wd_step3_nominal, kode)

def wd_step3_nominal(message, kode):
    akun = message.text.strip()
    msg = bot.reply_to(message, "3️⃣ Masukkan NOMINAL:")
    bot.register_next_step_handler(msg, wd_step4_name, kode, akun)

def wd_step4_name(message, kode, akun):
    try: nom = int(message.text.replace(".",""))
    except: return bot.reply_to(message, "Error angka")
    msg = bot.reply_to(message, "4️⃣ Masukkan NAMA PEMILIK:")
    bot.register_next_step_handler(msg, wd_step5_exec, kode, akun, nom)

def wd_step5_exec(message, kode, akun, nom):
    nama = message.text.strip()
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("✅ KIRIM", callback_data=f"wd_fix|{kode}|{akun}|{nom}|{nama}"), InlineKeyboardButton("❌ BATAL", callback_data="owner_wd_menu"))
    bot.send_message(message.chat.id, f"Konfirmasi:\nKe: {nama} ({kode}-{akun})\nRp {nom:,}", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_fix|"))
def wd_process_api(call):
    _, kode, akun, nom, nama = call.data.split("|")
    res = request_atlantic_transfer(kode, akun, int(nom), nama)
    if res and res.get('status'):
        bot.send_message(call.message.chat.id, "✅ Transfer Berhasil", reply_markup=get_back_markup())
    else:
        bot.send_message(call.message.chat.id, f"❌ Gagal: {res.get('message')}", reply_markup=get_back_markup())

# --- CEK SALDO OKE CONNECT (OPTIONAL) ---
try:
    from orderkuota_service import get_okeconnect_profile
except ImportError: get_okeconnect_profile = None

@bot.callback_query_handler(func=lambda call: call.data == "cek_profil_pusat")
def owner_check_provider_profile(call):
    if str(call.from_user.id) != str(ADMIN_ID): return
    if get_okeconnect_profile:
        data = get_okeconnect_profile()
        bot.answer_callback_query(call.id, f"Saldo Pusat: {data}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Service OrderKuota tidak ditemukan", show_alert=True)