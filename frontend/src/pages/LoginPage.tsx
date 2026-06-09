import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

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
import { useLogin } from "@/hooks/useLogin";
import { loginSchema, type LoginFormValues } from "@/lib/validation";

const GENERIC_LOGIN_ERROR = "Invalid email or password. Check your details and try again.";
const GENERIC_SERVER_ERROR = "Something went wrong on our end. Please try again in a moment.";

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
    reValidateMode: "onBlur",
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = (values: LoginFormValues) => {
    setErrorMessage(null);
    login.mutate(values, {
      onSuccess: () => navigate("/", { replace: true }),
      onError: (err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        setErrorMessage(status === 401 ? GENERIC_LOGIN_ERROR : GENERIC_SERVER_ERROR);
      },
    });
  };

  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="gap-1">
          <h1 className="text-display text-foreground">Log in</h1>
          <CardTitle className="text-heading font-normal text-muted-foreground">
            Welcome back — sign in to continue
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {errorMessage ? (
            <Alert variant="destructive" role="alert">
              <AlertDescription className="text-body">{errorMessage}</AlertDescription>
            </Alert>
          ) : null}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-label">Email</FormLabel>
                    <FormControl>
                      <Input type="email" autoComplete="email" placeholder="you@university.edu" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-label">Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          autoComplete="current-password"
                          className="pr-11"
                          {...field}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword((v) => !v)}
                          aria-label={showPassword ? "Hide password" : "Show password"}
                          className="absolute inset-y-0 right-0 flex h-11 w-11 items-center justify-center text-muted-foreground hover:text-foreground"
                        >
                          {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" className="mt-2" disabled={login.isPending}>
                {login.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
                Log in
              </Button>
            </form>
          </Form>

          <div className="flex flex-col gap-2">
            <p className="text-label text-muted-foreground">
              Don&apos;t have an account?{" "}
              <Link to="/signup" className="text-blue-600 underline underline-offset-4">
                Sign up
              </Link>
            </p>
            <p className="text-label text-muted-foreground">
              <Link to="/forgot-password" className="text-blue-600 underline underline-offset-4">
                Forgot password?
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
