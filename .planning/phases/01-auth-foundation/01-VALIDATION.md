---
phase: 01
slug: auth-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-08
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (backend); vitest 4.x + @testing-library/react 16.x (frontend) — none installed yet (greenfield) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_auth.py -x -q` (backend); `npx vitest run src/components/ProtectedRoute.test.tsx` (frontend) |
| **Full suite command** | `pytest -q` (backend); `npx vitest run` (frontend) |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_auth.py -x -q` (backend changes) or `npx vitest run` for touched frontend files
- **After every plan wave:** Run `pytest -q` (full backend suite) + `npx vitest run` (full frontend suite)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-XX | 01 | 0 | — | — | Test infrastructure scaffolded (conftest, fixtures, framework install) | setup | `pytest --collect-only -q` | ❌ W0 | ⬜ pending |
| 01-XX-XX | TBD | TBD | AUTH-01 | T-01-01 | Signup creates user with correct role; librarian signup requires valid `LIBRARIAN_SIGNUP_CODE`; wrong/missing code rejected with clear error, no silent fallback | integration | `pytest tests/test_auth.py::test_signup_student tests/test_auth.py::test_signup_librarian_valid_code tests/test_auth.py::test_signup_librarian_invalid_code -x -q` | ❌ W0 | ⬜ pending |
| 01-XX-XX | TBD | TBD | AUTH-02 | T-01-02 | Login issues access+refresh tokens; refresh rotates on use; silent refresh on page load restores session; access token never persisted to localStorage | integration (backend) + component (frontend) | `pytest tests/test_auth.py::test_login_issues_tokens tests/test_auth.py::test_refresh_rotates_token -x -q` + `npx vitest run src/hooks/useSilentRefresh.test.ts` | ❌ W0 | ⬜ pending |
| 01-XX-XX | TBD | TBD | AUTH-03 | T-01-03 | Forgot-password returns generic enumeration-safe response regardless of email validity; reset link is single-use with 1-hour TTL; completing reset revokes ALL sessions and auto-logs-in | integration | `pytest tests/test_auth.py::test_forgot_password_enumeration_safe tests/test_auth.py::test_reset_password_single_use tests/test_auth.py::test_reset_revokes_all_sessions -x -q` | ❌ W0 | ⬜ pending |
| 01-XX-XX | TBD | TBD | AUTH-04 | T-01-04 | `require_role("librarian")` / `require_role("student")` returns 403 for wrong-role tokens on at least one real protected route, regardless of UI state | integration | `pytest tests/test_auth.py::test_require_role_rejects_wrong_role -x -q` | ❌ W0 | ⬜ pending |

*Task IDs and plan/wave assignments are TBD — the planner fills these in once plans are written; this map records the requirement→test contract that every plan covering AUTH-01..04 MUST satisfy.*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — async test client fixture (`httpx.AsyncClient` against the FastAPI app), test-database fixture (separate Postgres schema or transactional rollback per test), factory helpers for creating test users (student/librarian)
- [ ] `backend/tests/test_auth.py` — stub test functions for AUTH-01 through AUTH-04 (see map above)
- [ ] `backend/pyproject.toml [tool.pytest.ini_options]` — `asyncio_mode = "auto"` for pytest-asyncio
- [ ] `frontend/vitest.config.ts` — Vite-native test config (shares config with `vite.config.ts`)
- [ ] `frontend/src/test/setup.ts` — RTL + jest-dom matchers setup
- [ ] Framework install: `uv add --dev pytest pytest-asyncio httpx` (backend); `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom` (frontend)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Password reset email arrives in Mailpit and reset link works end-to-end | AUTH-03 | Requires live SMTP capture (Mailpit UI at `localhost:8025`) and clicking a real emailed link — not practically automatable in the Wave 0 test suite for this phase | 1. Trigger "forgot password" for a test account. 2. Open `localhost:8025`, find the email, click the reset link. 3. Set a new password, confirm auto-login + redirect to dashboard, confirm old sessions are revoked (re-check any other open session is logged out). |
| "Stay logged in across browser refresh" feels seamless in the browser | AUTH-02 | Silent-refresh-on-load is a UX/timing behavior best confirmed visually (no flash of login screen, no dropped session) — integration tests cover the token mechanics but not the perceived UX | 1. Log in. 2. Hard-refresh the browser (Ctrl+Shift+R). 3. Confirm the user lands on their dashboard without a visible login flash or redirect to `/login`. |
| Librarian-only / student-only UI elements are hidden AND server-enforced | AUTH-04 | Confirms the "regardless of what the UI shows" success criterion — requires manually forging/replaying a wrong-role token against a route the UI wouldn't normally expose | 1. Log in as a student. 2. Use browser devtools or `httpx`/curl with the student's access token to call a librarian-only endpoint directly. 3. Confirm a 403 response, not 200 — independent of what the UI renders. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
