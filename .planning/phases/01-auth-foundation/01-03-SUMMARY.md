---
phase: 01-auth-foundation
plan: 03
subsystem: frontend-auth
tags: [react, zustand, axios, react-query, silent-refresh, protected-route, vite]

# Dependency graph
requires: [01-01, 01-02]
provides:
  - Zustand authStore (accessToken + user; NO persist middleware — D-05)
  - axios apiClient with withCredentials + isRefreshing/failedQueue 401-interceptor
  - useLogin / useSignup / useLogout / useSilentRefresh hooks (TanStack Query mutations)
  - ProtectedRoute (unauthenticated → /login; role mismatch → /; match → Outlet)
  - LoginPage + SignupPage (react-hook-form + zod; exact UI-SPEC copy)
  - DashboardPage stub (role-differentiated; librarian accent element)
  - App routing wired (/login, /signup, / protected); blank-canvas StrictMode guard
  - useSilentRefresh.test.ts + ProtectedRoute.test.tsx (vitest + RTL)
affects: [01-04]

# Tech tracking
tech-stack:
  added:
    - "Zustand 5.x create<AuthState> — no persist, in-memory access token only (D-05)"
    - "axios 1.x withCredentials:true; isRefreshing + failedQueue prevents concurrent-401 refresh storms"
    - "useSilentRefresh module-level singleton (inflightRefresh) to survive React 18 StrictMode double-invoke"
    - "react-hook-form 7.x + zod 4.x + @hookform/resolvers/zod for Login/Signup validation"
    - "ProtectedRoute copies RESEARCH Pattern role-gated route verbatim; server 403 is authoritative"
  patterns:
    - "Module-level inflightRefresh singleton in useSilentRefresh: fires exactly one /auth/refresh per page load regardless of StrictMode effect double-fire"
    - "401 interceptor guards against self-triggering on /auth/refresh (isRefreshEndpoint check prevents infinite loop)"
    - "Blank canvas (bg-slate-50, no spinner) while isResolving=true — invisible silent refresh per UI-SPEC"
    - "values_callable=lambda x: [e.value for e in x] on SQLAlchemy UserRole Enum keeps DB ↔ Python parity"
    - "Alembic 0001: idempotent DO $$ BEGIN...EXCEPTION block + postgresql.ENUM(create_type=False) survives repeated upgrade/downgrade cycles"

key-files:
  created:
    - frontend/src/stores/authStore.ts
    - frontend/src/api/client.ts
    - frontend/src/hooks/useLogin.ts
    - frontend/src/hooks/useSignup.ts
    - frontend/src/hooks/useSilentRefresh.ts
    - frontend/src/hooks/useLogout.ts
    - frontend/src/components/ProtectedRoute.tsx
    - frontend/src/pages/LoginPage.tsx
    - frontend/src/pages/SignupPage.tsx
    - frontend/src/pages/DashboardPage.tsx
    - frontend/src/lib/validation.ts
    - frontend/src/hooks/useSilentRefresh.test.ts
    - frontend/src/components/ProtectedRoute.test.tsx
  modified:
    - frontend/src/App.tsx
    - backend/app/routers/auth.py (InvalidLibrarianCode → 422)
    - backend/app/models/user.py (values_callable enum fix)
    - backend/alembic/versions/0001_create_users_and_refresh_tokens.py (idempotent enum)
    - backend/tests/test_auth.py (email domains + 422 assertion)

key-decisions:
  - "Module-level inflightRefresh singleton instead of useRef: React 18 StrictMode double-invokes effects in dev, causing two concurrent /auth/refresh calls with the same cookie. The second call arrives after the first has already rotated the token, trips reuse-detection, revokes all sessions, and lands the user on /login on every hard refresh. A module-level variable (not a React ref) persists across the mount/unmount/remount cycle that StrictMode exercises."
  - "InvalidLibrarianCode changed from 400 → 422: Pydantic validation errors return 422; making this exception consistent avoids a special-case in test assertions and keeps the API's error taxonomy uniform."
  - "Alembic enum creation switched to raw DO $$ BEGIN...EXCEPTION block: the original sa.Enum.create() call fails if the Postgres type already exists (e.g., second `alembic upgrade head` after a partial teardown). The DO block with EXCEPTION WHEN duplicate_object is idempotent."

requirements-completed: [AUTH-01, AUTH-02, AUTH-04]
checkpoint: approved

# Metrics
duration: 90min (tasks) + post-checkpoint fixes
completed: 2026-06-09
---

# Phase 1 Plan 3: Frontend Auth Slice (Walking Skeleton) Summary

**Completed the end-to-end Walking Skeleton: signup → login → silent refresh on hard reload → role-gated dashboard stub, with server-side 403 for wrong-role access. The frontend auth backbone (Zustand store, axios interceptor with refresh-queue, ProtectedRoute) is the canonical client-side analog for all later phases. Checkpoint approved after Docker end-to-end verification.**

## Performance

- **Duration:** ~90 min (implementation) + post-checkpoint fix pass
- **Tasks:** 3/3 completed (including blocking human-verify checkpoint)
- **Files created:** 13 (store, api client, 4 hooks, 2 tests, 2 pages + signup, dashboard, validation)
- **Files modified:** 5 (App.tsx, auth router, user model, 0001 migration, test_auth.py)

## Accomplishments

- `authStore.ts` uses `create<AuthState>` with `accessToken`, `user`, `setAuth`, `setAccessToken`, `clearAuth`; `persist` is deliberately absent — nothing touches localStorage (D-05 enforced; useSilentRefresh test asserts `localStorage.getItem` is never called)
- `api/client.ts` implements the full RESEARCH Pattern 7 refresh-queue: `withCredentials:true`, `isRefreshing`/`failedQueue`/`processQueue`, single `/auth/refresh` call per 401 burst, retry queue drained on success, `clearAuth()` + redirect on failure; `!isRefreshEndpoint` guard prevents the interceptor from triggering on the refresh endpoint itself
- `useSilentRefresh` fires on mount, restores session from httpOnly cookie, returns `isResolving`; module-level `inflightRefresh` singleton ensures one request per page load under React 18 StrictMode
- `ProtectedRoute` redirects unauthenticated → `/login` and role-mismatch → `/`; the "UX convenience only" comment is preserved — server-side `require_role` is the real enforcement
- `LoginPage`/`SignupPage` built with shadcn card/form/input/label/button/alert; exact UI-SPEC Copywriting Contract strings; Signup has radio segmented control (not `<select>`) with progressive disclosure of librarian-code field; password show/hide with 44×44 hit target
- `DashboardPage` stub: "Welcome, {email.split('@')[0]}", role subtext, and a visibly distinct accent-colored "Librarian tools" badge visible only to librarians (AUTH-04 UI surface)
- `App.tsx` gates root render on `useSilentRefresh.isResolving` with a blank `bg-slate-50` canvas — no spinner, no flash per UI-SPEC
- Both frontend tests pass (`useSilentRefresh.test.ts`: success/failure paths + localStorage assertion; `ProtectedRoute.test.tsx`: all three branches)

## Task Commits

1. **Task 1: Zustand store + axios client + auth hooks** — `95738a9` (feat)
2. **Task 2: ProtectedRoute + pages + routing** — `eff5691` (feat)
3. **Post-checkpoint fixes** — `ad0d45d` (fix)

## Post-Checkpoint Fixes (ad0d45d)

Four issues surfaced during Docker end-to-end verification:

| Fix | Root Cause |
|-----|------------|
| StrictMode double-refresh | React 18 StrictMode double-invokes effects in dev; `useRef` doesn't survive the remount cycle; module-level singleton does |
| Interceptor infinite loop | 401 interceptor fired on `/auth/refresh` itself, causing an infinite self-call; `!isRefreshEndpoint` guard added |
| Alembic "type already exists" | `sa.Enum.create()` is not idempotent; raw DO block with `EXCEPTION WHEN duplicate_object` is |
| `UserRole` DB round-trip | SQLAlchemy mapped enum names ('STUDENT') not values ('student'); `values_callable` fix aligns Python ↔ Postgres |

## Decisions Made

- **Module-level inflightRefresh over useRef:** See key-decisions above — this is the only pattern that survives StrictMode's mount/unmount/remount cycle.
- **422 for InvalidLibrarianCode:** Pydantic returns 422 for all validation errors; keeping this exception at 422 makes the error taxonomy uniform rather than having a special 400 carve-out.
- **Idempotent Alembic enum:** DO block with EXCEPTION WHEN duplicate_object is the Postgres-idiomatic pattern for "create if not exists" on types; avoids a separate `checkfirst` round-trip.

## Known Stubs

- `DashboardPage` is a stub — real dashboard content (catalog search, loan list, librarian queue) is built in Phases 2-5. The role-differentiation element proves AUTH-04 UI surface now.
- AUTH-03 (password reset) is untouched; `test_forgot_password_*` and `test_reset_*` remain `xfail` — covered by Plan 04.

## Self-Check: PASSED

- All 13 created + 5 modified files verified present on disk
- Task commits `95738a9`, `eff5691`, `ad0d45d` verified in git log
- Checkpoint approved after Docker end-to-end verification (all 6 steps passing)
- AUTH-01, AUTH-02, AUTH-04 are user-visible and clickable; server-side 403 confirmed via curl
