from kyt import *

@bot.on(events.CallbackQuery(data=b'create-trojan'))
async def create_trojan(event):
	async def create_trojan_(event):
		async with bot.conversation(chat) as user:
			await event.respond('**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text
		async with bot.conversation(chat) as pw:
			await event.respond("**Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
		async with bot.conversation(chat) as exp:
			await event.respond("**Choose Expiry Day**",buttons=[
[Button.inline(" 3 Day ","3"),
Button.inline(" 7 Day ","7")],
[Button.inline(" 30 Day ","30"),
Button.inline(" 60 Day ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		await event.edit("Processing.")
		await event.edit("Processing..")
		await event.edit("Processing...")
		await event.edit("Processing....")
		time.sleep(1)
		await event.edit("`Processing Crate Premium Account`")
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
		time.sleep(1)
		await event.edit("`Wait.. Setting up an Account`")
		cmd = f'printf "%s\n" "{user}" "{exp}" "{pw}" | addtr-bot'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("trojan://(.*)",a)]
			print(b)
			domain = re.search("@(.*?):",b[0]).group(1)
			uuid = re.search("trojan://(.*?)@",b[0]).group(1)
			msg = f"""
**━━━━━━━━━━━━━━━━━**
**🟢 Trojan Account 🟢**
**━━━━━━━━━━━━━━━━━**
**» Remarks     :** `{user}`
**» Host Server :** `{domain}`
**» Host XrayDNS:** `{HOST}`
**» User Quota  :** `{pw} GB`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» User ID     :** `{uuid}`
**» Pub Key     :** {PUB}
**━━━━━━━━━━━━━━━━**
**» Link WS    :** 
`{b[0].replace(" ","")}`
**━━━━━━━━━━━━━━━━**
**» Link GRPC  :** 
`{b[1].replace(" ","")}`
**━━━━━━━━━━━━━━━━**
**» Format OpenClash : https://{domain}:81/trojan-{user}.txt
**━━━━━━━━━━━━━━━━**
**Expired Until:** `{later}`
**» 🤖@HokageLegend**
"""
			await event.respond(msg)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'cek-trojan'))
async def cek_trojan(event):
	async def cek_trojan_(event):
		cmd = 'bot-cek-tr'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""

{z}

**Shows Logged In Users Trojan**
**» 🤖@HokageLegend**
""",buttons=[[Button.inline("‹ Main Menu ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await cek_trojan_(event)
	else:
		await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'trial-trojan'))
async def trial_trojan(event):
	async def trial_trojan_(event):
		async with bot.conversation(chat) as exp:
			await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		cmd = f'printf "%s\n" "{exp}" | bot-trialtr'
		await event.edit("Processing.")
		await event.edit("Processing..")
		await event.edit("Processing...")
		await event.edit("Processing....")
		time.sleep(3)
		await event.edit("`Processing Crate Premium Account`")
		time.sleep(1)
		await event.edit("`Processing... 0%\n▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 4%\n█▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(2)
		await event.edit("`Processing... 8%\n██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(3)
		await event.edit("`Processing... 20%\n█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(2)
		await event.edit("`Processing... 36%\n█████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 52%\n█████████████▒▒▒▒▒▒▒▒▒▒▒▒ `")
		time.sleep(1)
		await event.edit("`Processing... 84%\n█████████████████████▒▒▒▒ `")
		time.sleep(0)
		await event.edit("`Processing... 100%\n█████████████████████████ `")
		time.sleep(1)
		await event.edit("`Wait.. Setting up an Account`")
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			#today = DT.date.today()
			#later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("trojan://(.*)",a)]
			print(b)
			remarks = re.search("#(.*)",b[0]).group(1)
			domain = re.search("@(.*?):",b[0]).group(1)
			uuid = re.search("trojan://(.*?)@",b[0]).group(1)
			msg = f"""
**━━━━━━━━━━━━━━━━━**
**🟢 Trojan Account 🟢**
**━━━━━━━━━━━━━━━━━**
**» Remarks     :** `{remarks}`
**» Host Server :** `{domain}`
**» Host XrayDNS:** `{HOST}`
**» User Quota  :** `Unlimited`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» Path Trojan :** `(/multi path)/trojan-ws`
**» User ID     :** `{uuid}`
**» Pub Key     :** {PUB}
**━━━━━━━━━━━━━━━━**
**» Link WS    :** 
`{b[0].replace(" ","")}`
**━━━━━━━━━━━━━━━━**
**» Link GRPC  :** 
`{b[1].replace(" ","")}`
**━━━━━━━━━━━━━━━━**
**» Expired Until:** `{exp} Minutes`
**» 🤖@HokageLegend**
"""
			await event.respond(msg)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-trojan'))
async def delete_trojan(event):
    chat = event.chat_id
    sender = await event.get_sender()
    
    # Validasi Admin (sesuaikan logic validasi Anda)
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return

    async def delete_trojan_(event):
        async with bot.conversation(chat) as user:
            await event.respond('**Username to Delete:**')
            user_msg = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user_to_delete = (await user_msg).raw_text

        try:
            # --- LOGIKA HAPUS LANGSUNG (Revisi tag #!) ---
            config_path = "/etc/xray/config.json"
            
            # 1. Cek apakah user ada (Cari tag #! namauser)
            check_user = subprocess.run(f"grep -q '^#! {user_to_delete} ' {config_path}", shell=True)
            
            if check_user.returncode != 0:
                await event.respond("**❌ User Not Found!**")
                return

            # 2. Hapus dari Config Xray (Hapus baris #! user dan 1 baris di bawahnya/password)
            subprocess.run(f"sed -i '/^#! {user_to_delete} /,+1d' {config_path}", shell=True)
            
            # 3. Bersihkan baris kosong sisa hapus
            subprocess.run(f"sed -i '/^$/d' {config_path}", shell=True)
            
            # 4. Hapus File Limit/Usage
            subprocess.run(f"rm -f /etc/xray/limit/trojan/{user_to_delete}", shell=True)
            subprocess.run(f"rm -f /etc/trojan/{user_to_delete}", shell=True)

            # 5. Restart Xray
            subprocess.run("systemctl restart xray", shell=True)

            msg = f"""**✅ User {user_to_delete} Successfully Deleted**"""
            await event.respond(msg)
            
        except Exception as e:
            await event.respond(f"**Error:** {str(e)}")

    await delete_trojan_(event)

@bot.on(events.CallbackQuery(data=b'trojan'))
async def trojan(event):
	async def trojan_(event):
		inline = [
[Button.inline(" TRIAL TROJAN ","trial-trojan"),
Button.inline(" CREATE TROJAN ","create-trojan")],
[Button.inline(" CHECK TROJAN ","cek-trojan"),
Button.inline(" DELETE TROJAN ","delete-trojan")],
[Button.inline("‹ Main Menu ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		msg = f"""
━━━━━━━━━━━━━━━━━━━━━━━ 
** HOKAGE PREMIUM TUNNELING **
━━━━━━━━━━━━━━━━━━━━━━━ 
━━━━━━━━━━━━━━━━━━━━━━━ 
   **⚠️ MENU TROJAN ⚠️**
━━━━━━━━━━━━━━━━━━━━━━━ 
🟢 **» Service:** `TROJAN`
🟢 **» Hostname/IP:** `{DOMAIN}`
🟢 **» ISP:** `{z["isp"]}`
🟢 **» Country:** `{z["country"]}`
🛑 **» @HokageLegend**
━━━━━━━━━━━━━━━━━━━━━━━ 
"""
		await event.edit(msg,buttons=inline)
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trojan_(event)
	else:
		await event.answer("Access Denied",alert=True)
