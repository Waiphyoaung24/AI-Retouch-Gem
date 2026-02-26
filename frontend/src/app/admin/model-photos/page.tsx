'use client';

import { useEffect, useState } from 'react';
import { getModelPhotos, createModelPhoto, deleteModelPhoto, type ModelPhoto } from '@/lib/api';
import { Plus, Trash2, Camera, Loader2 } from 'lucide-react';

const BODY_PARTS = [
  { value: 'hand', label: 'Hand' },
  { value: 'ear', label: 'Ear' },
  { value: 'neck', label: 'Neck' },
];

export default function AdminModelPhotosPage() {
  const [photos, setPhotos] = useState<ModelPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filterPart, setFilterPart] = useState<string | undefined>(undefined);

  const [name, setName] = useState('');
  const [bodyPart, setBodyPart] = useState('hand');
  const [image, setImage] = useState<File | null>(null);

  const adminKey = typeof window !== 'undefined' ? localStorage.getItem('adminKey') || '' : '';

  const fetchPhotos = async () => {
    setLoading(true);
    try { setPhotos(await getModelPhotos(filterPart)); } catch { /* empty */ }
    setLoading(false);
  };

  useEffect(() => { fetchPhotos(); }, [filterPart]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !image) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('name', name);
      fd.append('body_part', bodyPart);
      fd.append('image', image);
      await createModelPhoto(fd, adminKey);
      setName(''); setImage(null);
      await fetchPhotos();
    } catch (err) {
      alert('Upload failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
    setUploading(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this model photo?')) return;
    try { await deleteModelPhoto(id, adminKey); await fetchPhotos(); } catch { /* empty */ }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-stone-100">Model Photos</h1>
          <p className="text-stone-500 text-sm mt-1">Preset body-part photos for gem previews</p>
        </div>
        <span className="text-stone-600 text-sm">{photos.length} photos</span>
      </div>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="glass-panel rounded-2xl p-6 mb-8">
        <h2 className="text-lg font-semibold text-stone-200 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-gold" /> Add Model Photo
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Female hand, light skin"
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 placeholder:text-stone-600 focus:border-gold focus:outline-none transition-colors"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Body Part *</label>
            <select
              value={bodyPart}
              onChange={e => setBodyPart(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-stone-800 border border-stone-700 text-stone-100 focus:border-gold focus:outline-none transition-colors cursor-pointer"
            >
              {BODY_PARTS.map(bp => (
                <option key={bp.value} value={bp.value}>{bp.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-400 mb-1">Photo *</label>
            <input
              type="file"
              accept="image/*"
              onChange={e => setImage(e.target.files?.[0] || null)}
              className="w-full text-sm text-stone-400 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-stone-700 file:text-stone-200 file:font-medium file:cursor-pointer hover:file:bg-stone-600"
              required
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={uploading || !name || !image}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gold text-stone-950 font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
        >
          {uploading ? <><Loader2 className="w-4 h-4 animate-spin" /> Uploading...</> : <><Plus className="w-4 h-4" /> Upload Photo</>}
        </button>
      </form>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => setFilterPart(undefined)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
            !filterPart ? 'bg-gold text-stone-950' : 'bg-stone-800 text-stone-400 hover:text-stone-200'
          }`}
        >
          All
        </button>
        {BODY_PARTS.map(bp => (
          <button
            key={bp.value}
            onClick={() => setFilterPart(bp.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
              filterPart === bp.value ? 'bg-gold text-stone-950' : 'bg-stone-800 text-stone-400 hover:text-stone-200'
            }`}
          >
            {bp.label}
          </button>
        ))}
      </div>

      {/* Photos Grid */}
      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 text-gold animate-spin" /></div>
      ) : photos.length === 0 ? (
        <div className="text-center py-16">
          <Camera className="w-10 h-10 text-stone-700 mx-auto mb-3" />
          <p className="text-stone-500">No model photos{filterPart ? ` for ${filterPart}` : ''}. Upload some above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {photos.map(photo => (
            <div key={photo.id} className="glass-panel rounded-2xl overflow-hidden group">
              <img src={photo.image_url} alt={photo.name} className="w-full aspect-square object-cover" />
              <div className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-stone-200 truncate">{photo.name}</p>
                  <p className="text-xs text-stone-500 capitalize">{photo.body_part}</p>
                </div>
                <button
                  onClick={() => handleDelete(photo.id)}
                  className="p-2 rounded-lg text-stone-500 hover:text-red-400 hover:bg-stone-800 transition-colors cursor-pointer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
