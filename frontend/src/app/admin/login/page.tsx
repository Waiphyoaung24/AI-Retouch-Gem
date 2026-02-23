'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminLogin() {
  const [key, setKey] = useState('');
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (key) {
      localStorage.setItem('adminKey', key);
      router.push('/admin');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
      <form onSubmit={handleLogin} className="flex flex-col gap-6 p-10 bg-slate-900 rounded-xl shadow-2xl border border-slate-800 w-full max-w-md">
        <div className="space-y-2">
          <h1 className="text-3xl font-extrabold text-center text-white tracking-tight">Admin Portal</h1>
          <p className="text-slate-400 text-center text-sm">Enter your credentials to access the dashboard</p>
        </div>
        <div className="space-y-4">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-slate-300 ml-1">Admin Key</label>
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="••••••••"
              className="p-3 border border-slate-700 rounded-lg bg-slate-800 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              required
            />
          </div>
          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-lg shadow-lg shadow-blue-900/20 transition-all active:scale-[0.98]"
          >
            Sign In
          </button>
        </div>
      </form>
    </div>
  );
}
