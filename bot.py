import os
import requests
import telebot
import base64
import json
from flask import Flask, request, abort
from pymongo import MongoClient

# --- কনফিগারেশন ---
API_TOKEN = '8876597863:AAE3A99UKha71_6X1hpJyZe8ySbTJkbLg_s'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') 
GITHUB_REPO = 'ya753121988/Apkbot'
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
ADMIN_ID = 7120801813

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
    if not GITHUB_TOKEN:
        return "TOKEN_MISSING"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # ফাইল আছে কি না চেক করা (SHA পাওয়ার জন্য)
    r_get = requests.get(url, headers=headers)
    sha = r_get.json().get('sha') if r_get.status_code == 200 else None
    
    payload = {
        "message": f"Update {path}", 
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'), 
        "branch": "main"
    }
    if sha: payload["sha"] = sha
    
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

# --- মাস্টার সেটআপ (Home Route) ---
@app.route("/")
def index():
    if not GITHUB_TOKEN:
        return "<h1>❌ GITHUB_TOKEN সেট করা নেই!</h1><p>Render Dashboard > Environment এ গিয়ে GITHUB_TOKEN সেট করুন।</p>", 500
    
    files = {
        "pubspec.yaml": "name: apkbot\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter: {sdk: flutter}\n  webview_flutter: ^4.2.2\n  url_launcher: ^6.1.11\nflutter: {uses-material-design: true}",
        "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(body:Center(child:Text('Ready')))));",
        "android/app/build.gradle": "apply plugin: 'com.android.application'\nandroid { compileSdkVersion 33 }",
        ".github/workflows/main.yml": f"name: Build\non: [repository_dispatch, push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: subosito/flutter-action@v2\n      - run: flutter build apk --release\n      - name: Send Document\n        run: curl -F chat_id='${{{{ github.event.client_payload.cid }}}}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument"
    }
    
    report = []
    for p, c in files.items():
        status = push_gh(p, c)
        report.append(f"{p}: {status}")
    
    return f"<h1>✅ মাস্টার সেটআপ রিপোর্ট</h1><p>{'<br>'.join(report)}</p>", 200

# --- বটের কমান্ডসমূহ ---
@bot.message_handler(commands=['start', 'balance'])
def start_cmd(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    bot.send_message(m.chat.id, f"🚀 ব্যালেন্স: {u['bal']} TK\nঅ্যাপ তৈরি: /create")

@bot.message_handler(commands=['create'])
def create_cmd(m):
    u = get_u(m.chat.id)
    if u['bal'] < 10:
        bot.reply_to(m, "❌ ব্যালেন্স নেই!")
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
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৩. অ্যাপ লোগো (ছবি) দিন:")
    elif s == "logo" and m.content_type == 'photo':
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -10, "apps": 1}, "$set": {"step": "n"}})
        
        sent_msg = bot.send_message(m.chat.id, "⏳ গিটহাবে ফাইল পুশ হচ্ছে... [██░░░░░░░░] 20%")

        n, url = u['data']['name'], u['data']['url']
        
        # ফাইল পুশ এবং স্ট্যাটাস চেক
        st = push_gh("lib/main.dart", f"import 'package:flutter/material.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}')),body:Center(child:Text('{url}')))));")
        
        if st in [200, 201]:
            bot.edit_message_text(f"🔨 বিল্ড শুরু হয়েছে... [██████░░░░] 60%", m.chat.id, sent_msg.message_id)
            
            # বিল্ড ট্রিগার
            res = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
                json={"event_type":"build_app","client_payload":{"cid":str(m.chat.id)}},
                headers={"Authorization":f"token {GITHUB_TOKEN}"})
            
            if res.status_code == 204:
                bot.edit_message_text("✅ বিল্ড প্রসেস সফল! গিটহাব থেকে APK আসা পর্যন্ত অপেক্ষা করুন।", m.chat.id, sent_msg.message_id)
            else:
                bot.send_message(m.chat.id, f"❌ গিটহাব ট্রিগার ফেইল! কোড: {res.status_code}")
        else:
            bot.send_message(m.chat.id, f"❌ ফাইল পুশ ফেইল! কোড: {st}\nআপনার টোকেন চেক করুন।")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "Forbidden", 403

if __name__ == "__main__":
    # রেন্ডার পোর্টের জন্য ডাইনামিক বাইন্ডিং
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
