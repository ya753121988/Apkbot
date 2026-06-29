import os
import requests
import telebot
import base64
import json
from flask import Flask, request, abort
from pymongo import MongoClient

# --- কনফিগারেশন ---
API_TOKEN = '8876597863:AAE3A99UKha71_6X1hpJyZe8ySbTJkbLg_s'
GITHUB_TOKEN = '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'
GITHUB_REPO = 'ya753121988/Apkbot'
MONGO_URI = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
ADMIN_ID = 7120801813
OWNER_ID = '@AkashDeveloperBot'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client['FinalUltimateDB']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "apps": 0, "data": {}}
        db.insert_one(u)
    return u

def push_gh(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": f"Auto Setup: {path}", "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'), "branch": "main"}
    if sha: payload["sha"] = sha
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

# --- রুট রাউট (এটি থাকলে আর Not Found আসবে না) ---
@app.route('/')
def index():
    return "✅ Server is Running!", 200

# --- ওয়েবহুক রাউট (সবচেয়ে সহজ পাথ) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        abort(403)

# --- বটের কমান্ডসমূহ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ ব্যালেন্স যোগ সফল!")
    except: bot.reply_to(m, "Format: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['start', 'balance'])
def start_cmd(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    msg = (f"🚀 **Full Multi-Platform Builder**\n\n💰 ব্যালেন্স: {u['bal']} TK\n"
           f"📦 তৈরি অ্যাপ: {u['apps']} টি\n💳 দাম: {price} TK\n\nঅ্যাপ তৈরি: /create\nরিচার্জ: {OWNER_ID}")
    bot.send_message(m.chat.id, msg)

@bot.message_handler(commands=['create'])
def create_cmd(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    if u['bal'] < price:
        bot.reply_to(m, f"❌ ব্যালেন্স নেই! নক দিন: {OWNER_ID}")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "১. অ্যাপের নাম দিন:")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def steps(m):
    u = get_u(m.chat.id)
    s = u.get('step', 'n')
    if s == "name":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.name": m.text, "step": "url"}})
        bot.send_message(m.chat.id, "২. ওয়েবসাইট URL দিন:")
    elif s == "url":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "color"}})
        bot.send_message(m.chat.id, "৩. কালার কোড (যেমন: #ff5733):")
    elif s == "color":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.color": m.text, "step": "dev"}})
        bot.send_message(m.chat.id, "৪. ৩-ডট মেনু লিংক (চ্যানেল লিংক):")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. অ্যাপ লোগো (ছবি) দিন:")
    elif s == "logo" and m.content_type == 'photo':
        price = 10 if u['apps'] == 0 else 20
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -price, "apps": 1}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড শুরু হয়েছে। ১৫ মিনিট অপেক্ষা করুন।")
        n, url, c, d = u['data']['name'], u['data']['url'], u['data']['color'], u['data']['dev']
        main_dart = f"import 'package:flutter/material.dart';\nimport 'package:webview_flutter/webview_flutter.dart';\nimport 'package:url_launcher/url_launcher.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}'),backgroundColor:Color({c.replace('#','0xff')}),actions:[PopupMenuButton(onSelected:(v)=>launchUrl(Uri.parse('{d}')),itemBuilder:(c)=>[PopupMenuItem(value:1,child:Text('Developer'))])]),body:WebViewWidget(controller:WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse('{url}')))),debugShowCheckedModeBanner:false));"
        push_gh("lib/main.dart", main_dart)
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={"event_type":"build_app","client_payload":{"cid":str(m.chat.id)}},
            headers={"Authorization":f"token {GITHUB_TOKEN}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
