import telebot
import subprocess
import time
import requests
from bot_instance import bot
from config import ADMIN_ID, DOMAIN_HOST, ATLANTIC_API_KEY
from database import find_user, add_balance, get_user_data, set_role, set_reseller_start, get_all_ids, get_all_users_list, get_resellers_list, get_user_transaction_history, get_reseller_history
from utils_view import get_back_markup, HARGA_DAFTAR_RESELLER, TARGET_RESELLER

PATH_KYT = "/root/bot_store/kyt/shell/bot"

# --- MANAJEMEN SALDO ---
@bot.callback_query_handler(func=lambda call: call.data == "manage_saldo")
def saldo_menu_handler(call):
    # ... (Code Anda)
    pass

# --- SETTING SERVER (REBOOT/BACKUP) ---
@bot.callback_query_handler(func=lambda call: call.data == "setting_menu")
def setting_menu(call):
    # ... (Code Anda)
    pass

# --- BROADCAST ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast_menu")
def broadcast_ask(call):
    # ... (Code Anda)
    pass
    
def broadcast_process(message):
    # ... (Code Anda)
    pass

# --- WITHDRAW OWNER ---
# ... (Paste code WD Owner disini)