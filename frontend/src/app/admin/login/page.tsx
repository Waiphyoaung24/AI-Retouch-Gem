'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Diamond } from 'lucide-react';

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
    <div className="flex min-h-screen items-center justify-center bg-stone-950 text-stone-50 px-4">
      <form onSubmit={handleLogin} className="glass-panel rounded-2xl p-10 w-full max-w-md">
        <div className="text-center mb-8">
          <Diamond className="w-10 h-10 text-gold mx-auto mb-4" />
          <h1 className="font-[family-name:var(--font-display)] text-3xl font-bold text-stone-50">Admin Portal</h1>
          <p className="text-stone-500 text-sm mt-1">Enter your credentials to access the dashboard</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1.5">Admin Key</label>
            <input
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Enter admin key"
              className="w-full px-4 py-3 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 rounded-xl bg-gold text-stone-950 font-semibold hover:bg-gold-light transition-colors cursor-pointer"
          >
            Sign In
          </button>
        </div>
      </form>
    </div>
  );
}
