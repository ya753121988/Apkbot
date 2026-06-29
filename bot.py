import os, requests, telebot, base64, json
from flask import Flask, request
from pymongo import MongoClient

# --- আপনার দেওয়া ইনফরমেশন (Hardcoded) ---
API_TOKEN = '8876597863:AAH1VB8WbDUn9pGvskiNLAQSL29rGNerMec'
GITHUB_TOKEN = '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'
GITHUB_REPO = 'ya753121988/Apkbot'
MONGO_URI = 'mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
ADMIN_ID = 7120801813
OWNER_ID = '@AkashDeveloperBot'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['SuperFinalBuilder']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "apps": 0, "data": {}}
        db.insert_one(u)
    return u

# --- গিটহাবে ফাইল ও ফোল্ডার তৈরি করার ফাংশন ---
def push_to_github(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # বর্তমান ফাইল আছে কি না চেক করা (SHA পাওয়ার জন্য)
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    payload = {
        "message": f"Setup: {path}",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "branch": "main"
    }
    if sha: payload["sha"] = sha
    
    response = requests.put(url, json=payload, headers=headers)
    return response.status_code, response.text

# --- অটো সেটআপ রুট (এই লিঙ্কে ঢুকলেই কাজ শুরু হবে) ---
@app.route("/")
def auto_setup():
    # এখানে সব ফোল্ডার ও ফাইল এর কোড
    files_to_push = {
        "pubspec.yaml": "name: apkbot\ndescription: Master\nversion: 1.0.0+1\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter: {sdk: flutter}\n  webview_flutter: ^4.2.2\n  url_launcher: ^6.1.11\nflutter: {uses-material-design: true}",
        
        "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(body:Center(child:Text('Bot Setup Done')))));",
        
        "android/build.gradle": "buildscript { repositories { google(); mavenCentral() }; dependencies { classpath 'com.android.tools.build:gradle:7.3.0' } }\nallprojects { repositories { google(); mavenCentral() } }",
        
        "android/app/build.gradle": "apply plugin: 'com.android.application'\nandroid {\n    compileSdkVersion 33\n    defaultConfig { applicationId \"com.apkbot.app\"; minSdkVersion 21; targetSdkVersion 33 }\n}",
        
        "android/app/src/main/AndroidManifest.xml": "<manifest xmlns:android='http://schemas.android.com/apk/res/android'>\n<uses-permission android:name='android.permission.INTERNET'/>\n<application android:label='ApkBot'>\n<activity android:name='.MainActivity' android:exported='true'><intent-filter><action android:name='android.intent.action.MAIN'/><category android:name='android.intent.category.LAUNCHER'/></intent-filter></activity></application></manifest>",
        
        ".github/workflows/main.yml": f"name: Build\non: [repository_dispatch, push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: subosito/flutter-action@v2\n      - run: flutter build apk --release\n      - name: Send\n        run: |\n          curl -F chat_id='${{{{ github.event.client_payload.cid }}}}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument"
    }

    report = []
    for path, content in files_to_push.items():
        code, msg = push_to_github(path, content)
        report.append(f"<li><b>{path}</b>: {code} ({'✅ Success' if code in [200, 201] else '❌ Failed'})</li>")

    return f"<h2>বিল্ড রিপোর্ট:</h2><ul>{''.join(report)}</ul><p>যদি সবগুলা Failed দেখায়, তবে আপনার GitHub Token এর পারমিশন চেক করুন।</p>", 200

# --- বট কমান্ডস ---
@bot.message_handler(commands=['start', 'balance'])
def start_bot(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    bot.send_message(m.chat.id, f"👋 স্বাগতম!\n💰 ব্যালেন্স: {u['bal']} TK\n💳 অ্যাপের দাম: {price} TK\n\nঅ্যাপ তৈরি: /create\nরিচার্জ: {OWNER_ID}")

@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ ব্যালেন্স যোগ করা হয়েছে।")
    except: bot.reply_to(m, "Format: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['create'])
def create_app(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    if u['bal'] < price:
        bot.reply_to(m, f"❌ ব্যালেন্স নেই! ওনারকে নক দিন: {OWNER_ID}")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "১. অ্যাপের নাম দিন:")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_steps(m):
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
        bot.send_message(m.chat.id, "৪. ৩-ডট মেনুর জন্য লিংক:")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. অ্যাপের লোগো (ছবি) পাঠান:")
    elif s == "logo" and m.content_type == 'photo':
        # এখানে ফাইল প্রসেস করে GitHub এ Dispatch পাঠানো হবে।
        bot.reply_to(m, "✅ সব তথ্য পাওয়া গেছে। বিল্ড প্রসেস শুরু হচ্ছে...")
        db.update_one({"cid": m.chat.id}, {"$inc": {"apps": 1, "bal": -10}, "$set": {"step": "n"}})
        # Dispatch Request
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={"event_type": "build_app", "client_payload": {"cid": str(m.chat.id)}},
            headers={"Authorization": f"token {GITHUB_TOKEN}"})

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
