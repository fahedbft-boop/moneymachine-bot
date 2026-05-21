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
user_last_reset = defaultdict(datetime)

# Database
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
    conn.close()
    return user

def set_premium(user_id, days=30):
    until = (datetime.now() + timedelta(days=days)).isoformat()
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    conn.commit()
    conn.close()

# AI Function
def ask_gemini(prompt):
    try:
        full_prompt = f"""You are a practical money-making expert in Saudi Arabia. 
Give realistic, step-by-step advice suitable for Saudi market.

User question: {prompt}"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": full_prompt}]}]}
        resp = requests.post(url, json=data, timeout=15).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 Ask me specific questions like:\n• How to earn 500 SAR per hour in Riyadh\n• Best side hustle in Saudi Arabia"

# ====================== START ======================
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💰 Make Money", callback_data="money"))
    markup.add(types.InlineKeyboardButton("📈 BTC Price", callback_data="btc"))
    markup.add(types.InlineKeyboardButton("🛒 Digital Shop", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🧠 AI Advisor", callback_data="ai"))
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("🔗 Invite & Earn", callback_data="refer"))

    bot.send_message(message.chat.id, 
                     "👋 Welcome to **MoneyMachine Bot** 🔥\n\n"
                     "🇸🇦 Real Ways to Make Money in Saudi Arabia\n"
                     "Choose below 👇", 
                     reply_markup=markup)

@bot.message_handler(commands=['myplan'])
def myplan(message):
    user = get_user(message.from_user.id)
    if user and user[1] == 1:
        bot.reply_to(message, "✅ **Premium Active**")
    else:
        bot.reply_to(message, "🆓 **Free Plan** (5 queries/day)")

# ====================== FIXED CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id

    if call.data == "money":
        bot.send_message(uid, "💰 **Make Money Ideas**\n\nJust type your question!\n\nExamples:\n• How to earn 500 SAR per hour\n• Best side hustle in Riyadh\n• How to start dropshipping in Saudi")

    elif call.data == "btc":
        price = get_btc_price()
        bot.send_message(uid, f"📈 **Bitcoin Price**\n\n${price:,} USD")

    elif call.data == "shop":
        bot.send_message(uid, "🛒 **Digital Shop**", reply_markup=get_shop_menu())

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")

    elif call.data == "premium":
        bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Exclusive Strategies", 
                        "premium_monthly", "", "XTR", [types.LabeledPrice("Premium 30 Days", 500)])

    elif call.data == "refer":
        link = f"https://t.me/{bot.get_me().username}?start=ref{uid}"
        bot.send_message(uid, f"🔗 **Your Referral Link**\n\n`{link}`\n\nEvery 3 referrals = 1 Free Premium Month!", parse_mode='Markdown')

    elif call.data.startswith("buy_"):
        bot.send_message(uid, "✅ Payment option selected!")

def get_shop_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📘 Affiliate Mastery - 150 Stars", callback_data="buy_affiliate"))
    markup.add(types.InlineKeyboardButton("🚀 Dropshipping Kit - 250 Stars", callback_data="buy_dropship"))
    return markup

def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10)
        return r.json()['bitcoin']['usd']
    except:
        return 77000

# Payments
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    if "premium" in message.successful_payment.invoice_payload:
        set_premium(message.from_user.id, 30)
        bot.send_message(message.chat.id, "🎉 **Premium Activated Successfully!**\nUnlimited AI unlocked 🔥")

# Main Chat
@bot.message_handler(func=lambda message: True)
def chat(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if user and user[1] == 1:
        bot.send_message(uid, "🤔 Thinking...")
        bot.reply_to(message, ask_gemini(message.text))
    else:
        if user_queries[uid] < 5:
            user_queries[uid] += 1
            bot.send_message(uid, "🤔 Thinking...")
            bot.reply_to(message, ask_gemini(message.text))
        else:
            bot.reply_to(message, "💎 Free limit reached.\nUpgrade to Premium!")

print("🚀 MoneyMachine Bot Running...")
bot.infinity_polling()
