import subprocess
import os
import uuid
import datetime

# --- KONFIGURASI PATH ---
CONFIG_JSON = "/etc/xray/config.json"
DOMAIN_FILE = "/etc/xray/domain"
DB_TROJAN = "/etc/trojan/.trojan.db"
LIMIT_IP_DIR = "/etc/hokage/limit/trojan/ip"
QUOTA_DIR = "/etc/trojan"
CLASH_DIR = "/var/www/html"

def get_domain():
    try:
        with open(DOMAIN_FILE, 'r') as f:
            return f.read().strip()
    except:
        return subprocess.check_output("curl -sS ipv4.icanhazip.com", shell=True).decode().strip()

def create_trojan_user(username, quota_gb, masa_aktif_hari):
    """
    Membuat user TROJAN meniru PERSIS script Bash 'addtr'.
    Teknik: Inject },{"password": "uuid","email": "user"
    """
    try:
        domain = get_domain()
        u_uuid = str(uuid.uuid4())
        
        # Hitung Expired Date
        today = datetime.datetime.now()
        exp_date = today + datetime.timedelta(days=int(masa_aktif_hari))
        exp_str = exp_date.strftime("%Y-%m-%d") 
        
        # --- 1. MANIPULASI CONFIG.JSON (Teknik SED Bash Style) ---
        # Bash Script menyisipkan:
        # #! user exp
        # },{"password": "uuid","email": "user"
        
        entry_content = f"#! {username} {exp_str}\\n}},{{\"password\": \"{u_uuid}\",\"email\": \"{username}\""
        
        # Inject ke TROJAN WS (marker: #trojanws$)
        cmd_sed_ws = f"sed -i '/#trojanws$/a\\{entry_content}' {CONFIG_JSON}"
        
        # Inject ke TROJAN GRPC (marker: #trojangrpc$)
        cmd_sed_grpc = f"sed -i '/#trojangrpc$/a\\{entry_content}' {CONFIG_JSON}"

        # Eksekusi
        subprocess.run(cmd_sed_ws, shell=True, check=True)
        subprocess.run(cmd_sed_grpc, shell=True, check=True)

        # --- 2. UPDATE DATABASE ---
        # Hapus user lama
        subprocess.run(f"sed -i '/\\b{username}\\b/d' {DB_TROJAN}", shell=True)
        
        # Convert Quota
        if quota_gb == "Unlimited": quota_bytes = 0
        else: quota_bytes = int(quota_gb) * 1024 * 1024 * 1024
        
        # Tulis ke DB
        limit_ip = 2
        # Format DB: ### user exp uuid quota iplimit
        with open(DB_TROJAN, "a") as db:
            db.write(f"### {username} {exp_str} {u_uuid} {quota_bytes} {limit_ip}\n")

        # --- 3. BUAT FILE LIMIT IP & QUOTA ---
        os.makedirs(LIMIT_IP_DIR, exist_ok=True)
        with open(f"{LIMIT_IP_DIR}/{username}", "w") as f:
            f.write(str(limit_ip))
            
        os.makedirs(QUOTA_DIR, exist_ok=True)
        with open(f"{QUOTA_DIR}/{username}", "w") as f:
            f.write(str(quota_bytes))

        # --- 4. GENERATE LINK ---
        # Sesuai script bash:
        link_ws = f"trojan://{u_uuid}@{domain}:443?path=%2Ftrojan-ws&security=tls&host={domain}&type=ws&sni={domain}#{username}"
        link_grpc = f"trojan://{u_uuid}@{domain}:443?mode=gun&security=tls&type=grpc&serviceName=trojan-grpc&sni={domain}#{username}"

        # --- 5. BUAT FILE CLASH (Format Bash Asli) ---
        try:
            clash_content = f"""
◇━━━━━━━━━━━━━━━━━◇
   Format For Clash
◇━━━━━━━━━━━━━━━━━◇

# Format Trojan GO/WS

- name: Trojan-{username}-GO/WS
  server: {domain}
  port: 443
  type: trojan
  password: {u_uuid}
  network: ws
  sni: {domain}
  skip-cert-verify: true
  udp: true
  ws-opts:
    path: /trojan-ws
    headers:
        Host: {domain}

# Format Trojan gRPC

- name: Trojan-{username}-gRPC
  type: trojan
  server: {domain}
  port: 443
  password: {u_uuid}
  udp: true
  sni: {domain}
  skip-cert-verify: true
  network: grpc
  grpc-opts:
    grpc-service-name: trojan-grpc
"""
            with open(f"{CLASH_DIR}/trojan-{username}.txt", "w") as f:
                f.write(clash_content)
        except: pass

        # --- 6. RESTART SERVICE ---
        subprocess.run("systemctl restart xray", shell=True)
        # subprocess.run("service cron restart", shell=True) # Opsional

        # --- 7. RETURN DATA ---
        result_data = {
            'username': username,
            'uuid': u_uuid,
            'link_ws': link_ws,
            'link_grpc': link_grpc,
            'domain': domain
        }
        
        return True, "Sukses", result_data

    except Exception as e:
        return False, f"Error System: {str(e)}", {}