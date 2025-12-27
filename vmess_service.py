import subprocess
import os
import uuid
import datetime
import base64
import json

# --- KONFIGURASI PATH ---
CONFIG_JSON = "/etc/xray/config.json"
DOMAIN_FILE = "/etc/xray/domain"
DB_VMESS = "/etc/vmess/.vmess.db"
LIMIT_IP_DIR = "/etc/hokage/limit/vmess/ip"
CLASH_DIR = "/var/www/html"

def get_domain():
    try:
        with open(DOMAIN_FILE, 'r') as f:
            return f.read().strip()
    except:
        # Fallback jika file domain tidak ada, ambil dari ipvps.conf atau IP public
        try:
            cmd = "curl -sS ipv4.icanhazip.com"
            return subprocess.check_output(cmd, shell=True).decode().strip()
        except:
            return "your.domain.com"

def create_vmess_user(username, quota_gb, masa_aktif_hari):
    """
    Membuat user Vmess meniru persis logic script 'addws' bash.
    """
    try:
        domain = get_domain()
        u_uuid = str(uuid.uuid4())
        
        # Hitung Expired Date
        today = datetime.datetime.now()
        exp_date = today + datetime.timedelta(days=int(masa_aktif_hari))
        exp_str = exp_date.strftime("%Y-%m-%d") # Format: 2025-12-15
        
        # --- 1. MANIPULASI CONFIG.JSON MENGGUNAKAN SED (AGAR TIDAK MERUSAK FORMAT) ---
        # Logic Bash Asli:
        # sed -i '/#vmess$/a\### '"$user $exp"'\
        # },{"id": "'""$uuid""'","alterId": '"0"',"email": "'""$user""'"' /etc/xray/config.json
        
        # Kita susun string yang akan disisipkan
        # Perhatikan: Format ini menyisipkan entry baru SEBELUM penutup array sebelumnya (teknik inject json array)
        entry_content = f'### {username} {exp_str}\\n}},{{"id": "{u_uuid}","alterId": 0,"email": "{username}"'
        
        # Perintah SED untuk VMESS TLS (marker: #vmess$)
        cmd_sed_tls = f"sed -i '/#vmess$/a\\{entry_content}' {CONFIG_JSON}"
        
        # Perintah SED untuk VMESS GRPC (marker: #vmessgrpc$)
        cmd_sed_grpc = f"sed -i '/#vmessgrpc$/a\\{entry_content}' {CONFIG_JSON}"

        # Eksekusi SED
        subprocess.run(cmd_sed_tls, shell=True, check=True)
        subprocess.run(cmd_sed_grpc, shell=True, check=True)

        # --- 2. UPDATE DATABASE & LIMIT ---
        # Update .vmess.db (Hapus user lama jika ada, lalu tambah baru)
        try:
            cmd_clean_db = f"sed -i '/\\b{username}\\b/d' {DB_VMESS}"
            subprocess.run(cmd_clean_db, shell=True)
            
            # Convert Quota ke Bytes (GB -> Bytes)
            if quota_gb == "Unlimited": quota_bytes = 0
            else: quota_bytes = int(quota_gb) * 1024 * 1024 * 1024
            
            # Format DB: ### user exp uuid quota iplimit
            entry_db = f"### {username} {exp_str} {u_uuid} {quota_bytes} 2"
            with open(DB_VMESS, "a") as db:
                db.write(entry_db + "\n")
        except Exception as e:
            print(f"Error DB Update: {e}")

        # Limit IP (Default 2 sesuai script)
        try:
            os.makedirs(LIMIT_IP_DIR, exist_ok=True)
            with open(f"{LIMIT_IP_DIR}/{username}", "w") as f:
                f.write("2")
        except: pass

        # --- 3. GENERATE LINK VMESS (BASE64) ---
        # Meniru struktur JSON di script bash (asu, ask, grpc)
        
        # Link 1: WS TLS
        json_tls = {
            "v": "2", "ps": username, "add": domain, "port": "443", "id": u_uuid,
            "aid": "0", "net": "ws", "path": "/vmess", "type": "none", 
            "host": domain, "tls": "tls"
        }
        
        # Link 2: WS Non-TLS
        json_ntls = {
            "v": "2", "ps": username, "add": domain, "port": "80", "id": u_uuid,
            "aid": "0", "net": "ws", "path": "/vmess", "type": "none", 
            "host": domain, "tls": "none"
        }
        
        # Link 3: GRPC
        json_grpc = {
            "v": "2", "ps": username, "add": domain, "port": "443", "id": u_uuid,
            "aid": "0", "net": "grpc", "path": "vmess-grpc", "type": "none", 
            "host": domain, "tls": "tls"
        }

        # Encode ke Base64
        link_tls = "vmess://" + base64.b64encode(json.dumps(json_tls).encode()).decode()
        link_ntls = "vmess://" + base64.b64encode(json.dumps(json_ntls).encode()).decode()
        link_grpc = "vmess://" + base64.b64encode(json.dumps(json_grpc).encode()).decode()

        # --- 4. BUAT FILE CLASH (Opsional, meniru script asli) ---
        try:
            clash_content = f"""
- name: Vmess-{username}-WS TLS
  type: vmess
  server: {domain}
  port: 443
  uuid: {u_uuid}
  alterId: 0
  cipher: auto
  udp: true
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: ws
  ws-opts:
    path: /vmess
    headers:
      Host: {domain}
"""
            with open(f"{CLASH_DIR}/vmess-{username}.txt", "w") as f:
                f.write(clash_content)
        except: pass

        # --- 5. RESTART SERVICE ---
        subprocess.run("systemctl restart xray", shell=True)
        # subprocess.run("service cron restart", shell=True) # Opsional

        # --- 6. RETURN DATA KE BOT ---
        result_data = {
            'username': username,
            'uuid': u_uuid,
            'link_tls': link_tls,
            'link_ntls': link_ntls,
            'link_grpc': link_grpc,
            'domain': domain
        }
        
        return True, "Sukses", result_data

    except Exception as e:
        return False, f"Error System: {str(e)}", {}