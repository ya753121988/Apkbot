import os
import requests
import telebot
from flask import Flask, request
from pymongo import MongoClient

# --- ভেরিয়েবল কনফিগারেশন (এগুলো Vercel থেকে আসবে) ---
API_TOKEN = os.environ.get('API_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
ADMIN_ID = os.environ.get('ADMIN_ID')
OWNER_ID = os.environ.get('OWNER_ID')
PRICE = os.environ.get('PRICE', '10')

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['AppDB']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "data": {}}
        db.insert_one(u)
    return u

@bot.message_handler(commands=['addbalance'])
def add(m):
    if str(m.from_user.id) != str(ADMIN_ID): return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ Balance Added Successfully!")
    except: bot.reply_to(m, "❌ Format: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_u(m.chat.id)
    bot.send_message(m.chat.id, f"💰 Balance: {u['bal']} TK\nTo Create App: /create\nOwner: {OWNER_ID}")

@bot.message_handler(commands=['create'])
def create(m):
    u = get_u(m.chat.id)
    if u['bal'] < int(PRICE):
        bot.reply_to(m, f"❌ Low Balance! Contact {OWNER_ID} to recharge.")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "Enter App Name:")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle(m):
    u = get_u(m.chat.id)
    s = u.get('step', 'n')
    
    if s == "name":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.name": m.text, "step": "url"}})
        bot.send_message(m.chat.id, "Enter Website URL:")
    elif s == "url":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "color"}})
        bot.send_message(m.chat.id, "Enter Hex Color (e.g. #ff5733):")
    elif s == "color":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.color": m.text, "step": "dev"}})
        bot.send_message(m.chat.id, "Enter Developer Channel Link:")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "Send App Logo (Image):")
    elif s == "logo" and m.content_type == 'photo':
        img = bot.get_file(m.photo[-1].file_id)
        l_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{img.file_path}"
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -int(PRICE)}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ Payment Success! Building App... Please wait 15 mins.")
        
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={"event_type":"build","client_payload":{"name":u['data']['name'],"url":u['data']['url'],"color":u['data']['color'],"dev":u['data']['dev'],"logo":l_url,"cid":str(m.chat.id)}},
            headers={"Authorization":f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"})

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return "Forbidden", 403

@app.route("/")
def index():
    return "Bot is Running Securely!", 200
