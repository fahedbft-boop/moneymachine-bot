import telebot
import requests
import os
from telebot import types
import sqlite3
from datetime import datetime

# ====================== CONFIG ======================
TOKEN = os.getenv("TOKEN") or "8962392711:AAGoYjSYq4iuMupJaruE13YnHMrsJ3lVh-E"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDLbCpgUB1Tz68VEnobglQ3h_RbCUrt6yM"

bot = telebot.TeleBot(TOKEN)

def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=data, timeout=15).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 I'm ready to help! Ask me how to make money in Saudi Arabia."

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💰 Make Money", callback_data="money"))
    markup.add(types.InlineKeyboardButton("📈 BTC Price", callback_data="btc"))
    markup.add(types.InlineKeyboardButton("🛒 Digital Shop", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🧠 AI Advisor", callback_data="ai"))
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("🔗 Invite & Earn", callback_data="refer"))

    bot.send_message(message.chat.id, "👋 Welcome to **MoneyMachine Bot** 🔥\n\n🇸🇦 Make Money in Saudi Arabia", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id

    if call.data == "money":
        bot.send_message(uid, "💰 **Make Money Ideas**\n\nJust type your question!\nExample: How to earn 500 SAR per hour in Riyadh?")
    elif call.data == "btc":
        bot.send_message(uid, "📈 Bitcoin Price feature coming soon...")
    elif call.data == "shop":
        bot.send_message(uid, "🛒 Digital Shop coming soon...")
    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")
    elif call.data == "premium":
        bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Exclusive Strategies", "premium", "", "XTR", [types.LabeledPrice("Premium 30 Days", 500)])
    elif call.data == "refer":
        bot.send_message(uid, "🔗 Referral feature coming soon!")

@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    bot.send_message(message.chat.id, "🎉 Premium Activated!")

@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_message(message.chat.id, "🤔 Thinking...")
    response = ask_gemini(message.text)
    bot.reply_to(message, response)

print("🚀 Bot Running...")
bot.infinity_polling()
