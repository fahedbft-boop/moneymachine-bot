import telebot
import requests
import os
from telebot import types
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("TOKEN") or "8962392711:AAGoYjSYq4iuMupJaruE13YnHMrsJ3lVh-E"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDLbCpgUB1Tz68VEnobglQ3h_RbCUrt6yM"

bot = telebot.TeleBot(TOKEN)
user_queries = defaultdict(int)

# Database
def init_db():
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    is_premium INTEGER DEFAULT 0,
                    premium_until TEXT,
                    joined DATE)''')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, joined) VALUES (?, ?)", (user_id, datetime.now().date()))
        conn.commit()
    conn.close()
    return user

# AI Function
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=data, timeout=15).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 Tell me your skills or interests, I'll give you good money ideas."

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
    get_user(message.from_user.id)
    bot.send_message(message.chat.id, "👋 Welcome to **MoneyMachine Bot** 🔥\n\n🇸🇦 Make Money in Saudi Arabia", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id

    if call.data == "money":
        bot.send_message(uid, """💰 **Make Money Options**

1. Affiliate Marketing
2. Digital Products
3. Dropshipping
4. Telegram Services

Reply with a number (1-4) or tell me your skills!""")

    elif call.data == "shop":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📘 Affiliate Guide - 150 Stars", callback_data="buy_affiliate"))
        markup.add(types.InlineKeyboardButton("🚀 Dropshipping Kit - 250 Stars", callback_data="buy_dropship"))
        bot.send_message(uid, "🛒 **Digital Shop** - Choose a product:", reply_markup=markup)

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")

    elif call.data == "premium":
        bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Exclusive Content", "premium_monthly", "", "XTR", [types.LabeledPrice("Premium", 500)])

    elif call.data == "refer":
        link = f"https://t.me/kkmachinebot?start=ref{uid}"
        bot.send_message(uid, f"🔗 Your Link:\n`{link}`", parse_mode='Markdown')

    elif call.data.startswith("buy_"):
        bot.send_message(uid, "✅ Payment ready!")

# Payments
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    bot.send_message(message.chat.id, "🎉 Premium Activated!")

@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = message.from_user.id
    if user_queries[uid] < 5:
        user_queries[uid] += 1
        bot.reply_to(message, ask_gemini(message.text))
    else:
        bot.reply_to(message, "💎 Free limit reached. Upgrade to Premium!")

print("🚀 Bot Running - v6.8")
bot.infinity_polling()
