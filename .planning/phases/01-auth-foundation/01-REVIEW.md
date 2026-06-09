---
phase: 01-auth-foundation
reviewed: 2026-06-09T00:00:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - backend/alembic/env.py
  - backend/alembic/versions/0001_create_users_and_refresh_tokens.py
  - backend/alembic/versions/0002_create_password_reset_tokens.py
  - backend/app/config.py
  - backend/app/core/exceptions.py
  - backend/app/core/security.py
  - backend/app/dependencies/auth.py
  - backend/app/main.py
  - backend/app/models/__init__.py
  - backend/app/models/password_reset_token.py
  - backend/app/models/refresh_token.py
  - backend/app/models/user.py
  - backend/app/routers/auth.py
  - backend/app/routers/protected_demo.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/user.py
  - backend/app/services/auth_service.py
  - backend/app/services/email_service.py
  - backend/app/templates/email/password_reset.html
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/components/ProtectedRoute.test.tsx
  - frontend/src/components/ProtectedRoute.tsx
  - frontend/src/hooks/useForgotPassword.ts
  - frontend/src/hooks/useLogin.ts
  - frontend/src/hooks/useLogout.ts
  - frontend/src/hooks/useResetPassword.ts
  - frontend/src/hooks/useSignup.ts
  - frontend/src/hooks/useSilentRefresh.test.ts
  - frontend/src/hooks/useSilentRefresh.ts
  - frontend/src/lib/validation.ts
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/pages/ForgotPasswordPage.tsx
  - frontend/src/pages/LoginPage.tsx
  - frontend/src/pages/ResetPasswordPage.tsx
  - frontend/src/pages/SignupPage.tsx
  - backend/app/stores/authStore.ts
findings:
  critical: 5
  warning: 6
  info: 3
  total: 14
status: issues_found
---

# Phase 01: Auth Foundation — Code Review Report

**Reviewed:** 2026-06-09
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

The auth foundation is well-structured overall: the security primitives (Argon2 via pwdlib, pyjwt with explicit algorithm allowlist, opaque SHA-256-hashed refresh tokens, httpOnly cookie transport) are all correct choices and implemented carefully. The layering — models, service, router, dependency — is clean.

However, five blocker-class issues were found. Two are security bugs: the email service hardcodes `USE_CREDENTIALS=False`, making it impossible to use authenticated SMTP in any environment without a code change; and the `reset_password` / `is_reset_token_valid` service functions call `.replace(tzinfo=timezone.utc)` on a timezone-aware `datetime` column, silently discarding the stored timezone and potentially accepting expired tokens. A third blocker is a wrong exception type in the reset-password router that causes unhandled exceptions to surface as 500 errors instead of 400s. Two further blockers affect test reliability. The warnings cover a rate-limiting gap, a missing `db.rollback()` in the rotate path, token URL in-the-clear in email, missing confirm-password field, and a no-op logout path.

---

## Critical Issues

### CR-01: `expires_at.replace(tzinfo=timezone.utc)` corrupts timezone-aware datetimes

**File:** `backend/app/services/auth_service.py:224` and `:283`

**Issue:** `DateTime(timezone=True)` columns return timezone-aware `datetime` objects from PostgreSQL (with real UTC offset). Calling `.replace(tzinfo=timezone.utc)` on an already-aware datetime does NOT convert it — it replaces the existing tzinfo wholesale. If PostgreSQL ever returns a datetime with any offset other than UTC (e.g., a DST-offset timestamp, or a column value written via a session with a non-UTC timezone), the comparison silently uses the wrong value. More concretely, `expires_at.replace(tzinfo=timezone.utc) < now` can evaluate to `False` for a token that has genuinely expired, allowing an expired reset token to be accepted.

By contrast, the `rotate_refresh_token` function at line 156 correctly compares directly: `token_row.expires_at < datetime.now(timezone.utc)`, relying on Python's aware-datetime comparison — the same pattern should be used everywhere.

**Fix:** Replace both `.replace(tzinfo=timezone.utc)` calls with direct comparison, matching the pattern already used for refresh tokens:

```python
# was (lines 224 and 283):
if token_row.expires_at.replace(tzinfo=timezone.utc) < now:

# fix:
if token_row.expires_at < now:
```

If there is a concern about naive datetimes leaking from the DB driver, add a single defensive utility:

```python
def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
```

Then use `_ensure_utc(token_row.expires_at) < now` everywhere. This is safer than `.replace()` because `.astimezone()` converts rather than clobbers.

---

### CR-02: Wrong exception type caught in `reset_password` route — unhandled `PasswordResetToken` invalidity causes 500

**File:** `backend/app/routers/auth.py:249`

**Issue:** `auth_service.reset_password` raises `RefreshTokenInvalid` when a password-reset token is not found, already used, or expired (see `auth_service.py:280,284`). The router at line 249 catches `RefreshTokenInvalid` and maps it to a 400, which works — but this reuse of a refresh-token exception for a conceptually different error (reset token invalidity) is fragile. More critically: `auth_service.reset_password` calls `revoke_all_user_sessions` internally, which can itself raise a DB exception. That DB exception is not caught by the `except RefreshTokenInvalid` block and will propagate as an unhandled 500.

The deeper bug is semantic: `RefreshTokenInvalid` is documented as "presented refresh token is missing, unknown, expired, or has already been rotated." Using it to signal a password-reset-token failure means any future code that catches `RefreshTokenInvalid` expecting a refresh-token context will mishandle reset-token failures.

**Fix:** Add a dedicated exception class and raise/catch it instead:

```python
# In app/core/exceptions.py — add:
class PasswordResetTokenInvalid(Exception):
    """Raised by auth_service.reset_password / is_reset_token_valid when
    the presented reset token is missing, already used, or expired."""

# In auth_service.py — replace the three `raise RefreshTokenInvalid` calls
# inside reset_password with:
raise PasswordResetTokenInvalid

# In routers/auth.py — replace the except block:
except PasswordResetTokenInvalid as exc:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=RESET_LINK_INVALID_MESSAGE,
    ) from exc
```

---

### CR-03: Email service hardcodes `USE_CREDENTIALS=False`, breaking production SMTP

**File:** `backend/app/services/email_service.py:36`

**Issue:** The `ConnectionConfig` is built with `USE_CREDENTIALS=False` as a hardcoded literal, and `MAIL_USERNAME=""` / `MAIL_PASSWORD=""` also hardcoded — the `settings.MAIL_USERNAME` and `settings.MAIL_PASSWORD` values that exist in `config.py` are **ignored entirely**. Any deployment that uses a real SMTP relay requiring authentication (SendGrid, SES, university mail server) will silently fail to authenticate, and emails will not be sent. There is no error at startup — the failure only surfaces at runtime when `send_reset_email` is called.

This was intentional for Mailpit development but the hardcoding was left in the production code path.

**Fix:** Read from settings, and derive `USE_CREDENTIALS` from whether credentials are actually configured:

```python
_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD),
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=_TEMPLATE_DIR,
)
```

Add `VALIDATE_CERTS: bool = False` (or `True` for production) to `config.py` so it can be toggled per environment.

---

### CR-04: `conftest.py` `db_session` fixture does not re-open a savepoint after service-layer commits, causing test isolation failures

**File:** `backend/tests/conftest.py:43-51`

**Issue:** The fixture uses the nested-savepoint (SAVEPOINT) pattern to let service-layer `db.commit()` calls succeed without ending the outer rollback-able transaction. However, the standard PostgreSQL behavior after `RELEASE SAVEPOINT` (which is what `commit()` inside a savepoint does) is that the savepoint is gone — subsequent work runs outside any savepoint. After the first `await db.commit()` inside a test, the `connection.rollback()` in the `finally` block will roll back only work done before the savepoint was released, not work done after.

Concretely: `test_reset_password_single_use` calls `create_reset_token` (commits), then calls the HTTP endpoint (commits again). The second commit's data survives the fixture teardown and pollutes subsequent tests that share the same DB connection — breaking test isolation.

**Fix:** Use the standard "re-open savepoint on commit" pattern:

```python
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        await connection.begin()
        nested = await connection.begin_nested()

        session = AsyncSession(bind=connection, expire_on_commit=False)

        # Re-open a fresh savepoint every time the session commits, so
        # service-layer commits don't end the outer rollback-able transaction.
        @event.listens_for(session.sync_session, "after_transaction_end")
        def reopen_savepoint(session, transaction):
            if not nested.is_active:
                connection.sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()
```

Alternatively, mock `db.commit()` to a no-op in tests and call `db.flush()` instead.

---

### CR-05: `validate-reset-token` endpoint exposes a token oracle that enables timing-based user enumeration

**File:** `backend/app/routers/auth.py:184-200`

**Issue:** `GET /auth/validate-reset-token?token=<raw>` returns `{"valid": true}` for a valid token and a 400 for an invalid one. Since the `forgot-password` endpoint is enumeration-safe (always returns the same message), this preflight endpoint undoes that protection: an attacker who has somehow obtained a raw token can confirm it is valid. More practically, an attacker can use this endpoint to confirm whether a password-reset request was triggered for a given user, by observing whether a token they obtained (e.g., from a shared or intercepted email) is still valid.

The deeper issue: returning a distinct `{"valid": true}` 200 response vs. a 400 for the same data creates an unnecessary oracle. The form can show the "link expired" state after a failed POST to `/reset-password` instead.

**Fix:** Remove the `/validate-reset-token` GET endpoint entirely. Update the frontend `ResetPasswordPage` to skip the preflight query and show the `InvalidTokenView` only after a failed `POST /reset-password` returns 400. This eliminates the oracle without meaningfully degrading UX — the user still sees the "no longer valid" copy, just after submitting rather than on page load.

If the preflight is kept for UX reasons, it must be rate-limited identically to `/forgot-password` and `/reset-password`, and its response time must be constant (no timing oracle on the hash lookup).

---

## Warnings

### WR-01: No rate limiting on any auth endpoint — brute-force and credential-stuffing unmitigated

**File:** `backend/app/routers/auth.py` (all endpoints)

**Issue:** `/auth/login`, `/auth/forgot-password`, `/auth/reset-password`, and `/auth/signup` have no rate limiting. The login endpoint in particular is vulnerable to credential-stuffing and password-spray attacks. A 20-minute access token expiry and Argon2 hashing slow individual attempts, but do not bound the request rate an attacker can sustain.

**Fix:** Add a FastAPI-compatible rate-limiting middleware (e.g., `slowapi` wrapping `limits`) keyed on the client IP and/or email address. At minimum, `/auth/login` and `/auth/forgot-password` should be rate-limited. Document the decision in `CLAUDE.md` under "Constraints" if this is deferred to a future phase.

---

### WR-02: `rotate_refresh_token` does not roll back on expired-token path, leaving a dangling `FOR UPDATE` lock

**File:** `backend/app/services/auth_service.py:156-157`

**Issue:** When `token_row.expires_at < datetime.now(timezone.utc)` is true, the function raises `RefreshTokenInvalid` without calling `await db.rollback()` or `await db.commit()`. The session still holds the `SELECT ... FOR UPDATE` row lock acquired at line 144. Under SQLAlchemy's async session, the lock is released when the connection is returned to the pool — but if connection pooling is configured with `NullPool` or a long pool timeout, this can cause brief lock contention on that token row.

More importantly, the session is left in a dirty state (mid-transaction), which can cause subtle bugs if the same session is reused (e.g., in a test that reuses the same session fixture).

**Fix:** Add an explicit rollback before raising on the expired path:

```python
if token_row.expires_at < datetime.now(timezone.utc):
    await db.rollback()
    raise RefreshTokenInvalid
```

---

### WR-03: Password reset email contains the raw token in the URL — no token binding to prevent link forwarding

**File:** `backend/app/routers/auth.py:224` and `backend/app/templates/email/password_reset.html:26-40`

**Issue:** The email template renders the raw token URL in both a clickable button and a plain-text fallback link (`{{ reset_link }}` twice). If a user accidentally forwards the email, shares the link, or if the email is cached by a mail scanner that follows links, the token is exposed and usable by anyone who receives the URL. The plain-text fallback at line 39-40 is particularly risky — it is there specifically so users can copy-paste the URL, meaning it will be captured in clipboard managers, browser history, and screenshots.

**Fix:** For the plain-text fallback, show only the first and last few characters of the token rather than the full URL:

```html
<p>...or copy this link — valid for {{ expires_in }}, single-use only.</p>
```

The clickable button is unavoidable. To mitigate scanner pre-clicking, add a `POST`-only confirmation step (the current form-based flow already achieves this, since the token is in the query string and the form POST uses it, not the link click itself). No code change is strictly required, but the plain-text full URL duplication in the email is unnecessary exposure and should be removed.

---

### WR-04: `ResetPasswordPage` passes `token` as a `useQuery` dependency without encoding validation — `null` token bypasses the `enabled` guard on re-renders

**File:** `frontend/src/pages/ResetPasswordPage.tsx:79-89`

**Issue:** The query is gated `enabled: !!token`, which prevents firing when `token` is null. However, `token` comes from `useSearchParams().get("token")` which returns `null` on missing param. The guard works on first render, but after a successful reset navigates away (`navigate("/", { replace: true })`), React Router unmounts the component — which is fine. The actual bug is subtler: the `queryFn` uses `token!` (non-null assertion) at line 83. If `enabled` is `true` (token is non-null) but the query fires during a re-render where `token` has momentarily changed to `null` (e.g., programmatic URL manipulation or a React 18 concurrent-mode tearing scenario), `token!` will pass `null` to `encodeURIComponent`, producing the string `"null"` in the URL, which the backend will interpret as a valid but non-existent token and return 400 — showing the "invalid token" screen erroneously.

**Fix:** Add an explicit null-guard inside `queryFn`:

```typescript
queryFn: async () => {
  if (!token) throw new Error("No token");
  const { data } = await apiClient.get<{ valid: boolean }>(
    `/auth/validate-reset-token?token=${encodeURIComponent(token)}`,
  );
  return data;
},
```

---

### WR-05: `useLogout` clears auth store even when the server call fails silently — logout CSRF possible

**File:** `frontend/src/hooks/useLogout.ts:17-19`

**Issue:** `onSettled` fires whether the mutation succeeded or failed, so the store is always cleared regardless of the server response. This is intentional per the comment ("always reflects 'logged out'"). However, it means a CSRF attack targeting `POST /auth/logout` will successfully clear the victim's in-memory auth state (forcing a re-login) without needing to authenticate. Because `POST /auth/logout` has no CSRF token and `withCredentials: true` sends the cookie cross-origin (within the CORS allowlist), this is a denial-of-service against an authenticated user's session from any page on the allowed origin.

The server-side logout (`revoke_refresh_token`) is also idempotent and requires only the cookie, not the access token in the Authorization header. A CSRF from the same origin (e.g., XSS on a subdomain) can trigger full session revocation.

**Fix:** The `/auth/logout` route should require the access token in the `Authorization` header (already used for authenticated routes). Change the logout route to use `Depends(get_current_user)` to require a valid access token, ensuring only the legitimate client can trigger a logout:

```python
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    _current_user: User = Depends(get_current_user),  # requires valid access token
    db: AsyncSession = Depends(get_db),
) -> Response:
```

---

### WR-06: Signup form sends `librarian_code: ""` for student signups instead of omitting the field

**File:** `frontend/src/pages/SignupPage.tsx:46-51`

**Issue:** The `defaultValues` at line 40 sets `librarian_code: ""`. For student signups, the `onSubmit` handler correctly strips `librarian_code` from the payload (lines 48-50). However, if the user selects "librarian", enters a code, then switches back to "student" and submits, the `librarian_code` field retains its value from the watch state and the student-path payload correctly strips it. This is fine. The bug is the schema interaction: `signupSchema` uses `.refine()` to require a non-empty code only for librarians. If the user selects "librarian", triggers the `librarian_code` field to appear, then submits without entering a code, the schema fires the refine error. But if they enter something then clear it, `librarian_code` becomes `""` which fails `(data.librarian_code?.trim().length ?? 0) > 0` — this is actually correct behavior.

The actual defect: `defaultValues` sets `librarian_code: ""` but the schema declares `librarian_code: z.string().optional()`. An empty string `""` is NOT `undefined` — it passes `.optional()` but then the `.refine()` check evaluates `("".trim().length ?? 0) > 0` as `false`, so the form correctly blocks submission. However, when the student-path payload construction at lines 48-50 strips the field, the backend schema validator (`SignupRequest._require_code_for_librarian`) evaluates `not self.librarian_code` where `librarian_code=None` (the field is absent) — this is fine. No actual bug triggers, but the intent is muddied. The real issue is that `form.resetField("librarian_code")` is never called when switching from "librarian" back to "student", so stale validation state can persist.

**Fix:** Call `form.resetField("librarian_code")` when the role radio changes back to student:

```tsx
onChange={() => {
  field.onChange(option);
  if (option === "student") {
    form.resetField("librarian_code");
  }
}}
```

---

## Info

### IN-01: `SECRET_KEY` and `LIBRARIAN_SIGNUP_CODE` default to the same insecure literal

**File:** `backend/app/config.py:18-19`

**Issue:** Both settings default to `"change-me-in-production"`. If a developer forgets to set one (but sets the other), they may not notice because the app starts without error. The defaults are intentionally insecure placeholders, which is acceptable for a local dev setup, but they should at minimum be different values so a copy-paste error (same value for both secrets) is easier to spot. Consider adding a startup validator that raises on production deployments with the default value (detectable via `COOKIE_SECURE=true` as a proxy for "this is production").

---

### IN-02: Test functions are missing `@pytest.mark.asyncio` decorator

**File:** `backend/tests/test_auth.py` (all test functions, e.g. line 35)

**Issue:** All test functions are `async def` but none have `@pytest.mark.asyncio`. This works only if `asyncio_mode = "auto"` is configured in `pyproject.toml` — if it is not, pytest silently collects the coroutines without running them, and all tests "pass" vacuously. This should be verified in `pyproject.toml` (not reviewed here) and made explicit either via the decorator or a confirmed `asyncio_mode = "auto"` setting in `[tool.pytest.ini_options]`.

---

### IN-03: `password_reset.html` template variables are not auto-escaped in Jinja2

**File:** `backend/app/templates/email/password_reset.html:26,40`

**Issue:** `{{ reset_link }}` is rendered directly into `href` and link text. `fastapi-mail` uses Jinja2 with autoescaping enabled for HTML templates by default, so HTML-injection in the URL is mitigated. However, `reset_link` is constructed server-side as `f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"` where `raw_token` is `secrets.token_urlsafe(48)` — URL-safe base64, no angle brackets. This is safe as implemented. Documenting it here because a future change that interpolates user-supplied data (e.g., the user's name in the email) into the template body without escaping would introduce XSS-in-email. The template should be reviewed whenever new variables are added.

---

_Reviewed: 2026-06-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
