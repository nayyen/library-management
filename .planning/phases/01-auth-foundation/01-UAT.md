---
status: resolved
phase: 01-auth-foundation
source: [01-VERIFICATION.md]
started: 2026-06-09T15:00:00Z
updated: 2026-06-09T15:10:00Z
---

## Current Test

number: 1
name: Full backend test suite green
expected: |
  `docker compose exec backend uv run pytest -q` exits 0.
  All 12 AUTH tests + 1 health test pass, 0 failures.
awaiting: resolved

---

## Pending Tests

number: 2
name: Silent refresh — no flash on hard reload
expected: |
  Hard-reload (`Ctrl+Shift+R`) while logged in stays on the dashboard.
  No flash of the login page. Blank canvas shown briefly, then dashboard.

number: 3
name: Librarian signup gating
expected: |
  Signing up as librarian with the correct invite code succeeds (201, gets dashboard).
  Signing up as librarian with a wrong/missing code returns the exact error:
  "Invalid librarian code — check with your library administrator, or sign up as a student."

number: 4
name: Server-side role enforcement (AUTH-04)
expected: |
  `curl -H "Authorization: Bearer <student_token>" http://localhost:8000/demo/librarian-only`
  returns 403. Same request with a librarian token returns 200.

number: 5
name: Full Mailpit reset flow (AUTH-03 end-to-end)
expected: |
  - forgot-password returns identical generic message for registered and unregistered emails.
  - Reset email appears in Mailpit (http://localhost:8025).
  - Clicking the link opens /reset-password with the D-07 "signs you out of all devices" notice.
  - Resetting logs in automatically (D-10) and revokes the other session (D-07).
  - Clicking the same link again shows "This reset link is no longer valid…" immediately (D-08).

number: 6
name: Access token NOT in localStorage
expected: |
  After login, `localStorage.getItem('access_token')` returns `null` in the browser console.
  The access token lives only in the Zustand in-memory store (D-05).
