'use client';

import { useEffect, useState } from 'react';
import { getGems, createGem, deleteGem, type Gem } from '@/lib/api';
import { Plus, Trash2, Copy, Check, Diamond, Loader2 } from 'lucide-react';

export default function AdminGemsPage() {
  const [gems, setGems] = useState<Gem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [caratWeight, setCaratWeight] = useState('');
  const [lengthMm, setLengthMm] = useState('');
  const [widthMm, setWidthMm] = useState('');
  const [depthMm, setDepthMm] = useState('');
  const [productImage, setProductImage] = useState<File | null>(null);
  const [contextImage, setContextImage] = useState<File | null>(null);

  const adminKey = typeof window !== 'undefined' ? localStorage.getItem('adminKey') || '' : '';

  const fetchGems = async () => {
    setLoading(true);
    try { setGems(await getGems()); } catch { /* empty */ }
    setLoading(false);
  };

  useEffect(() => { fetchGems(); }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !productImage || !contextImage) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('name', name);
      fd.append('product_image', productImage);
      fd.append('context_image', contextImage);
      if (description) fd.append('description', description);
      if (caratWeight) fd.append('carat_weight', caratWeight);
      if (lengthMm) fd.append('length_mm', lengthMm);
      if (widthMm) fd.append('width_mm', widthMm);
      if (depthMm) fd.append('depth_mm', depthMm);
      await createGem(fd, adminKey);
      setName(''); setDescription(''); setCaratWeight(''); setLengthMm(''); setWidthMm(''); setDepthMm(''); setProductImage(null); setContextImage(null);
      await fetchGems();
    } catch (err) {
      alert('Upload failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
    setUploading(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this gem?')) return;
    try {
      await deleteGem(id, adminKey);
      await fetchGems();
    } catch (err) {
      alert('Delete failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleCopyLink = (id: string) => {
    const url = `${window.location.origin}/gem/${id}`;
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-stone-100">Gems</h1>
          <p className="text-stone-500 text-sm mt-1">Upload gemstones with product &amp; context images</p>
        </div>
        <span className="text-stone-600 text-sm">{gems.length} gems</span>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="glass-panel rounded-2xl p-6 mb-8">
        <h2 className="text-lg font-semibold text-stone-200 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-gold" /> Add New Gem
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Blue Sapphire 2.5ct"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Description</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Carat Weight</label>
            <input
              type="number"
              step="0.01"
              value={caratWeight}
              onChange={e => setCaratWeight(e.target.value)}
              placeholder="e.g. 2.5"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Length (mm)</label>
            <input
              type="number"
              step="0.1"
              value={lengthMm}
              onChange={e => setLengthMm(e.target.value)}
              placeholder="e.g. 8.5"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Width (mm)</label>
            <input
              type="number"
              step="0.1"
              value={widthMm}
              onChange={e => setWidthMm(e.target.value)}
              placeholder="e.g. 6.5"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Depth (mm)</label>
            <input
              type="number"
              step="0.1"
              value={depthMm}
              onChange={e => setDepthMm(e.target.value)}
              placeholder="e.g. 4.0"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
            />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Product Image *</label>
            <input
              type="file"
              accept="image/*"
              onChange={e => setProductImage(e.target.files?.[0] || null)}
              className="w-full text-sm text-stone-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-stone-700 file:text-stone-200 file:font-medium file:cursor-pointer hover:file:bg-stone-600"
              required
            />
            <p className="text-xs text-stone-600 mt-1">Clean product photo of the loose gemstone</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Context Image *</label>
            <input
              type="file"
              accept="image/*"
              onChange={e => setContextImage(e.target.files?.[0] || null)}
              className="w-full text-sm text-stone-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-stone-700 file:text-stone-200 file:font-medium file:cursor-pointer hover:file:bg-stone-600"
              required
            />
            <p className="text-xs text-stone-600 mt-1">Photo showing the gem in context (on hand, etc.)</p>
          </div>
        </div>
        <button
          type="submit"
          disabled={uploading || !name || !productImage || !contextImage}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gold text-stone-950 font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
        >
          {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</> : <><Plus className="w-4 h-4" /> Upload Gem</>}
        </button>
      </form>

      {/* Gems Grid */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 text-gold animate-spin" /></div>
      ) : gems.length === 0 ? (
        <div className="text-center py-16">
          <Diamond className="w-10 h-10 text-stone-700 mx-auto mb-3" />
          <p className="text-stone-500">No gems yet. Upload your first gem above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {gems.map(gem => (
            <div key={gem.id} className="glass-panel rounded-2xl overflow-hidden group">
              <div className="flex">
                <img src={gem.product_image_url} alt={gem.name} className="w-1/2 h-40 object-cover" />
                <img src={gem.context_image_url} alt={`${gem.name} context`} className="w-1/2 h-40 object-cover" />
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-stone-100">{gem.name}</h3>
                {gem.description && <p className="text-stone-500 text-xs mt-0.5">{gem.description}</p>}
                {(gem.carat_weight || gem.length_mm) && (
                  <p className="text-stone-600 text-xs mt-1">
                    {gem.carat_weight && <span>{gem.carat_weight}ct</span>}
                    {gem.carat_weight && gem.length_mm && <span> &middot; </span>}
                    {gem.length_mm && gem.width_mm && <span>{gem.length_mm}&times;{gem.width_mm}mm</span>}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-3">
                  <button
                    onClick={() => handleCopyLink(gem.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-stone-800 border border-stone-700 text-stone-300 text-xs hover:border-gold hover:text-gold transition-colors cursor-pointer"
                  >
                    {copiedId === gem.id ? <><Check className="w-3 h-3" /> Copied!</> : <><Copy className="w-3 h-3" /> Copy Link</>}
                  </button>
                  <button
                    onClick={() => handleDelete(gem.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-stone-800 border border-stone-700 text-stone-300 text-xs hover:border-red-500 hover:text-red-400 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3 h-3" /> Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
