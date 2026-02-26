import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-950 text-stone-50">
      {/* Header */}
      <header className="w-full px-6 py-5 flex justify-between items-center max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold to-gold-light flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-stone-950"><path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/></svg>
          </div>
          <span className="font-[family-name:var(--font-display)] text-xl font-bold tracking-tight">retouch-gem</span>
        </div>
        <Link href="/admin/login" className="text-sm text-stone-500 hover:text-stone-300 transition-colors cursor-pointer">
          Admin
        </Link>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="text-center max-w-2xl">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-stone-900 border border-stone-800 text-stone-400 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
            AI-Powered Gem Preview
          </div>

          <h1 className="font-[family-name:var(--font-display)] text-5xl sm:text-7xl font-bold leading-[1.1] mb-6">
            See Your Gem in{' '}
            <span className="text-shimmer">Any Setting</span>
          </h1>

          <p className="text-lg sm:text-xl text-stone-400 mb-10 leading-relaxed max-w-lg mx-auto font-[family-name:var(--font-body)]">
            Dealers share a link. Customers choose their category, metal, and style —
            then preview the gemstone in a photorealistic jewelry setting.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <div className="glass-panel rounded-2xl px-8 py-5 text-center">
              <p className="text-3xl font-[family-name:var(--font-display)] font-bold text-gold mb-1">3</p>
              <p className="text-xs text-stone-500 uppercase tracking-wider">Categories</p>
            </div>
            <div className="glass-panel rounded-2xl px-8 py-5 text-center">
              <p className="text-3xl font-[family-name:var(--font-display)] font-bold text-gold mb-1">4</p>
              <p className="text-xs text-stone-500 uppercase tracking-wider">Metals</p>
            </div>
            <div className="glass-panel rounded-2xl px-8 py-5 text-center">
              <p className="text-3xl font-[family-name:var(--font-display)] font-bold text-gold mb-1">12</p>
              <p className="text-xs text-stone-500 uppercase tracking-wider">Styles</p>
            </div>
          </div>

          <p className="text-stone-600 text-sm mt-12">
            Received a gem link from a dealer? Open it directly to start customizing.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-stone-700 text-xs">
        &copy; 2026 Retouch Gem &middot; Powered by Gemini
      </footer>
    </div>
  );
}
