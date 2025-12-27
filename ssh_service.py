import subprocess
import datetime
import json
import os

# ==========================================
#  HELPER: SINKRONISASI KE ZIVPN
# ==========================================
def sync_to_zivpn(username, exp_date, limit):
    """
    Menambahkan user baru ke config.json dan user-db.json milik ZIVPN
    Agar bisa connect via UDP 5667
    """
    config_path = "/etc/zivpn/config.json"
    db_path = "/etc/zivpn/user-db.json"
    
    try:
        # 1. UPDATE CONFIG.JSON (AUTH LIST)
        # Cek apakah file config ada
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                try:
                    config_data = json.load(f)
                except:
                    config_data = {"auth": {"config": []}} # Default jika corrupt
            
            # Pastikan struktur JSON valid
            if "auth" not in config_data: config_data["auth"] = {}
            if "config" not in config_data["auth"]: config_data["auth"]["config"] = []
            
            # Tambahkan user jika belum ada di list
            if username not in config_data["auth"]["config"]:
                config_data["auth"]["config"].append(username)
                
                # Simpan kembali
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=2)

        # 2. UPDATE USER-DB.JSON (DETAIL EXP, IP, QUOTA)
        db_data = {}
        if os.path.exists(db_path):
            with open(db_path, 'r') as f:
                try:
                    db_data = json.load(f)
                except:
                    db_data = {} 
            
        # Format data sesuai standar script ZIVPN Bash
        # Quota 0 artinya unlimited di ZIVPN
        db_data[username] = {
            "exp": exp_date,
            "ip": int(limit),
            "quota": 0 
        }
        
        # Simpan kembali
        with open(db_path, 'w') as f:
            json.dump(db_data, f, indent=2)
        
        # 3. RESTART SERVICE ZIVPN
        # Agar perubahan terbaca oleh systemd
        subprocess.run("systemctl restart zivpn", shell=True)
        return True
        
    except Exception as e:
        print(f"❌ Gagal Sync ZIVPN: {e}")
        return False

# ==========================================
#  FUNGSI UTAMA: CREATE USER LINUX
# ==========================================
def create_linux_user(username, password, days=30, limit=2):
    try:
        # 1. Hitung Tanggal Expired (Format YYYY-MM-DD)
        cmd_date = f'date -d "{days} days" +"%Y-%m-%d"'
        exp_date = subprocess.check_output(cmd_date, shell=True).decode().strip()
        
        # 2. Cek apakah user sudah ada di sistem
        check_user = f"id {username}"
        try:
            subprocess.check_output(check_user, shell=True, stderr=subprocess.STDOUT)
            return False, "Username sudah digunakan!", None
        except:
            pass # Lanjut jika user belum ada (aman)

        # 3. Perintah Pembuatan Akun Linux (SSH/Dropbear)
        # useradd: membuat user tanpa shell login
        # passwd: set password
        cmd_create = f'useradd -e {exp_date} -s /bin/false -M {username} && echo "{username}:{password}" | chpasswd'
        subprocess.check_output(cmd_create, shell=True, stderr=subprocess.STDOUT)
        
        # 4. Set Limit IP (Limits.conf)
        # Menambahkan batasan login di /etc/security/limits.conf
        cmd_limit = f'echo "{username} hard maxlogins {limit}" >> /etc/security/limits.conf'
        subprocess.run(cmd_limit, shell=True)
        
        # 5. [PENTING] SINKRONISASI KE ZIVPN
        # Memanggil fungsi helper di atas
        sync_to_zivpn(username, exp_date, limit)
        
        return True, "Sukses", exp_date
        
    except subprocess.CalledProcessError as e:
        try:
            err_msg = e.output.decode()
        except:
            err_msg = str(e)
        return False, f"Error System: {err_msg}", None
        
    except Exception as e:
        return False, f"Error Unknown: {str(e)}", None