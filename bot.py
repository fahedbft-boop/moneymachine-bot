import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
import requests
import os
from collections import defaultdict

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

def set_premium(user_id):
    until = (datetime.now() + timedelta(days=30)).isoformat()
    conn = sqlite3.connect('moneybot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1, premium_until=? WHERE user_id=?", (until, user_id))
    conn.commit()
    conn.close()

# ====================== PRODUCT FILES (Change these IDs) ======================
PRODUCT_FILES = {
    "affiliate": {"name": "Affiliate_Mastery_Guide.pdf", "file_id": "YOUR_FILE_ID_HERE"},
    "dropship": {"name": "Dropshipping_Kit_Saudi.pdf", "file_id": "YOUR_FILE_ID_HERE"},
    "signals": {"name": "Crypto_Signals_Pack.pdf", "file_id": "YOUR_FILE_ID_HERE"},
    "notion": {"name": "Notion_Business_Planner.pdf", "file_id": "YOUR_FILE_ID_HERE"}
}

# ====================== AI ======================
def ask_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=data, timeout=20).json()
        return resp['candidates'][0]['content']['parts'][0]['text']
    except:
        return "💡 Tell me your skills or capital and I'll give you practical ideas for Saudi Arabia."

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💰 Make Money", callback_data="money"))
    markup.add(types.InlineKeyboardButton("🛒 Digital Shop", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("🧠 AI Advisor", callback_data="ai"))
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("🔗 Invite & Earn", callback_data="refer"))
    return markup

def shop_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📘 Affiliate Mastery Guide - 150 Stars", callback_data="buy_affiliate"))
    markup.add(types.InlineKeyboardButton("🚀 Dropshipping Kit (Saudi) - 250 Stars", callback_data="buy_dropship"))
    markup.add(types.InlineKeyboardButton("📊 Crypto Signals Pack - 300 Stars", callback_data="buy_signals"))
    markup.add(types.InlineKeyboardButton("📋 Notion Business Planner - 200 Stars", callback_data="buy_notion"))
    return markup

# ====================== START ======================
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    bot.send_message(message.chat.id, 
                     "👋 Welcome to **MoneyMachine Bot** 🔥\n\n"
                     "🇸🇦 Your Personal Money Making Machine in Saudi Arabia",
                     reply_markup=main_menu())

# ====================== CALLBACKS ======================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id

    if call.data == "money":
        bot.send_message(uid, """💰 **Best Money Making Methods in Saudi Arabia**

1. Affiliate Marketing
2. Digital Products
3. Dropshipping with local suppliers
4. Telegram Channels & Services

Reply with number or tell me your skills!""")

    elif call.data == "shop":
        bot.send_message(uid, "🛒 **Digital Shop** - Instant Delivery", reply_markup=shop_menu())

    elif call.data == "ai":
        bot.send_message(uid, "🧠 Ask me anything about making money!")

    elif call.data == "premium":
        bot.send_invoice(uid, "Premium Monthly", "Unlimited AI + Daily Tips + Exclusive Guides", 
                        "premium_monthly", "", "XTR", [types.LabeledPrice("Premium 30 Days", 500)])

    elif call.data == "refer":
        link = f"https://t.me/kkmachinebot?start=ref{uid}"
        bot.send_message(uid, f"🔗 **Your Referral Link**\n\n`{link}`", parse_mode='Markdown')

    elif call.data.startswith("buy_"):
        product = call.data.replace("buy_", "")
        bot.send_message(uid, f"✅ Processing payment for **{product}**...")

# ====================== PAYMENTS + AUTO FILE DELIVERY ======================
@bot.pre_checkout_query_handler(func=lambda q: True)
def checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    payload = message.successful_payment.invoice_payload
    uid = message.from_user.id

    if "premium" in payload:
        set_premium(uid)
        bot.send_message(uid, "🎉 **Premium Activated!** Unlimited AI unlocked!")
    else:
        product = payload.replace("buy_", "")
        bot.send_message(uid, f"✅ Payment Successful!\n📤 Sending your file...")

        if product in PRODUCT_FILES:
            file_info = PRODUCT_FILES[product]
            try:
                with open(file_info["name"], "rb") as f:   # If you upload files to same folder
                    bot.send_document(uid, f, caption=f"Here is your **{file_info['name']}** ✅")
            except:
                bot.send_message(uid, f"📥 **Your File:**\n{file_info.get('link', 'File delivered!')}")
        else:
            bot.send_message(uid, "✅ Product delivered!")

@bot.message_handler(func=lambda message: True)
def chat(message):
    uid = message.from_user.id
    if user_queries[uid] < 5:
        user_queries[uid] += 1
        bot.reply_to(message, ask_gemini(message.text))
    else:
        bot.reply_to(message, "💎 Free limit reached. Upgrade to Premium!")

print("🚀 MoneyMachine Bot v9.3 with Auto File Delivery Running!")
bot.infinity_polling()
