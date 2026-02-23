'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

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

  if (isLoading) {
    return null;
  }

  // If it's the login page, just render children without the admin header
  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleLogout = () => {
    localStorage.removeItem('adminKey');
    router.push('/admin/login');
  };

  return (
    <div className="flex flex-col min-h-screen">
      <header className="bg-gray-800 text-white p-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-bold">Admin Dashboard</h1>
        <nav>
          <ul className="flex gap-4 items-center">
            <li><Link href="/admin/products" className="hover:text-blue-400 transition-colors">Products</Link></li>
            <li><Link href="/admin/hand-models" className="hover:text-blue-400 transition-colors">Hand Models</Link></li>
            <li>
              <button onClick={handleLogout} className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded transition-colors">
                Logout
              </button>
            </li>
          </ul>
        </nav>
      </header>
      <main className="flex-1 p-8 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        {children}
      </main>
    </div>
  );
}
