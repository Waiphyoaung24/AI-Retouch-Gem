import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-900 text-white p-4">
      <header className="absolute top-0 w-full p-6 flex justify-between items-center">
        <h1 className="text-2xl font-serif text-yellow-500">retouch-gem</h1>
        <Link href="/admin/login" className="text-sm text-gray-400 hover:text-white">Admin</Link>
      </header>
      
      <main className="text-center max-w-2xl">
        <h2 className="text-5xl font-serif mb-6 leading-tight">
          Experience Jewellery <br />
          <span className="text-yellow-500">Like Never Before</span>
        </h2>
        <p className="text-xl text-gray-300 mb-10 font-sans">
          Visualize our exquisite pieces on your hand instantly with our AI-powered virtual try-on.
        </p>
        <Link 
          href="/try-on" 
          className="bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-4 px-10 rounded-full transition-all transform hover:scale-105 shadow-lg"
        >
          Try On Now
        </Link>
      </main>
      
      <footer className="absolute bottom-0 w-full p-4 text-center text-gray-500 text-sm">
        &copy; 2026 Retouch Gem. Powered by Gemini.
      </footer>
    </div>
  );
}
