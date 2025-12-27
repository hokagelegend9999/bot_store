import time
import logging
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton 
from bot_init import bot

# --- BACKGROUND TASKS ---
from background_tasks import start_background_tasks

# --- IMPORT MODULE HANDLERS ---
# ATURAN PENTING: Urutan import menentukan prioritas handler.
# 1. Handler Fitur Baru/Spesifik (PPOB) ditaruh paling atas agar tidak tertimpa.
# 2. Handler Produk VPN (SSH, Vmess, dll).
# 3. Handler Navigasi & Payment.
# 4. Handler Admin (Catch-All) WAJIB paling bawah.

# [PRIORITAS 1] Fitur PPOB & Payment
import handlers.ppob      
import handlers.payment
import handlers.handlers_users
# [PRIORITAS 2] Produk VPN
import handlers.ssh
import handlers.vmess
import handlers.vless
import handlers.trojan

# [PRIORITAS 3] Navigasi Umum
import handlers.nav       

# [PRIORITAS TERAKHIR] Admin & Catch-All
import handlers.admin     

if __name__ == "__main__":
    print("🚀 BOT SELLER MODULAR SYSTEM STARTED (start.py)!")
    print("✅ System: Handler PPOB diprioritaskan.")
    
    # ========================================================
    # [FITUR] CEK STATUS RESTART & NOTIFIKASI ADMIN
    # ========================================================
    if os.path.exists("restart_state.json"):
        try:
            print("🔄 Mendeteksi status restart...")
            with open("restart_state.json", "r") as f:
                data = json.load(f)
            
            chat_id = data.get('chat_id')
            msg_id = data.get('message_id')
            
            # 1. Hapus pesan "Mematikan Service..." yang lama agar rapi
            try:
                bot.delete_message(chat_id, msg_id)
            except: 
                pass
            
            # 2. Buat Tombol Kembali ke Panel Owner
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 KEMBALI KE PANEL", callback_data="switch_owner"))
            
            # 3. Kirim Pesan Sukses dengan Tombol
            bot.send_message(
                chat_id, 
                "✅ <b>BOT BERHASIL DI-RESTART!</b>\nSistem kini sudah online kembali.", 
                parse_mode='HTML', 
                reply_markup=markup
            )
            
            # 4. Hapus file jejak agar pesan ini tidak muncul terus menerus
            os.remove("restart_state.json")
            
        except Exception as e:
            print(f"⚠️ Error cek restart status: {e}")
    # ========================================================

    # Jalankan pengecekan reseller otomatis (Background Task)
    try:
        start_background_tasks()
        print("✅ Background Tasks: Running...")
    except Exception as e:
        print(f"⚠️ Warning Background Tasks: {e}")
    
    # Jalankan Bot dengan Auto-Restart (Anti-Crash Loop)
    while True:
        try:
            print("📡 Bot Polling dimulai... (Tekan Ctrl+C untuk STOP)")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except KeyboardInterrupt:
            # Ini menangkap Ctrl+C agar bot benar-benar berhenti jika kita stop manual
            print("\n⛔ Bot dihentikan oleh user (Ctrl+C). Bye!")
            break
        except Exception as e:
            logging.error(f"Bot Polling Error: {e}")
            print(f"❌ Error Connection: {e} | Reconnecting in 5s...")
            time.sleep(5)