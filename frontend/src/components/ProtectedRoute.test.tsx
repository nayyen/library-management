import { render, screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "@/stores/authStore";

import { ProtectedRoute } from "./ProtectedRoute";

const studentUser = { id: 1, email: "student@example.com", role: "student" as const };
const librarianUser = { id: 2, email: "librarian@example.com", role: "librarian" as const };

function renderAt(path: string, requiredRole?: "student" | "librarian") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/" element={<div>Home page</div>} />
        <Route element={<ProtectedRoute requiredRole={requiredRole} />}>
          <Route path={path} element={<div>Protected content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, user: null });
  });

  afterEach(() => {
    useAuthStore.setState({ accessToken: null, user: null });
  });

  it("redirects to /login when there is no authenticated user", () => {
    renderAt("/dashboard");

    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("redirects to / when the user's role does not match requiredRole", () => {
    useAuthStore.setState({ accessToken: "token", user: studentUser });

    renderAt("/librarian-only", "librarian");

    expect(screen.getByText("Home page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders the nested route when authenticated and role matches (or no role required)", () => {
    useAuthStore.setState({ accessToken: "token", user: librarianUser });

    renderAt("/librarian-only", "librarian");

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
