import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import { useAuthStore, type User } from "@/stores/authStore";

interface SignupPayload {
  email: string;
  password: string;
  role: "student" | "librarian";
  librarian_code?: string;
}

interface TokenResponse {
  access_token: string;
  user: User;
}

/**
 * POST /auth/signup -> {access_token, user}; auto-logs the user in on
 * success (AUTH-01 "auto-login on success") by populating the auth store.
 */
export function useSignup() {
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: async (payload: SignupPayload) => {
      const { data } = await apiClient.post<TokenResponse>("/auth/signup", payload);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
    },
  });
}
