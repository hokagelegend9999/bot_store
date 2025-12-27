import threading
import time
from bot_init import bot
from config import ADMIN_ID
from database import check_and_downgrade_resellers

def auto_check_loop():
    while True:
        try:
            korban = check_and_downgrade_resellers()
            for uid in korban:
                try:
                    bot.send_message(uid, f"⚠️ <b>PERINGATAN</b>\nStatus Reseller dicabut karena target tidak tercapai.", parse_mode='HTML')
                    bot.send_message(ADMIN_ID, f"📉 Downgrade ID {uid}")
                except: pass
            time.sleep(21600) 
        except: time.sleep(60)

def start_background_tasks():
    t = threading.Thread(target=auto_check_loop)
    t.daemon = True
    t.start()