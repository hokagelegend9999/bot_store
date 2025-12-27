import time
import threading
import qrcode
import urllib.parse
import os
import requests
import telebot
from io import BytesIO
from bot_instance import bot
from config import ADMIN_ID, WA_ADMIN, TG_ADMIN, ATLANTIC_API_KEY
from database import add_user, add_balance
from utils_view import get_back_markup
from atlantic import create_deposit_qris, check_deposit_status, cancel_deposit, claim_instant_deposit

# --- TOPUP MENU ---
@bot.callback_query_handler(func=lambda call: call.data == "topup")
def topup_menu(call):
    # ... (Code topup_menu Anda)
    pass

# --- AUTO DEPOSIT ---
@bot.callback_query_handler(func=lambda call: call.data == "topup_auto")
def topup_auto_start(call):
    # ... (Code topup_auto_start Anda)
    pass

def process_topup_atlantic(message):
    # ... (Code process_topup_atlantic Anda)
    # ... Termasuk threading monitor_deposit_loop
    pass

def monitor_deposit_loop(chat_id, user_id, trx_id, message_id):
    # ... (Code looping cek status deposit)
    pass

# --- MANUAL DEPOSIT ---
# ... (Paste code manual deposit disini)