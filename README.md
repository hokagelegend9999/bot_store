# 🤖 BOT STORE & VPS MANAGER TELEGRAM

**Bot Store Modular System** adalah solusi lengkap untuk manajemen penjualan produk digital (PPOB), SSH/VPN Tunneling, dan monitoring VPS secara otomatis melalui Telegram.

Dikembangkan dengan Python (`telebot`) dan mendukung manajemen database SQLite serta backup otomatis.

## ✨ Fitur Unggulan

### 🛍️ Store & PPOB
- **Topup Otomatis**: Pulsa, Data, E-Wallet (Integrasi Atlantic/OkeConnect).
- **Produk VPN**: Jual SSH, Vmess, Vless, Trojan, dll secara otomatis.
- **Deposit Saldo**: Sistem saldo member dengan riwayat transaksi.

### 👑 Panel Owner (God Mode)
- **Unlimited Balance**: Akses penuh tanpa batas saldo.
- **Manajemen User**: Tambah/Kurang saldo, Cek Profil, Ban/Unban.
- **Manajemen Reseller**: Angkat reseller, atur harga khusus.
- **Backup & Restore**: Export database (.db & .xlsx) ke Telegram/Email.
- **Broadcast**: Kirim pesan massal ke seluruh member.

### ⚡ Panel Reseller
- **Harga Khusus**: Mendapatkan harga lebih murah untuk dijual kembali.
- **Manajemen Downline**: Mendaftarkan user baru di bawah jaringan reseller.
- **Laporan Transaksi**: Cek riwayat transaksi pribadi dan downline.

### 🖥️ Monitoring VPS
- **Real-time Status**: Cek status service (SSH, Dropbear, Xray, Nginx, dll).
- **Dashboard**: Statistik penggunaan user & uptime server.
- **Control**: Restart service/VPS langsung dari bot.

---

## 🛠️ Cara Install (Auto Install)

Jalankan perintah berikut di Terminal VPS Anda (Wajib **Ubuntu/Debian**):

```bash
apt update && apt install -y git
git clone [https://github.com/hokagelegend9999/bot_store.git](https://github.com/hokagelegend9999/bot_store.git)
cd bot_store
chmod +x install.sh
./install.sh

```

=======================================================

⚙️ Konfigurasi
Setelah instalasi selesai, Anda WAJIB mengedit file konfigurasi untuk memasukkan Token Bot dan API Key Anda.

Buka file config:

Bash

nano config.py
Isi data berikut:

BOT_TOKEN: Token dari @BotFather.

ADMIN_ID: ID Telegram Anda (Owner).

ATLANTIC_API_KEY: API Key Provider PPOB.

SMTP_EMAIL: Email untuk pengiriman backup.

Restart bot setelah edit:

Bash

systemctl restart bot-store
📜 Perintah Berguna
Cek Log (Jika ada error):

Bash

journalctl -u bot-store -f
Stop Bot:

Bash

systemctl stop bot-store
Update Bot (Ambil update terbaru dari GitHub):

Bash

cd /root/bot_store
git pull
systemctl restart bot-store
Developed by Hokage Legend


---

### Apa yang harus Anda lakukan sekarang?

1.  **Di Komputer/VPS Anda saat ini:**
    * Buat file `requirements.txt`.
    * Buat file `install.sh`.
    * Buat file `README.md`.
2.  **Upload ke GitHub:**
    Jalankan perintah ini di folder bot Anda untuk mengupdate GitHub:
    ```bash
    git add .
    git commit -m "Add installer and readme"
    git push origin main
    ```

Setelah itu, jika Anda punya VPS baru, Anda tinggal copy-paste perintah di bagian **"Cara Install"*
