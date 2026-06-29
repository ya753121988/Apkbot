import os, requests, telebot, base64, json
from flask import Flask, request
from pymongo import MongoClient

# --- পরিবেশ ভেরিয়েবল (Vercel Settings এ অবশ্যই সেট করবেন) ---
API_TOKEN = os.environ.get('API_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO') # ইউজার/রিপো-নাম
ADMIN_ID = os.environ.get('ADMIN_ID')
OWNER_ID = os.environ.get('OWNER_ID') 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client['AppMasterDB']['users']

# --- গিটহাবে ফাইল পুশ করার মাস্টার ফাংশন ---
def push_to_github(path, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {"message": f"Auto setup: {path}", "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# --- অটো সেটআপ সিস্টেম (সব সোর্স কোড এখানে) ---
@app.route("/")
def auto_setup():
    try:
        # ১. Flutter Project Config (pubspec.yaml)
        pubspec = "name: apkbot\ndescription: Auto App\nversion: 1.0.0+1\nenvironment:\n  sdk: '>=3.0.0 <4.0.0'\ndependencies:\n  flutter: {sdk: flutter}\n  webview_flutter: ^4.2.2\n  url_launcher: ^6.1.11\nflutter: {uses-material-design: true}"
        push_to_github("pubspec.yaml", pubspec)

        # ২. Android Build Config (build.gradle)
        gradle_app = "apply plugin: 'com.android.application'\napply plugin: 'kotlin-android'\nandroid {\n    compileSdkVersion 33\n    defaultConfig {\n        applicationId \"com.yourapp.maker\"\n        minSdkVersion 21\n        targetSdkVersion 33\n        versionCode 1\n        versionName \"1.0\"\n    }\n    buildTypes { release { signingConfig signingConfigs.debug } }\n}"
        push_to_github("android/app/build.gradle", gradle_app)

        # ৩. Android Manifest (Internet and Title)
        manifest = "<manifest xmlns:android='http://schemas.android.com/apk/res/android'>\n<uses-permission android:name='android.permission.INTERNET'/>\n<application android:label='AppMaker'>\n<activity android:name='.MainActivity' android:exported='true'>\n<intent-filter><action android:name='android.intent.action.MAIN'/><category android:name='android.intent.category.LAUNCHER'/></intent-filter>\n</activity></application></manifest>"
        push_to_github("android/app/src/main/AndroidManifest.xml", manifest)

        # ৪. GitHub Actions Workflow (The Build Engine)
        workflow = f"name: Build\non: [repository_dispatch, push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: subosito/flutter-action@v2\n      - run: flutter build apk --release\n      - run: flutter build appbundle --release\n      - name: Send Document\n        run: |\n          curl -F chat_id='${{ github.event.client_payload.cid }}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument"
        push_to_github(".github/workflows/main.yml", workflow)

        return "<h1>✅ সব সোর্স কোড এবং ফোল্ডার আপনার গিটহাবে পুশ হয়ে গেছে!</h1><p>এখন বটটি ব্যবহার করা শুরু করুন।</p>", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

# --- বট ফাংশনালিটি ---
def get_u(cid):
    u = db.find_one({"cid": cid})
    if not u:
        u = {"cid": cid, "bal": 0, "step": "n", "apps": 0, "data": {}}
        db.insert_one(u)
    return u

@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    bot.send_message(m.chat.id, f"💰 ব্যালেন্স: {u['bal']} TK\n📦 তৈরি অ্যাপ: {u['apps']} টি\n💳 দাম: {price} TK\n\nঅ্যাপ বানাতে: /create\nরিচার্জ: {OWNER_ID}")

@bot.message_handler(commands=['create'])
def create(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    if u['bal'] < price:
        bot.reply_to(m, "❌ ব্যালেন্স নেই!")
        return
    db.update_one({"cid": m.chat.id}, {"$set": {"step": "name"}})
    bot.reply_to(m, "১. অ্যাপের নাম কি?")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle(m):
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
        bot.send_message(m.chat.id, "৫. লোগো (ছবি) দিন:")
    elif s == "logo" and m.content_type == 'photo':
        f_info = bot.get_file(m.photo[-1].file_id)
        logo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}"
        price = 10 if u['apps'] == 0 else 20
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -price, "apps": 1}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড শুরু হয়েছে।")

        n, url, color, dev = u['data']['name'], u['data']['url'], u['data']['color'], u['data']['dev']
        
        # অ্যাপের মূল কোড ইনজেকশন
        main_dart = f"import 'package:flutter/material.dart';\nimport 'package:webview_flutter/webview_flutter.dart';\nimport 'package:url_launcher/url_launcher.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}'),backgroundColor:Color({color.replace('#','0xff')}),actions:[PopupMenuButton(onSelected:(v)=>launchUrl(Uri.parse('{dev}')),itemBuilder:(c)=>[PopupMenuItem(value:1,child:Text('Developer'))])]),body:WebViewWidget(controller:WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse('{url}')))),debugShowCheckedModeBanner:false));"
        push_to_github("lib/main.dart", main_dart)
        
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
