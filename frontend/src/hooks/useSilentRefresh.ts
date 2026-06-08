import { useEffect, useState } from "react";

import { apiClient } from "@/api/client";
import { useAuthStore, type User } from "@/stores/authStore";

interface TokenResponse {
  access_token: string;
  user: User;
}

/**
 * On-mount silent refresh — restores the session from the httpOnly refresh
 * cookie without ever touching localStorage (D-05). Exposes `isResolving`
 * so the app can render a blank canvas (NOT a spinner — UI-SPEC "Silent
 * refresh on app load") until the check resolves, avoiding any flash of
 * the login screen on a hard reload (AUTH-02).
 */
export function useSilentRefresh() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const [isResolving, setIsResolving] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function resolve() {
      try {
        const { data } = await apiClient.post<TokenResponse>("/auth/refresh");
        if (!cancelled) {
          setAuth(data.access_token, data.user);
        }
      } catch {
        if (!cancelled) {
          clearAuth();
        }
      } finally {
        if (!cancelled) {
          setIsResolving(false);
        }
      }
    }

    void resolve();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { isResolving };
}
