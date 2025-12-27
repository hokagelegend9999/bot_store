import sqlite3
import os

# --- NAMA DATABASE YANG BENAR ---
DB_NAME = "store_data.db"

def upgrade_database():
    # Cek apakah file ada
    if not os.path.exists(DB_NAME):
        print(f"❌ File database '{DB_NAME}' tidak ditemukan di folder ini!")
        print("Pastikan Anda menjalankan script ini di folder: /root/bot_store/")
        return

    print(f"🔄 Membuka database: {DB_NAME}...")
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Perintah SQL untuk menambah kolom 'uplink'
        c.execute("ALTER TABLE users ADD COLUMN uplink INTEGER DEFAULT 0")
        
        conn.commit()
        conn.close()
        print("✅ SUKSES! Kolom 'uplink' berhasil ditambahkan.")
        print("Sekarang fitur Reseller Downline sudah bisa digunakan.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ Kolom 'uplink' SUDAH ADA. Tidak perlu update lagi.")
        else:
            print(f"❌ Error SQLite: {e}")
            print("Pastikan tabel 'users' memang ada di database ini.")
    except Exception as e:
        print(f"❌ Error Lain: {e}")

if __name__ == "__main__":
    upgrade_database()