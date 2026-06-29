import os
import requests
import telebot
from flask import Flask, request

API_TOKEN = '8876597863:AAE3A99UKha71_6X1hpJyZe8ySbTJkbLg_s'
# রেন্ডারের এনভায়রনমেন্টে অবশ্যই GITHUB_TOKEN সেট করবেন
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') 
GITHUB_REPO = 'ya753121988/Apkbot'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

@app.route('/')
def index(): return "Bot is Running", 200

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "🚀 অ্যাপ তৈরি করতে /create লিখুন।")

@bot.message_handler(commands=['create'])
def create(m):
    bot.reply_to(m, "১. অ্যাপের নাম দিন:")
    bot.register_next_step_handler(m, get_name)

def get_name(m):
    user_data[m.chat.id] = {'name': m.text}
    bot.reply_to(m, "২. ওয়েবসাইট URL দিন:")
    bot.register_next_step_handler(m, get_url)

def get_url(m):
    name = user_data[m.chat.id]['name']
    url = m.text
    bot.reply_to(m, f"⏳ বিল্ড প্রসেস শুরু হচ্ছে...\nনাম: {name}\nলিঙ্ক: {url}\n\n১০-১৫ মিনিট অপেক্ষা করুন।")

    # গিটহাবকে বিল্ড সিগন্যাল পাঠানো
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    payload = {
        "event_type": "build_app",
        "client_payload": {
            "cid": str(m.chat.id),
            "name": name,
            "url": url,
            "token": API_TOKEN
        }
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    res = requests.post(dispatch_url, json=payload, headers=headers)
    if res.status_code != 204:
        bot.send_message(m.chat.id, "❌ গিটহাবের সাথে কানেক্ট করতে সমস্যা হয়েছে। টোকেন চেক করুন।")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "Forbidden", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
