import os
import requests
import telebot
import base64
from flask import Flask, request
from pymongo import MongoClient

# --- কনফিগারেশন (Vercel Environment Variables এ সেট করবেন) ---
API_TOKEN = os.environ.get('API_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO') # Example: ya753121988/Apkbot
ADMIN_ID = os.environ.get('ADMIN_ID')
OWNER_USERNAME = os.environ.get('OWNER_USERNAME') # @YourUsername
PRICE = int(os.environ.get('PRICE', 10))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['FinalBuilder']['users']

def get_user(cid):
    user = db.find_one({"cid": cid})
    if not user:
        user = {"cid": cid, "bal": 0, "step": "n", "data": {}}
        db.insert_one(user)
    return user

# --- গিটহাব ফাইল অটোমেশন কোড (Standalone System) ---
# এই ফাংশনটি আপনার গিটহাবে সোর্স কোড ইনজেক্ট করবে যাতে অ্যাপ সারা জীবন চলে
def push_to_github(path, content, message="Update"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # বর্তমান ফাইলের SHA চেক করা (যদি ফাইল আগে থেকে থাকে)
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# --- অ্যাডমিন কমান্ডস ---
@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if str(m.from_user.id) != str(ADMIN_ID): return
    try:
        _, uid, amt = m.text.split()
        db.update_one({"cid": int(uid)}, {"$inc": {"bal": int(amt)}}, upsert=True)
        bot.reply_to(m, f"✅ User {uid} কে {amt} টাকা দেওয়া হয়েছে।")
        bot.send_message(int(uid), f"💰 আপনার ব্যালেন্সে {amt} টাকা যোগ হয়েছে।")
    except: bot.reply_to(m, "❌ Format: /addbalance [UID] [Amount]")

# --- ইউজার প্রসেস ---
@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_user(m.chat.id)
    msg = (f"🚀 **Full Multi-Platform App Builder**\n\n"
           f"💰 ব্যালেন্স: {u['bal']} টাকা\n"
           f"💳 খরচ: {PRICE} টাকা প্রতি অ্যাপ\n\n"
           f"অ্যাপ তৈরি করতে: /create লিখুন\n"
           f"রিচার্জ করতে নক দিন: {OWNER_USERNAME}")
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['create'])
def create(m):
    u = get_user(m.chat.id)
    if u['bal'] < PRICE:
        bot.send_message(m.chat.id, f"⚠️ ব্যালেন্স নেই! নক দিন: {OWNER_USERNAME}\nআপনার আইডি: `{m.chat.id}`", parse_mode="Markdown")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "১. অ্যাপের নাম দিন:")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_steps(m):
    u = get_user(m.chat.id)
    step = u.get('step', 'n')

    if step == "name":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.name": m.text, "step": "url"}})
        bot.send_message(m.chat.id, "২. ওয়েবসাইট URL দিন:")
    elif step == "url":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "color"}})
        bot.send_message(m.chat.id, "৩. কালার কোড (Hex) দিন (যেমন: #000000):")
    elif step == "color":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.color": m.text, "step": "dev"}})
        bot.send_message(m.chat.id, "৪. ডেভেলপার চ্যানেল লিংক দিন:")
    elif step == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. লোগো (ছবি) পাঠান:")
    elif step == "logo" and m.content_type == 'photo':
        f_info = bot.get_file(m.photo[-1].file_id)
        logo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}"
        
        # পেমেন্ট কাটা
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -PRICE}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড কনফিগারেশন তৈরি হচ্ছে...")

        # সোর্স কোড ইনজেকশন (এই এক বিন্দু কোড ও মিস হবে না)
        app_name = u['data']['name']
        app_url = u['data']['url']
        app_color = u['data']['color'].replace("#", "0xFF")
        dev_link = u['data']['dev']

        # ১. Flutter Main Code তৈরি করা
        flutter_code = f"""
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
void main() => runApp(MaterialApp(home: Scaffold(
  appBar: AppBar(title: Text("{app_name}"), backgroundColor: Color({app_color}), 
  actions: [PopupMenuButton(onSelected: (v)=> launchUrl(Uri.parse("{dev_link}")), 
  itemBuilder: (c)=> [PopupMenuItem(value: 1, child: Text("Developer Channel"))])]),
  body: WebViewWidget(controller: WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse("{app_url}"))),
), debugShowCheckedModeBanner: false));
"""
        push_to_github("lib/main.dart", flutter_code)

        # ২. GitHub Workflow তৈরি করা (বিল্ড প্রসেস)
        workflow_code = f"""
name: Build App
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
      - run: flutter build apk --release
      - name: Send to Telegram
        run: curl -F chat_id="{m.chat.id}" -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument
"""
        push_to_github(".github/workflows/main.yml", workflow_code)

        bot.send_message(m.chat.id, "🛠 সব ফাইল সিঙ্ক হয়েছে। গিটহাব এখন আপনার APK তৈরি করছে। ১০-১৫ মিনিট পর ইনবক্সে ফাইল পেয়ে যাবেন।")

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    return "Standalone Builder is Online!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
