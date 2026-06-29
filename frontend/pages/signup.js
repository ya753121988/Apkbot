import { useState } from 'react';
import { useRouter } from 'next/router';

export default function Signup() {
  const [form, setForm] = useState({ fullName: '', email: '', password: '' });
  const router = useRouter();

  const handleSignup = async () => {
    await fetch('https://your-backend-render.com/api/signup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(form)
    });
    router.push('/login');
  };

  return (
    <div className="flex flex-col items-center p-20">
      <h2 className="text-2xl font-bold mb-4">Create Account</h2>
      <input className="border p-2 mb-2 w-80" placeholder="Full Name" onChange={e => setForm({...form, fullName: e.target.value})} />
      <input className="border p-2 mb-2 w-80" placeholder="Email" onChange={e => setForm({...form, email: e.target.value})} />
      <input className="border p-2 mb-4 w-80" type="password" placeholder="Password" onChange={e => setForm({...form, password: e.target.value})} />
      <button onClick={handleSignup} className="bg-blue-600 text-white p-2 w-80 rounded">Sign Up</button>
    </div>
  );
}
