import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import { useAuthStore, type User } from "@/stores/authStore";

interface LoginPayload {
  email: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  user: User;
}

/**
 * POST /auth/login -> {access_token, user}; populates the in-memory auth
 * store on success (D-05 — never touches localStorage).
 */
export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: async (payload: LoginPayload) => {
      const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
    },
  });
}
