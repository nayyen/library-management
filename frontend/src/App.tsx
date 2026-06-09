import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useSilentRefresh } from "@/hooks/useSilentRefresh";
import DashboardPage from "@/pages/DashboardPage";
import ForgotPasswordPage from "@/pages/ForgotPasswordPage";
import LoginPage from "@/pages/LoginPage";
import ResetPasswordPage from "@/pages/ResetPasswordPage";
import SignupPage from "@/pages/SignupPage";

function App() {
  const { isResolving } = useSilentRefresh();

  // Silent refresh on app load (D-05 / UI-SPEC "Interaction & State Contract")
  // MUST be invisible — render a blank canvas matching the page background,
  // NOT a spinner, until the refresh check resolves. A spinner here would
  // itself be the "jarring flash" the success criteria warns against.
  if (isResolving) {
    return <div className="min-h-svh bg-slate-50" aria-hidden="true" />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<DashboardPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
