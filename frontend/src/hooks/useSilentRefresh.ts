import { useEffect, useState } from "react";

import { apiClient } from "@/api/client";
import { useAuthStore, type User } from "@/stores/authStore";

interface TokenResponse {
  access_token: string;
  user: User;
}

// Module-level singleton: only one /auth/refresh request is ever dispatched
// per page load, even under React 18 StrictMode which double-invokes effects
// in development. Without this guard, StrictMode fires two parallel requests
// with the same refresh cookie; the second arrives after the first has already
// rotated the token, trips reuse-detection, revokes all sessions, and lands
// the user on /login on every hard refresh.
let inflightRefresh: Promise<void> | null = null;

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
    if (inflightRefresh === null) {
      // First invocation (or first after a page reload): fire the request.
      inflightRefresh = (async () => {
        try {
          const { data } = await apiClient.post<TokenResponse>("/auth/refresh");
          setAuth(data.access_token, data.user);
        } catch {
          clearAuth();
        }
      })();
    }

    // Both this mount and any StrictMode re-mount attach their own
    // setIsResolving to the shared promise. Whichever instance is live
    // when the promise settles will receive the state update; the call
    // on the unmounted instance is a no-op.
    void inflightRefresh.finally(() => setIsResolving(false));
  }, []);

  return { isResolving };
}
