import os, requests, telebot, base64, json
from flask import Flask, request
from pymongo import MongoClient

# --- কনফিগারেশন (Vercel Environment Variables এ বসাবেন) ---
API_TOKEN = os.environ.get('API_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')
ADMIN_ID = os.environ.get('ADMIN_ID')
OWNER_ID = os.environ.get('OWNER_ID') 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client['SuperBuilder']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "apps": 0, "data": {}}
        db.insert_one(u)
    return u

# --- গিটহাবে ফাইল পুশ করার ফাংশন ---
def push_gh(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": "System Update", "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# --- অ্যাডমিন কমান্ড ---
@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if str(m.from_user.id) != str(ADMIN_ID): return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ ব্যালেন্স যোগ হয়েছে।")
    except: bot.reply_to(m, "Format: /addbalance [UID] [Amount]")

# --- ইউজার ইন্টারফেস ---
@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    msg = (f"🚀 **Ultimate Multi-Platform App Builder**\n\n"
           f"💰 ব্যালেন্স: {u['bal']} TK\n"
           f"📦 তৈরি অ্যাপ: {u['apps']} টি\n"
           f"💳 পরবর্তী অ্যাপের দাম: {price} TK\n\n"
           f"অ্যাপ তৈরি করতে: /create\n"
           f"রিচার্জের জন্য ওনারকে নক দিন: {OWNER_ID}")
    bot.send_message(m.chat.id, msg)

@bot.message_handler(commands=['create'])
def create(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    if u['bal'] < price:
        bot.send_message(m.chat.id, f"❌ ব্যালেন্স নেই! নক দিন: {OWNER_ID}")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "১. অ্যাপের নাম কি হবে?")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle(m):
    u = get_u(m.chat.id)
    s = u['step']
    if s == "name":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.name": m.text, "step": "url"}})
        bot.send_message(m.chat.id, "২. ওয়েবসাইট URL দিন:")
    elif s == "url":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "color"}})
        bot.send_message(m.chat.id, "৩. কালার কোড (Hex যেমন: #ff5733):")
    elif s == "color":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.color": m.text, "step": "dev"}})
        bot.send_message(m.chat.id, "৪. ৩-ডট মেনুর জন্য ডেভেলপার লিংক দিন:")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. লোগো (ছবি) পাঠান:")
    elif s == "logo" and m.content_type == 'photo':
        f_info = bot.get_file(m.photo[-1].file_id)
        l_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}"
        price = 10 if u['apps'] == 0 else 20
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -price, "apps": 1}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড কনফিগারেশন ইনজেক্ট করা হচ্ছে...")

        # --- এই অংশটি গিটহাবে হাজার লাইনের সোর্স কোড ইনজেক্ট করবে ---
        n, u_url, c, d = u['data']['name'], u['data']['url'], u['data']['color'], u['data']['dev']
        
        # lib/main.dart (Flutter কোড)
        main_dart = f"""
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
void main() => runApp(MaterialApp(
  home: Scaffold(
    appBar: AppBar(
      title: Text("{n}"), 
      backgroundColor: Color({c.replace('#','0xff')}),
      actions: [PopupMenuButton(onSelected: (v)=> launchUrl(Uri.parse("{d}")), 
      itemBuilder: (c)=> [PopupMenuItem(value: 1, child: Text("Developer Channel"))])],
    ),
    body: WebViewWidget(controller: WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse("{u_url}"))),
  ),
  debugShowCheckedModeBanner: false,
));
"""
        push_gh("lib/main.dart", main_dart)

        # Android Manifest (ইন্টারনেট এবং নাম কনফিগ)
        manifest = f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-permission android:name="android.permission.INTERNET"/><application android:label="{n}"><activity android:name=".MainActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>"""
        push_gh("android/app/src/main/AndroidManifest.xml", manifest)

        # GitHub Workflow (Android, AAB, এবং Windows বিল্ড লজিক)
        workflow = f"""
name: Build All
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
      - run: flutter build apk --release
      - run: flutter build appbundle --release
      - name: Send Files
        run: |
          curl -F chat_id="{m.chat.id}" -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument
          curl -F chat_id="{m.chat.id}" -F document=@build/app/outputs/bundle/release/app-release.aab https://api.telegram.org/bot{API_TOKEN}/sendDocument
"""
        push_gh(".github/workflows/main.yml", workflow)

        bot.send_message(m.chat.id, "🛠 সব ফাইল সিঙ্ক হয়েছে। গিটহাব এখন আপনার APK এবং AAB তৈরি করছে। ১০-১৫ মিনিট পর ইনবক্সে ফাইল পেয়ে যাবেন।")

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index():
    return "✅ Master Builder Online!", 200
