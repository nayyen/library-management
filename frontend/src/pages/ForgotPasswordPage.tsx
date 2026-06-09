import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

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
import { useForgotPassword } from "@/hooks/useForgotPassword";
import { forgotPasswordSchema, type ForgotPasswordFormValues } from "@/lib/validation";

// UI-SPEC Copywriting Contract — generic confirmation shown after submit
// (D-09: never reveals whether the email is registered).
const CONFIRMATION_MESSAGE =
  "If that email is registered, you'll receive a reset link shortly.";
const GENERIC_SERVER_ERROR = "Something went wrong on our end. Please try again in a moment.";

export default function ForgotPasswordPage() {
  const forgotPassword = useForgotPassword();
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    mode: "onBlur",
    reValidateMode: "onBlur",
    defaultValues: { email: "" },
  });

  const onSubmit = (values: ForgotPasswordFormValues) => {
    setServerError(null);
    forgotPassword.mutate(values, {
      onSuccess: () => setSubmitted(true),
      onError: () => setServerError(GENERIC_SERVER_ERROR),
    });
  };

  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="gap-1">
          <h1 className="text-display text-foreground">Reset your password</h1>
          <CardTitle className="text-heading font-normal text-muted-foreground">
            Enter your email to receive a reset link
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {submitted ? (
            <Alert role="status">
              <AlertDescription className="text-body">{CONFIRMATION_MESSAGE}</AlertDescription>
            </Alert>
          ) : (
            <>
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
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-label">Email</FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            autoComplete="email"
                            placeholder="you@university.edu"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button type="submit" className="mt-2" disabled={forgotPassword.isPending}>
                    {forgotPassword.isPending ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : null}
                    Send reset link
                  </Button>
                </form>
              </Form>
            </>
          )}

          <p className="text-label text-muted-foreground">
            Remembered your password?{" "}
            <Link
              to="/login"
              className="text-blue-600 underline underline-offset-4"
            >
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
