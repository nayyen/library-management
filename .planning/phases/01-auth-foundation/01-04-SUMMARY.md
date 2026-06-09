---
phase: 01-auth-foundation
plan: "04"
subsystem: auth
tags: [password-reset, fastapi-mail, mailpit, jinja2, tanstack-query, argon2]

requires:
  - phase: 01-02
    provides: revoke_all_user_sessions, issue_token_pair, RefreshToken model
  - phase: 01-03
    provides: auth store (setAuth), axios client, ProtectedRoute

provides:
  - password_reset_tokens table + PasswordResetToken model (hashed token, single-use, 1-hour TTL)
  - GET /auth/validate-reset-token (read-only preflight — does NOT consume token)
  - POST /auth/forgot-password (enumeration-safe, fires email via BackgroundTask)
  - POST /auth/reset-password (validates token, wipes all sessions, auto-logins)
  - ForgotPasswordPage + ResetPasswordPage with proactive token validation on mount
  - Email service (fastapi-mail + Jinja2 template, Mailpit in dev)
  - AUTH-03 fully complete (D-07/D-08/D-09/D-10 all enforced and tested)

affects: [future phases calling /auth/* endpoints, any feature requiring session security]

tech-stack:
  added: [fastapi-mail, jinja2 templates (email), useQuery for preflight validation]
  patterns:
    - "BackgroundTask fire-and-forget SMTP — never block HTTP response on mail delivery"
    - "Hashed-at-rest reset tokens (sha256 hex, raw value only in email link)"
    - "Read-only preflight endpoint for UX-critical validity checks before form render"
    - "useQuery on page mount for immediate error state without form submission"

key-files:
  created:
    - backend/app/models/password_reset_token.py
    - backend/app/services/email_service.py
    - backend/app/templates/email/password_reset.html
    - backend/alembic/versions/0002_create_password_reset_tokens.py
    - frontend/src/hooks/useForgotPassword.ts
    - frontend/src/hooks/useResetPassword.ts
    - frontend/src/pages/ForgotPasswordPage.tsx
    - frontend/src/pages/ResetPasswordPage.tsx
  modified:
    - backend/app/services/auth_service.py
    - backend/app/routers/auth.py
    - backend/app/models/__init__.py
    - backend/app/schemas/auth.py
    - backend/app/config.py
    - backend/tests/test_auth.py
    - frontend/src/lib/validation.ts
    - frontend/src/App.tsx

key-decisions:
  - "GET /auth/validate-reset-token added as a read-only preflight — lets the frontend show the error immediately on page load without consuming the token"
  - "USE_CREDENTIALS=False hardcoded for Mailpit dev (no SMTP auth needed); prod swap is env-var only"
  - "InvalidTokenView extracted as a shared component — covers both missing-token and rejected-token paths so both look identical to the user"
  - "submissionTokenInvalid state kept alongside query-based loadTokenInvalid to handle the concurrent-use edge case"

patterns-established:
  - "Preflight GET + mutation POST pattern: validate cheaply first, mutate only when valid"
  - "BackgroundTasks.add_task for all email sends — grep for add_task to confirm no sync SMTP"

requirements-completed: [AUTH-03]

duration: multi-session
completed: "2026-06-09"
---

# Plan 01-04: Password Reset Vertical Slice Summary

**Enumeration-safe forgot/reset flow (AUTH-03): hashed single-use tokens, Mailpit email delivery, all-session revocation on reset, auto-login, and immediate invalid-link feedback via read-only preflight endpoint**

## Performance

- **Duration:** multi-session (implementation + checkpoint verification + fix)
- **Completed:** 2026-06-09
- **Tasks:** 4 (3 auto + 1 blocking checkpoint)
- **Files modified:** 18

## Accomplishments

- `password_reset_tokens` table with hashed-at-rest token, single-use `used_at` marker, and 1-hour TTL — mirrors `refresh_tokens` pattern from Plan 02
- `POST /auth/forgot-password` always returns the same generic message regardless of whether the email is registered (D-09); if registered, fires `send_reset_email` as a `BackgroundTask` (never synchronous SMTP)
- `POST /auth/reset-password` validates the token, sets new Argon2 hash, calls `revoke_all_user_sessions` (D-07), issues a fresh token pair for auto-login (D-10)
- `GET /auth/validate-reset-token` read-only preflight — used by `ResetPasswordPage` via `useQuery` on mount to show the "no longer valid" copy **immediately** on page load (not only after form submission)
- `ForgotPasswordPage` always shows the generic confirmation copy; `ResetPasswordPage` renders the D-07 "signs you out of all devices" inline notice before submit
- 12 backend tests green (including 2 new preflight tests); 7 frontend tests green

## Task Commits

1. **Task 1: PasswordResetToken model + migration + reset-token helpers** — `9cfa190`
2. **Task 2: Email service + forgot/reset endpoints + AUTH-03 tests** — `7d467f5`
3. **Task 3: ForgotPassword + ResetPassword pages + hooks + routing** — `65beb1a`
4. **Fix: email service absolute template path + mailpit depends_on** — `919626a`
5. **Fix: hardcode USE_CREDENTIALS=False + empty creds for Mailpit** — `ddeebd1`
6. **Refactor: extract InvalidTokenView component** — `1ee4c9e`
7. **Fix (checkpoint): validate reset token on page load** — `33c5524`

## Deviations from Plan

### Auto-fixed Issues

**1. Email template path was relative — failed inside Docker container**
- **Found during:** Task 2 verification (email delivery)
- **Issue:** `TEMPLATE_FOLDER` set with relative path; Docker CWD differs from dev
- **Fix:** Changed to absolute path via `Path(__file__).parent.parent / "templates" / "email"`
- **Committed in:** `919626a`

**2. Mailpit SMTP rejected connection with credentials**
- **Found during:** Task 2 verification (Mailpit delivery)
- **Issue:** `USE_CREDENTIALS=True` caused Mailpit to reject the connection (Mailpit requires no auth)
- **Fix:** Hardcoded `USE_CREDENTIALS=False` and empty `MAIL_USERNAME`/`MAIL_PASSWORD` for the dev config
- **Committed in:** `ddeebd1`

**3. Checkpoint revealed: used reset link showed form instead of error**
- **Found during:** Task 4 checkpoint verification (step 6)
- **Issue:** Token validity was only checked on form submission — clicking a used link showed the password form, not the error
- **Fix:** Added `GET /auth/validate-reset-token` preflight endpoint + `useQuery` on `ResetPasswordPage` mount to surface the error immediately
- **Committed in:** `33c5524`

---

**Total deviations:** 3 auto-fixed (2 config/path issues, 1 UX gap caught by checkpoint)
**Impact on plan:** All fixes necessary for correctness. The preflight endpoint is an additive improvement that better matches the UX spec's intent.

## Issues Encountered

- Mailpit requires `USE_CREDENTIALS=False` and blank credentials — not obvious from fastapi-mail docs; discovered during live testing
- Email template path must be absolute for Docker container compatibility

## Next Phase Readiness

- AUTH-03 complete and checkpoint-verified end-to-end via Mailpit
- Phase 01 all four plans complete — auth foundation ready for Phase 02 (catalog)
- `revoke_all_user_sessions`, `issue_token_pair`, `require_role`, `get_current_user` available as service/dependency building blocks for all future phases

---
*Phase: 01-auth-foundation*
*Completed: 2026-06-09*
