'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { Diamond, Gem, Camera, LogOut } from 'lucide-react';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const key = localStorage.getItem('adminKey');
    const isLoginPage = pathname === '/admin/login';

    if (!key && !isLoginPage) {
      router.push('/admin/login');
    } else {
      if (key) setIsAuthenticated(true);
      setIsLoading(false);
    }
  }, [router, pathname]);

  if (isLoading) return null;

  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  if (!isAuthenticated) return null;

  const handleLogout = () => {
    localStorage.removeItem('adminKey');
    router.push('/admin/login');
  };

  const navItems = [
    { href: '/admin/gems', label: 'Gems', icon: Gem },
    { href: '/admin/model-photos', label: 'Model Photos', icon: Camera },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-stone-950">
      <header className="sticky top-0 z-50 glass-panel px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/admin/gems" className="flex items-center gap-2 cursor-pointer">
              <Diamond className="w-5 h-5 text-gold" />
              <span className="font-[family-name:var(--font-display)] text-lg font-semibold text-stone-50">Admin</span>
            </Link>
            <nav className="flex items-center gap-1">
              {navItems.map(item => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                      isActive
                        ? 'bg-stone-800 text-gold'
                        : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800/50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-stone-400 hover:text-red-400 hover:bg-stone-800/50 text-sm transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {children}
      </main>
    </div>
  );
}
