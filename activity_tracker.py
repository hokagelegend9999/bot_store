# activity_tracker.py
import time

# Dictionary untuk menyimpan waktu terakhir user aktif
# Format: {user_id: timestamp}
USER_LAST_SEEN = {}

# Batas waktu dianggap ONLINE (detik)
# 600 detik = 10 menit
TIMEOUT_ONLINE = 600 

def update_user_activity(user_id):
    """Panggil fungsi ini setiap kali user interaksi"""
    USER_LAST_SEEN[user_id] = time.time()

def get_online_icon(user_id):
    """Cek status dan kembalikan icon"""
    last_seen = USER_LAST_SEEN.get(user_id, 0)
    if time.time() - last_seen < TIMEOUT_ONLINE:
        return "🟢" # Online
    else:
        return "⚪" # Offline