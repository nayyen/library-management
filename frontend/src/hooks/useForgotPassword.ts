import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/api/client";

interface ForgotPasswordPayload {
  email: string;
}

interface ForgotPasswordResponse {
  message: string;
}

/**
 * POST /auth/forgot-password → generic confirmation message.
 * Never reveals whether the email is registered (D-09 enumeration-safety).
 * The server always returns the same message regardless of email validity.
 */
export function useForgotPassword() {
  return useMutation({
    mutationFn: async (payload: ForgotPasswordPayload) => {
      const { data } = await apiClient.post<ForgotPasswordResponse>(
        "/auth/forgot-password",
        payload,
      );
      return data;
    },
  });
}
