from telebot import types
from bot_init import bot
from atlantic_service import get_atlantic_products, get_atlantic_categories, filter_products_by_category

# --- MENU UTAMA KATEGORI ---
@bot.callback_query_handler(func=lambda call: call.data == "ppob_atlantic")
def atlantic_main_menu(call):
    bot.answer_callback_query(call.id, "🔄 Memuat Kategori...")
    products = get_atlantic_products("prabayar") # Default prabayar
    categories = get_atlantic_categories(products)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(cat, callback_data=f"atl_cat|{cat}") for cat in categories]
    markup.add(*btns)
    markup.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_user"))
    
    bot.edit_message_text("📱 <b>PILIH KATEGORI LAYANAN (ATLANTIC)</b>", 
                         call.message.chat.id, call.message.message_id, 
                         parse_mode='HTML', reply_markup=markup)

# --- MENU LIST PRODUK BERDASARKAN KATEGORI ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("atl_cat|"))
def atlantic_product_list(call):
    category = call.data.split("|")[1]
    bot.answer_callback_query(call.id, f"Memuat {category}...")
    
    products = get_atlantic_products("prabayar")
    filtered = filter_products_by_category(products, category)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in filtered[:20]: # Limit 20 produk agar tidak kepanjangan
        # Format: [Harga Asli + Profit 1000]
        sell_price = int(p['price']) + 1000 
        btn_text = f"{p['name']} - Rp {sell_price:,}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"atl_buy|{p['code']}"))
    
    markup.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="ppob_atlantic"))
    
    bot.edit_message_text(f"🎁 <b>PRODUK {category.upper()}</b>\nSilahkan pilih produk yang ingin dibeli:", 
                         call.message.chat.id, call.message.message_id, 
                         parse_mode='HTML', reply_markup=markup)