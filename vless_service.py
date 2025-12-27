import subprocess
import os
import uuid
import datetime
import time

# --- KONFIGURASI PATH ---
CONFIG_JSON = "/etc/xray/config.json"
DOMAIN_FILE = "/etc/xray/domain"
DB_VLESS = "/etc/vless/.vless.db"
LIMIT_IP_DIR = "/etc/hokage/limit/vless/ip"
QUOTA_DIR = "/etc/vless"
CLASH_DIR = "/var/www/html"

def get_domain():
    try:
        with open(DOMAIN_FILE, 'r') as f:
            return f.read().strip()
    except:
        return subprocess.check_output("curl -sS ipv4.icanhazip.com", shell=True).decode().strip()

def create_vless_user(username, quota_gb, masa_aktif_hari):
    """
    Membuat user VLESS meniru PERSIS script Bash 'addvless'.
    Teknik: Inject },{"id":... tanpa penutup kurawal akhir.
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
        # #& user exp
        # },{"id": "uuid","email": "user"
        
        # Kita susun string yang SAMA PERSIS.
        # Perhatikan: 
        # - \\n untuk baris baru
        # - }},{{ untuk mencetak },{ (karena f-string butuh double kurung)
        # - \" untuk tanda kutip di dalam string
        
        entry_content = f"#& {username} {exp_str}\\n}},{{\"id\": \"{u_uuid}\",\"email\": \"{username}\""
        
        # Perintah SED untuk VMESS TLS (marker: #vless$)
        # format sed: sed -i '/pattern/a\text'
        cmd_sed_ws = f"sed -i '/#vless$/a\\{entry_content}' {CONFIG_JSON}"
        
        # Perintah SED untuk VMESS GRPC (marker: #vlessgrpc$)
        cmd_sed_grpc = f"sed -i '/#vlessgrpc$/a\\{entry_content}' {CONFIG_JSON}"

        # Eksekusi
        subprocess.run(cmd_sed_ws, shell=True, check=True)
        subprocess.run(cmd_sed_grpc, shell=True, check=True)

        # --- 2. UPDATE DATABASE ---
        # Hapus user lama
        subprocess.run(f"sed -i '/\\b{username}\\b/d' {DB_VLESS}", shell=True)
        
        # Convert Quota
        if quota_gb == "Unlimited": quota_bytes = 0
        else: quota_bytes = int(quota_gb) * 1024 * 1024 * 1024
        
        # Tulis ke DB
        limit_ip = 2
        with open(DB_VLESS, "a") as db:
            db.write(f"### {username} {exp_str} {u_uuid} {quota_bytes} {limit_ip}\n")

        # --- 3. BUAT FILE LIMIT IP & QUOTA ---
        os.makedirs(LIMIT_IP_DIR, exist_ok=True)
        with open(f"{LIMIT_IP_DIR}/{username}", "w") as f:
            f.write(str(limit_ip))
            
        os.makedirs(QUOTA_DIR, exist_ok=True)
        with open(f"{QUOTA_DIR}/{username}", "w") as f:
            f.write(str(quota_bytes))

        # --- 4. GENERATE LINK ---
        link_tls = f"vless://{u_uuid}@{domain}:443?path=/vless&security=tls&encryption=none&type=ws#{username}"
        link_ntls = f"vless://{u_uuid}@{domain}:80?path=/vless&encryption=none&type=ws#{username}"
        link_grpc = f"vless://{u_uuid}@{domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={domain}#{username}"

        # --- 5. BUAT FILE CLASH (Format Bash Asli) ---
        try:
            clash_content = f"""
◇━━━━━━━━━━━━━━━━━◇
   Format For Clash
◇━━━━━━━━━━━━━━━━━◇
# Format Vless WS TLS

- name: Vless-{username}-WS TLS
  server: {domain}
  port: 443
  type: vless
  uuid: {u_uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {domain}

# Format Vless WS Non TLS

- name: Vless-{username}-WS (CDN) Non TLS
  server: {domain}
  port: 80
  type: vless
  uuid: {u_uuid}
  cipher: auto
  tls: false
  skip-cert-verify: false
  servername: {domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {domain}
  udp: true

# Format Vless gRPC (SNI)

- name: Vless-{username}-gRPC (SNI)
  server: {domain}
  port: 443
  type: vless
  uuid: {u_uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: grpc
  grpc-opts:
  grpc-mode: gun
    grpc-service-name: vless-grpc

◇━━━━━━━━━━━━━━━━━◇
Link Akun Vless 
◇━━━━━━━━━━━━━━━━━◇
Link TLS      : 
{link_tls}
◇━━━━━━━━━━━━━━━━━◇
Link none TLS : 
{link_ntls}
◇━━━━━━━━━━━━━━━━━◇
Link GRPC     : 
{link_grpc}
◇━━━━━━━━━━━━━━━━━◇
"""
            with open(f"{CLASH_DIR}/vless-{username}.txt", "w") as f:
                f.write(clash_content)
        except: pass

        # --- 6. RESTART SERVICE ---
        subprocess.run("systemctl restart xray", shell=True)
        subprocess.run("systemctl restart nginx", shell=True)

        # --- 7. RETURN DATA ---
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