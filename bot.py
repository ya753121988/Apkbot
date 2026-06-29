import os
import json
import datetime
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-9988'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Database ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['AppBuildSaaS']
users_col = db['users']
orders_col = db['orders']

# --- Configuration ---
# এই দুটি জিনিস আপনার নিজের গিটহাব থেকে অবশ্যই দেবেন
GITHUB_TOKEN = "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" 
GITHUB_REPO = "ya753121988/Apkbot"
ADMIN_PASS = "admin1234" 

# --- UI Layout (Single Page Application) ---
UI_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>WebToApp SaaS - PRO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen font-sans">
    <div id="app">
        <!-- Navigation -->
        <nav class="bg-indigo-700 text-white p-4 shadow-xl flex justify-between items-center sticky top-0 z-50">
            <div class="flex items-center gap-2">
                <i class="fas fa-rocket text-2xl"></i>
                <h1 class="text-xl font-black italic tracking-tighter">APPBUILDER PRO</h1>
            </div>
            <div id="nav-info" class="flex items-center gap-4"></div>
        </nav>

        <div class="container mx-auto p-4 max-w-6xl" id="view-container">
            <div class="flex justify-center items-center h-64"><i class="fas fa-spinner fa-spin text-4xl text-indigo-600"></i></div>
        </div>
    </div>

    <script>
        const socket = io();
        let user = JSON.parse(localStorage.getItem('user'));
        let isAdminAuthenticated = localStorage.getItem('admin_auth') === 'true';

        // --- Router ---
        function router() {
            const hash = window.location.hash;
            if (!user && hash !== '#signup') return showLogin();
            if (hash === '#signup') return showSignup();
            if (hash === '#admin') return isAdminAuthenticated ? showAdmin() : askAdminPass();
            showDashboard();
        }

        function saveUser(u) { localStorage.setItem('user', JSON.stringify(u)); user = u; }
        function logout() { localStorage.clear(); window.location.href = '/'; }

        // --- Views ---
        function showLogin() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-2xl mt-12 border-b-8 border-indigo-600">
                <h2 class="text-3xl font-black mb-6 text-center text-indigo-700 underline decoration-indigo-200">WELCOME BACK</h2>
                <input id="email" type="email" placeholder="Gmail Address" class="w-full border-2 p-3 mb-4 rounded-xl outline-none focus:border-indigo-500 transition">
                <input id="pass" type="password" placeholder="Password" class="w-full border-2 p-3 mb-4 rounded-xl outline-none focus:border-indigo-500 transition">
                <button onclick="handleLogin()" class="w-full bg-indigo-600 text-white p-4 rounded-xl font-bold text-lg hover:bg-indigo-800 shadow-lg active:scale-95 transition">LOGIN NOW <i class="fas fa-arrow-right ml-2"></i></button>
                <p class="mt-6 text-center text-gray-600">New User? <a href="#signup" onclick="setTimeout(router,100)" class="text-indigo-600 font-bold underline">Create Account</a></p>
            </div>`;
        }

        function showSignup() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-2xl mt-12 border-b-8 border-green-600">
                <h2 class="text-3xl font-black mb-6 text-center text-green-700">SIGN UP</h2>
                <input id="fname" type="text" placeholder="Full Name" class="w-full border-2 p-3 mb-4 rounded-xl">
                <input id="email" type="email" placeholder="Gmail Address" class="w-full border-2 p-3 mb-4 rounded-xl">
                <input id="pass" type="password" placeholder="Password" class="w-full border-2 p-3 mb-4 rounded-xl">
                <button onclick="handleSignup()" class="w-full bg-green-600 text-white p-4 rounded-xl font-bold text-lg shadow-lg active:scale-95 transition">CREATE ACCOUNT <i class="fas fa-user-plus ml-2"></i></button>
                <p class="mt-6 text-center"><a href="#" onclick="setTimeout(router,100)" class="text-indigo-600 font-bold underline">Back to Login</a></p>
            </div>`;
        }

        function showDashboard() {
            document.getElementById('nav-info').innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="bg-indigo-900 px-4 py-1.5 rounded-full text-sm font-black border border-indigo-400">💰 ${user.balance} TK</span>
                    <button onclick="logout()" class="text-white hover:text-red-300 transition text-sm font-bold uppercase tracking-widest"><i class="fas fa-power-off"></i></button>
                </div>
            `;

            document.getElementById('view-container').innerHTML = `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- App Builder -->
                <div class="bg-white p-8 rounded-3xl shadow-xl border border-gray-100">
                    <h2 class="text-2xl font-black mb-6 flex items-center gap-2"><i class="fas fa-magic text-indigo-600"></i> BUILD NEW APP</h2>
                    <div class="space-y-4">
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase ml-1">App Identity</label>
                            <input id="appName" placeholder="App Name (e.g. My Shop)" class="w-full border-2 p-4 rounded-2xl focus:border-indigo-500 outline-none transition">
                        </div>
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase ml-1">Target Website URL</label>
                            <input id="appUrl" placeholder="https://www.yoursite.com" class="w-full border-2 p-4 rounded-2xl focus:border-indigo-500 outline-none transition">
                        </div>
                        <div>
                            <label class="text-xs font-bold text-gray-500 uppercase ml-1">Select Platform</label>
                            <select id="platform" class="w-full border-2 p-4 rounded-2xl bg-white font-bold">
                                <option value="android_apk">Android (APK Mobile)</option>
                                <option value="android_aab">Playstore (AAB File)</option>
                                <option value="windows">Windows PC (.exe)</option>
                                <option value="ios">iPhone (iOS Project)</option>
                            </select>
                        </div>
                        <div class="flex gap-4 items-center">
                            <div class="flex-1">
                                <label class="text-xs font-bold text-gray-500 uppercase ml-1">Theme Color</label>
                                <input id="color" type="color" class="w-full h-14 rounded-2xl cursor-pointer">
                            </div>
                        </div>
                        <button onclick="handleOrder()" class="w-full bg-indigo-600 text-white p-5 rounded-3xl font-black text-xl shadow-indigo-200 shadow-2xl hover:scale-105 active:scale-95 transition">START BUILD (500 TK)</button>
                    </div>
                </div>

                <!-- My Apps -->
                <div class="bg-white p-8 rounded-3xl shadow-xl">
                    <h2 class="text-2xl font-black mb-6 flex items-center gap-2"><i class="fas fa-layer-group text-indigo-600"></i> MY APPS</h2>
                    <div id="order-list" class="space-y-6">
                        <div class="text-center py-12 text-gray-400 font-bold italic">No apps ordered yet. Start building now!</div>
                    </div>
                </div>
            </div>`;
            loadOrders();
        }

        // --- Admin Functions ---
        function askAdminPass() {
            const p = prompt("Enter Master Admin Password:");
            if (p === "${ADMIN_PASS}") {
                localStorage.setItem('admin_auth', 'true');
                isAdminAuthenticated = true;
                router();
            } else {
                alert("Access Denied!");
                window.location.hash = "";
            }
        }

        async function showAdmin() {
            document.getElementById('view-container').innerHTML = `
            <div class="bg-white p-8 rounded-3xl shadow-2xl border-t-8 border-black">
                <div class="flex justify-between items-center mb-8">
                    <h2 class="text-3xl font-black">ADMIN CONTROL</h2>
                    <button onclick="localStorage.removeItem('admin_auth'); location.reload();" class="bg-red-500 text-white px-4 py-2 rounded-xl text-sm font-bold">Close Panel</button>
                </div>
                <div class="flex gap-2 mb-8">
                    <input id="searchMail" placeholder="Search by Gmail..." class="flex-1 border-2 p-4 rounded-2xl outline-none focus:border-indigo-600 transition">
                    <button onclick="searchUser()" class="bg-indigo-600 text-white px-8 rounded-2xl font-bold"><i class="fas fa-search"></i></button>
                </div>
                <div id="admin-result" class="overflow-x-auto"></div>
            </div>`;
        }

        // --- Core Logic ---
        async function handleLogin() {
            const email = document.getElementById('email').value;
            const pass = document.getElementById('pass').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, pass})
            });
            const data = await res.json();
            if(res.ok) { saveUser(data); router(); } else alert(data.error);
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

        async function handleOrder() {
            if(user.balance < 500) return alert("Low Balance! Please contact admin to add money.");
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
            if(res.ok) {
                user.balance -= 500;
                saveUser(user);
                showDashboard();
            } else {
                alert("Error placing order!");
            }
        }

        async function loadOrders() {
            const res = await fetch('/api/user-orders/' + user._id);
            const orders = await res.json();
            const list = document.getElementById('order-list');
            if(orders.length === 0) return;
            list.innerHTML = "";
            orders.forEach(o => {
                const isComplete = o.status === 'Completed';
                list.innerHTML += `
                <div class="border-2 p-5 rounded-2xl bg-gray-50 relative group hover:border-indigo-400 transition">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="font-black text-lg text-indigo-900">${o.appName.toUpperCase()}</h3>
                            <p class="text-xs font-bold text-gray-500">${o.platform.toUpperCase()} • ${new Date(o.at).toLocaleDateString()}</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-black uppercase ${isComplete ? 'bg-green-100 text-green-700' : 'bg-indigo-100 text-indigo-700 animate-pulse'}">
                            ${isComplete ? '<i class="fas fa-check-circle mr-1"></i> DONE' : '<i class="fas fa-sync fa-spin mr-1"></i> BUILDING'}
                        </span>
                    </div>
                    ${isComplete ? `
                        <div class="mt-4 flex gap-2">
                            <a href="${o.downloadUrl}" target="_blank" class="flex-1 bg-green-600 text-white text-center py-3 rounded-xl font-black text-sm shadow-lg hover:shadow-green-200 transition"><i class="fas fa-download mr-2"></i> INSTALL APP</a>
                            <button onclick="shareApp('${o.downloadUrl}')" class="bg-indigo-900 text-white px-6 py-3 rounded-xl hover:bg-black transition"><i class="fas fa-share-alt"></i></button>
                        </div>
                    ` : `
                        <div class="mt-4 w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                            <div class="bg-indigo-600 h-full w-2/3 animate-pulse"></div>
                        </div>
                        <p class="text-[10px] mt-2 font-bold text-gray-400 uppercase tracking-widest">Compiling assets and building your binary...</p>
                    `}
                </div>`;
            });
        }

        async function searchUser() {
            const mail = document.getElementById('searchMail').value;
            const res = await fetch('/api/admin/users');
            const all = await res.json();
            const filtered = all.filter(u => u.email.includes(mail));
            let h = '<table class="w-full text-left font-bold text-sm"><thead><tr class="text-gray-400 border-b"><th>GMAIL</th><th>PASS</th><th>BALANCE</th><th>ACTION</th></tr></thead><tbody>';
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
            if(!amount) return;
            const res = await fetch('/api/admin/add-balance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uid, amount: parseInt(amount)})
            });
            if(res.ok) { alert("Money Added!"); searchUser(); }
        }

        function shareApp(url) {
            if (navigator.share) {
                navigator.share({ title: 'Install My App', url });
            } else {
                prompt("Copy App Link:", url);
            }
        }

        // Live Socket Update
        socket.on('update', (d) => { if(user && d.uid === user._id) loadOrders(); });

        window.addEventListener('hashchange', router);
        router();
    </script>
</body>
</html>
"""

# --- Backend API ---

@app.route('/')
def index():
    return render_template_string(UI_HTML, ADMIN_PASS=ADMIN_PASS)

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    if users_col.find_one({"email": data['email']}):
        return jsonify({"error": "User already exists"}), 400
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
    return jsonify({"error": "Invalid login credentials"}), 401

@app.route('/api/order', methods=['POST'])
def api_order():
    data = request.json
    user = users_col.find_one({"_id": ObjectId(data['userId'])})
    if user['balance'] < 500:
        return jsonify({"error": "Low balance"}), 400
    
    # Deduct Balance
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

    # Trigger GitHub (যদি টোকেন থাকে)
    try:
        payload = {
            "event_type": "app_build",
            "client_payload": {
                "orderId": order_id,
                "userId": data['userId'],
                "appName": data['appName'],
                "appUrl": data['appUrl']
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

# Webhook for GitHub to call when build is done
@app.route('/api/build-done', methods=['POST'])
def api_build_done():
    data = request.json # orderId, downloadUrl, userId
    orders_col.update_one({"_id": ObjectId(data['orderId'])}, {"$set": {"status": "Completed", "downloadUrl": data['downloadUrl']}})
    socketio.emit('update', {"uid": data['userId']})
    return jsonify({"success": True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
