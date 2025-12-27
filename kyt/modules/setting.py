from kyt import *

@bot.on(events.CallbackQuery(data=b'reboot'))
async def rebooot(event):
	async def rebooot_(event):
		cmd = f'reboot'
		await event.edit("Processing.")
		await event.edit("Processing..")
		await event.edit("Processing...")
		await event.edit("Processing....")
		time.sleep(1)
		await event.edit("`Processing Restart Service Server...`")
		time.sleep(1)
		await event.edit("`Processing... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 84%\n█████████████████████▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 100%\n█████████████████████████ `")
		subprocess.check_output(cmd, shell=True)
		await event.edit(f"""
**» REBOOT SERVER**
**» 🧊@HokageLegend**
""",buttons=[[Button.inline("‹ Main Menu ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await rebooot_(event)
	else:
		await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'resx'))
async def resx(event):
	async def resx_(event):
		cmd = f'resservice'
		subprocess.check_output(cmd, shell=True)
		await event.edit("Processing.")
		await event.edit("Processing..")
		await event.edit("Processing...")
		await event.edit("Processing....")
		time.sleep(1)
		await event.edit("`Processing Restart Service Server...`")
		time.sleep(1)
		await event.edit("`Processing... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 84%\n█████████████████████▒▒▒▒ `")
		time.sleep(1)
		await event.edit(f"""
```Processing... 100%\n█████████████████████████ ```
**» Restarting Service Done**
**» 🤖@HokageLegend**
""",buttons=[[Button.inline("‹ Main Menu ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await resx_(event)
	else:
		await event.answer("Access Denied",alert=True)
		
@bot.on(events.CallbackQuery(data=b'speedtest'))
async def speedtest(event):
	async def speedtest_(event):
		cmd = 'speedtest-cli --share'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		time.sleep(0)
		await event.edit("`Processing... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 84%\n█████████████████████▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 100%\n█████████████████████████ `")
		await event.respond(f"""
**
{z}
**
**» 🤖@HokageLegend**
""",buttons=[[Button.inline("‹ Main Menu ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await speedtest_(event)
	else:
		await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'backup'))
async def backup(event):
    from datetime import date
    import subprocess

    chat = event.chat_id
    sender = await event.get_sender()
    
    async def backup_(event):
        # 1. Input Email
        async with bot.conversation(chat) as conv:
            await event.respond('**📩 Input Email Tujuan:**')
            try:
                response_event = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id), timeout=60)
                email_input = response_event.raw_text.strip()
            except:
                await event.respond("**❌ Waktu habis. Silakan coba lagi.**", buttons=[[Button.inline("‹ Main Menu ›", "menu")]])
                return
        
        # 2. Pesan Loading
        processing_msg = await event.respond(f"⏳ **Processing Backup...**\n`Mohon tunggu, sedang memproses data...`")
        
        # 3. Jalankan Script
        cmd = f'/root/bot_store/kyt/shell/bot/bot-backup "{email_input}"'
        
        try:
            # Eksekusi Script
            process = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            output_str = process.decode("utf-8")
            
            # --- PARSING DATA ---
            data = {
                "IP": "Unknown", "Domain": "Unknown", "ISP": "Unknown", 
                "Location": "Unknown", "Link": "#"
            }
            
            for line in output_str.splitlines():
                if "IP:" in line: data["IP"] = line.replace("IP:", "").strip()
                if "Domain:" in line: data["Domain"] = line.replace("Domain:", "").strip()
                if "ISP:" in line: data["ISP"] = line.replace("ISP:", "").strip()
                if "Location:" in line: data["Location"] = line.replace("Location:", "").strip()
                if "Link:" in line: data["Link"] = line.replace("Link:", "").strip()
            
            # --- TAMPILAN FINAL ---
            pesan_sukses = f"""
<b>✅ SUCCESSFULL BACKUP DATA</b>
━━━━━━━━━━━━━━━━━━━━━━
<code>📶 IP VPS    :</code> <code>{data['IP']}</code>
<code>🌐 DOMAIN    :</code> <code>{data['Domain']}</code>
<code>📅 DATE      :</code> <code>{date.today()}</code>
<code>🚀 ISP       :</code> <code>{data['ISP']}</code>
<code>🌍 LOCATION  :</code> <code>{data['Location']}</code>
━━━━━━━━━━━━━━━━━━━━━━
☁️ <b>Google Drive Link</b>
🔗 <a href="{data['Link']}">CLICK HERE TO DOWNLOAD FILE</a>
━━━━━━━━━━━━━━━━━━━━━━
<i>Please Check your Email backup file</i>
<b>👤 @HokageLegend</b>
"""
            # Hapus pesan loading
            await processing_msg.delete()
            
            # Kirim Pesan Sukses DENGAN TOMBOL
            await event.respond(
                pesan_sukses, 
                parse_mode='html', 
                link_preview=False,
                buttons=[[Button.inline("‹ Main Menu ›", "menu")]]
            )

        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode("utf-8")
            await processing_msg.delete()
            await event.respond(
                f"<b>❌ BACKUP ERROR</b>\n<pre>{error_msg}</pre>", 
                parse_mode='html',
                buttons=[[Button.inline("‹ Main Menu ›", "menu")]]
            )
        except Exception as e:
            await processing_msg.delete()
            await event.respond(
                f"<b>❌ SYSTEM ERROR</b>\n<pre>{str(e)}</pre>", 
                parse_mode='html',
                buttons=[[Button.inline("‹ Main Menu ›", "menu")]]
            )

    # Validasi User
    a = valid(str(sender.id))
    if a == "true":
        await backup_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'restore'))
async def restore(event):
    # 1. Definisikan variabel Chat & Sender DI AWAL
    chat = event.chat_id
    sender = await event.get_sender()

    async def restore_(event):
        async with bot.conversation(chat) as conv:
            await event.respond('**Input Link Backup:**')
            response_event = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            link_input = response_event.raw_text.strip()
        
        await event.respond("Processing restore...")

        # Command Restore dengan Path Lengkap
        cmd = f'/root/bot_store/kyt/shell/bot/bot-restore "{link_input}"'
        
        try:
            process = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            output = process.decode("utf-8")
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode("utf-8")
            await event.respond(f"**❌ Restore Gagal / Link Error:**\n\n`{error_msg}`")
        else:
            msg = f"""
`{output}`
**» 🤖@HookageLegend**
"""
            await event.respond(msg)
            
    # Cek Validasi User
    a = valid(str(sender.id))
    if a == "true":
        await restore_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'restore'))
async def restsore(event):
	async def rssestore_(event):
		async with bot.conversation(chat) as conv:
			await event.respond('**Input Link Backup:**')
			response_event = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			link_input = response_event.raw_text
		
		# UPDATE: Menggunakan Full Path untuk Restore juga
		cmd = f'/root/bot_store/kyt/shell/bot/bot-restore "{link_input}"'
		
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8")
		except subprocess.CalledProcessError as e:
			# Jika script restore gagal
			await event.respond(f"**Link Error / Restore Gagal:**\n{e.output.decode('utf-8')}")
		else:
			# UPDATE: Memperbaiki variabel 'z' menjadi 'a'
			msg = f"""```{a}```
**» 🤖@HokageLegend**
"""
			await event.respond(msg)
			
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await rssestore_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'backer'))
async def backers(event):
	async def backers_(event):
		inline = [
[Button.inline(" BACKUP","backup"),
Button.inline(" RESTORE","restore")],
[Button.inline("‹ Main Menu ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		msg = f"""
━━━━━━━━━━━━━━━━━━━━━━━ 
 **⚠️ BACKUP & RESTORE ⚠️**
━━━━━━━━━━━━━━━━━━━━━━━ 
🔰 **» Hostname/IP:** `{DOMAIN}`
🔰 **» ISP:** `{z["isp"]}`
🔰 **» Country:** `{z["country"]}`
━━━━━━━━━━━━━━━━━━━━━━━ 
"""
		await event.edit(msg,buttons=inline)
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await backers_(event)
	else:
		await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'setting'))
async def settings(event):
	async def settings_(event):
		inline = [
[Button.inline(" SPEEDTEST ","speedtest"),
Button.inline(" BACKUP & RESTORE ","backer")],
[Button.inline(" REBOOT SERVER ","reboot"),
Button.inline(" RESTART SERVICE ","resx")],
[Button.inline("‹ Main Menu ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		msg = f"""
━━━━━━━━━━━━━━━━━━━━━━━ 
 **⚠️ OTHER PANEL MENU ⚠️**
━━━━━━━━━━━━━━━━━━━━━━━ 
**» 🟢 Hostname/IP:** `{DOMAIN}`
**» 🟢 ISP:** `{z["isp"]}`
**» 🟢 Country:** `{z["country"]}`
**» 🤖@HokageLegend**
━━━━━━━━━━━━━━━━━━━━━━━ 
"""
		await event.edit(msg,buttons=inline)
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await settings_(event)
	else:
		await event.answer("Access Denied",alert=True)