import os
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)

# --- কনফিগারেশন ও ডাটাবেস ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['WebToAppSaaS']
users_col = db['users']
apps_col = db['apps']

ADMIN_PASS = "admin1234" # এডমিন প্যানেলের পাসওয়ার্ড
APP_PRICE = 500 # প্রতি অ্যাপের দাম

# --- স্টাইল এবং ফ্রন্টএন্ড টেম্পলেট (Tailwind CSS ব্যবহার করা হয়েছে) ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web to APK Maker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <nav class="bg-blue-600 p-4 text-white flex justify-between">
        <h1 class="font-bold text-xl">WebToApp SaaS</h1>
        <div id="nav-links"></div>
    </nav>
    <div class="container mx-auto p-6">
        {{ content | safe }}
    </div>

    <script>
        const user = JSON.parse(localStorage.getItem('user'));
        const nav = document.getElementById('nav-links');
        if(user) {
            nav.innerHTML = `<span class="mr-4">Balance: ${user.balance} TK</span><button onclick="logout()" class="bg-red-500 px-3 py-1 rounded">Logout</button>`;
        } else {
            nav.innerHTML = `<a href="/login" class="mr-4">Login</a><a href="/signup" class="bg-white text-blue-600 px-3 py-1 rounded">Signup</a>`;
        }
        function logout() { localStorage.clear(); window.location.href='/login'; }
    </script>
</body>
</html>
"""

# --- রুটস (Pages) ---

@app.route('/')
def index():
    content = """
    <div class="text-center mt-20">
        <h1 class="text-5xl font-bold text-gray-800">Convert Any Website to Android & iOS App</h1>
        <p class="text-xl text-gray-600 mt-4">Professional APK, AAB, and PC executable in minutes.</p>
        <a href="/signup" class="inline-block mt-8 bg-blue-600 text-white px-8 py-3 rounded-full text-lg">Start Building Now</a>
    </div>
    """
    return render_template_string(HTML_LAYOUT, content=content)

@app.route('/signup')
def signup_page():
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-6">Create Account</h2>
        <input id="name" type="text" placeholder="Full Name" class="w-full border p-2 mb-4">
        <input id="email" type="email" placeholder="Email" class="w-full border p-2 mb-4">
        <input id="pass" type="password" placeholder="Password" class="w-full border p-2 mb-4">
        <button onclick="signup()" class="w-full bg-blue-600 text-white p-2 rounded">Register</button>
    </div>
    <script>
        async function signup() {
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const pass = document.getElementById('pass').value;
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({fullName: name, email, password: pass})
            });
            if(res.ok) { alert('Success! Please Login'); window.location.href='/login'; }
        }
    </script>
    """
    return render_template_string(HTML_LAYOUT, content=content)

@app.route('/login')
def login_page():
    content = """
    <div class="max-w-md mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-6">User Login</h2>
        <input id="email" type="email" placeholder="Email" class="w-full border p-2 mb-4">
        <input id="pass" type="password" placeholder="Password" class="w-full border p-2 mb-4">
        <button onclick="login()" class="w-full bg-blue-600 text-white p-2 rounded">Login</button>
    </div>
    <script>
        async function login() {
            const email = document.getElementById('email').value;
            const pass = document.getElementById('pass').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password: pass})
            });
            const data = await res.json();
            if(res.ok) { localStorage.setItem('user', JSON.stringify(data)); window.location.href='/dashboard'; }
            else { alert('Invalid Login'); }
        }
    </script>
    """
    return render_template_string(HTML_LAYOUT, content=content)

@app.route('/dashboard')
def dashboard():
    content = """
    <div class="max-w-2xl mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">Create Your Web App</h2>
        <p class="text-red-500 mb-6 font-bold">Cost: 500 TK per Build</p>
        
        <label>App Name</label>
        <input id="appName" class="w-full border p-2 mb-4" placeholder="My Awesome App">
        
        <label>Website URL</label>
        <input id="appUrl" class="w-full border p-2 mb-4" placeholder="https://example.com">
        
        <label>Platform</label>
        <select id="platform" class="w-full border p-2 mb-4">
            <option value="Android APK">Android APK</option>
            <option value="Android AAB (Play Store)">Android AAB (Play Store)</option>
            <option value="iOS App">iOS (.ipa)</option>
            <option value="Windows PC">Windows (.exe)</option>
        </select>
        
        <label>Primary Color</label>
        <input id="color" type="color" class="w-full h-10 mb-6">
        
        <button onclick="buildApp()" class="w-full bg-green-600 text-white p-3 rounded font-bold text-lg">Order Build</button>
    </div>
    <script>
        async function buildApp() {
            const user = JSON.parse(localStorage.getItem('user'));
            const appData = {
                userId: user._id,
                appName: document.getElementById('appName').value,
                appUrl: document.getElementById('appUrl').value,
                platform: document.getElementById('platform').value,
                appColor: document.getElementById('color').value
            };
            const res = await fetch('/api/create-app', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(appData)
            });
            const data = await res.json();
            if(res.ok) { alert('Build Request Sent!'); location.reload(); }
            else { alert(data.error); }
        }
    </script>
    """
    return render_template_string(HTML_LAYOUT, content=content)

@app.route('/admin')
def admin_page():
    content = """
    <div class="bg-white p-8 rounded shadow">
        <h2 class="text-3xl font-bold mb-6">Admin Panel - User Management</h2>
        <input id="adminPass" type="password" placeholder="Admin Password" class="border p-2 mb-4 w-full">
        <button onclick="loadUsers()" class="bg-black text-white px-4 py-2 rounded">Load User Data</button>
        
        <div class="mt-8 overflow-x-auto">
            <table class="w-full border">
                <thead>
                    <tr class="bg-gray-200">
                        <th class="p-2 border">Name</th>
                        <th class="p-2 border">Email</th>
                        <th class="p-2 border">Password</th>
                        <th class="p-2 border">Balance</th>
                        <th class="p-2 border">Add Money</th>
                    </tr>
                </thead>
                <tbody id="userTable"></tbody>
            </table>
        </div>
    </div>
    <script>
        async function loadUsers() {
            const adminPass = document.getElementById('adminPass').value;
            const res = await fetch('/api/admin/users', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({adminPass})
            });
            const users = await res.json();
            const table = document.getElementById('userTable');
            table.innerHTML = '';
            users.forEach(u => {
                table.innerHTML += `
                <tr>
                    <td class="p-2 border">${u.fullName}</td>
                    <td class="p-2 border">${u.email}</td>
                    <td class="p-2 border text-red-500 font-mono">${u.password}</td>
                    <td class="p-2 border font-bold">${u.balance} TK</td>
                    <td class="p-2 border">
                        <input id="amt-${u.email}" type="number" class="border w-20" placeholder="Amount">
                        <button onclick="addMoney('${u.email}')" class="bg-green-500 text-white px-2 rounded">Add</button>
                    </td>
                </tr>`;
            });
        }
        async function addMoney(email) {
            const adminPass = document.getElementById('adminPass').value;
            const amount = document.getElementById('amt-'+email).value;
            await fetch('/api/admin/add-balance', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({adminPass, email, amount})
            });
            alert('Money Added!');
            loadUsers();
        }
    </script>
    """
    return render_template_string(HTML_LAYOUT, content=content)

# --- API ENDPOINTS ---

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    if users_col.find_one({"email": data['email']}):
        return jsonify({"error": "Exists"}), 400
    data['balance'] = 0
    users_col.insert_one(data)
    return jsonify({"success": True})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = users_col.find_one({"email": data['email'], "password": data['password']})
    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user)
    return jsonify({"error": "Failed"}), 401

@app.route('/api/create-app', methods=['POST'])
def api_create_app():
    data = request.json
    user = users_col.find_one({"_id": ObjectId(data['userId'])})
    if user['balance'] < APP_PRICE:
        return jsonify({"error": "Insufficient Balance"}), 400
    
    users_col.update_one({"_id": ObjectId(data['userId'])}, {"$inc": {"balance": -APP_PRICE}})
    apps_col.insert_one(data)
    return jsonify({"success": True})

@app.route('/api/admin/users', methods=['POST'])
def api_admin_users():
    if request.json.get('adminPass') != ADMIN_PASS:
        return jsonify({"error": "Unauth"}), 403
    users = list(users_col.find({}))
    for u in users: u['_id'] = str(u['_id'])
    return jsonify(users)

@app.route('/api/admin/add-balance', methods=['POST'])
def api_add_balance():
    data = request.json
    if data.get('adminPass') != ADMIN_PASS:
        return jsonify({"error": "Unauth"}), 403
    users_col.update_one({"email": data['email']}, {"$inc": {"balance": int(data['amount'])}})
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
