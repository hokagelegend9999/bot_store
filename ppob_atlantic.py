from telebot import types
from bot_init import bot
from atlantic_service import get_atlantic_price_list, get_unique_categories, filter_products_by_category

# Profit yang ingin Anda ambil (Contoh: 1000 rupiah per transaksi)
MARKUP_PROFIT = 1000

# ==========================================
# 1. MENU UTAMA: PILIH KATEGORI
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "ppob_atlantic")
def ppob_atlantic_main(call):
    bot.answer_callback_query(call.id, "🔄 Memuat Data Atlantic...")
    
    # Ambil data prabayar dari API Atlantic
    result = get_atlantic_price_list("prabayar")
    
    if result.get('status'):
        products = result.get('data', [])
        categories = get_unique_categories(products)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Buat tombol kategori secara dinamis
        btns = []
        for cat in categories:
            # Gunakan prefix 'atlcat|' untuk membedakan dengan provider lain
            btns.append(types.InlineKeyboardButton(cat, callback_data=f"atlcat|{cat}"))
        
        markup.add(*btns)
        markup.add(InlineKeyboardButton("🔥 PROMO XL DATA (XLD)", callback_data="list_xld_promo"))
        markup.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_user"))
        
        bot.edit_message_text(
            "📱 <b>PULSA & DATA LENGKAP (ATLANTIC)</b>\n"
            "Silahkan pilih kategori layanan di bawah ini:",
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=markup
        )
    else:
        bot.send_message(call.message.chat.id, f"❌ Gagal mengambil data provider: {result.get('message', 'Unknown Error')}")

# ==========================================
# 2. MENU KEDUA: LIST PRODUK PER KATEGORI
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("atlcat|"))
def ppob_atlantic_products(call):
    category = call.data.split("|")[1]
    bot.answer_callback_query(call.id, f"Kategori: {category}")
    
    result = get_atlantic_price_list("prabayar")
    if result.get('status'):
        all_products = result.get('data', [])
        # Filter produk sesuai kategori yang dipilih
        filtered = filter_products_by_category(all_products, category)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Tampilkan maksimal 15 produk agar tidak kepanjangan (Limit Telegram API)
        for p in filtered[:15]:
            try:
                # Hitung harga jual = Harga pusat + Profit
                sell_price = int(p['price']) + MARKUP_PROFIT
                
                # Format text tombol: Nama Produk - Rp Harga
                btn_text = f"{p['name']} - Rp {sell_price:,}"
                
                # Callback untuk proses beli nanti: atlbeli|KODE|HARGA
                # Contoh: atlbeli|PLN100|101000
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"atlbeli|{p['code']}|{sell_price}"))
            except:
                continue
            
        markup.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_atlantic"))
        
        bot.edit_message_text(
            f"🎁 <b>PRODUK {category}</b>\nSilahkan pilih produk yang ingin dibeli:",
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML', reply_markup=markup
        )