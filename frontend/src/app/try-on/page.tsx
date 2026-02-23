'use client';

import { useState, useEffect, useRef } from 'react';
import { Product, HandModel, TryOnResult, getProducts, getHandModels, tryOn, API_URL } from '@/lib/api';
import clsx from 'clsx';
import Link from 'next/link';

const getImageUrl = (url: string) => {
  if (url.startsWith('http')) return url;
  return `${API_URL}${url}`;
};

export default function TryOnPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [handModels, setHandModels] = useState<HandModel[]>([]);
  
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [selectedHandModelId, setSelectedHandModelId] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TryOnResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getProducts().then(setProducts).catch(console.error);
    getHandModels().then(setHandModels).catch(console.error);
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      setProgress(0);
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) return 95;
          // Increment by a random amount that decreases as we get closer to 95
          const remaining = 95 - prev;
          const increment = Math.random() * (remaining / 10) + 0.5;
          return prev + increment;
        });
      }, 500);
    } else {
      setProgress(100);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleProductSelect = (id: string) => {
    setSelectedProductId(id);
    setCustomFile(null); // Clear custom file
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCustomFile(file);
      setSelectedProductId(null); // Clear product selection
    }
  };

  const handleTryOn = async () => {
    if (!selectedHandModelId) return;
    if (!selectedProductId && !customFile) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('hand_model_id', selectedHandModelId);
    if (selectedProductId) {
      formData.append('product_id', selectedProductId);
    } else if (customFile) {
      formData.append('jewellery_image', customFile);
    }

    try {
      const res = await tryOn(formData);
      setResult(res);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Try-on failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  const GemIcon = ({ className }: { className?: string }) => (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <path d="M12 2L2 9L12 22L22 9L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 9H22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 2V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 22V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans p-4 md:p-8 relative">
      {loading && (
        <div className="fixed inset-0 z-50 bg-gray-900/90 backdrop-blur-md flex flex-col items-center justify-center animate-fade-in">
          <div className="relative w-32 h-32 mb-8">
            {/* Outer rotating ring */}
            <div className="absolute inset-0 border-4 border-yellow-600/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-t-yellow-500 rounded-full animate-spin"></div>
            
            {/* Inner pulsing circle */}
            <div className="absolute inset-4 bg-yellow-900/20 rounded-full animate-pulse"></div>
            
            {/* Gem Icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <GemIcon className="w-12 h-12 text-yellow-400 drop-shadow-[0_0_15px_rgba(234,179,8,0.5)] animate-bounce" />
            </div>
          </div>
          
          <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-200 to-yellow-600 font-serif mb-4 tabular-nums">
            {Math.round(progress)}%
          </div>
          
          <p className="text-yellow-100/80 text-lg font-light tracking-wide animate-pulse">
            Polishing your gem...
          </p>
        </div>
      )}

      <header className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-serif text-yellow-500">Virtual Try-On</h1>
        <Link href="/" className="text-gray-400 hover:text-white">Back to Home</Link>
      </header>

      {result ? (
        <div className="flex flex-col items-center animate-fade-in">
          <div className="bg-gray-800 p-4 rounded-lg shadow-lg max-w-2xl w-full">
            <h2 className="text-2xl font-serif mb-4 text-center">Your Result</h2>
            <img 
              src={getImageUrl(result.result_url)} 
              alt="Try On Result" 
              className="w-full rounded-lg shadow-lg mb-4"
            />
            <div className="flex justify-center gap-4">
              <a 
                href={getImageUrl(result.result_url)} 
                download="retouch-gem-result.jpg"
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-2 rounded-full transition-colors"
                target="_blank"
                rel="noreferrer"
              >
                Download
              </a>
              <button 
                onClick={reset}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-full transition-colors"
              >
                Try Another
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Step 1: Select Jewellery */}
          <section className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span className="bg-yellow-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm">1</span>
              Select Jewellery
            </h2>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6 max-h-96 overflow-y-auto custom-scrollbar">
              {products.map(p => (
                <div 
                  key={p.id}
                  onClick={() => handleProductSelect(p.id)}
                  className={clsx(
                    "cursor-pointer border-2 rounded-lg overflow-hidden transition-all",
                    selectedProductId === p.id ? "border-yellow-500 ring-2 ring-yellow-500/50" : "border-gray-700 hover:border-gray-500"
                  )}
                >
                  <img src={getImageUrl(p.image_url)} alt={p.name} className="w-full h-32 object-cover" />
                  <p className="p-2 text-sm text-center truncate bg-gray-900">{p.name}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-gray-700 pt-4">
              <p className="text-sm text-gray-400 mb-2">Or upload your own photo:</p>
              <input 
                type="file" 
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="block w-full text-sm text-gray-400
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-yellow-600 file:text-white
                  hover:file:bg-yellow-700
                "
              />
              {customFile && (
                <p className="mt-2 text-green-400 text-sm">Selected: {customFile.name}</p>
              )}
            </div>
          </section>

          {/* Step 2: Select Hand Model */}
          <section className="bg-gray-800 p-6 rounded-lg shadow-lg flex flex-col">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span className="bg-yellow-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm">2</span>
              Select Hand Model
            </h2>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 flex-1 overflow-y-auto max-h-96 custom-scrollbar">
              {handModels.map(h => (
                <div 
                  key={h.id}
                  onClick={() => setSelectedHandModelId(h.id)}
                  className={clsx(
                    "cursor-pointer border-2 rounded-lg overflow-hidden transition-all relative group",
                    selectedHandModelId === h.id ? "border-yellow-500 ring-2 ring-yellow-500/50" : "border-gray-700 hover:border-gray-500"
                  )}
                >
                  <img src={getImageUrl(h.image_url)} alt={h.name} className="w-full h-40 object-cover" />
                  <div className="absolute inset-x-0 bottom-0 bg-black/70 p-1 text-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="text-xs text-white">{h.name}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-6 pt-6 border-t border-gray-700">
               <button
                onClick={handleTryOn}
                disabled={loading || !selectedHandModelId || (!selectedProductId && !customFile)}
                className="w-full bg-gradient-to-r from-yellow-600 to-yellow-500 hover:from-yellow-700 hover:to-yellow-600 text-white font-bold py-4 rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {loading ? 'Processing...' : 'Try On Now'}
              </button>
              {error && (
                <p className="mt-4 text-red-400 text-center text-sm bg-red-900/20 p-2 rounded border border-red-900/50">{error}</p>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
