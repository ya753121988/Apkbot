import os
import requests
import telebot
import base64
from flask import Flask, request, abort
from pymongo import MongoClient

# --- কনফিগারেশন ---
API_TOKEN = '8876597863:AAE3A99UKha71_6X1hpJyZe8ySbTJkbLg_s'
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') 
GITHUB_REPO = 'ya753121988/Apkbot'
MONGO_URI = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
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
    if not GITHUB_TOKEN: return "TOKEN_MISSING"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r_get = requests.get(url, headers=headers)
    sha = r_get.json().get('sha') if r_get.status_code == 200 else None
    payload = {"message": f"Update {path}", "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'), "branch": "main"}
    if sha: payload["sha"] = sha
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

# --- মাস্টার সেটআপ (Home Route) ---
@app.route("/")
def index():
    if not GITHUB_TOKEN: return "GITHUB_TOKEN Missing!", 500
    
    # এটি গিটহাবে ফাইলগুলো তৈরি করবে
    files = {
        "pubspec.yaml": "name: apkbot\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter: {sdk: flutter}\n  webview_flutter: ^4.2.2\nflutter: {uses-material-design: true}",
        "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(body:Center(child:Text('Ready')))));",
        "android/app/build.gradle": "apply plugin: 'com.android.application'\nandroid { compileSdkVersion 33 }",
        # পারসেন্টেজ আপডেট করার মেইন ম্যাজিক এই ফাইলে:
        ".github/workflows/main.yml": f"""
name: Build APK
on: [repository_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Update to 20%
        run: curl -s -X POST https://api.telegram.org/bot{API_TOKEN}/editMessageText -d chat_id=${{{{ github.event.client_payload.cid }}}} -d message_id=${{{{ github.event.client_payload.mid }}}} -d text="🔨 পরিবেশ সেটআপ হচ্ছে... [██░░░░░░░░] 20%"

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.10.0'
      
      - name: Update to 60%
        run: curl -s -X POST https://api.telegram.org/bot{API_TOKEN}/editMessageText -d chat_id=${{{{ github.event.client_payload.cid }}}} -d message_id=${{{{ github.event.client_payload.mid }}}} -d text="🔨 APK বিল্ড হচ্ছে... [██████░░░░] 60%"

      - run: flutter build apk --release

      - name: Update to 100%
        run: curl -s -X POST https://api.telegram.org/bot{API_TOKEN}/editMessageText -d chat_id=${{{{ github.event.client_payload.cid }}}} -d message_id=${{{{ github.event.client_payload.mid }}}} -d text="✅ বিল্ড সম্পন্ন! ফাইল পাঠানো হচ্ছে... [██████████] 100%"

      - name: Send APK
        run: curl -F chat_id='${{{{ github.event.client_payload.cid }}}}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument
"""
    }
    
    report = [f"{p}: {push_gh(p, c)}" for p, c in files.items()]
    return f"Setup Result: {report}", 200

# --- ব্যালেন্স অ্যাড কমান্ড ---
@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        args = m.text.split()
        target_id, amount = int(args[1]), int(args[2])
        db.update_one({"cid": target_id}, {"$inc": {"bal": amount}}, upsert=True)
        bot.send_message(m.chat.id, f"✅ ইউজার `{target_id}` কে {amount} TK দেওয়া হয়েছে।", parse_mode="Markdown")
    except:
        bot.reply_to(m, "ব্যবহার: `/addbalance আইিডি টাকা`", parse_mode="Markdown")

@bot.message_handler(commands=['start', 'balance'])
def start_cmd(m):
    u = get_u(m.chat.id)
    bot.send_message(m.chat.id, f"🚀 আইডি: `{m.chat.id}`\n💰 ব্যালেন্স: {u['bal']} TK\nঅ্যাপ তৈরি: /create", parse_mode="Markdown")

@bot.message_handler(commands=['create'])
def create_cmd(m):
    u = get_u(m.chat.id)
    if u['bal'] < 10:
        bot.reply_to(m, "❌ ব্যালেন্স নেই! রিচার্জ করুন।")
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
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -10}, "$set": {"step": "n"}})
        
        # প্রোগ্রেস মেসেজ শুরু
        sent_msg = bot.send_message(m.chat.id, "⏳ বিল্ড রিকোয়েস্ট পাঠানো হচ্ছে... [░░░░░░░░░░] 0%")
        n, url = u['data']['name'], u['data']['url']
        
        # ১. সোর্স কোড পুশ
        main_dart = f"import 'package:flutter/material.dart';\nimport 'package:webview_flutter/webview_flutter.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}')),body:WebViewWidget(controller:WebViewController()..loadRequest(Uri.parse('{url}'))))));"
        push_gh("lib/main.dart", main_dart)
        
        # ২. গিটহাব ট্রিগার (মেসেজ আইডি সহ)
        res = requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={
                "event_type": "build_app",
                "client_payload": {"cid": str(m.chat.id), "mid": str(sent_msg.message_id)}
            },
            headers={"Authorization": f"token {GITHUB_TOKEN}"})
        
        if res.status_code == 204:
            bot.edit_message_text("⏳ গিটহাব বিল্ড শুরু করেছে... [█░░░░░░░░░] 10%", m.chat.id, sent_msg.message_id)
        else:
            bot.send_message(m.chat.id, f"❌ এরর: {res.status_code}")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "!", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
