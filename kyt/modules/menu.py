from kyt import *
import subprocess
from telethon import events, Button
from database import get_balance
from config import ADMIN_IDS

# ==========================================
# 1. MENU UTAMA (STORE / TOKO)
# ==========================================
@bot.on(events.NewMessage(pattern=r"(?:.menu|/menu)$"))
@bot.on(events.CallbackQuery(data=b'menu'))
async def menu_store(event):
    # Ambil Data User
    sender = await event.get_sender()
    user_id = sender.id
    full_name = f"{sender.first_name} {sender.last_name or ''}".strip()
    
    # Ambil Saldo dari Database
    saldo = get_balance(user_id)
    
    # Pesan Tampilan Toko
    msg = f"""
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>🛒 STORE SSH & XRAY OTOMATIS</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
👋 Halo, <b>{full_name}</b>!

💰 <b>Saldo Anda:</b> <code>Rp {saldo:,}</code>
🟢 <b>Status Bot:</b> <code>ONLINE</code>

<i>Silakan pilih layanan yang ingin dibeli:</i>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
"""
    # Tombol Menu Toko
    buttons = [
        [Button.inline("🚀 SSH & OVPN", "buy_ssh_menu"), Button.inline("⚡ VMESS", "buy_vmess_menu")],
        [Button.inline("🛡️ VLESS", "buy_vless_menu"), Button.inline("🐎 TROJAN", "buy_trojan_menu")],
        [Button.inline("➕ ISI SALDO (TOPUP)", "topup")],
        [Button.inline("👤 Cek Profil", "info_user")]
    ]

    # KHUSUS ADMIN: Tambahkan tombol ke Panel Dashboard Lama
    if user_id in ADMIN_IDS:
        buttons.append([Button.inline("👑 Owner Dashboard", "admin_dashboard")])

    try:
        await event.edit(msg, buttons=buttons, parse_mode='html')
    except:
        await event.reply(msg, buttons=buttons, parse_mode='html')


# ==========================================
# 2. MENU ADMIN (DASHBOARD LAMA ANDA)
# ==========================================
@bot.on(events.CallbackQuery(data=b'admin_dashboard'))
async def admin_menu(event):
    sender = await event.get_sender()
    user_id = sender.id

    # Proteksi: Jika bukan Admin, tendang ke menu biasa
    if user_id not in ADMIN_IDS:
        await event.answer("⚠️ Menu ini khusus Owner!", alert=True)
        return

    # Loading effect
    await event.answer("Memuat Data Server...", alert=False)

    # --- SCRIPT CEK SERVER (Dari kode lama Anda) ---
    try:
        # -- SSH --
        sh_cmd = "awk -F: '$3 >= 1000 && $1 != \"nobody\" {print $1}' /etc/passwd | wc -l"
        ssh = subprocess.check_output(sh_cmd, shell=True).decode("utf-8").strip()

        # -- VMESS --
        vm_cmd = 'vmc=$(grep -c -E "^### " "/etc/xray/config.json"); echo $((vmc / 2))'
        vms = subprocess.check_output(vm_cmd, shell=True).decode("utf-8").strip()

        # -- VLESS --
        vl_cmd = 'vlx=$(grep -c -E "^#& " "/etc/xray/config.json"); echo $((vlx / 2))'
        vls = subprocess.check_output(vl_cmd, shell=True).decode("utf-8").strip()

        # -- TROJAN --
        tr_cmd = 'trx=$(grep -c -E "^#! " "/etc/xray/config.json"); echo $((trx / 2))'
        trj = subprocess.check_output(tr_cmd, shell=True).decode("utf-8").strip()
        
        # -- OS NAME --
        os_cmd = "cat /etc/os-release | grep -w PRETTY_NAME | head -n1 | sed 's/=//g' | sed 's/PRETTY_NAME//g' | sed 's/\"//g'"
        namaos = subprocess.check_output(os_cmd, shell=True).decode("utf-8").strip()

        # -- IP VPS --
        ipvps = "curl -s ipv4.icanhazip.com"
        ipsaya = subprocess.check_output(ipvps, shell=True).decode("utf-8").strip()

        # -- CITY & ISP --
        try:
            city = subprocess.check_output("cat /root/.info/.city", shell=True).decode("utf-8").strip()
            isp = subprocess.check_output("cat /root/.info/.isp", shell=True).decode("utf-8").strip()
        except:
            city = "Unknown"
            isp = "Unknown"

    except Exception as e:
        ssh = vms = vls = trj = "Err"
        namaos = "Ubuntu"
        ipsaya = "127.0.0.1"
        city = "Unknown"
        isp = "Unknown"

    # TAMPILAN DASHBOARD ADMIN
    msg = f"""
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>🟢 ADMIN DASHBOARD PANEL</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>👤 USER INFORMATION</b>
<code>🆔 ID        :</code> <code>{user_id}</code>
<code>💎 STATUS    :</code> <code>Premium Owner</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>🖥️ SERVER INFORMATION</b>
<code>⚙️ OS        :</code> <code>{namaos}</code>
<code>🌍 CITY      :</code> <code>{city}</code>
<code>🚀 ISP       :</code> <code>{isp}</code>
<code>🌐 DOMAIN    :</code> <code>{DOMAIN}</code>
<code>📶 IP VPS    :</code> <code>{ipsaya}</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>📊 ACCOUNT MANAGER</b>
<code>🟢 SSH OVPN    :</code> <code>{ssh} Account</code>
<code>🟢 XRAY VMESS  :</code> <code>{vms} Account</code>
<code>🟢 XRAY VLESS  :</code> <code>{vls} Account</code>
<code>🟢 XRAY TROJAN :</code> <code>{trj} Account</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>🤖 @HokageLegend</b>
"""
    
    # Tombol-tombol Admin (Management)
    inline = [
        # Tombol management script asli Anda arahkan ke sini
        [Button.inline("Manage SSH","ssh"), Button.inline("Manage VMESS","vmess")],
        [Button.inline("Manage VLESS","vless"), Button.inline("Manage TROJAN","trojan")],
        [Button.inline("SHADOWSOCKS","shadowsocks"), Button.inline("SETTING","setting")],
        [Button.inline("CHECK SERVICE","info")],
        [Button.inline("‹ Kembali ke Toko","menu")]
    ]
    
    await event.edit(msg, buttons=inline, parse_mode='html')