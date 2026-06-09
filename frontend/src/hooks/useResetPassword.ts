import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import { useAuthStore, type User } from "@/stores/authStore";

interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

interface TokenResponse {
  access_token: string;
  user: User;
}

/**
 * POST /auth/reset-password → sets new password, revokes all sessions (D-07),
 * and auto-logs-in by populating the in-memory auth store (D-10).
 */
export function useResetPassword() {
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: async (payload: ResetPasswordPayload) => {
      const { data } = await apiClient.post<TokenResponse>("/auth/reset-password", payload);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
    },
  });
}
