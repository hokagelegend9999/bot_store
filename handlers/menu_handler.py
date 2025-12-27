from bot_instance import bot, TEMP_VIEW
from config import ADMIN_ID
from database import add_user, get_user_data
from utils_view import get_menu_content

@bot.message_handler(commands=['start', 'menu'])
def start(m):
    add_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
    if m.from_user.id in TEMP_VIEW: del TEMP_VIEW[m.from_user.id]
    txt, mark = get_menu_content(m.from_user.id, m.from_user.first_name, m.from_user.username)
    bot.reply_to(m, txt, parse_mode='HTML', reply_markup=mark)

@bot.callback_query_handler(func=lambda call: call.data.startswith('switch_'))
def switch(call):
    uid = call.from_user.id
    if str(uid) == str(ADMIN_ID) or (get_user_data(uid)['role']=='reseller' and 'user' in call.data):
        if "reseller" in call.data and "back" not in call.data: TEMP_VIEW[uid] = "reseller"
        elif "user" in call.data: TEMP_VIEW[uid] = "user"
        else: 
            if uid in TEMP_VIEW: del TEMP_VIEW[uid]
        txt, mark = get_menu_content(uid, call.from_user.first_name, call.from_user.username)
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=mark)

@bot.callback_query_handler(func=lambda call: call.data == "menu_back")
def back(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    txt, mark = get_menu_content(call.from_user.id, call.from_user.first_name, call.from_user.username)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    bot.send_message(call.message.chat.id, txt, parse_mode='HTML', reply_markup=mark)