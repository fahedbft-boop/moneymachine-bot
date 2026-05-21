import telebot
import requests
import os
from telebot import types
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import random

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

def set_premium(user_id, days=30):
    until = (datetime.now() + timedelta(days=days)).isoformat()
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    conn.commit()
    conn.close()

# ====================== AI ======================
def ask_gemini(prompt):
    try:
        full_prompt = f"You are a practical money-making expert. Give realistic step-by-step advice.\nUser: {prompt}"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": full_prompt}]}]}
        resp = requests.post(url, json=data, timeout=15).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 Tell me your skills, location (Saudi), or interest and I'll give you personalized money ideas."

# ====================== KEYBOARDS ======================
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

@bot.message_handler(commands=['myplan'])
def myplan(message):
    user = get_user(message.from_user.id)
    if user[1] == 1:
        bot.reply_to(message, "✅ **Premium Active**")
    else:
        bot.reply_to(message, "🆓 **Free Plan** (5 queries/day)")

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    user = get_user(uid)

    if call.data == "money":
        bot.send_message(uid, """💰 **Make Money Options**

1. Affiliate Marketing (Best for beginners)
2. Digital Products (Highest profit)
3. Dropshipping
4. Telegram Services

Reply with a number or tell me your skills!""")

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!\nExample: Best side hustle in Saudi Arabia")

    elif call.data == "shop":
        bot.send_message(uid, "🛒 **Digital Shop**", reply_markup=get_shop_menu())

    elif call.data == "premium":
        if user[1] == 1:
            bot.send_message(uid, "✅ You already have Premium!")
        else:
            bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Exclusive Content + Priority Support", 
                           "premium_monthly", "", "XTR", [types.LabeledPrice("Premium 30 Days", 500)])

    elif call.data == "refer":
        link = f"https://t.me/{bot.get_me().username}?start=ref{uid}"
        bot.send_message(uid, f"🔗 **Your Referral Link**\n\n`{link}`\n\nEvery 3 successful referrals = 1 Free Month!", parse_mode='Markdown')

    elif call.data.startswith("buy_"):
        bot.send_message(uid, "✅ Payment feature is ready! (Test mode)")

# ====================== PAYMENTS ======================
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    if "premium" in message.successful_payment.invoice_payload:
        set_premium(message.from_user.id)
        bot.send_message(message.chat.id, "🎉 **Premium Activated!** Unlimited AI unlocked!")

# ====================== MAIN CHAT ======================
@bot.message_handler(func=lambda message: True)
def chat(message):
    uid = message.from_user.id
    user = get_user(uid)

    if user[1] == 1:  # Premium
        bot.send_message(uid, "🤔 Thinking...")
        bot.reply_to(message, ask_gemini(message.text))
    else:
        if user_queries[uid] < 5:
            user_queries[uid] += 1
            bot.send_message(uid, "🤔 Thinking...")
            bot.reply_to(message, ask_gemini(message.text))
        else:
            bot.reply_to(message, "💎 Free limit reached (5/day).\nUpgrade to Premium!")

print("🚀 MoneyMachine Bot Updated & Fixed!")
bot.infinity_polling()
