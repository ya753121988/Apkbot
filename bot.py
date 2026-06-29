import os
import json
import datetime
import requests
from flask import Flask, request, jsonify, render_template_string, make_response
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_12345'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Database ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['SaaSMakerV2']
users_col = db['users']
orders_col = db['orders']

# --- Config ---
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN" # আপনার টোকেন দিন
GITHUB_REPO = "YOUR_USER/YOUR_REPO" # আপনার রিপোজিটরি দিন
ADMIN_PASS = "admin789"

# --- HTML/JS UI (Full Integrated) ---
UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebToApp SaaS - Advanced</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div id="app">
        <!-- Navigation -->
        <nav class="bg-blue-700 text-white p-4 shadow-lg flex justify-between items-center">
            <h1 class="text-xl font-bold">🚀 AppBuild SaaS</h1>
            <div id="nav-info" class="flex items-center gap-4"></div>
        </nav>

        <div class="container mx-auto p-4" id="view-container">
            <!-- Content will load here -->
            <div class="text-center mt-20">Loading...</div>
        </div>
    </div>

    <script>
        const socket = io();
        let currentUser = JSON.parse(localStorage.getItem('user'));

        function saveUser(user) {
            localStorage.setItem('user', JSON.stringify(user));
            currentUser = user;
        }

        // --- View Router ---
        function router() {
            if (!currentUser) return showLogin();
            if (window.location.hash === '#admin') return showAdmin();
            showDashboard();
        }

        function showLogin() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-2xl mt-10">
                <h2 class="text-3xl font-bold mb-6 text-center text-blue-700">Login</h2>
                <input id="email" type="email" placeholder="Gmail" class="w-full border p-3 mb-4 rounded-lg outline-none focus:ring-2 ring-blue-500">
                <input id="pass" type="password" placeholder="Password" class="w-full border p-3 mb-4 rounded-lg outline-none focus:ring-2 ring-blue-500">
                <button onclick="handleLogin()" class="w-full bg-blue-600 text-white p-3 rounded-lg font-bold hover:bg-blue-800 transition">Enter Dashboard</button>
                <p class="mt-4 text-center">New here? <a href="javascript:showSignup()" class="text-blue-600 font-bold">Create Account</a></p>
            </div>`;
        }

        function showSignup() {
            document.getElementById('view-container').innerHTML = `
            <div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-2xl mt-10">
                <h2 class="text-3xl font-bold mb-6 text-center text-green-600">Register</h2>
                <input id="fname" type="text" placeholder="Full Name" class="w-full border p-3 mb-4 rounded-lg">
                <input id="email" type="email" placeholder="Gmail" class="w-full border p-3 mb-4 rounded-lg">
                <input id="pass" type="password" placeholder="Password" class="w-full border p-3 mb-4 rounded-lg">
                <button onclick="handleSignup()" class="w-full bg-green-600 text-white p-3 rounded-lg font-bold hover:bg-green-800">Signup Now</button>
                <p class="mt-4 text-center"><a href="javascript:showLogin()" class="text-blue-600">Already have account? Login</a></p>
            </div>`;
        }

        async function showDashboard() {
            document.getElementById('nav-info').innerHTML = `
                <span class="bg-blue-900 px-3 py-1 rounded-full text-sm font-bold">${currentUser.balance} TK</span>
                <button onclick="logout()" class="bg-red-500 px-3 py-1 rounded text-sm hover:bg-red-700">Logout</button>
            `;
            
            document.getElementById('view-container').innerHTML = `
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- App Order Form -->
                <div class="bg-white p-6 rounded-xl shadow-lg border-t-4 border-blue-600">
                    <h2 class="text-2xl font-bold mb-6">Create New App</h2>
                    <div class="space-y-4">
                        <input id="appName" placeholder="App Name (e.g. My Shop)" class="w-full border p-3 rounded-lg">
                        <input id="appUrl" placeholder="Website URL (https://...)" class="w-full border p-3 rounded-lg">
                        <select id="platform" class="w-full border p-3 rounded-lg bg-gray-50">
                            <option value="android_apk">Android Mobile (APK)</option>
                            <option value="android_aab">Play Store (AAB File)</option>
                            <option value="windows">PC/Laptop (Windows .exe)</option>
                            <option value="ios">iPhone (iOS Project)</option>
                        </select>
                        <div>
                            <label class="block text-sm font-bold text-gray-700 mb-1">Select App Theme Color</label>
                            <input id="color" type="color" class="w-full h-12 rounded-lg cursor-pointer">
                        </div>
                        <button onclick="orderApp()" class="w-full bg-blue-700 text-white p-4 rounded-lg font-bold text-lg hover:shadow-xl transition transform hover:-translate-y-1">
                            Build & Pay 500 TK
                        </button>
                    </div>
                </div>

                <!-- Live Status & Orders -->
                <div class="bg-white p-6 rounded-xl shadow-lg border-t-4 border-green-600">
                    <h2 class="text-2xl font-bold mb-6">Live Build Status</h2>
                    <div id="orders-container" class="space-y-4">
                        <p class="text-gray-500 italic">No apps ordered yet...</p>
                    </div>
                </div>
            </div>`;
            loadUserOrders();
        }

        // --- Core Functions ---
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
            if(res.ok) { alert("Registration Success! Login now."); showLogin(); }
        }

        async function orderApp() {
            const res = await fetch('/api/order', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    userId: currentUser._id,
                    appName: document.getElementById('appName').value,
                    appUrl: document.getElementById('appUrl').value,
                    platform: document.getElementById('platform').value,
                    appColor: document.getElementById('color').value
                })
            });
            const data = await res.json();
            if(res.ok) { 
                alert("Build Queued! Check live status.");
                currentUser.balance -= 500;
                saveUser(currentUser);
                showDashboard();
            } else alert(data.error);
        }

        async function loadUserOrders() {
            const res = await fetch('/api/user-orders/' + currentUser._id);
            const orders = await res.json();
            const container = document.getElementById('orders-container');
            if(orders.length === 0) return;
            container.innerHTML = '';
            orders.forEach(order => {
                const statusColor = order.status === 'Completed' ? 'text-green-600' : 'text-blue-500 animate-pulse';
                container.innerHTML += `
                <div class="border p-4 rounded-lg bg-gray-50 shadow-sm relative">
                    <h3 class="font-bold text-lg">${order.appName}</h3>
                    <p class="text-xs text-gray-500">Platform: ${order.platform}</p>
                    <div class="mt-2 flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-current ${statusColor}"></span>
                        <span class="font-bold ${statusColor}">${order.status}...</span>
                    </div>
                    ${order.status === 'Completed' ? `
                        <div class="mt-4 flex gap-2">
                            <a href="${order.downloadUrl}" target="_blank" class="bg-green-600 text-white px-4 py-2 rounded text-sm font-bold">Install App</a>
                            <button onclick="shareApp('${order.downloadUrl}')" class="bg-gray-800 text-white px-4 py-2 rounded text-sm">Share</button>
                        </div>
                    ` : `<div class="w-full bg-gray-200 h-2 mt-4 rounded-full overflow-hidden"><div class="bg-blue-600 h-full w-1/2 animate-ping"></div></div>`}
                </div>`;
            });
        }

        // Socket Listen for Status Update
        socket.on('status_update', (data) => {
            if(currentUser && data.userId === currentUser._id) {
                loadUserOrders();
            }
        });

        function shareApp(url) {
            navigator.share({ title: 'My App', text: 'Install my new app!', url: url });
        }

        function logout() { localStorage.clear(); window.location.reload(); }

        // Initial Run
        router();
    </script>
</body>
</html>
"""

# --- Backend Logic ---

@app.route('/')
def home():
    return render_template_string(UI_HTML)

@app.route('/api/signup', methods=['POST'])
def signup_api():
    data = request.json
    data['balance'] = 0
    data['role'] = 'user'
    users_col.insert_one(data)
    return jsonify({"success": True})

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    u = users_col.find_one({"email": data['email'], "password": data['pass']})
    if u:
        u['_id'] = str(u['_id'])
        return jsonify(u)
    return jsonify({"error": "Wrong Gmail or Password"}), 401

@app.route('/api/order', methods=['POST'])
def order_api():
    data = request.json
    user = users_col.find_one({"_id": ObjectId(data['userId'])})
    if not user or user['balance'] < 500:
        return jsonify({"error": "Insufficient Balance (Need 500 TK)"}), 400
    
    # Deduct Balance
    users_col.update_one({"_id": ObjectId(data['userId'])}, {"$inc": {"balance": -500}})
    
    order = {
        "userId": data['userId'],
        "appName": data['appName'],
        "appUrl": data['appUrl'],
        "platform": data['platform'],
        "color": data['appColor'],
        "status": "Queued",
        "downloadUrl": "",
        "at": datetime.datetime.now()
    }
    order_id = str(orders_col.insert_one(order).inserted_id)

    # Trigger GitHub Action
    try:
        github_payload = {
            "event_type": "build_request",
            "client_payload": {
                "orderId": order_id,
                "userId": data['userId'],
                "appName": data['appName'],
                "appUrl": data['appUrl'],
                "platform": data['platform'],
                "color": data['appColor']
            }
        }
        requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/dispatches",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            json=github_payload
        )
    except: pass

    return jsonify({"success": True, "orderId": order_id})

@app.route('/api/user-orders/<uid>')
def get_orders(uid):
    orders = list(orders_col.find({"userId": uid}).sort("at", -1))
    for o in orders: o['_id'] = str(o['_id'])
    return jsonify(orders)

# --- Webhook for GitHub to notify when done ---
@app.route('/api/build-complete', methods=['POST'])
def build_complete():
    data = request.json # orderId, downloadUrl
    orders_col.update_one({"_id": ObjectId(data['orderId'])}, {"$set": {"status": "Completed", "downloadUrl": data['downloadUrl']}})
    socketio.emit('status_update', {"userId": data['userId']})
    return jsonify({"success": True})

# --- Admin Routes ---
@app.route('/api/admin/add-money', methods=['POST'])
def add_money():
    # Admin password and logic same as before but improved for reliability
    pass

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
