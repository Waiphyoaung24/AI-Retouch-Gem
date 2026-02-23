'use client';
import { useState, useEffect } from 'react';
import { HandModel, getHandModels, uploadHandModel, deleteHandModel, API_URL } from '@/lib/api';

const getImageUrl = (url: string) => {
  if (url.startsWith('http')) return url;
  return `${API_URL}${url}`;
};

export default function AdminHandModels() {
  const [handModels, setHandModels] = useState<HandModel[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchHandModels = async () => {
    try {
      const data = await getHandModels();
      setHandModels(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchHandModels();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !name) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('name', name);
    const adminKey = localStorage.getItem('adminKey') || '';

    try {
      await uploadHandModel(formData, adminKey);
      fetchHandModels();
      setFile(null);
      setName('');
      // Reset file input value
      const fileInput = document.getElementById('hand-model-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this hand model?')) return;
    
    setDeleting(id);
    const adminKey = localStorage.getItem('adminKey') || '';
    
    try {
      await deleteHandModel(id, adminKey);
      setHandModels(handModels.filter(m => m.id !== id));
    } catch (err) {
      console.error(err);
      alert('Delete failed');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Manage Hand Models</h1>
      
      <form onSubmit={handleUpload} className="mb-8 p-4 bg-white rounded shadow dark:bg-gray-800">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2 dark:text-gray-300">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline dark:bg-gray-700 dark:text-white"
            placeholder="Hand Model Name"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2 dark:text-gray-300">Image</label>
          <input
            id="hand-model-file"
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline dark:bg-gray-700 dark:text-white"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          {loading ? 'Uploading...' : 'Add Hand Model'}
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {handModels.map((model) => (
          <div key={model.id} className="bg-white rounded shadow p-4 dark:bg-gray-800 relative group">
            <img src={getImageUrl(model.image_url)} alt={model.name} className="w-full h-48 object-cover rounded mb-2" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">{model.name}</h3>
            <button
              onClick={() => handleDelete(model.id)}
              disabled={deleting === model.id}
              className="mt-2 bg-red-500 hover:bg-red-700 text-white text-sm font-bold py-1 px-3 rounded focus:outline-none focus:shadow-outline w-full disabled:opacity-50"
            >
              {deleting === model.id ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
