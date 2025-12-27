import sqlite3
import datetime

DB_NAME = "store_data.db"

# --- FUNGSI UTAMA DATABASE ---

def get_connection():
    # check_same_thread=False DIPERLUKAN untuk fitur threading (Anti-Stuck) di start.py
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabel User (Update Struktur)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, 
                  balance INTEGER DEFAULT 0, 
                  role TEXT DEFAULT 'user',
                  first_name TEXT,
                  username TEXT,
                  trx_count INTEGER DEFAULT 0,
                  cycle_date TEXT)''')
    
    # 2. Tabel Transaksi
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  amount INTEGER, 
                  description TEXT, 
                  date TEXT)''')
                  
    # --- MIGRASI OTOMATIS (Mencegah Error "No Such Column") ---
    # Script ini akan otomatis menambahkan kolom jika di database lama belum ada
    
    try: 
        c.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    except: pass
    
    try: 
        c.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except: pass

    try: 
        c.execute("ALTER TABLE users ADD COLUMN trx_count INTEGER DEFAULT 0")
        print("✅ Database: Kolom trx_count berhasil ditambahkan.")
    except: pass

    try: 
        c.execute("ALTER TABLE users ADD COLUMN cycle_date TEXT")
        print("✅ Database: Kolom cycle_date berhasil ditambahkan.")
    except: pass
    
    conn.commit()
    conn.close()

def add_user(user_id, first_name, username):
    conn = get_connection()
    c = conn.cursor()
    res = c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
    if res:
        c.execute("UPDATE users SET first_name=?, username=? WHERE user_id=?", (first_name, username, user_id))
    else:
        # Default trx_count = 0
        c.execute("INSERT INTO users (user_id, balance, role, first_name, username, trx_count) VALUES (?, 0, 'user', ?, ?, 0)", 
                  (user_id, first_name, username))
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = get_connection()
    # Ambil role, balance, dan trx_count
    res = conn.cursor().execute("SELECT role, balance, trx_count FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    # Default return jika user belum ada
    return {"role": res[0], "balance": res[1], "trx": res[2]} if res else {"role": "user", "balance": 0, "trx": 0}

# FUNGSI SALDO + PENCATAT TRANSAKSI
def add_balance(user_id, amount, description="Topup"):
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Update Saldo
    res = c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    if res:
        new_bal = res[0] + amount
        c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_bal, user_id))
    else:
        c.execute("INSERT INTO users (user_id, balance, role, trx_count) VALUES (?, ?, 'user', 0)", (user_id, amount))
    
    # 2. Catat Riwayat Transaksi
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO transactions (user_id, amount, description, date) VALUES (?, ?, ?, ?)", 
              (user_id, amount, description, now))
              
    conn.commit()
    conn.close()

def get_all_users_list():
    conn = get_connection()
    # Ambil semua user urut saldo
    data = conn.cursor().execute("SELECT user_id, balance, role, first_name, username FROM users ORDER BY balance DESC").fetchall()
    conn.close()
    return data

# AMBIL KHUSUS RESELLER
def get_resellers_list():
    conn = get_connection()
    # Ambil data reseller termasuk target transaksi
    data = conn.cursor().execute("SELECT user_id, balance, role, first_name, username, trx_count FROM users WHERE role='reseller' ORDER BY balance DESC").fetchall()
    conn.close()
    return data

# AMBIL RIWAYAT TRANSAKSI (Filter: Hanya Reseller)
def get_reseller_history():
    conn = get_connection()
    query = """
        SELECT t.date, u.first_name, t.description, t.amount 
        FROM transactions t 
        JOIN users u ON t.user_id = u.user_id 
        WHERE u.role = 'reseller' 
        ORDER BY t.id DESC LIMIT 20
    """
    data = conn.cursor().execute(query).fetchall()
    conn.close()
    return data

# AMBIL RIWAYAT TRANSAKSI SPESIFIK USER (Limit 15 Terakhir)
def get_user_transaction_history(user_id):
    conn = get_connection()
    query = "SELECT date, description, amount FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 15"
    data = conn.cursor().execute(query, (user_id,)).fetchall()
    conn.close()
    return data
    
# FUNGSI CARI USER (BY ID ATAU USERNAME)
def find_user(query):
    conn = get_connection()
    c = conn.cursor()
    
    query = str(query).strip().replace("@", "")
    
    if query.isdigit():
        sql = "SELECT user_id, first_name, balance, role, username FROM users WHERE user_id=?"
        data = c.execute(sql, (query,)).fetchone()
    else:
        sql = "SELECT user_id, first_name, balance, role, username FROM users WHERE username LIKE ?"
        data = c.execute(sql, (query,)).fetchone()
        
    conn.close()
    return data 
    
# --- FITUR SISTEM RESELLER ---

# 1. Update Transaksi Reseller (Fix: Pastikan trx_count ada)
def increment_reseller_trx(user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET trx_count = trx_count + 1 WHERE user_id = ? AND role = 'reseller'", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"DB Error Increment: {e}")
    finally:
        conn.close()

# 2. Reset / Set Tanggal Awal Reseller
def set_reseller_start(user_id):
    conn = get_connection()
    c = conn.cursor()
    today = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("UPDATE users SET cycle_date = ?, trx_count = 0 WHERE user_id = ?", (today, user_id))
    conn.commit()
    conn.close()

# 3. Fungsi Cek & Downgrade Otomatis
def check_and_downgrade_resellers():
    conn = get_connection()
    c = conn.cursor()
    
    today = datetime.date.today()
    downgraded_users = []
    
    # Ambil kolom trx_count & cycle_date
    try:
        c.execute("SELECT user_id, trx_count, cycle_date FROM users WHERE role = 'reseller'")
        resellers = c.fetchall()
        
        for r in resellers:
            uid, count, start_date_str = r
            if not start_date_str: continue 
            
            # Jika count None, anggap 0
            if count is None: count = 0
            
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            delta = (today - start_date).days
            
            # Jika sudah lewat 30 hari
            if delta >= 30:
                if count < 5:
                    # GAGAL TARGET -> Downgrade
                    c.execute("UPDATE users SET role = 'user', trx_count = 0, cycle_date = NULL WHERE user_id = ?", (uid,))
                    downgraded_users.append(uid)
                else:
                    # TEMBUS TARGET -> Reset untuk bulan depan
                    new_cycle = today.strftime("%Y-%m-%d")
                    c.execute("UPDATE users SET trx_count = 0, cycle_date = ? WHERE user_id = ?", (new_cycle, uid))
        
        conn.commit()
    except Exception as e:
        print(f"Error Check Reseller: {e}")
        
    conn.close()
    return downgraded_users
    

def get_all_ids():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids

def set_role(user_id, new_role):
    conn = get_connection()
    conn.cursor().execute("UPDATE users SET role=? WHERE user_id=?", (new_role, user_id))
    conn.commit()
    conn.close()

def get_reseller_downline_transactions(reseller_id):
    """
    Mengambil daftar transaksi yang dilakukan oleh user milik reseller tertentu.
    Asumsi: Tabel 'users' punya kolom 'uplink' (reseller_id) dan tabel 'transactions' terhubung ke users.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Query ini menggabungkan tabel transaksi dan users
    # Mencari transaksi dimana user.uplink = reseller_id
    query = """
        SELECT t.date, u.username, t.description, t.amount
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        WHERE u.uplink = ?
        ORDER BY t.date DESC
        LIMIT 20
    """
    try:
        c.execute(query, (reseller_id,))
        result = c.fetchall()
        return result
    except Exception as e:
        print(f"Error get_downline_trx: {e}")
        return []
    finally:
        conn.close()
        
def add_downline_user(target_id, name, reseller_id):
    """
    Mendaftarkan user baru di bawah reseller tertentu.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Cek dulu apakah user sudah ada
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
        if c.fetchone():
            return False, "User sudah terdaftar sebelumnya."

        # Masukkan data baru (Role default: USER, Saldo: 0)
        # Pastikan tabel users Anda punya kolom 'uplink' atau 'reseller_id'
        # Jika belum ada kolom uplink, query ini mungkin perlu disesuaikan atau kolomnya dibuat dulu.
        query = """
        INSERT INTO users (user_id, name, username, role, balance, uplink)
        VALUES (?, ?, 'UserBaru', 'user', 0, ?)
        """
        c.execute(query, (target_id, name, reseller_id))
        conn.commit()
        return True, "Sukses"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
# Jalankan init saat file di-import untuk memastikan tabel lengkap
init_db()