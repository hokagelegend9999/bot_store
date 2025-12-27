import re
import time
import subprocess
import datetime as DT
from telethon import events, Button

# Pastikan handler ini ada di file bot utama Anda
@bot.on(events.CallbackQuery(data=b'create-vless'))
async def create_vless(event):
    # Cek Validitas User (Admin/Reseller)
    sender = await event.get_sender()
    chat = event.chat_id
    
    # Fungsi pengecekan izin (sesuai kode Anda)
    if valid(str(sender.id)) != "true":
        return await event.answer("Akses Ditolak / Access Denied", alert=True)

    # Mulai Percakapan Input Data
    async with bot.conversation(chat) as conv:
        try:
            # 1. Input Username
            await conv.send_message('**Masukkan Username VLESS:**\n*(Hanya huruf dan angka)*')
            response_user = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = response_user.raw_text.strip()
            
            # Validasi username sederhana (opsional)
            if not re.match("^[a-zA-Z0-9]+$", user):
                return await conv.send_message("❌ **Username tidak valid!** Jangan gunakan spasi atau simbol.")

            # 2. Input Quota
            await conv.send_message(f"**Masukkan Quota untuk {user} (GB):**\n*(Contoh: 10)*")
            response_pw = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            pw = response_pw.raw_text.strip()

            # 3. Input Expired (Button)
            msg_exp = await conv.send_message(
                f"**Pilih Masa Aktif untuk {user}:**",
                buttons=[
                    [Button.inline("3 Hari", "3"), Button.inline("7 Hari", "7")],
                    [Button.inline("30 Hari", "30"), Button.inline("60 Hari", "60")]
                ]
            )
            response_exp = await conv.wait_event(events.CallbackQuery)
            exp = response_exp.data.decode("ascii")
            
            # Hapus pesan pilihan agar rapi
            await msg_exp.delete()

            # --- PROSES LOADING (Sesuai style Anda) ---
            status_msg = await conv.send_message("`Processing...`")
            loading_bar = [
                "Processing... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
                "Processing... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
                "Processing... 50%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒",
                "Processing... 80%\n█████████████████████▒▒▒▒",
                "Processing... 100%\n█████████████████████████"
            ]
            
            for bar in loading_bar:
                await status_msg.edit(f"`{bar}`")
                time.sleep(0.5)
            
            await status_msg.edit("`Wait.. Generating VLESS Account`")

            # --- EKSEKUSI SCRIPT VPS ---
            # Perintah disesuaikan dengan input: user, exp, quota
            cmd = f'printf "%s\n" "{user}" "{exp}" "{pw}" | addvless-bot'
            
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            output = stdout.decode("utf-8")
            
            # Cek jika error atau user sudah ada
            if "Error" in output or "exist" in output.lower():
                await status_msg.delete()
                return await conv.send_message(f"❌ **Gagal:** User `{user}` mungkin sudah ada atau terjadi kesalahan sistem.")

            # --- PARSING OUTPUT (REGEX LEBIH AMAN) ---
            # Mencari link VLESS dalam output
            vless_links = re.findall(r"vless://[^\s]+", output)
            
            if len(vless_links) >= 1:
                link_tls = vless_links[0]
                # Coba cari link non-tls dan grpc jika ada
                link_ntls = vless_links[1] if len(vless_links) > 1 else "Link Not Found"
                link_grpc = vless_links[2] if len(vless_links) > 2 else "Link Not Found"
                
                # Ambil UUID dari link pertama
                try:
                    uuid = re.search(r"vless://(.*?)@", link_tls).group(1)
                except:
                    uuid = "Unknown"

                # Hitung tanggal expired
                today = DT.date.today()
                later = today + DT.timedelta(days=int(exp))

                # --- FORMAT PESAN SUKSES ---
                msg = f"""
**━━━━━━━━━━━━━━━━━**
** 🔮 VLESS ACCOUNT 🔮**
**━━━━━━━━━━━━━━━━━**
**» Remarks      :** `{user}`
**» Domain       :** `{DOMAIN}`
**» User Quota   :** `{pw} GB`
**» Expiry Days  :** `{exp} Days`
**» Expired Date :** `{later}`
**» UUID         :** `{uuid}`
**━━━━━━━━━━━━━━━━━**
**» Port TLS     :** `443`
**» Port NTLS    :** `80`
**» Network      :** `WS / GRPC`
**━━━━━━━━━━━━━━━━━**
**» LINK TLS :**
`{link_tls}`
**━━━━━━━━━━━━━━━━━**
**» LINK NTLS :**
`{link_ntls}`
**━━━━━━━━━━━━━━━━━**
**» LINK GRPC :**
`{link_grpc}`
**━━━━━━━━━━━━━━━━━**
**» Format OpenClash :** `https://{DOMAIN}:81/vless-{user}.txt`
**━━━━━━━━━━━━━━━━━**
**» 🤖 Created By @HokageLegend**
"""
                await status_msg.delete()
                await conv.send_message(msg)
            else:
                await status_msg.edit("⚠️ **Error Parsing:** Output script tidak mengeluarkan link Vless yang valid.")
                # Debugging: Tampilkan output asli jika gagal parsing (hapus baris bawah ini jika sudah fix)
                # await conv.send_message(f"Raw Output:\n{output}")

        except Exception as e:
            await conv.send_message(f"⚠️ **Error:** Terjadi kesalahan sistem.\n`{str(e)}`")
            if 'status_msg' in locals():
                await status_msg.delete()