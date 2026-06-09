import { z } from "zod";

/**
 * loginSchema — email + non-empty password. Validation messages are
 * intentionally generic; the server is the source of truth for "is this a
 * valid account" (D-09 enumeration-safety extends to client-side copy too —
 * we never claim to know whether the email format implies an account exists).
 */
export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

/**
 * signupSchema — email + password + self-selected role (D-01) + an
 * invite code that is REQUIRED only when role === "librarian" (D-01/D-02),
 * enforced via `.refine` so the librarian branch surfaces a field-level error.
 */
export const signupSchema = z
  .object({
    email: z.string().email("Enter a valid email address."),
    password: z.string().min(8, "Password must be at least 8 characters."),
    role: z.enum(["student", "librarian"]),
    librarian_code: z.string().optional(),
  })
  .refine(
    (data) => data.role !== "librarian" || (data.librarian_code?.trim().length ?? 0) > 0,
    {
      message: "Enter your librarian invite code.",
      path: ["librarian_code"],
    },
  );

export type SignupFormValues = z.infer<typeof signupSchema>;

/**
 * forgotPasswordSchema — email only.
 */
export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address."),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

/**
 * resetPasswordSchema — new password with minimum length requirement.
 */
export const resetPasswordSchema = z.object({
  new_password: z.string().min(8, "Password must be at least 8 characters."),
});

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
