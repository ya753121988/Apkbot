import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [app, setApp] = useState({ name: '', url: '', color: '#000000', platform: 'Android' });

  useEffect(() => {
    const data = JSON.parse(localStorage.getItem('user'));
    setUser(data);
  }, []);

  const buildApp = async () => {
    const res = await fetch('https://your-backend-render.com/api/build-app', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ ...app, userId: user._id })
    });
    const result = await res.json();
    if(result.success) alert("Build Request Sent! 500 TK Deducted.");
    else alert(result.error);
  };

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold">Welcome, {user?.fullName}</h1>
      <p className="text-green-600 font-bold">Balance: {user?.balance} TK</p>
      
      <div className="mt-10 border p-6 max-w-lg">
        <h3 className="text-xl mb-4">Create New App (Cost: 500 TK)</h3>
        <input className="border w-full p-2 mb-2" placeholder="App Name" onChange={e => setApp({...app, name: e.target.value})} />
        <input className="border w-full p-2 mb-2" placeholder="URL (https://example.com)" onChange={e => setApp({...app, url: e.target.value})} />
        <select className="border w-full p-2 mb-2" onChange={e => setApp({...app, platform: e.target.value})}>
           <option value="Android">Android (APK/AAB)</option>
           <option value="iOS">iOS (.ipa)</option>
           <option value="PC">Windows (.exe)</option>
        </select>
        <input type="color" className="w-full h-10 mb-4" onChange={e => setApp({...app, color: e.target.value})} />
        <button onClick={buildApp} className="bg-green-600 text-white w-full py-2 rounded">Order Build</button>
      </div>
    </div>
  );
}
