import { create } from "zustand";

/**
 * Authenticated user shape — mirrors backend's UserRead schema
 * (id, email, role). Never includes hashed_password (D-05 / backend never
 * sends it either).
 */
export interface User {
  id: number;
  email: string;
  role: "student" | "librarian";
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  setAccessToken: (token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAuth: (accessToken, user) => set({ accessToken, user }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clearAuth: () => set({ accessToken: null, user: null }),
}));
// Deliberately NOT using zustand's `persist` middleware — that would write to
// localStorage, which is exactly what D-05 forbids for the access token.
// The access token lives ONLY in this in-memory store; the refresh token
// lives ONLY in an httpOnly cookie the browser manages — JS never touches it.
