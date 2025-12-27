# handlers/handlers_ppob.py
import telebot
import requests
import json
import time
import logging
import re
from datetime import datetime
from bot_init import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.apihelper import ApiTelegramException # Penting untuk handle error API
from database import get_user_data, add_balance, increment_reseller_trx
from config import ADMIN_ID, ATLANTIC_API_KEY, ATLANTIC_TRX_URL

# Import Service Atlantic & OkeConnect
from atlantic_service import get_atlantic_price_list, get_grouped_providers, get_categories_by_provider
try:
    from orderkuota_service import get_okeconnect_price, request_orderkuota_trx, check_orderkuota_status
except ImportError:
    from orderkuota_service import get_okeconnect_price, request_orderkuota_trx
    check_orderkuota_status = None
# ==========================================
#  HELPER: PARSING PESAN PPOB
# ==========================================
def parse_respon_server(raw_text):
    """Memecah respon server jadi SN, Harga, dan Info Sisa"""
    data = {'sn': '-', 'harga': '0', 'info_sisa': '-'}
    try:
        # Regex mencari pola: SN: [isi]. Hrg [angka] [sisa]
        # Menangani variasi huruf besar/kecil dan spasi
        pattern = r"SN:\s*(.*?)\.\s*Hrg\s*([\d\.]+)\s*(.*)"
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)

        if match:
            data['sn'] = match.group(1).strip()
            data['harga'] = match.group(2).strip()
            data['info_sisa'] = match.group(3).strip()
        else:
            # Fallback jika format tidak standar
            simple_sn = re.search(r"SN:\s*(.*?)(?:\.|$)", raw_text, re.IGNORECASE)
            if simple_sn: data['sn'] = simple_sn.group(1).strip()
            
    except Exception as e:
        print(f"Regex Error: {e}")
    return data
# ==========================================
#  KONFIGURASI MARKUP & LOGGING
# ==========================================

MARKUP_MEMBER = 3000
MARKUP_RESELLER = 2000
logger = logging.getLogger(__name__)

def log_act(user, action, detail=""):
    """Mencatat aktivitas user ke journalctl/systemd log"""
    try:
        username = user.username if user.username else "NoUsername"
        print(f"📝 [AKTIVITAS] ID:{user.id} | @{username} | {action} | {detail}")
    except:
        print(f"📝 [AKTIVITAS] ID:{user.id} | {action}")

# ==========================================
#  1. JALUR PROVIDER: OKECONNECT (MURAH)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "ppob_menu" or call.data == "ppob_orderkuota")
def ppob_okeconnect_main(call):
    try:
        log_act(call.from_user, "MEMBUKA MENU OKECONNECT")
        bot.answer_callback_query(call.id)
        
        uid = call.from_user.id
        user = get_user_data(uid)
        balance = user['balance'] if user else 0
        
        markup = InlineKeyboardMarkup()
        # Baris 1
        markup.row(
            InlineKeyboardButton("🔴 TELKOMSEL", callback_data="oke_op|TELKOMSEL|1"),
            InlineKeyboardButton("🟡 INDOSAT", callback_data="oke_op|INDOSAT|1"),
            InlineKeyboardButton("🔵 XL", callback_data="oke_op|XL|1")
        )
        # Baris 2
        markup.row(
            InlineKeyboardButton("🟣 AXIS", callback_data="oke_op|AXIS|1"),
            InlineKeyboardButton("3️⃣ TRI", callback_data="oke_op|THREE|1"),
            InlineKeyboardButton("📶 SMARTFREN", callback_data="oke_op|SMARTFREN|1")
        )
        # Baris 3
        markup.row(
            InlineKeyboardButton("💡 PLN TOKEN", callback_data="oke_op|PLN|1"),
            InlineKeyboardButton("💎 GAMES", callback_data="oke_op|GAME|1"),
            InlineKeyboardButton("💳 E-MONEY", callback_data="oke_op|DANA|1")
        )
        # Baris 4 (BARU: CEK DIGITAL)
        markup.row(
            InlineKeyboardButton("🔍 CEK VALIDASI AKUN", callback_data="oke_op|DIGITAL_CHECK|1")
        )
        
        markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU UTAMA", callback_data="switch_owner"))
        
        msg = (f"🏪 <b>PPOB OKECONNECT (MURAH)</b>\n"
               f"━━━━━━━━━━━━━━━━━━━━━\n"
               f"💰 <b>Saldo:</b> <code>Rp {balance:,}</code>\n"
               f"👇 <i>Pilih operator layanan:</i>")
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
    except Exception as e: 
        logger.error(f"Error Oke Main: {e}")



# ==========================================
#  HANDLER LIST PRODUK OKECONNECT (FILTER PLN FIX)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("oke_op|"))
def ppob_oke_list_product(call):
    parts = call.data.split("|")
    operator, page = parts[1].upper(), int(parts[2])
    
    # Log aktivitas
    if page == 1: 
        log_act(call.from_user, "MELIHAT HARGA OKE", operator)
    
    all_data = get_okeconnect_price()
    
    if not all_data:
        return bot.edit_message_text("❌ Gagal mengambil data harga.", call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_menu")))

    # --- LOGIKA FILTERING ---
    filtered = []
    for p in all_data:
        raw_kode = str(p.get('kode', '')).upper()
        raw_ket = str(p.get('keterangan', '')).upper()
        raw_kat = str(p.get('kategori', '')).upper()
        
        # 1. FILTER KHUSUS CEK DIGITAL (BARU)
        if operator == "DIGITAL_CHECK":
            # Hanya ambil produk yang kodenya berawalan "CEK" (Contoh: CEKGRB, CEKOVO)
            if raw_kode.startswith("CEK"):
                filtered.append(p)

        # 2. FILTER KHUSUS PLN
        elif operator == "PLN":
            if "PLN" in raw_kode:
                filtered.append(p)
        
        # 3. FILTER KHUSUS E-MONEY
        elif operator == "DANA":
            if any(x in raw_kat or x in raw_ket for x in ["DANA", "OVO", "GOPAY", "SHOPEE", "LINKAJA", "EMONEY", "BRIZZI", "TAPCASH", "FLAZZ"]):
                filtered.append(p)

        # 4. FILTER STANDAR
        else:
            if operator in (raw_kat + raw_ket):
                filtered.append(p)

    # Urutkan berdasarkan Kode/Nama agar rapi
    filtered.sort(key=lambda x: x['keterangan'])

    # Pagination
    LIMIT = 10
    total_items = len(filtered)
    total_pages = (total_items + LIMIT - 1) // LIMIT if total_items > 0 else 1
    page = max(1, min(page, total_pages))
    current_items = filtered[(page-1)*LIMIT : page*LIMIT]
    
    udata = get_user_data(call.from_user.id)
    markup_val = MARKUP_RESELLER if udata and str(udata.get('role')).lower() == 'reseller' else MARKUP_MEMBER
    
    # Judul Header (Custom untuk Digital Check)
    display_op = "CEK VALIDASI AKUN" if operator == "DIGITAL_CHECK" else operator
    
    msg = f"✨ <b>DAFTAR PRODUK: {display_op}</b>\n"
    msg += f"📄 Halaman: {page} / {total_pages}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    markup = InlineKeyboardMarkup(row_width=5)
    btns = []
    
    if not current_items:
        msg += "❌ <b>Produk tidak ditemukan / Kosong.</b>"
    else:
        for i, item in enumerate(current_items, 1):
            # Harga produk CEK biasanya murah/gratis, tetap tambahkan markup jika perlu
            # Atau bisa diset markup 0 khusus CEK jika diinginkan
            price = int(item['harga']) + markup_val
            
            # Status Logic
            raw_status = str(item.get('status', '1')) 
            
            if raw_status == '1':
                status_icon = "🟢"
                status_text = "Tersedia"
                btn_label = str(i)
                cb_data = f"okebuy|{item['kode']}|{price}|{operator}"
            else:
                status_icon = "🔴"
                status_text = "Gangguan"
                btn_label = "❌"
                cb_data = "ignore"

            msg += f"<b>[{i}] {item['keterangan']}</b>\n"
            msg += f"🆔 <b>CODE:</b> <code>{item['kode']}</code>\n"
            msg += f"💰 <b>HARGA:</b> <b>Rp {price:,}</b>\n"
            msg += f"📊 <b>STATUS:</b> {status_icon} <i>{status_text}</i>\n"
            msg += "─────────────────────\n"
            
            btns.append(InlineKeyboardButton(btn_label, callback_data=cb_data))
    
    markup.add(*btns)
    
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"oke_op|{operator}|{page-1}"))
    nav.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
    if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"oke_op|{operator}|{page+1}"))
    
    markup.row(*nav)
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_menu"))
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

# ==========================================
#  2. JALUR PROVIDER: ATLANTIC (LENGKAP)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "ppob_atlantic")
def ppob_atlantic_main(call):
    # LOG AKTIVITAS
    log_act(call.from_user, "MEMBUKA MENU UTAMA PPOB (ATL)")
    
    bot.answer_callback_query(call.id, "🔄 Memuat Atlantic...")
    res = get_atlantic_price_list("prabayar")
    
    if res.get('status') is True:
        markup = InlineKeyboardMarkup()
        
        # --- BARIS 1: TELKOMSEL & INDOSAT ---
        markup.row(
            InlineKeyboardButton("🔴 TELKOMSEL", callback_data="atl_prov|TELKOMSEL"),
            InlineKeyboardButton("🟡 INDOSAT", callback_data="atl_prov|INDOSAT")
        )
        
        # --- BARIS 2: XL AXIATA & THREE ---
        markup.row(
            InlineKeyboardButton("🔵 XL AXIATA", callback_data="atl_prov|XL"),
            InlineKeyboardButton("3️⃣ THREE", callback_data="atl_prov|TRI")
        )
        
        # --- BARIS 3: GAME POPULER (MLBB & PUBG) ---
        markup.row(
            InlineKeyboardButton("💎 MLBB", callback_data="atl_cat|MOBILE LEGENDS|Games|1"),
            InlineKeyboardButton("🔫 PUBG", callback_data="atl_cat|PUBG MOBILE|Games|1")
        )
        
        # --- BARIS 4: APP & GAME LAIN (ROBLOX & CANVA) ---
        markup.row(
            InlineKeyboardButton("🏗️ ROBLOX", callback_data="atl_cat|ROBLOX|Games|1"),
            InlineKeyboardButton("🪄 CANVA", callback_data="atl_cat|CANVA|Akun Premium|1")
        )
        
        # --- BARIS 5: UTILITY & LAINNYA ---
        markup.row(
            InlineKeyboardButton("💡 PLN", callback_data="atl_prov|PLN"),
            InlineKeyboardButton("🎮 LAYANAN LAINNYA", callback_data="atl_more_menu")
        )
        
        # --- BARIS 6: NAVIGASI ---
        markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU UTAMA", callback_data="switch_owner"))
        
        # Pesan Header
        msg = (
            "🏛 <b>PUSAT LAYANAN DIGITAL TERLENGKAP</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "💎 <b>Solusi Transaksi Cepat & Terpercaya</b>\n\n"
            "🚀 <i>Nikmati kemudahan akses produk digital dengan "
            "harga kompetitif dan proses instan 24 jam nonstop.</i>\n\n"
            "✨ <b>Keunggulan Kami:</b>\n"
            "✅ <b>Produk Selalu Update</b>\n"
            "✅ <b>Keamanan Transaksi Terjamin</b>\n"
            "✅ <b>Layanan Premium & VIP</b>\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "👇 <b>Pilih Kategori Layanan Anda:</b>"
        )
        
        bot.edit_message_text(
            msg, 
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode='HTML', 
            reply_markup=markup
        )
    else: 
        bot.send_message(call.message.chat.id, "❌ Gagal koneksi ke server Atlantic. Silakan coba lagi.")
        print("❌ [ERROR] Atlantic Connection Failed")

# ==========================================
#  3. HANDLER KATEGORI (FIX TRI & LOGGING)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("atl_prov|"))
def ppob_atl_category(call):
    try:
        provider = call.data.split("|")[1]
        
        # LOG AKTIVITAS
        log_act(call.from_user, "MEMBUKA PROVIDER", provider)
        
        bot.answer_callback_query(call.id, f"🔄 Memuat kategori {provider}...")
        
        res = get_atlantic_price_list("prabayar")
        if res.get('status') is True:
            all_data = res.get('data', [])
            cats = set()
            
            # --- LOGIKA PENCARIAN KATEGORI (ROBUST) ---
            search_prov = provider.lower().replace(" ", "")
            
            for p in all_data:
                data_prov = str(p.get('provider', '')).lower().replace(" ", "")
                # Logika Match Provider (Termasuk TRI)
                match_prov = (data_prov == search_prov) or \
                             (search_prov == 'tri' and 'three' in data_prov) or \
                             (search_prov == 'three' and 'tri' in data_prov)
                
                if match_prov:
                    cats.add(p.get('category'))
            
            sorted_cats = sorted(list(cats))
            
            markup = InlineKeyboardMarkup(row_width=2)
            for c in sorted_cats: 
                markup.add(InlineKeyboardButton(f"📂 {c}", callback_data=f"atl_cat|{provider}|{c}|1"))
            
            markup.row(InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_atlantic"))
            
            if not sorted_cats:
                msg = f"❌ Kategori untuk <b>{provider}</b> tidak ditemukan."
            else:
                msg = f"🔵 <b>LAYANAN: {provider}</b>\n👇 Silakan pilih kategori produk:"
                
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ Gagal mengambil data.", show_alert=True)
    except Exception as e:
        print(f"❌ [ERROR] category: {e}")
        bot.answer_callback_query(call.id, "❌ Terjadi kesalahan sistem.")

# ==========================================
#  4. HANDLER PRODUK (FIX LOGGING & ERROR)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("atl_cat|"))
def ppob_atl_products(call):
    try:
        parts = call.data.split("|")
        prov, cat, page = parts[1], parts[2], int(parts[3])
        
        # LOG AKTIVITAS (Hanya log halaman 1)
        if page == 1:
            log_act(call.from_user, "MELIHAT PRODUK", f"{prov} - {cat}")
        
        bot.answer_callback_query(call.id, f"🔄 Memuat detail {prov}...")
        res = get_atlantic_price_list("prabayar")
        
        if res.get('status') is True:
            all_products = res.get('data', [])
            
            def clean(text): return str(text).lower().replace(" ", "")
            search_prov = clean(prov)
            search_cat = clean(cat)

            filtered_products = []
            for p in all_products:
                item_prov = clean(p.get('provider', ''))
                item_cat = clean(p.get('category', ''))
                
                # Filter Direct Show
                if any(x in search_prov for x in ["mobilelegends", "roblox", "pubg"]):
                    if search_prov in item_prov: filtered_products.append(p)
                else:
                    match_prov = (item_prov == search_prov) or \
                                 (search_prov == 'tri' and 'three' in item_prov) or \
                                 (search_prov == 'three' and 'tri' in item_prov)
                    if match_prov and search_cat in item_cat:
                         filtered_products.append(p)
            
            filtered_products = sorted(filtered_products, key=lambda x: int(x.get('price', 0)))
            
            LIMIT = 10
            total_items = len(filtered_products)
            total_pages = (total_items + LIMIT - 1) // LIMIT if total_items > 0 else 1
            page = max(1, min(page, total_pages))
            current_items = filtered_products[(page-1)*LIMIT : page*LIMIT]
            
            uid = call.from_user.id
            udata = get_user_data(uid)
            markup_val = MARKUP_RESELLER if udata and str(udata.get('role')).lower() == 'reseller' else MARKUP_MEMBER
            
            msg = f"✨ <b>DETAIL LAYANAN: {prov.upper()}</b>\n"
            msg += f"📄 Halaman: {page} / {total_pages}\n"
            
            # Info Header
            if "NETFLIX" in prov.upper(): msg += "━━━━━━━━━━━━━━━━━━━━━\n⚠️ <b>CATATAN:</b> Tujuan: DEVICE - LOKASI\n"
            elif any(x in prov.upper() for x in ["PICSART", "CANVA", "PERPLEXITY"]): msg += "━━━━━━━━━━━━━━━━━━━━━\n📝 <b>INFO:</b> Tujuan WAJIB Email\n"
            elif "ROBLOX" in prov.upper(): msg += "━━━━━━━━━━━━━━━━━━━━━\n🧱 <b>INFO:</b> Masukkan Username Roblox Anda\n"
            elif "MOBILE LEGENDS" in prov.upper(): msg += "━━━━━━━━━━━━━━━━━━━━━\n⚔️ <b>INFO:</b> Format ID (Server)\n"
            elif "PUBG" in prov.upper(): msg += "━━━━━━━━━━━━━━━━━━━━━\n🔫 <b>INFO PUBG:</b> Masukkan ID Player (Tanpa Server)\n"
            elif "VIDIO" in prov.upper(): msg += "━━━━━━━━━━━━━━━━━━━━━\n📺 <b>INFO VIDIO:</b> Garansi sesuai deskripsi.\n"
            
            msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            markup = InlineKeyboardMarkup(row_width=5)
            nums_btns = []
            
            if not current_items:
                msg += "❌ <b>Produk tidak ditemukan atau sedang gangguan.</b>"
            else:
                for i, p in enumerate(current_items, 1):
                    price = int(p.get('price', 0)) + markup_val
                    raw_status = str(p.get('status', 'empty')).lower()
                    status_icon = "🟢" if raw_status == 'available' else "🔴"
                    catatan = p.get('note') or "Tidak ada catatan khusus."
                    is_zone = "Ya" if any(x in str(p.get('provider')).upper() for x in ["MOBILE LEGENDS", "ROBLOX"]) else "Tidak"

                    msg += f"<b>[{i}] {p.get('name')}</b>\n"
                    msg += f"🆔 <b>CODE:</b> <code>{p.get('code')}</code>\n"
                    msg += f"📂 <b>KATEGORI:</b> {p.get('category')}\n"
                    msg += f"🏢 <b>PROVIDER:</b> {p.get('provider')}\n"
                    msg += f"🌐 <b>ZONE ID:</b> {is_zone}\n"
                    msg += f"💰 <b>HARGA:</b> <b>Rp {price:,}</b>\n"
                    msg += f"📊 <b>STATUS:</b> {status_icon} <i>{raw_status.capitalize()}</i>\n"
                    msg += f"📝 <b>CATATAN:</b>\n<i>{catatan}</i>\n"
                    msg += "─────────────────────\n"
                    
                    btn_label = str(i) if raw_status == 'available' else "❌"
                    cb_buy = f"atlbeli|{p['code']}|{price}|{prov}" if raw_status == 'available' else "ignore"
                    nums_btns.append(InlineKeyboardButton(btn_label, callback_data=cb_buy))
            
            markup.add(*nums_btns)
            
            nav = []
            if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"atl_cat|{prov}|{cat}|{page-1}"))
            nav.append(InlineKeyboardButton(f"📑 {page}/{total_pages}", callback_data="ignore"))
            if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"atl_cat|{prov}|{cat}|{page+1}"))
            markup.row(*nav)
            
            # Smart Back Button
            main_provs = ["MOBILE LEGENDS", "PUBG", "CANVA", "ROBLOX", "TELKOMSEL", "INDOSAT", "XL", "TRI", "THREE"]
            premium_provs = ["NETFLIX", "PICSART", "VIDIO", "WIFI", "PERPLEXITY"]
            
            if any(x in prov.upper() for x in main_provs):
                markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="ppob_atlantic"))
            elif any(x in prov.upper() for x in premium_provs):
                markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU PREMIUM", callback_data="atl_more_menu"))
            else:
                markup.add(InlineKeyboardButton("🔙 KEMBALI KE KATEGORI", callback_data=f"atl_prov|{prov}"))
            
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ Gagal sinkronisasi data server.", show_alert=True)
            
    except ApiTelegramException as e:
        # --- FIX UTAMA: MENGABAIKAN ERROR MESSAGE NOT MODIFIED ---
        if "message is not modified" in str(e):
            print(f"⚠️ [INFO] User {call.from_user.id} klik tombol refresh (Data tidak berubah).")
        else:
            print(f"❌ [ERROR] Telegram API: {e}")
            
    except Exception as e:
        print(f"❌ [ERROR] atl_products: {e}")
        bot.answer_callback_query(call.id, "❌ Terjadi gangguan sistem.")

# Handler Ignore (Penting untuk tombol yang tidak ada aksi)
@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore_handler(call):
    bot.answer_callback_query(call.id)

# ==========================================
#  5. PROSES TRANSAKSI & KONFIRMASI (GENERAL)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("okebuy|") or call.data.startswith("atlbeli|"))
def ppob_input_dest(call):
    parts = call.data.split("|")
    prefix = "OKE" if parts[0] == "okebuy" else "ATL"
    kode, harga, op = parts[1], parts[2], parts[3]
    
    # LOG
    log_act(call.from_user, "KLIK BELI", f"{op} - {kode}")
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(call.message.chat.id, f"🛒 <b>BELI {op} ({prefix})</b>\n\n📦 Kode: <code>{kode}</code>\n💰 Harga: Rp {int(harga):,}\n\n👇 <b>Kirim Nomor HP / ID Tujuan:</b>", parse_mode='HTML')
    
    if prefix == "OKE": bot.register_next_step_handler(msg, oke_confirm, kode, harga)
    else: bot.register_next_step_handler(msg, atl_confirm, kode, harga, op)

def oke_confirm(message, kode, harga):
    dest = message.text.strip()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ BELI SEKARANG", callback_data=f"okefix|{kode}|{harga}|{dest}"))
    markup.add(InlineKeyboardButton("❌ BATAL", callback_data="ppob_menu"))
    bot.reply_to(message, f"⚠️ <b>KONFIRMASI OKECONNECT</b>\n\n📦 Produk: {kode}\n📱 Tujuan: {dest}\n💸 Harga: <b>Rp {int(harga):,}</b>", parse_mode='HTML', reply_markup=markup)

def atl_confirm(message, kode, harga, prov):
    dest = message.text.strip()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ BELI SEKARANG", callback_data=f"atlfix|{kode}|{harga}|{dest}"))
    markup.add(InlineKeyboardButton("❌ BATAL", callback_data=f"atl_prov|{prov}"))
    bot.reply_to(message, f"⚠️ <b>KONFIRMASI ATLANTIC</b>\n\n📦 Produk: {kode}\n📱 Tujuan: {dest}\n💸 Harga: <b>Rp {int(harga):,}</b>", parse_mode='HTML', reply_markup=markup)

# ==========================================
#  6. EKSEKUSI TRANSAKSI (ATLANTIC DENGAN LOG)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("atlfix|"))
def ppob_execute_atl(call):
    _, kode, harga, dest = call.data.split("|")
    harga, uid = int(harga), call.from_user.id
    user = get_user_data(uid)
    
    if not user or (str(uid) != str(ADMIN_ID) and user['balance'] < harga):
        return bot.answer_callback_query(call.id, "❌ Saldo Kurang!", show_alert=True)
    
    bot.edit_message_text("⏳ <b>Sedang Memproses Atlantic...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    add_balance(uid, -harga, f"Beli {kode} (ATL)")
    ref_id = f"ATL{int(time.time())}{uid}"
    
    # LOG SYSTEMD: MEMULAI TRANSAKSI
    print(f"🚀 [TRANSAKSI] START | ID:{uid} | Ref:{ref_id} | Kode:{kode} | Tujuan:{dest}")
    
    # Request Atlantic
    payload = {'api_key': ATLANTIC_API_KEY, 'code': kode, 'dest': dest, 'ref_id': ref_id}
    try:
        res = requests.post(ATLANTIC_TRX_URL, data=payload, timeout=30).json()
        is_success = res.get('status') is True
        msg_srv = res.get('message', 'No Message')
    except Exception as e: 
        is_success, msg_srv = False, f"Connection Timeout: {e}"
        print(f"❌ [TRANSAKSI] CONNECTION ERROR: {e}")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU PPOB", callback_data="ppob_atlantic"))
    
    if is_success:
        status_h = "✅ <b>SUKSES / DIPROSES</b>"
        increment_reseller_trx(uid)
        # LOG SUKSES
        print(f"✅ [TRANSAKSI] SUKSES | ID:{uid} | Ref:{ref_id} | Msg:{msg_srv}")
    else:
        status_h = "❌ <b>GAGAL</b>"
        add_balance(uid, harga, f"Refund {kode}")
        # LOG GAGAL
        print(f"❌ [TRANSAKSI] GAGAL | ID:{uid} | Ref:{ref_id} | Msg:{msg_srv}")

    msg = f"{status_h}\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📦 Produk: {kode}\n📱 Tujuan: {dest}\n💰 Harga: Rp {harga:,}\n🧾 RefID: {ref_id}\n📝 Ket: {msg_srv}"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

# ==========================================
#  7. EKSEKUSI TRANSAKSI (OKECONNECT)
# ==========================================

# ==========================================
#  4. EKSEKUSI TRANSAKSI (OKECONNECT - FIX DISPLAY)
# ==========================================

# ==========================================
#  7. EKSEKUSI TRANSAKSI (OKECONNECT - UPDATED)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("okefix|"))
def ppob_execute_oke(call):
    _, kode, harga, dest = call.data.split("|")
    harga, uid = int(harga), call.from_user.id
    user = get_user_data(uid)
    
    if not user or (str(uid) != str(ADMIN_ID) and user['balance'] < harga):
        return bot.answer_callback_query(call.id, "❌ Saldo Kurang!", show_alert=True)
    
    bot.edit_message_text("⏳ <b>Sedang Memproses OkeConnect...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    add_balance(uid, -harga, f"Beli {kode} (OKE)")
    ref_id = f"TRX{int(time.time())}{uid}"
    
    # Request ke OkeConnect
    res = request_orderkuota_trx(kode, dest, ref_id)
    markup = InlineKeyboardMarkup()
    
    if res['success']:
        server_id = res.get('server_id', '')
        # Coba parsing langsung jika pesan mengandung SN (untuk produk instan)
        parsed = parse_respon_server(res['msg'])
        
        # Tentukan Header
        if "sukses" in res['msg'].lower():
            status_header = "✅ <b>TRANSAKSI SUKSES</b>"
        else:
            status_header = "✅ <b>TRANSAKSI DIPROSES</b>"

        # Format Pesan Baru (Sesuai Request)
        msg_body = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f" Produk : {kode}\n"
            f" Tujuan : {dest}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"SN: {parsed['sn']}\n"
            f"Hrg : {parsed['harga']}\n\n"
            f"info : {parsed['info_sisa']}\n"
            f" Info Lengkap:\n"
            f"{res['msg']}"
        )

        # Tombol Refresh
        markup.add(InlineKeyboardButton("🔄 Refresh Status", callback_data=f"cs|{server_id}|{ref_id}|{dest}|{kode}"))
        print(f"✅ [TRANSAKSI OKE] ACCEPTED | Ref:{ref_id}")

    else:
        status_header = "❌ <b>TRANSAKSI GAGAL</b>"
        add_balance(uid, harga, f"Refund {kode}")
        print(f"❌ [TRANSAKSI OKE] REJECTED | Msg:{res['msg']}")
        
        msg_body = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f" Produk : {kode}\n"
            f" Tujuan : {dest}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Alasan Gagal:</b>\n{res['msg']}\n\n"
            f"💰 <i>Saldo telah dikembalikan otomatis.</i>"
        )

    markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU PPOB", callback_data="ppob_menu"))
    
    full_msg = f"{status_header}\n{msg_body}"
    bot.edit_message_text(full_msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)

# ==========================================
#  8. HANDLER LAINNYA (MORE MENU & CEK STATUS)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "atl_more_menu")
def ppob_atl_more_menu(call):
    bot.answer_callback_query(call.id)
    log_act(call.from_user, "MEMBUKA MENU PREMIUM")
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton("🎬 NETFLIX", callback_data="atl_cat|NETFLIX|Akun Premium|1"),
        InlineKeyboardButton("📽️ VIDIO", callback_data="atl_cat|VIDIO|Akun Premium|1")
    )
    markup.row(
        InlineKeyboardButton("🎨 PICSART", callback_data="atl_cat|PICSART|Akun Premium|1"),
        InlineKeyboardButton("🤖 PERPLEXITY", callback_data="atl_cat|AI PERPLEXITY|Akun Premium|1")
    )
    markup.row(
        InlineKeyboardButton("📶 WIFI.ID", callback_data="atl_cat|WIFI.ID|Internet|1"),
        InlineKeyboardButton("🏦 E-MONEY", callback_data="atl_prov|E-MONEY")
    )
    markup.add(InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_atlantic"))
    
    msg = (
        "🎮 <b>MENU LAYANAN PREMIUM & LAINNYA</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "✨ <i>Tersedia berbagai akun aplikasi premium,\nstreaming, AI, dan voucher digital.</i>\n\n"
        "👇 <b>Silakan pilih kategori:</b>"
    )
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)


# ==========================================
#  6. HANDLER CEK STATUS (UPDATED)
# ==========================================

# ==========================================
#  HANDLER CEK STATUS (UPDATED)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("cs|"))
def ppob_refresh_status(call):
    try:
        parts = call.data.split("|")
        _, srv_id, ref_id, dest, kode = parts
        
        # Ambil respon terbaru dari server
        raw_response = check_orderkuota_status(ref_id, server_id=srv_id, nomor_tujuan=dest, kode_produk=kode)
        
        # Header Status
        resp_lower = raw_response.lower()
        if "sukses" in resp_lower: header = "✅ TRANSAKSI SUKSES"
        elif "gagal" in resp_lower: header = "❌ TRANSAKSI GAGAL"
        elif "tujuan salah" in resp_lower: header = "⚠️ NOMOR SALAH"
        else: header = "⏳ SEDANG DIPROSES"

        # Parsing Data (Gunakan Helper)
        parsed = parse_respon_server(raw_response)
        waktu = datetime.now().strftime('%H:%M:%S')

        # Format Pesan Akhir (Sama persis dengan saat execute)
        msg = (
            f"<b>{header}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f" Produk : {kode}\n"
            f" Tujuan : {dest}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"SN: {parsed['sn']}\n"
            f"Hrg : {parsed['harga']}\n\n"
            f"info : {parsed['info_sisa']}\n"
            f" Info Lengkap:\n"
            f"{raw_response}\n\n"
            f" Last Check: {waktu}"
        )

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Refresh Status", callback_data=call.data))
        markup.add(InlineKeyboardButton("🔙 KEMBALI KE MENU", callback_data="ppob_menu"))
        
        try:
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=markup)
        except ApiTelegramException as e:
            if "message is not modified" in str(e):
                bot.answer_callback_query(call.id, "Data belum berubah.")
            else:
                raise e
        
    except Exception as e:
        print(f"Error CS: {e}")
        bot.answer_callback_query(call.id, "Gagal update status.")