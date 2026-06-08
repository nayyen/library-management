import { QueryClient } from "@tanstack/react-query";

/**
 * Shared TanStack Query client. Server-state (catalog, loans, auth/session
 * data) lives here — NOT in Zustand (CLAUDE.md "Stack Patterns by Variant":
 * Zustand is for ephemeral UI state only).
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
