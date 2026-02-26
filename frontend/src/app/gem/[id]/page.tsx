'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getGem, getSettingOptions, getModelPhotos, generatePreview, validatePhoto,
  type Gem, type SettingCategory, type Metal, type SettingStyle, type ModelPhoto,
} from '@/lib/api';
import { Diamond, ChevronLeft, ChevronRight, Upload, Download, X, Loader2, Sparkles, Check } from 'lucide-react';

type Step = 'category' | 'metal' | 'style' | 'photo' | 'result';

const STEPS: { key: Step; label: string }[] = [
  { key: 'category', label: 'Category' },
  { key: 'metal', label: 'Metal' },
  { key: 'style', label: 'Style' },
  { key: 'photo', label: 'Photo' },
];

export default function GemPreviewPage() {
  const params = useParams();
  const gemId = params.id as string;

  const [gem, setGem] = useState<Gem | null>(null);
  const [categories, setCategories] = useState<SettingCategory[]>([]);
  const [metals, setMetals] = useState<Metal[]>([]);
  const [allStyles, setAllStyles] = useState<SettingStyle[]>([]);
  const [modelPhotos, setModelPhotos] = useState<ModelPhoto[]>([]);

  const [selectedCategory, setSelectedCategory] = useState<SettingCategory | null>(null);
  const [selectedMetal, setSelectedMetal] = useState<Metal | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<SettingStyle | null>(null);
  const [selectedModelPhoto, setSelectedModelPhoto] = useState<ModelPhoto | null>(null);
  const [customerPhoto, setCustomerPhoto] = useState<File | null>(null);
  const [customerPhotoPreview, setCustomerPhotoPreview] = useState<string | null>(null);

  const [step, setStep] = useState<Step>('category');
  const [generating, setGenerating] = useState(false);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!gemId) return;
    Promise.all([getGem(gemId), getSettingOptions()]).then(([g, opts]) => {
      setGem(g);
      setCategories(opts.categories);
      setMetals(opts.metals);
      setAllStyles(opts.styles);
    }).catch(() => setError('Failed to load gem details.'));
  }, [gemId]);

  const filteredStyles = allStyles.filter(s => s.category_id === selectedCategory?.id);
  const bodyPart = selectedCategory?.body_part || 'hand';

  useEffect(() => {
    if (selectedCategory) {
      getModelPhotos(selectedCategory.body_part).then(setModelPhotos).catch(() => setModelPhotos([]));
    }
  }, [selectedCategory]);

  const stepIndex = STEPS.findIndex(s => s.key === step);

  const handleCustomerPhotoUpload = useCallback(async (file: File) => {
    if (!selectedCategory) return;
    setCustomerPhoto(file);
    setCustomerPhotoPreview(URL.createObjectURL(file));
    setSelectedModelPhoto(null);
    setValidating(true);
    try {
      const fd = new FormData();
      fd.append('photo', file);
      fd.append('body_part', bodyPart);
      await validatePhoto(fd);
    } catch {
      // Validation endpoint optional — continue anyway
    } finally {
      setValidating(false);
    }
  }, [selectedCategory, bodyPart]);

  const canGenerate = selectedCategory && selectedMetal && selectedStyle && (selectedModelPhoto || customerPhoto);

  const handleGenerate = async () => {
    if (!canGenerate || !gem) return;
    setGenerating(true);
    setError(null);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress(prev => Math.min(prev + Math.random() * 8, 92));
    }, 500);

    try {
      const fd = new FormData();
      fd.append('gem_id', gem.id);
      fd.append('category_id', selectedCategory!.id);
      fd.append('metal_id', selectedMetal!.id);
      fd.append('style_id', selectedStyle!.id);
      if (selectedModelPhoto) {
        fd.append('model_photo_id', selectedModelPhoto.id);
      } else if (customerPhoto) {
        fd.append('customer_photo', customerPhoto);
      }
      const result = await generatePreview(fd);
      setProgress(100);
      setTimeout(() => {
        setResultUrl(result.result_url);
        setStep('result');
        setGenerating(false);
      }, 400);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Generation failed';
      setError(msg);
      setGenerating(false);
    } finally {
      clearInterval(interval);
    }
  };

  const handleReset = () => {
    setResultUrl(null);
    setStep('category');
    setSelectedCategory(null);
    setSelectedMetal(null);
    setSelectedStyle(null);
    setSelectedModelPhoto(null);
    setCustomerPhoto(null);
    setCustomerPhotoPreview(null);
    setProgress(0);
  };

  if (!gem) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Diamond className="w-8 h-8 text-gold gem-pulse" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-stone-400 hover:text-gold transition-colors cursor-pointer">
            <Diamond className="w-5 h-5" />
            <span className="font-[family-name:var(--font-display)] text-lg font-semibold text-stone-50">retouch-gem</span>
          </Link>
          <div className="flex items-center gap-3">
            <img src={gem.product_image_url} alt={gem.name} className="w-8 h-8 rounded-full object-cover border border-stone-700" />
            <span className="text-sm font-medium text-stone-300">{gem.name}</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Gem Hero */}
        <div className="flex flex-col sm:flex-row items-center gap-6 mb-10">
          <div className="relative">
            <img
              src={gem.product_image_url}
              alt={gem.name}
              className="w-28 h-28 rounded-2xl object-cover border border-stone-800 shadow-lg"
            />
            <div className="absolute -bottom-2 -right-2 w-7 h-7 rounded-full bg-gold flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-stone-950" />
            </div>
          </div>
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-3xl sm:text-4xl font-bold text-stone-50">{gem.name}</h1>
            {gem.description && <p className="text-stone-400 mt-1 text-sm max-w-md">{gem.description}</p>}
            {(gem.carat_weight || gem.length_mm) && (
              <p className="text-stone-500 text-xs mt-1.5">
                {gem.carat_weight && <span>{gem.carat_weight} carat</span>}
                {gem.carat_weight && gem.length_mm && <span> &middot; </span>}
                {gem.length_mm && gem.width_mm && <span>{gem.length_mm} &times; {gem.width_mm}mm</span>}
                {gem.depth_mm && <span> &times; {gem.depth_mm}mm</span>}
              </p>
            )}
            <p className="text-stone-500 text-xs mt-2">Customize your setting below</p>
          </div>
        </div>

        {/* Step Indicator */}
        {step !== 'result' && (
          <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
            {STEPS.map((s, i) => {
              const isCurrent = s.key === step;
              const isCompleted = i < stepIndex;
              return (
                <div key={s.key} className="flex items-center gap-2">
                  {i > 0 && <div className={`w-8 h-px ${isCompleted ? 'bg-gold' : 'bg-stone-700'}`} />}
                  <button
                    onClick={() => { if (isCompleted) setStep(s.key); }}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                      isCurrent
                        ? 'step-active text-stone-950'
                        : isCompleted
                        ? 'step-completed text-gold cursor-pointer'
                        : 'bg-stone-800/50 text-stone-500'
                    }`}
                    disabled={!isCompleted && !isCurrent}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : <span>{i + 1}</span>}
                    {s.label}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/50 border border-red-900/50 text-red-300 text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="cursor-pointer"><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* Step: Category */}
        {step === 'category' && (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold text-stone-100 mb-1">Choose a Category</h2>
            <p className="text-stone-500 text-sm mb-6">What type of jewelry setting?</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => { setSelectedCategory(cat); setSelectedStyle(null); setSelectedModelPhoto(null); setCustomerPhoto(null); setCustomerPhotoPreview(null); }}
                  className={`option-card p-6 rounded-2xl border text-left ${
                    selectedCategory?.id === cat.id ? 'selected border-gold' : 'border-stone-800 bg-stone-900/50'
                  }`}
                >
                  <div className="text-2xl mb-3">{cat.name === 'Ring' ? '💍' : cat.name === 'Earring' ? '✨' : '📿'}</div>
                  <h3 className="font-semibold text-stone-100 text-lg">{cat.name}</h3>
                  <p className="text-stone-500 text-xs mt-1">Fits on {cat.body_part}</p>
                </button>
              ))}
            </div>
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => selectedCategory && setStep('metal')}
                disabled={!selectedCategory}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gold text-stone-950 font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </section>
        )}

        {/* Step: Metal */}
        {step === 'metal' && (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold text-stone-100 mb-1">Choose a Metal</h2>
            <p className="text-stone-500 text-sm mb-6">Select the metal for your {selectedCategory?.name?.toLowerCase()} setting</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {metals.map(m => (
                <button
                  key={m.id}
                  onClick={() => setSelectedMetal(m)}
                  className={`option-card p-5 rounded-2xl border text-center ${
                    selectedMetal?.id === m.id ? 'selected border-gold' : 'border-stone-800 bg-stone-900/50'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full mx-auto mb-3 ${
                    m.name === 'Gold' ? 'bg-yellow-500' :
                    m.name === 'White Gold' ? 'bg-gray-200' :
                    m.name === 'Rose Gold' ? 'bg-rose-300' :
                    'bg-gray-400'
                  }`} />
                  <h3 className="font-medium text-stone-200 text-sm">{m.name}</h3>
                </button>
              ))}
            </div>
            <div className="mt-8 flex justify-between">
              <button onClick={() => setStep('category')} className="flex items-center gap-2 px-5 py-3 rounded-xl border border-stone-700 text-stone-300 hover:border-stone-500 transition-colors cursor-pointer">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => selectedMetal && setStep('style')}
                disabled={!selectedMetal}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gold text-stone-950 font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </section>
        )}

        {/* Step: Style */}
        {step === 'style' && (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold text-stone-100 mb-1">Choose a Style</h2>
            <p className="text-stone-500 text-sm mb-6">{selectedMetal?.name} {selectedCategory?.name?.toLowerCase()} styles</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {filteredStyles.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStyle(s)}
                  className={`option-card p-5 rounded-2xl border text-center ${
                    selectedStyle?.id === s.id ? 'selected border-gold' : 'border-stone-800 bg-stone-900/50'
                  }`}
                >
                  <Diamond className={`w-6 h-6 mx-auto mb-3 ${selectedStyle?.id === s.id ? 'text-gold' : 'text-stone-500'}`} />
                  <h3 className="font-medium text-stone-200 text-sm">{s.name}</h3>
                </button>
              ))}
            </div>
            <div className="mt-8 flex justify-between">
              <button onClick={() => setStep('metal')} className="flex items-center gap-2 px-5 py-3 rounded-xl border border-stone-700 text-stone-300 hover:border-stone-500 transition-colors cursor-pointer">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => selectedStyle && setStep('photo')}
                disabled={!selectedStyle}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gold text-stone-950 font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </section>
        )}

        {/* Step: Photo */}
        {step === 'photo' && (
          <section>
            <h2 className="font-[family-name:var(--font-display)] text-2xl font-semibold text-stone-100 mb-1">Choose a Photo</h2>
            <p className="text-stone-500 text-sm mb-6">Select a model photo or upload your own {bodyPart} photo</p>

            {/* Model photos grid */}
            {modelPhotos.length > 0 && (
              <div className="mb-6">
                <h3 className="text-stone-400 text-xs uppercase tracking-wider font-semibold mb-3">Preset Models</h3>
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
                  {modelPhotos.map(mp => (
                    <button
                      key={mp.id}
                      onClick={() => { setSelectedModelPhoto(mp); setCustomerPhoto(null); setCustomerPhotoPreview(null); }}
                      className={`option-card rounded-xl border overflow-hidden aspect-square ${
                        selectedModelPhoto?.id === mp.id ? 'selected border-gold' : 'border-stone-800'
                      }`}
                    >
                      <img src={mp.image_url} alt={mp.name} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Upload own photo */}
            <div className="mb-6">
              <h3 className="text-stone-400 text-xs uppercase tracking-wider font-semibold mb-3">Or Upload Your Own</h3>
              {customerPhotoPreview ? (
                <div className="relative inline-block">
                  <img src={customerPhotoPreview} alt="Your photo" className="w-32 h-32 rounded-xl object-cover border border-gold" />
                  <button
                    onClick={() => { setCustomerPhoto(null); setCustomerPhotoPreview(null); }}
                    className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-stone-800 border border-stone-600 flex items-center justify-center cursor-pointer hover:bg-stone-700 transition-colors"
                  >
                    <X className="w-3 h-3 text-stone-300" />
                  </button>
                  {validating && (
                    <div className="absolute inset-0 rounded-xl bg-stone-950/70 flex items-center justify-center">
                      <Loader2 className="w-5 h-5 text-gold animate-spin" />
                    </div>
                  )}
                </div>
              ) : (
                <label className="option-card flex flex-col items-center justify-center w-32 h-32 rounded-xl border border-dashed border-stone-700 bg-stone-900/30 hover:border-gold/50">
                  <Upload className="w-5 h-5 text-stone-500 mb-1" />
                  <span className="text-stone-500 text-xs">Upload</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={e => { if (e.target.files?.[0]) handleCustomerPhotoUpload(e.target.files[0]); }}
                  />
                </label>
              )}
            </div>

            <div className="mt-8 flex justify-between">
              <button onClick={() => setStep('style')} className="flex items-center gap-2 px-5 py-3 rounded-xl border border-stone-700 text-stone-300 hover:border-stone-500 transition-colors cursor-pointer">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={handleGenerate}
                disabled={!canGenerate || generating}
                className="flex items-center gap-2 px-8 py-3 rounded-xl bg-gold text-stone-950 font-bold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gold-light transition-colors cursor-pointer"
              >
                {generating ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                ) : (
                  <><Sparkles className="w-4 h-4" /> Generate Preview</>
                )}
              </button>
            </div>
          </section>
        )}

        {/* Generating overlay */}
        {generating && (
          <div className="fixed inset-0 z-50 bg-stone-950/90 backdrop-blur-sm flex flex-col items-center justify-center">
            <Diamond className="w-12 h-12 text-gold gem-pulse mb-6" />
            <p className="text-stone-200 font-[family-name:var(--font-display)] text-2xl mb-2">Creating Your Preview</p>
            <p className="text-stone-500 text-sm mb-6">
              {selectedStyle?.name} {selectedCategory?.name?.toLowerCase()} in {selectedMetal?.name?.toLowerCase()}
            </p>
            <div className="w-64 h-1.5 bg-stone-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-gold-dark to-gold-light rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-stone-600 text-xs mt-2">{Math.round(progress)}%</p>
          </div>
        )}

        {/* Result */}
        {step === 'result' && resultUrl && (
          <section className="text-center">
            <h2 className="font-[family-name:var(--font-display)] text-3xl font-bold text-stone-50 mb-2">Your Preview</h2>
            <p className="text-stone-500 text-sm mb-8">
              {gem.name} &middot; {selectedStyle?.name} {selectedCategory?.name} &middot; {selectedMetal?.name}
            </p>
            <div className="relative inline-block max-w-lg mx-auto">
              <img
                src={resultUrl}
                alt="Generated preview"
                className="rounded-2xl border border-stone-800 shadow-2xl w-full"
              />
            </div>
            <div className="flex items-center justify-center gap-4 mt-8">
              <a
                href={resultUrl}
                download="gem-preview.png"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gold text-stone-950 font-semibold hover:bg-gold-light transition-colors cursor-pointer"
              >
                <Download className="w-4 h-4" /> Download
              </a>
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-3 rounded-xl border border-stone-700 text-stone-300 hover:border-stone-500 transition-colors cursor-pointer"
              >
                Try Another
              </button>
            </div>
          </section>
        )}
      </main>

      <footer className="text-center py-6 text-stone-600 text-xs">
        Powered by Gemini &middot; Retouch Gem
      </footer>
    </div>
  );
}
