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
