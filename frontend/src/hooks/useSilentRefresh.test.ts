import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/api/client";
import { useAuthStore } from "@/stores/authStore";

import { useSilentRefresh } from "./useSilentRefresh";

const mockUser = { id: 1, email: "student@example.com", role: "student" as const };

describe("useSilentRefresh", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, user: null });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("populates the store on a successful refresh and resolves to isResolving=false", async () => {
    vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { access_token: "fresh-token", user: mockUser },
    } as never);

    const { result } = renderHook(() => useSilentRefresh());

    expect(result.current.isResolving).toBe(true);

    await waitFor(() => expect(result.current.isResolving).toBe(false));

    expect(useAuthStore.getState().accessToken).toBe("fresh-token");
    expect(useAuthStore.getState().user).toEqual(mockUser);
  });

  it("clears the store on a failed refresh and still resolves", async () => {
    useAuthStore.setState({ accessToken: "stale-token", user: mockUser });
    vi.spyOn(apiClient, "post").mockRejectedValueOnce(new Error("401"));

    const { result } = renderHook(() => useSilentRefresh());

    await waitFor(() => expect(result.current.isResolving).toBe(false));

    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it("never reads the access token from localStorage (D-05 — memory only)", async () => {
    const getItemSpy = vi.spyOn(Storage.prototype, "getItem");
    vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: { access_token: "fresh-token", user: mockUser },
    } as never);

    const { result } = renderHook(() => useSilentRefresh());
    await waitFor(() => expect(result.current.isResolving).toBe(false));

    // The hook (and the store it relies on) must never consult localStorage
    // for the access token — it lives in Zustand memory only (D-05).
    expect(getItemSpy).not.toHaveBeenCalledWith(expect.stringMatching(/token/i));

    // Double-check the store itself is the sole source of truth.
    act(() => {
      expect(useAuthStore.getState().accessToken).toBe("fresh-token");
    });
  });
});
