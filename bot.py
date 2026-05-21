import telebot
from telebot import types
import os

TOKEN = os.getenv("TOKEN") or "8962392711:AAGoYjSYq4iuMupJaruE13YnHMrsJ3lVh-E"
bot = telebot.TeleBot(TOKEN)

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💰 Make Money", callback_data="money"))
    markup.add(types.InlineKeyboardButton("🛒 Digital Shop", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🧠 AI Advisor", callback_data="ai"))
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("🔗 Invite & Earn", callback_data="refer"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Welcome to **MoneyMachine Bot** 🔥", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id

    print(f"DEBUG: Button clicked -> {call.data}")   # This will show in Railway Logs

    if call.data == "money":
        bot.send_message(uid, "💰 **Make Money Section**\n\nThis is working now!")

    elif call.data == "shop":
        bot.send_message(uid, "🛒 **Digital Shop**\n\nProducts will be listed here soon!")

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")

    elif call.data == "premium":
        bot.send_message(uid, "⭐ Premium feature coming soon!")

    elif call.data == "refer":
        bot.send_message(uid, "🔗 Referral feature coming soon!")

print("🚀 Simple Test Bot Running...")
bot.infinity_polling()
