import os, requests, telebot
from flask import Flask, request
from pymongo import MongoClient

# কনফিগারেশন
API_TOKEN = 'YOUR_BOT_TOKEN'
MONGO_URI = 'YOUR_MONGODB_URI'
GITHUB_TOKEN = 'YOUR_GITHUB_TOKEN'
GITHUB_REPO = 'YOUR_USER/YOUR_REPO'
ADMIN_ID = 12345678 # আপনার আইডি
OWNER_ID = "@Your_Username"
PRICE = 10

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
db = MongoClient(MONGO_URI)['AppDB']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "data": {}}
        db.insert_one(u)
    return u

@bot.message_handler(commands=['addbalance'])
def add(m):
    if m.from_user.id != ADMIN_ID: return
    p = m.text.split()
    db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
    bot.reply_to(m, "✅ Added")

@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_u(m.chat.id)
    bot.send_message(m.chat.id, f"💰 Bal: {u['bal']} TK\nCreate: /create\nOwner: {OWNER_ID}")

@bot.message_handler(commands=['create'])
def create(m):
    u = get_u(m.chat.id)
    if u['bal'] < PRICE:
        bot.reply_to(m, f"❌ Low Balance! Contact {OWNER_ID}")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "Enter App Name:")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle(m):
    u = get_u(m.chat.id)
    s = u['step']
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
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -PRICE}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ Payment Success! Building App...")
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={"event_type":"build","client_payload":{"name":u['data']['name'],"url":u['data']['url'],"color":u['data']['color'],"dev":u['data']['dev'],"logo":l_url,"cid":str(m.chat.id)}},
            headers={"Authorization":f"token {GITHUB_TOKEN}"})

@app.route('/'+API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def i():
    bot.remove_webhook()
    bot.set_webhook(url='https://'+request.host+'/'+API_TOKEN)
    return "Running", 200
