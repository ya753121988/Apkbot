import os
import json
import datetime
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ultimate_secret_key_12345'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- Database Connection ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['WebToApp_SaaS']
users_col = db['users']
orders_col = db['orders']

# --- Configuration (নিজে পরিবর্তন করুন) ---
GITHUB_TOKEN = "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" # আপনার গিটহাব টোকেন দিন
GITHUB_REPO = "ya753121988/Apkbot" # আপনার রিপোজিটরি নাম
ADMIN_PASS = "admin1234" 

# --- UI (HTML/JavaScript/Tailwind) ---
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebToApp SaaS PRO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        body { font-family: 'Inter', sans-serif; background: #f3f4f6; }
    </style>
</head>
<body>
    <div id="app">
        <nav class="bg-indigo-700 text-white p-4 shadow-xl sticky top-0 z-50 flex justify-between items-center">
            <div class="flex items-center gap-2">
                <i class="fas fa-rocket text-2xl"></i>
                <h1 class="text-xl font-black">APPBUILDER PRO</h1>
            </div>
            <div id="nav-info" class="flex items-center gap-4"></div>
        </nav>

        <div class="container mx-auto p-4 max-w-6xl mt-6" id="view-container">
            <div class="flex justify-center mt-20"><i class="fas fa-circle-notch fa-spin text-5xl text-indigo-600"></i></div>
        </div>
    </div>

    <script>
        const socket = io();
        let user = JSON.parse(localStorage.getItem('user'));
        let adminAuth = localStorage.getItem('admin_auth') === 'true';

        function router() {
            const hash = window.location.hash;
            if (!user && hash !== '#signup') return showLogin();
            if (hash === '#signup') return showSignup();
            if (hash === '#admin') return adminAuth ? showAdmin() : askAdminPass();
            showDashboard();
        }

        // --- Auth Functions ---
        async function handleLogin() {
            const email = document.getElementById('email').value;
            const pass = document.getElementById('pass').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, pass})
            });
            const data = await res.json();
            if(res.ok) { localStorage.setItem('user', JSON.stringify(data)); user = data; router(); }
            else alert(data.error);
        }

        async function handleSignup() {
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    fullName: document.getElementById('fname').value,
                    email: document.getElementById('email').value,
                    password: document.getElementById('pass').value
                })
            });
            if(res.ok) { alert("Registration Success!"); window.location.hash = ""; router(); }
        }

        function logout() { localStorage.clear(); location.reload(); }

        // --- Views ---
        function showLogin() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-3xl shadow-2xl border-b-8 border-indigo-600">
                <h2 class="text-3xl font-black mb-6 text-center text-indigo-700">LOGIN</h2>
                <input id="email" type="email" placeholder="Gmail Address" class="w-full border-2 p-4 mb-4 rounded-2xl outline-none focus:border-indigo-600">
                <input id="pass" type="password" placeholder="Password" class="w-full border-2 p-4 mb-6 rounded-2xl outline-none focus:border-indigo-600">
                <button onclick="handleLogin()" class="w-full bg-indigo-600 text-white p-4 rounded-2xl font-bold text-lg hover:bg-indigo-800">LOGIN NOW</button>
                <p class="mt-6 text-center">New? <a href="#signup" class="text-indigo-600 font-bold">Signup</a></p>
            </div>`;
        }

        function showSignup() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-3xl shadow-2xl border-b-8 border-green-600">
                <h2 class="text-3xl font-black mb-6 text-center text-green-700">SIGN UP</h2>
                <input id="fname" placeholder="Full Name" class="w-full border-2 p-4 mb-4 rounded-2xl">
                <input id="email" placeholder="Gmail Address" class="w-full border-2 p-4 mb-4 rounded-2xl">
                <input id="pass" type="password" placeholder="Password" class="w-full border-2 p-4 mb-6 rounded-2xl">
                <button onclick="handleSignup()" class="w-full bg-green-600 text-white p-4 rounded-2xl font-bold text-lg">REGISTER</button>
                <p class="mt-6 text-center"><a href="#" class="text-indigo-600 font-bold">Back to Login</a></p>
            </div>`;
        }

        function showDashboard() {
            document.getElementById('nav-info').innerHTML = `
                <span class="bg-indigo-900 px-4 py-1.5 rounded-full font-bold">💰 ${user.balance} TK</span>
                <button onclick="logout()" class="text-xl ml-2"><i class="fas fa-power-off"></i></button>
            `;
            document.getElementById('view-container').innerHTML = `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="bg-white p-8 rounded-3xl shadow-xl">
                    <h2 class="text-2xl font-black mb-6 italic underline decoration-indigo-200">START NEW BUILD</h2>
                    <div class="space-y-4">
                        <input id="appName" placeholder="App Name" class="w-full border-2 p-4 rounded-2xl">
                        <input id="appUrl" placeholder="Website URL (https://...)" class="w-full border-2 p-4 rounded-2xl">
                        <select id="platform" class="w-full border-2 p-4 rounded-2xl bg-white font-bold">
                            <option value="android_apk">Android (APK)</option>
                            <option value="android_aab">Playstore (AAB)</option>
                            <option value="pc">PC (Windows .exe)</option>
                            <option value="ios">iOS (Project)</option>
                        </select>
                        <input id="color" type="color" class="w-full h-12 rounded-xl cursor-pointer">
                        <button onclick="handleOrder()" class="w-full bg-indigo-600 text-white p-5 rounded-2xl font-black text-xl hover:scale-105 transition">BUILD APP (500 TK)</button>
                    </div>
                </div>
                <div class="bg-white p-8 rounded-3xl shadow-xl">
                    <h2 class="text-2xl font-black mb-6">MY BUILDS</h2>
                    <div id="order-list" class="space-y-4"></div>
                </div>
            </div>`;
            loadOrders();
        }

        async function handleOrder() {
            if(user.balance < 500) return alert("Low Balance!");
            const res = await fetch('/api/order', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    userId: user._id,
                    appName: document.getElementById('appName').value,
                    appUrl: document.getElementById('appUrl').value,
                    platform: document.getElementById('platform').value,
                    color: document.getElementById('color').value
                })
            });
            if(res.ok) { user.balance -= 500; localStorage.setItem('user', JSON.stringify(user)); showDashboard(); }
        }

        async function loadOrders() {
            const res = await fetch('/api/user-orders/' + user._id);
            const orders = await res.json();
            const list = document.getElementById('order-list');
            if(orders.length === 0) { list.innerHTML = '<p class="text-gray-400 font-bold italic">No builds yet.</p>'; return; }
            list.innerHTML = "";
            orders.forEach(o => {
                const completed = o.status === 'Completed';
                list.innerHTML += `
                <div class="border-2 p-5 rounded-2xl bg-gray-50 relative group">
                    <div class="flex justify-between items-center">
                        <div>
                            <h3 class="font-black text-indigo-900">${o.appName.toUpperCase()}</h3>
                            <p class="text-xs font-bold text-gray-500">${o.platform.toUpperCase()}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-black ${completed ? 'bg-green-100 text-green-700' : 'bg-indigo-100 text-indigo-700 animate-pulse'}">
                            ${o.status.toUpperCase()}
                        </span>
                    </div>
                    ${completed ? `
                        <div class="mt-4 flex gap-2">
                            <a href="${o.downloadUrl}" target="_blank" class="flex-1 bg-green-600 text-white text-center py-2.5 rounded-xl font-bold text-sm shadow-lg hover:shadow-green-200 transition">INSTALL APP</a>
                            <button onclick="shareApp('${o.downloadUrl}')" class="bg-indigo-900 text-white px-5 rounded-xl hover:bg-black transition"><i class="fas fa-share-alt"></i></button>
                        </div>
                    ` : `<div class="mt-4 w-full bg-gray-200 h-2 rounded-full overflow-hidden"><div class="bg-indigo-600 h-full w-2/3 animate-pulse"></div></div>`}
                </div>`;
            });
        }

        // --- Admin Functions ---
        function askAdminPass() {
            const p = prompt("Admin Password:");
            if (p === "${ADMIN_PASS}") { localStorage.setItem('admin_auth', 'true'); adminAuth = true; router(); }
            else { alert("Wrong!"); window.location.hash = ""; }
        }

        async function showAdmin() {
            document.getElementById('view-container').innerHTML = `
            <div class="bg-white p-8 rounded-3xl shadow-2xl">
                <h2 class="text-3xl font-black mb-8">ADMIN PANEL</h2>
                <div class="flex gap-2 mb-8">
                    <input id="searchMail" placeholder="Search User Email..." class="flex-1 border-2 p-4 rounded-2xl outline-none focus:border-indigo-600">
                    <button onclick="searchUser()" class="bg-indigo-600 text-white px-8 rounded-2xl font-bold"><i class="fas fa-search"></i></button>
                </div>
                <div id="admin-result" class="overflow-x-auto"></div>
                <button onclick="localStorage.removeItem('admin_auth'); location.reload();" class="mt-10 bg-red-500 text-white px-6 py-2 rounded-xl font-bold">Logout Admin</button>
            </div>`;
        }

        async function searchUser() {
            const mail = document.getElementById('searchMail').value;
            const res = await fetch('/api/admin/users');
            const all = await res.json();
            const filtered = all.filter(u => u.email.includes(mail));
            let h = '<table class="w-full text-left font-bold text-sm"><thead><tr class="text-gray-400 border-b"><th>GMAIL</th><th>PASSWORD</th><th>BALANCE</th><th>ACTION</th></tr></thead><tbody>';
            filtered.forEach(u => {
                h += `<tr class="border-b h-16">
                    <td>${u.email}</td>
                    <td class="text-red-500 font-mono">${u.password}</td>
                    <td class="text-indigo-600">${u.balance} TK</td>
                    <td>
                        <input id="amt-${u._id}" type="number" placeholder="Amt" class="w-16 border rounded p-1">
                        <button onclick="addBalance('${u._id}')" class="bg-green-600 text-white px-3 py-1 rounded text-xs">ADD</button>
                    </td>
                </tr>`;
            });
            document.getElementById('admin-result').innerHTML = h + '</tbody></table>';
        }

        async function addBalance(uid) {
            const amount = document.getElementById('amt-'+uid).value;
            await fetch('/api/admin/add-balance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uid, amount: parseInt(amount)})
            });
            alert("Success!");
            searchUser();
        }

        function shareApp(url) {
            if (navigator.share) navigator.share({ title: 'My App', url });
            else prompt("Copy Link:", url);
        }

        socket.on('update', (d) => { if(user && d.uid === user._id) loadOrders(); });
        window.onhashchange = router;
        router();
    </script>
    <div class="fixed bottom-4 right-4"><button onclick="window.location.hash='#admin'; router();" class="bg-black/10 text-xs p-1 rounded">Admin</button></div>
</body>
</html>
"""

# --- Backend API Routes ---

@app.route('/')
def index():
    return render_template_string(UI_HTML, ADMIN_PASS=ADMIN_PASS)

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    if users_col.find_one({"email": data['email']}): return jsonify({"error": "User Exists"}), 400
    data['balance'] = 0
    uid = users_col.insert_one(data).inserted_id
    return jsonify({"success": True, "_id": str(uid)})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    u = users_col.find_one({"email": data['email'], "password": data['pass']})
    if u:
        u['_id'] = str(u['_id'])
        return jsonify(u)
    return jsonify({"error": "Invalid login"}), 401

@app.route('/api/order', methods=['POST'])
def api_order():
    data = request.json
    user = users_col.find_one({"_id": ObjectId(data['userId'])})
    if user['balance'] < 500: return jsonify({"error": "Low balance"}), 400
    
    users_col.update_one({"_id": ObjectId(data['userId'])}, {"$inc": {"balance": -500}})
    
    order = {
        "userId": data['userId'],
        "appName": data['appName'],
        "appUrl": data['appUrl'],
        "platform": data['platform'],
        "color": data['color'],
        "status": "Building",
        "downloadUrl": "",
        "at": datetime.datetime.now()
    }
    order_id = str(orders_col.insert_one(order).inserted_id)

    # Trigger GitHub Dispatch
    try:
        payload = {
            "event_type": "app_build",
            "client_payload": {
                "orderId": order_id,
                "userId": data['userId'],
                "appName": data['appName'],
                "appUrl": data['appUrl'],
                "platform": data['platform']
            }
        }
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/dispatches", 
                      headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
                      json=payload)
    except: pass
    return jsonify({"success": True})

@app.route('/api/user-orders/<uid>')
def api_user_orders(uid):
    orders = list(orders_col.find({"userId": uid}).sort("at", -1))
    for o in orders: o['_id'] = str(o['_id'])
    return jsonify(orders)

@app.route('/api/admin/users')
def api_admin_users():
    users = list(users_col.find({}))
    for u in users: u['_id'] = str(u['_id'])
    return jsonify(users)

@app.route('/api/admin/add-balance', methods=['POST'])
def api_admin_add_bal():
    data = request.json
    users_col.update_one({"_id": ObjectId(data['uid'])}, {"$inc": {"balance": data['amount']}})
    return jsonify({"success": True})

@app.route('/api/build-done', methods=['POST'])
def api_build_done():
    data = request.json # orderId, downloadUrl, userId
    orders_col.update_one({"_id": ObjectId(data['orderId'])}, {"$set": {"status": "Completed", "downloadUrl": data['downloadUrl']}})
    socketio.emit('update', {"uid": data['userId']})
    return jsonify({"success": True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
