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
import { useSignup } from "@/hooks/useSignup";
import { signupSchema, type SignupFormValues } from "@/lib/validation";
import { cn } from "@/lib/utils";

const INVALID_LIBRARIAN_CODE_ERROR =
  "Invalid librarian code — check with your library administrator, or sign up as a student.";
const DUPLICATE_EMAIL_ERROR =
  "An account with this email already exists. Log in instead, or use a different email.";
const GENERIC_SERVER_ERROR = "Something went wrong on our end. Please try again in a moment.";

export default function SignupPage() {
  const navigate = useNavigate();
  const signup = useSignup();
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    mode: "onBlur",
    reValidateMode: "onBlur",
    defaultValues: { email: "", password: "", role: "student", librarian_code: "" },
  });

  const role = form.watch("role");

  const onSubmit = (values: SignupFormValues) => {
    setErrorMessage(null);
    const payload =
      values.role === "librarian"
        ? values
        : { email: values.email, password: values.password, role: values.role };

    signup.mutate(payload, {
      onSuccess: () => navigate("/", { replace: true }),
      onError: (err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 422 || status === 403) {
          setErrorMessage(INVALID_LIBRARIAN_CODE_ERROR);
        } else if (status === 409) {
          setErrorMessage(DUPLICATE_EMAIL_ERROR);
        } else {
          setErrorMessage(GENERIC_SERVER_ERROR);
        }
      },
    });
  };

  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="gap-1">
          <h1 className="text-display text-foreground">Sign up</h1>
          <CardTitle className="text-heading font-normal text-muted-foreground">
            Create your account
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
                          {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Role segmented control — radio group, NOT a dropdown (UI-SPEC:
                  only 2 options, faster to scan/select). Selecting "Librarian"
                  reveals the invite-code field inline (progressive disclosure). */}
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-label">I am a...</FormLabel>
                    <FormControl>
                      <div role="radiogroup" aria-label="Account type" className="grid grid-cols-2 gap-2">
                        {(["student", "librarian"] as const).map((option) => (
                          <label
                            key={option}
                            className={cn(
                              "flex cursor-pointer items-center justify-center rounded-md border px-4 py-2 text-label capitalize transition-colors",
                              field.value === option
                                ? "border-blue-600 bg-blue-600/10 text-blue-600"
                                : "border-input text-foreground hover:bg-accent/50",
                            )}
                          >
                            <input
                              type="radio"
                              name="role"
                              value={option}
                              checked={field.value === option}
                              onChange={() => field.onChange(option)}
                              className="sr-only"
                            />
                            {option}
                          </label>
                        ))}
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {role === "librarian" ? (
                <FormField
                  control={form.control}
                  name="librarian_code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-label">Librarian invite code</FormLabel>
                      <FormControl>
                        <Input type="text" autoComplete="off" placeholder="Enter your invite code" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ) : null}

              <Button type="submit" className="mt-2" disabled={signup.isPending}>
                {signup.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
                Sign up
              </Button>
            </form>
          </Form>

          <p className="text-label text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-600 underline underline-offset-4">
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
