import os, requests, telebot, base64, json
from flask import Flask, request
from pymongo import MongoClient

# --- এই ভেরিয়েবলগুলো Vercel এর Settings > Environment Variables এ অবশ্যই বসাবেন ---
API_TOKEN = os.environ.get('API_TOKEN')
MONGO_URI = os.environ.get('MONGO_URI')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO') # Example: user/repo
ADMIN_ID = os.environ.get('ADMIN_ID')
OWNER_ID = os.environ.get('OWNER_ID') 

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client['FinalBuilderDB']['users']

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
    payload = {"message": "Injecting Source Code", "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

@bot.message_handler(commands=['addbalance'])
def add_bal(m):
    if str(m.from_user.id) != str(ADMIN_ID): return
    try:
        p = m.text.split()
        db.update_one({"cid": int(p[1])}, {"$inc": {"bal": int(p[2])}}, upsert=True)
        bot.reply_to(m, "✅ ব্যালেন্স যোগ সফল!")
    except: bot.reply_to(m, "Format: /addbalance [UID] [Amount]")

@bot.message_handler(commands=['start', 'balance'])
def start(m):
    u = get_u(m.chat.id)
    price = 10 if u['apps'] == 0 else 20
    msg = (f"🚀 **Multi-Platform App Builder**\n\n💰 ব্যালেন্স: {u['bal']} TK\n"
           f"📦 তৈরি অ্যাপ: {u['apps']} টি\n💳 দাম: {price} TK\n\n"
           f"অ্যাপ তৈরি: /create\nরিচার্জ: {OWNER_ID}")
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
    s = u.get('step', 'n')
    if s == "name":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.name": m.text, "step": "url"}})
        bot.send_message(m.chat.id, "২. ওয়েবসাইট URL দিন:")
    elif s == "url":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.url": m.text, "step": "color"}})
        bot.send_message(m.chat.id, "৩. কালার কোড (Hex যেমন: #ff5733):")
    elif s == "color":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.color": m.text, "step": "dev"}})
        bot.send_message(m.chat.id, "৪. ৩-ডট মেনুর জন্য চ্যানেল লিংক দিন:")
    elif s == "dev":
        db.update_one({"cid": m.chat.id}, {"$set": {"data.dev": m.text, "step": "logo"}})
        bot.send_message(m.chat.id, "৫. অ্যাপের লোগো (ছবি) পাঠান:")
    elif s == "logo" and m.content_type == 'photo':
        f_info = bot.get_file(m.photo[-1].file_id)
        logo_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}"
        price = 10 if u['apps'] == 0 else 20
        db.update_one({"cid": m.chat.id}, {"$inc": {"bal": -price, "apps": 1}, "$set": {"step": "n"}})
        bot.send_message(m.chat.id, "✅ পেমেন্ট সফল! বিল্ড শুরু হচ্ছে...")

        n, url, c, d = u['data']['name'], u['data']['url'], u['data']['color'], u['data']['dev']
        
        # --- ইনজেক্টিং সোর্স কোড (সব ফোল্ডারের কোড এখানে) ---
        main_dart = f"import 'package:flutter/material.dart';\nimport 'package:webview_flutter/webview_flutter.dart';\nimport 'package:url_launcher/url_launcher.dart';\nvoid main()=>runApp(MaterialApp(home:Scaffold(appBar:AppBar(title:Text('{n}'),backgroundColor:Color({c.replace('#','0xff')}),actions:[PopupMenuButton(onSelected:(v)=>launchUrl(Uri.parse('{d}')),itemBuilder:(c)=>[PopupMenuItem(value:1,child:Text('Developer'))])]),body:WebViewWidget(controller:WebViewController()..setJavaScriptMode(JavaScriptMode.unrestricted)..loadRequest(Uri.parse('{url}')))),debugShowCheckedModeBanner:false));"
        push_gh("lib/main.dart", main_dart)

        workflow = f"name: Build\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: subosito/flutter-action@v2\n      - run: flutter build apk --release\n      - run: flutter build appbundle --release\n      - name: Send\n        run: |\n          curl -F chat_id='{m.chat.id}' -F document=@build/app/outputs/flutter-apk/app-release.apk https://api.telegram.org/bot{API_TOKEN}/sendDocument\n          curl -F chat_id='{m.chat.id}' -F document=@build/app/outputs/bundle/release/app-release.aab https://api.telegram.org/bot{API_TOKEN}/sendDocument"
        push_gh(".github/workflows/main.yml", workflow)

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def index(): return "Bot Active!", 200
