import { Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/useLogout";
import { useAuthStore } from "@/stores/authStore";

const STUDENT_SUBTEXT = "Search the catalog to find your next book.";
const LIBRARIAN_SUBTEXT = "Manage requests and the catalog from here.";

/**
 * The protected dashboard stub — exists primarily to PROVE ProtectedRoute +
 * require_role server-side enforcement (AUTH-04 success criterion #4), not
 * to deliver real dashboard functionality. Librarians see a visibly distinct
 * "Librarian tools" accent badge a student does not — screenshot-provable
 * role differentiation.
 */
export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  if (!user) return null;

  const firstSegment = user.email.split("@")[0];
  const isLibrarian = user.role === "librarian";

  return (
    <main className="flex min-h-svh flex-col items-center bg-background px-4 py-16">
      <div className="flex w-full max-w-2xl flex-col gap-6">
        <div className="flex items-center justify-between">
          <h1 className="text-display text-foreground">Welcome, {firstSegment}</h1>
          <Button variant="outline" onClick={() => logout.mutate()} disabled={logout.isPending}>
            {logout.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Log out
          </Button>
        </div>

        <p className="text-body text-muted-foreground">
          {isLibrarian ? LIBRARIAN_SUBTEXT : STUDENT_SUBTEXT}
        </p>

        {isLibrarian ? (
          <div
            data-testid="librarian-tools-badge"
            className="flex w-fit items-center gap-2 rounded-md border border-blue-600 bg-blue-600/10 px-4 py-2 text-label text-blue-600"
          >
            <Sparkles className="size-4" />
            Librarian tools
          </div>
        ) : null}
      </div>
    </main>
  );
}
