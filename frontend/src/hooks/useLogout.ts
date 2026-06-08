import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import { useAuthStore } from "@/stores/authStore";

/**
 * POST /auth/logout -> revokes only the current session's refresh token
 * (D-06 — other devices stay logged in); clears the in-memory store
 * regardless of the server response so the UI always reflects "logged out".
 */
export function useLogout() {
  const clearAuth = useAuthStore((s) => s.clearAuth);

  return useMutation({
    mutationFn: async () => {
      await apiClient.post("/auth/logout");
    },
    onSettled: () => {
      clearAuth();
    },
  });
}
