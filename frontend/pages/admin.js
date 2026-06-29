import { useState, useEffect } from 'react';

export default function Admin() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [amount, setAmount] = useState(0);
  const [adminPass, setAdminPass] = useState('');

  const fetchUsers = async () => {
    const res = await fetch('https://your-backend-render.com/api/admin/users');
    setUsers(await res.json());
  };

  const addMoney = async (email) => {
    await fetch('https://your-backend-render.com/api/admin/add-balance', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email, amount: Number(amount), adminPass })
    });
    alert("Money Added!");
    fetchUsers();
  };

  return (
    <div className="p-10">
      <h2 className="text-3xl font-bold mb-6">Admin Control Panel</h2>
      <input type="password" placeholder="Admin Password" onChange={e => setAdminPass(e.target.value)} className="border p-2 mb-4 w-full" />
      <button onClick={fetchUsers} className="bg-black text-white p-2 mb-4">Load User List</button>
      
      <table className="w-full border text-left">
        <thead>
          <tr>
            <th className="p-2 border">Name</th>
            <th className="p-2 border">Email</th>
            <th className="p-2 border">Password</th>
            <th className="p-2 border">Balance</th>
            <th className="p-2 border">Action</th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u._id}>
              <td className="p-2 border">{u.fullName}</td>
              <td className="p-2 border">{u.email}</td>
              <td className="p-2 border text-red-500">{u.password}</td>
              <td className="p-2 border font-bold text-blue-600">{u.balance} TK</td>
              <td className="p-2 border">
                <input type="number" className="border w-20" onChange={e => setAmount(e.target.value)} />
                <button onClick={() => addMoney(u.email)} className="ml-2 bg-green-500 text-white px-2">Add</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
