import { Navigate, Outlet } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

interface ProtectedRouteProps {
  requiredRole?: "student" | "librarian";
}

/**
 * Role-gated route wrapper (RESEARCH "Role-gated route component", copied
 * verbatim). Redirects unauthenticated users to /login, redirects role
 * mismatches to / (home), and otherwise renders the nested route via Outlet.
 *
 * REMINDER: this is UX convenience only. The *enforcement* is the backend's
 * require_role() dependency (Pattern 1) returning 403 — this component merely
 * avoids showing a librarian-only page to a student who'd get a 403 anyway
 * (T-01-UIGATE — never trust the frontend's role claim).
 */
export function ProtectedRoute({ requiredRole }: ProtectedRouteProps) {
  const { user, accessToken } = useAuthStore();

  if (!accessToken || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
