import axios from "axios";

import { useAuthStore } from "@/stores/authStore";

/**
 * Shared axios instance every API call rides on (the canonical analog for
 * Phases 2-6 — RESEARCH Pattern 7, copied verbatim).
 *
 * `withCredentials: true` is REQUIRED — it makes the browser send the
 * httpOnly refresh cookie cross-port (localhost:5173 -> localhost:8000).
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token!)));
  failedQueue = [];
};

// Request interceptor: attach the in-memory access token (never read from
// localStorage — D-05).
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: on a 401, refresh exactly once even under a burst of
// concurrent 401s (isRefreshing + failedQueue guard — T-01-REFRESH-RACE),
// then retry the original request(s). On refresh failure, clear the store
// and bounce to /login.
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // queue this request until the in-flight refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { data } = await apiClient.post("/auth/refresh"); // cookie sent automatically
        useAuthStore.getState().setAccessToken(data.access_token);
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().clearAuth();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
