import telebot
import requests
import os
from telebot import types
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

# ====================== CONFIG ======================
TOKEN = os.getenv("TOKEN") or "8962392711:AAGoYjSYq4iuMupJaruE13YnHMrsJ3lVh-E"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDLbCpgUB1Tz68VEnobglQ3h_RbCUrt6yM"

bot = telebot.TeleBot(TOKEN)
user_queries = defaultdict(int)

# ====================== DATABASE ======================
def init_db():
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    is_premium INTEGER DEFAULT 0,
                    premium_until TEXT,
                    referral_count INTEGER DEFAULT 0,
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
        user = (user_id, 0, None, 0, datetime.now().date())
    conn.close()
    return user

def set_premium(user_id):
    until = (datetime.now() + timedelta(days=30)).isoformat()
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    conn.commit()
    conn.close()

# ====================== AI ======================
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=data, timeout=15).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 Tell me your skills or interests and I'll give you practical money making ideas."

# ====================== MENUS ======================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💰 Make Money", callback_data="money"))
    markup.add(types.InlineKeyboardButton("🛒 Digital Shop", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🧠 AI Advisor", callback_data="ai"))
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("🔗 Invite & Earn", callback_data="refer"))
    return markup

def get_shop_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📘 Affiliate Mastery - 150 Stars", callback_data="buy_affiliate"))
    markup.add(types.InlineKeyboardButton("🚀 Dropshipping Kit - 250 Stars", callback_data="buy_dropship"))
    markup.add(types.InlineKeyboardButton("📊 Crypto Signals - 300 Stars", callback_data="buy_signals"))
    return markup

# ====================== START ======================
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    bot.send_message(message.chat.id, 
                     "👋 Welcome to **MoneyMachine Bot** 🔥\n\n🇸🇦 Make Money in Saudi Arabia",
                     reply_markup=main_menu())

# ====================== CALLBACKS ======================
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

Reply with a number or tell me your skills!""")

    elif call.data == "shop":
        bot.send_message(uid, "🛒 **Digital Shop**", reply_markup=get_shop_menu())

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")

    elif call.data == "premium":
        bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Exclusive Content", 
                        "premium_monthly", "", "XTR", [types.LabeledPrice("Premium 30 Days", 500)])

    elif call.data == "refer":
        link = f"https://t.me/kkmachinebot?start=ref{uid}"
        bot.send_message(uid, f"🔗 **Your Referral Link**\n\n`{link}`", parse_mode='Markdown')

    elif call.data.startswith("buy_"):
        bot.send_message(uid, "✅ Payment system is ready!")

# ====================== PAYMENTS ======================
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    set_premium(message.from_user.id)
    bot.send_message(message.chat.id, "🎉 **Premium Activated!**")

# ====================== CHAT ======================
@bot.message_handler(func=lambda message: True)
def chat(message):
    uid = message.from_user.id
    user = get_user(uid)

    if user[1] == 1 or user_queries[uid] < 5:
        if user[1] == 0:
            user_queries[uid] += 1
        bot.reply_to(message, ask_gemini(message.text))
    else:
        bot.reply_to(message, "💎 Free limit reached. Upgrade to Premium!")

print("🚀 MoneyMachine Bot v6.7 Running!")
bot.infinity_polling()
