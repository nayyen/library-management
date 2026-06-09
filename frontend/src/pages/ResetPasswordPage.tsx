import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

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

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const resetPassword = useResetPassword();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const token = searchParams.get("token");

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    mode: "onBlur",
    reValidateMode: "onBlur",
    defaultValues: { new_password: "" },
  });

  // If no token in URL, show invalid link state immediately.
  if (!token) {
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

  const onSubmit = (values: ResetPasswordFormValues) => {
    setErrorMessage(null);
    resetPassword.mutate(
      { token, new_password: values.new_password },
      {
        onSuccess: () => navigate("/", { replace: true }),
        onError: (err: unknown) => {
          const status = (err as { response?: { status?: number } })?.response?.status;
          setErrorMessage(status === 400 ? TOKEN_INVALID_MESSAGE : GENERIC_SERVER_ERROR);
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

          {errorMessage ? (
            <Alert variant="destructive" role="alert">
              <AlertDescription className="text-body">{errorMessage}</AlertDescription>
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
