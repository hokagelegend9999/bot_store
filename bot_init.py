import telebot
import logging
from config import BOT_TOKEN

# Inisialisasi Bot
bot = telebot.TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# Penyimpanan sementara untuk fitur "View As" (Owner lihat menu User)
TEMP_VIEW = {}