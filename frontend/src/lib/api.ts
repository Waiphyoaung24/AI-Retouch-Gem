import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
export const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL.replace(/\/+$/, '')}/api`;

const api = axios.create({
  baseURL: API_URL,
  headers: { 'ngrok-skip-browser-warning': 'true' },
});

// --- Types ---
export interface Gem {
  id: string;
  name: string;
  product_image_url: string;
  context_image_url: string;
  description?: string;
  carat_weight?: number | null;
  length_mm?: number | null;
  width_mm?: number | null;
  depth_mm?: number | null;
  created_at: string;
}

export interface SettingCategory {
  id: string;
  name: string;
  body_part: string;
  sort_order: number;
}

export interface Metal {
  id: string;
  name: string;
  sort_order: number;
}

export interface SettingStyle {
  id: string;
  category_id: string;
  name: string;
  sort_order: number;
}

export interface SettingOptions {
  categories: SettingCategory[];
  metals: Metal[];
  styles: SettingStyle[];
}

export interface ModelPhoto {
  id: string;
  name: string;
  body_part: string;
  image_url: string;
  created_at: string;
}

export interface PhotoValidationResult {
  is_valid: boolean;
  body_part_detected: string | null;
  feedback: string;
}

export interface GeneratePreviewResult {
  result_url: string;
  processing_time_ms: number;
}

// --- Gems ---
export const getGems = () => api.get<Gem[]>('/gems/').then(r => r.data);
export const getGem = (id: string) => api.get<Gem>(`/gems/${id}`).then(r => r.data);
export const createGem = (formData: FormData, adminKey: string) =>
  api.post<Gem>('/gems/', formData, {
    headers: { 'Content-Type': 'multipart/form-data', 'x-admin-key': adminKey },
  }).then(r => r.data);
export const deleteGem = (id: string, adminKey: string) =>
  api.delete(`/gems/${id}`, { headers: { 'x-admin-key': adminKey } }).then(r => r.data);

// --- Settings ---
export const getSettingOptions = () => api.get<SettingOptions>('/settings/options').then(r => r.data);
export const getStylesForCategory = (categoryId: string) =>
  api.get<SettingStyle[]>(`/settings/styles/${categoryId}`).then(r => r.data);

// --- Model Photos ---
export const getModelPhotos = (bodyPart?: string) => {
  const params = bodyPart ? { body_part: bodyPart } : {};
  return api.get<ModelPhoto[]>('/model-photos/', { params }).then(r => r.data);
};
export const createModelPhoto = (formData: FormData, adminKey: string) =>
  api.post<ModelPhoto>('/model-photos/', formData, {
    headers: { 'Content-Type': 'multipart/form-data', 'x-admin-key': adminKey },
  }).then(r => r.data);
export const deleteModelPhoto = (id: string, adminKey: string) =>
  api.delete(`/model-photos/${id}`, { headers: { 'x-admin-key': adminKey } }).then(r => r.data);

// --- Validation & Generation ---
export const validatePhoto = (formData: FormData) =>
  api.post<PhotoValidationResult>('/try-on/validate-photo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
export const generatePreview = (formData: FormData) =>
  api.post<GeneratePreviewResult>('/try-on/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);

export default api;
