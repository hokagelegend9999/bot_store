import subprocess
import math
import os
import telebot
from bot_instance import bot
from config import ADMIN_ID

PATH_KYT = "/root/bot_store/kyt/shell/bot"

@bot.callback_query_handler(func=lambda call: call.data == "check_vps_menu")
def check_vps(call):
    # ... (Code menu cek vps)
    pass

# --- SSH VIEWER ---
def render_ssh_page(chat_id, message_id, page=0):
    # ... (Code render_ssh_page)
    pass

# --- VMESS/VLESS/TROJAN VIEWER ---
# ... (Paste semua logika viewer dan delete disini)