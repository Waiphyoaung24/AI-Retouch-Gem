import axios from 'axios';

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
     'ngrok-skip-browser-warning': 'true'
    }
});

export interface Product {
  id: string;
  name: string;
  image_url: string;
  created_at: string;
}

export interface HandModel {
  id: string;
  name: string;
  image_url: string;
}

export interface TryOnResult {
  result_url: string;
  cached: boolean;
  processing_time_ms: number;
}

export const getProducts = async () => {
  const response = await api.get<Product[]>('/products/');
  return response.data;
};

export const getHandModels = async () => {
  const response = await api.get<HandModel[]>('/hand-models/');
  return response.data;
};

export const uploadProduct = async (formData: FormData, adminKey: string) => {
  const response = await api.post<Product>('/products/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'x-admin-key': adminKey,
    },
  });
  return response.data;
};

export const uploadHandModel = async (formData: FormData, adminKey: string) => {
  const response = await api.post<HandModel>('/hand-models/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'x-admin-key': adminKey,
    },
  });
  return response.data;
};

export const deleteHandModel = async (id: string, adminKey: string) => {
  const response = await api.delete(`/hand-models/${id}`, {
    headers: {
      'x-admin-key': adminKey,
    },
  });
  return response.data;
};

export const deleteProduct = async (id: string, adminKey: string) => {
  const response = await api.delete(`/products/${id}`, {
    headers: {
      'x-admin-key': adminKey,
    },
  });
  return response.data;
};

export const tryOn = async (formData: FormData) => {
  const response = await api.post<TryOnResult>('/try-on/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export default api;
