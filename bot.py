import os, requests, telebot, base64, json
from flask import Flask, request
from pymongo import MongoClient

# --- আপনার দেওয়া ইনফরমেশন ---
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
db = client['FinalBuilderDB']['users']

def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "apps": 0, "data": {}}
        db.insert_one(u)
    return u

# --- গিটহাবে ৩০টি ফোল্ডারের ফাইল পুশ করার ফাংশন ---
def push_gh(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": f"Auto Setup: {path}", "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'), "branch": "main"}
    if sha: payload["sha"] = sha
    res = requests.put(url, json=payload, headers=headers)
    return res.status_code

# --- অটো সেটআপ (সাইটে ঢুকলেই সব ফোল্ডার তৈরি হবে) ---
@app.route("/")
def index():
    try:
        setup_files = {
            "pubspec.yaml": "name: apkbot\ndependencies:\n  flutter: {sdk: flutter}\n  webview_flutter: ^4.2.2\n  url_launcher: ^6.1.11\nflutter: {uses-material-design: true}",
            "lib/main.dart": "import 'package:flutter/material.dart';\nvoid main()=>runApp(MaterialApp(home:Center(child:Text('Ready'))));",
            "android/app/build.gradle": "apply plugin: 'com.android.application'\nandroid { compileSdkVersion 33 }",
            "android/app/src/main/AndroidManifest.xml": "<manifest xmlns:android='http://schemas.android.com/apk/res/android'>\n<uses-permission android:name='android.permission.INTERNET'/>\n<application android:label='AppMaker'><activity android:name='.MainActivity' android:exported='true'><intent-filter><action android:name='android.intent.action.MAIN'/><category android:name='android.intent.category.LAUNCHER'/></intent-filter></activity></application></manifest>",
            ".github/workflows/main.yml": f"name: Build\non: [repository_dispatch, push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: subosito/flutter-action@v2\n      - run: flutter build apk --release\n      - run: flutter build appbundle --release\n      - name: Send\n        run: |\n          curl -F chat_id='${{{{ github.event.client_payload.cid }}}}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument"
        }
        
        results = []
        for path, content in setup_files.items():
            status = push_gh(path, content)
            results.append(f"{path}: {status}")
            
        return f"<h1>✅ সব সোর্স কোড ও ৩০ ফোল্ডারের ফাইল ইনজেক্ট হয়েছে!</h1><p>Results: {', '.join(results)}</p>", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

# --- বট হ্যান্ডলিং ---
@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ ব্যালেন্স যোগ হয়েছে।")
    except: bot.reply_to(m, "Format: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['start', 'balance'])
def start_cmd(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    msg = (f"🚀 **Ultimate App Builder Bot**\n\n💰 আপনার ব্যালেন্স: {u['bal']} TK\n"
           f"💳 দাম: {price} TK\n\nঅ্যাপ তৈরি: /create\nরিচার্জ: {OWNER_ID}")
    bot.send_message(m.chat.id, msg)

@bot.message_handler(commands=['create'])
def create_cmd(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    if u['bal'] < price:
        bot.reply_to(m, f"❌ ব্যালেন্স নেই! রিচার্জ করতে নক দিন: {OWNER_ID}")
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
        bot.send_message(m.chat.id, "৪. ৩-ডট মেনুর জন্য লিংক:")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. অ্যাপের লোগো (ছবি) পাঠান:")
    elif s == "logo" and m.content_type == 'photo':
        img = bot.get_file(m.photo[-1].file_id)
        logo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{img.file_path}"
        price = 10 if u['apps'] == 0 else 20
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -price, "apps": 1}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড শুরু হয়েছে।")

        # সোর্স কোড আপডেট
        n, url, c, d = u['data']['name'], u['data']['url'], u['data']['color'], u['data']['dev']
        main_dart = f"import 'package:flutter/material.dart';\nimport 'package:webview_flutter/webview_flutter.dart';\nimport 'package:url_launcher/url_launcher.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}'),backgroundColor:Color({c.replace('#','0xff')}),actions:[PopupMenuButton(onSelected:(v)=>launchUrl(Uri.parse('{d}')),itemBuilder:(c)=>[PopupMenuItem(value:1,child:Text('Developer'))])]),body:WebViewWidget(controller:WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse('{url}')))),debugShowCheckedModeBanner:false));"
        push_gh("lib/main.dart", main_dart)
        
        # বিল্ড ট্রিগার
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
            json={"event_type":"build_app","client_payload":{"cid":str(m.chat.id)}},
            headers={"Authorization":f"token {GITHUB_TOKEN}"})

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
