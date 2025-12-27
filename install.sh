#!/bin/bash

# Warna
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}    INSTALLER BOT STORE & VPS MANAGER       ${NC}"
echo -e "${GREEN}         By: Hokage Legend                  ${NC}"
echo -e "${GREEN}============================================${NC}"

# 1. Cek Root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Script ini harus dijalankan sebagai ROOT!${NC}" 
   exit 1
fi

# 2. Update System & Install Dependencies
echo -e "${YELLOW}⚙️  Mengupdate System & Install Paket Dasar...${NC}"
apt update && apt upgrade -y
apt install -y python3 python3-pip git zip unzip jq curl nano

# 3. Setup Direktori Bot
DIR="/root/bot_store"

if [ -d "$DIR" ]; then
  echo -e "${YELLOW}⚠️  Folder $DIR sudah ada. Mengupdate file...${NC}"
  cd $DIR
  git pull
else
  echo -e "${YELLOW}📥 Mengunduh Repository dari GitHub...${NC}"
  # Ganti URL ini jika repository anda private atau berubah
  git clone https://github.com/hokagelegend9999/bot_store.git $DIR
  cd $DIR
fi

# 4. Install Python Library
echo -e "${YELLOW}🐍 Menginstall Library Python...${NC}"
pip3 install -r requirements.txt

# 5. Setup Systemd Service (Auto Start/Restart)
echo -e "${YELLOW}🔌 Membuat Service Auto-Start...${NC}"

cat > /etc/systemd/system/bot-store.service << ENDOFFILE
[Unit]
Description=Bot Store Telegram Otomatis
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bot_store
ExecStart=/usr/bin/python3 /root/bot_store/start.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
ENDOFFILE

# 6. Reload & Start Service
systemctl daemon-reload
systemctl enable bot-store
systemctl start bot-store

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ INSTALASI SELESAI!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "📂 Lokasi Bot: /root/bot_store"
echo -e "📝 Edit Config: nano /root/bot_store/config.py"
echo -e "▶️  Cek Status : systemctl status bot-store"
echo -e "🔄 Restart Bot: systemctl restart bot-store"
echo -e "📜 Cek Logs   : journalctl -u bot-store -f"
echo -e "${GREEN}============================================${NC}"
