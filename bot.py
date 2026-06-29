import os
import requests
import telebot
from flask import Flask, request
from pymongo import MongoClient

# --- কনফিগারেশন (এগুলো পরিবর্তন করুন) ---
API_TOKEN = 'YOUR_BOT_TOKEN'
MONGO_URI = 'YOUR_MONGODB_URI'
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN'
GITHUB_REPO = 'username/repo_name'
ADMIN_ID = 123456789  # আপনার আইডি
OWNER_USERNAME = "@Your_Username"
APP_PRICE = 10 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['PremiumAppBuilder']
users_col = db['users']

def get_user(chat_id):
    user = users_col.find_one({"chat_id": chat_id})
    if not user:
        user = {"chat_id": chat_id, "balance": 0, "step": "none", "data": {}}
        users_col.insert_one(user)
    return user

def update_user(chat_id, data):
    users_col.update_one({"chat_id": chat_id}, {"$set": data})

# --- অ্যাডমিন কমান্ডস ---
@bot.message_handler(commands=['addbalance'])
def add_bal(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amt = message.text.split()
        users_col.update_one({"chat_id": int(uid)}, {"$inc": {"balance": int(amt)}}, upsert=True)
        bot.reply_to(message, f"✅ সফল! ইউজার {uid} কে {amt} টাকা দেওয়া হয়েছে।")
        bot.send_message(int(uid), f"💰 অভিনন্দন! আপনার অ্যাকাউন্টে {amt} টাকা যোগ করা হয়েছে।")
    except: bot.reply_to(message, "❌ লিখুন: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['removebalance'])
def rem_bal(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, uid, amt = message.text.split()
        users_col.update_one({"chat_id": int(uid)}, {"$inc": {"balance": -int(amt)}})
        bot.reply_to(message, "✅ ব্যালেন্স কেটে নেওয়া হয়েছে।")
    except: bot.reply_to(message, "❌ ভুল ফরম্যাট!")

# --- ইউজার কমান্ডস ---
@bot.message_handler(commands=['start', 'balance'])
def start(message):
    user = get_user(message.chat.id)
    msg = (f"🚀 **Standalone App Builder Bot**\n\n"
           f"💰 আপনার ব্যালেন্স: {user['balance']} টাকা\n"
           f"💳 অ্যাপ প্রতি খরচ: {APP_PRICE} টাকা\n\n"
           f"অ্যাপ তৈরি করতে: /create\n"
           f"রিচার্জ করতে নক দিন: {OWNER_USERNAME}")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['create'])
def create(message):
    user = get_user(message.chat.id)
    if user['balance'] < APP_PRICE:
        bot.send_message(message.chat.id, f"⚠️ ব্যালেন্স নেই! রিচার্জ করতে নক দিন: {OWNER_USERNAME}\nআপনার আইডি: `{message.chat.id}`", parse_mode="Markdown")
        return
    update_user(message.chat.id, {"step": "name"})
    bot.reply_to(message, "১. অ্যাপের নাম কি হবে?")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    step = user.get('step')

    if step == "name":
        update_user(chat_id, {"data.name": message.text, "step": "url"})
        bot.send_message(chat_id, "২. ওয়েবসাইট URL দিন (যেমন: https://site.com):")
    
    elif step == "url":
        update_user(chat_id, {"data.url": message.text, "step": "color"})
        bot.send_message(chat_id, "৩. থিম কালার (Hex Code) দিন (যেমন: #ff5733):")

    elif step == "color":
        update_user(chat_id, {"data.color": message.text, "step": "dev"})
        bot.send_message(chat_id, "৪. ৩-ডট মেনুর জন্য ডেভেলপার লিংক দিন:")

    elif step == "dev":
        update_user(chat_id, {"data.dev": message.text, "step": "logo"})
        bot.send_message(chat_id, "৫. অ্যাপের লোগো (ছবি) পাঠান:")

    elif step == "logo" and message.content_type == 'photo':
        f_info = bot.get_file(message.photo[-1].file_id)
        l_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}"
        
        # ব্যালেন্স কাটুন
        users_col.update_one({"chat_id": chat_id}, {"$inc": {"balance": -APP_PRICE}, "$set": {"step": "none"}})
        
        bot.send_message(chat_id, "✅ পেমেন্ট সফল! বিল্ড শুরু হয়েছে। ১৫ মিনিট অপেক্ষা করুন।")
        
        # GitHub Dispatch (এখানেই আসল ম্যাজিক)
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={
                "event_type": "build_full_app",
                "client_payload": {
                    "name": user['data']['name'],
                    "url": user['data']['url'],
                    "color": user['data']['color'],
                    "dev": user['data']['dev'],
                    "logo": l_url,
                    "chat_id": str(chat_id)
                }
            }, 
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        )

# --- Vercel Webhook ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMsg():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + request.host + '/' + API_TOKEN)
    return "Standalone Builder Active", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
