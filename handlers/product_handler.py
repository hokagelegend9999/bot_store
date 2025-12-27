import threading
import datetime
import telebot
import subprocess
import requests
from bot_instance import bot
from config import ADMIN_ID, DOMAIN_HOST
from database import get_user_data, add_balance, increment_reseller_trx
from utils_view import get_price, get_back_markup
from ssh_service import create_linux_user
from vless_service import create_vless_user
from vmess_service import create_vmess_user
from trojan_service import create_trojan_user

# --- BAGIAN SSH ---
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
    # ... (Paste logika ssh_input_username Anda disini)
    # ... Panggil bot.register_next_step_handler ke ssh_input_password
    pass 

def ssh_input_password(m, username):
    # ... (Paste logika Anda)
    pass

def ssh_execution(m, u, password, uid, price, status_msg):
    # ... (Paste logika eksekusi SSH Anda disini)
    pass

# --- BAGIAN VMESS, VLESS, TROJAN ---
# Lakukan hal yang sama: Copy fungsi buy_vmess, vmess_process, vmess_execution, dll
# Pastikan semua import (create_vmess_user dll) sudah ada di atas file ini.