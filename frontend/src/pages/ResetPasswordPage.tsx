import { useState } from "react";

import { useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { apiClient } from "@/api/client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useResetPassword } from "@/hooks/useResetPassword";
import { resetPasswordSchema, type ResetPasswordFormValues } from "@/lib/validation";

// UI-SPEC Copywriting Contract strings.
const TOKEN_INVALID_MESSAGE =
  "This reset link is no longer valid. It may have expired or already been used — request a new one.";
const GENERIC_SERVER_ERROR = "Something went wrong on our end. Please try again in a moment.";

// UI-SPEC Destructive confirmation — shown inline on the form before submit
// (no separate confirm dialog; notice sets expectations at the right moment).
const SESSION_REVOCATION_NOTICE =
  "Resetting your password will sign you out of all devices, including this one once you're redirected — for your security.";

// Reusable terminal "link is dead" view — rendered for both missing and
// rejected (used/expired) tokens so both paths look identical to the user.
function InvalidTokenView() {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="gap-1">
          <h1 className="text-display text-foreground">Reset your password</h1>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <Alert variant="destructive" role="alert">
            <AlertDescription className="text-body">{TOKEN_INVALID_MESSAGE}</AlertDescription>
          </Alert>
          <p className="text-label text-muted-foreground">
            <Link to="/forgot-password" className="text-blue-600 underline underline-offset-4">
              Request a new reset link
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const resetPassword = useResetPassword();
  const [showPassword, setShowPassword] = useState(false);
  // Tracks token invalidity detected after form submission (race: was valid on
  // load but used/expired by the time the user submitted).
  const [submissionTokenInvalid, setSubmissionTokenInvalid] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const token = searchParams.get("token");

  // Validate the token on page load (read-only preflight — does NOT consume it).
  // This surfaces the "no longer valid" copy immediately when clicking a used or
  // expired link, instead of only after form submission (D-08).
  const {
    isFetching: isValidating,
    isError: loadTokenInvalid,
  } = useQuery({
    queryKey: ["reset-token-validate", token],
    queryFn: async () => {
      const { data } = await apiClient.get<{ valid: boolean }>(
        `/auth/validate-reset-token?token=${encodeURIComponent(token!)}`,
      );
      return data;
    },
    enabled: !!token,
    retry: false,
    staleTime: Infinity,
  });

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    mode: "onBlur",
    reValidateMode: "onBlur",
    defaultValues: { new_password: "" },
  });

  // Terminal states: no token in URL, token invalid on load, or token
  // invalidated between load and submission (edge case: concurrent use).
  if (!token || loadTokenInvalid || submissionTokenInvalid) {
    return <InvalidTokenView />;
  }

  // Brief loading state while the preflight check runs (~1 round trip).
  if (isValidating) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
        <Card className="w-full max-w-md">
          <CardHeader className="gap-1">
            <h1 className="text-display text-foreground">Reset your password</h1>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              <span className="text-label">Verifying reset link…</span>
            </div>
          </CardContent>
        </Card>
      </main>
    );
  }

  const onSubmit = (values: ResetPasswordFormValues) => {
    setServerError(null);
    resetPassword.mutate(
      { token, new_password: values.new_password },
      {
        onSuccess: () => navigate("/", { replace: true }),
        onError: (err: unknown) => {
          const status = (err as { response?: { status?: number } })?.response?.status;
          if (status === 400) {
            setSubmissionTokenInvalid(true);
          } else {
            setServerError(GENERIC_SERVER_ERROR);
          }
        },
      },
    );
  };

  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="gap-1">
          <h1 className="text-display text-foreground">Reset your password</h1>
          <CardTitle className="text-heading font-normal text-muted-foreground">
            Set a new password for your account
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {/* D-07 informational notice — shown inline before submit, not a confirm dialog */}
          <Alert role="note">
            <AlertDescription className="text-body text-destructive">
              {SESSION_REVOCATION_NOTICE}
            </AlertDescription>
          </Alert>

          {serverError ? (
            <Alert variant="destructive" role="alert">
              <AlertDescription className="text-body">{serverError}</AlertDescription>
            </Alert>
          ) : null}

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="flex flex-col gap-4"
              noValidate
            >
              <FormField
                control={form.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-label">New password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          autoComplete="new-password"
                          className="pr-11"
                          {...field}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword((v) => !v)}
                          aria-label={showPassword ? "Hide password" : "Show password"}
                          className="absolute inset-y-0 right-0 flex h-11 w-11 items-center justify-center text-muted-foreground hover:text-foreground"
                        >
                          {showPassword ? (
                            <EyeOff className="size-4" />
                          ) : (
                            <Eye className="size-4" />
                          )}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" className="mt-2" disabled={resetPassword.isPending}>
                {resetPassword.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
                Reset password
              </Button>
            </form>
          </Form>

          <p className="text-label text-muted-foreground">
            <Link to="/forgot-password" className="text-blue-600 underline underline-offset-4">
              Request a new reset link
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
