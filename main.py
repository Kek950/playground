import telebot
from db import init_db, add_missing_column
from hendlers import request_handler

TOKEN = '7486512360:AAFwOR98fC9oYyA2mUfI6b-FyD4BDfMqvbA'
bot = telebot.TeleBot(TOKEN)

attendance_sessions = {}  # Stores in-progress attendance sessions per user

if __name__ == '__main__':
    init_db()
    add_missing_column()

    request_handler(bot, attendance_sessions)  # Register your handlers before polling

    bot.polling(none_stop=True)
