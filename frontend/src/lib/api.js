import axios from 'axios';
import { getToken, clearToken } from './auth';

const api = axios.create({
  baseURL: '/api',
  // Serialize array params as ?kategori=A&kategori=B (not ?kategori[]=A&kategori[]=B)
  paramsSerializer: {
    indexes: null,
  },
});

// Attach Bearer token to every request
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Handle 401 responses — clear token and redirect
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearToken();
      window.location.href = '/login?session_expired=1';
    }
    return Promise.reject(error);
  },
);

export default api;
