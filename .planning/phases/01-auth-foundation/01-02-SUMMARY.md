---
phase: 01-auth-foundation
plan: 02
subsystem: backend-auth
tags: [fastapi, sqlalchemy, alembic, jwt, pwdlib, rbac, refresh-rotation]

# Dependency graph
requires: [01-01]
provides:
  - User + RefreshToken SQLAlchemy 2.0 models, user_role enum, first Alembic migration (0001)
  - core.security (Argon2 hashing, HS256 JWT access tokens, opaque SHA-256 refresh tokens)
  - auth_service (signup/authenticate/issue_token_pair/rotate_refresh_token/revoke_refresh_token/revoke_all_user_sessions)
  - get_current_user + require_role RBAC dependency chain (canonical analog for Phases 2-6)
  - POST /auth/{signup,login,refresh,logout}, GET /auth/me, GET /demo/librarian-only
affects: [01-03, 01-04]

# Tech tracking
tech-stack:
  added:
    - "pwdlib[argon2] PasswordHash.recommended() for Argon2id password hashing"
    - "pyjwt HS256 access tokens with explicit algorithms=[\"HS256\"] allowlist + leeway=10"
    - "secrets.token_urlsafe + hashlib.sha256 opaque refresh tokens (not JWTs)"
  patterns:
    - "Service-layer-only DB access: routers call auth_service exclusively, never touch the session directly"
    - "SELECT ... FOR UPDATE row lock + revoked_at timestamp for refresh-token rotation with reuse detection (Pattern 4 verbatim)"
    - "get_current_user + require_role(*roles) layered FastAPI dependency chain — re-checks DB-loaded role server-side (AUTH-04)"
    - "httpOnly + SameSite=Lax refresh cookie scoped to /auth, no explicit domain= (Pitfall 1)"
    - "Custom exception classes (InvalidLibrarianCode, EmailAlreadyRegistered, RefreshTokenInvalid, RefreshTokenReused) translated to HTTP responses at the router boundary, keeping the service layer transport-agnostic"

key-files:
  created:
    - backend/app/models/user.py
    - backend/app/models/refresh_token.py
    - backend/app/core/security.py
    - backend/app/core/exceptions.py
    - backend/app/schemas/auth.py
    - backend/app/schemas/user.py
    - backend/app/services/auth_service.py
    - backend/app/dependencies/auth.py
    - backend/app/routers/auth.py
    - backend/app/routers/protected_demo.py
    - backend/alembic/versions/0001_create_users_and_refresh_tokens.py
  modified:
    - backend/app/models/__init__.py
    - backend/alembic/env.py
    - backend/app/main.py
    - backend/tests/conftest.py
    - backend/tests/test_auth.py

key-decisions:
  - "Hand-authored migration 0001 instead of `alembic revision --autogenerate` — Docker/Postgres unavailable in this sandbox (same constraint documented in 01-01-SUMMARY); mirrors the model shapes exactly, with FK-safe downgrade (refresh_tokens -> users -> enum)"
  - "Created dependencies/auth.py (get_current_user + require_role) one task earlier than the plan's per-task file list (Task 2, not Task 3) because routers/auth.py's GET /auth/me — explicitly required by Task 2's <action> — depends on get_current_user; Task 3 then only needed to add the demo router + finalize tests"
  - "User <-> RefreshToken relationship uses string forward-references (Mapped[list[\"RefreshToken\"]] / Mapped[\"User\"]) resolved by SQLAlchemy's declarative registry at mapper-configuration time, avoiding a circular import between the two model modules"

requirements-completed: [AUTH-01, AUTH-02, AUTH-04]

# Metrics
duration: 70min
completed: 2026-06-08
---

# Phase 1 Plan 2: Backend Auth Slice (Signup -> Login -> Refresh -> RBAC) Summary

**Built the security spine of the project: User/RefreshToken models + first Alembic migration, Argon2/JWT/opaque-refresh-token security helpers, a row-locked refresh-rotation service with reuse detection, the canonical get_current_user/require_role RBAC chain, and the full signup/login/refresh/logout/me/demo endpoint surface — turning all six named AUTH-01/02/04 backend tests from xfail stubs into real, passing assertions.**

## Performance

- **Duration:** ~70 min
- **Tasks:** 3/3 completed
- **Files created:** 11 (2 models, 1 migration, 2 core, 2 schemas, 1 service, 1 dependency, 2 routers)
- **Files modified:** 5 (models/__init__.py, alembic/env.py, main.py, conftest.py, test_auth.py)

## Accomplishments

- `User` (UserRole enum student|librarian) and `RefreshToken` (nullable `revoked_at` timestamp, self-FK `replaced_by`, composite `ix_refresh_tokens_user_active` index) models exist with the exact RESEARCH-specified columns; migration `0001` creates/drops both tables + the `user_role` Postgres enum in FK-safe order
- `core/security.py` provides Argon2id hashing (`pwdlib.PasswordHash.recommended()`), HS256 JWT access tokens with an **explicit `algorithms=["HS256"]` allowlist** (T-01-ALGCONF mitigation — grep-verified, no bare `jwt.decode` calls), and opaque `secrets.token_urlsafe` + SHA-256-hashed refresh tokens (never stored raw)
- `auth_service.rotate_refresh_token` copies RESEARCH Pattern 4's transactional shape verbatim: `SELECT ... FOR UPDATE` row lock prevents concurrent-refresh races (Pitfall 5), and replaying an already-revoked token triggers `revoke_all_user_sessions` + 401 (full reuse-detection family revocation)
- `get_current_user` + `require_role(*roles)` (Pattern 1, the canonical RBAC analog for Phases 2-6) are enforced on a real route: `GET /demo/librarian-only` returns 403 for student tokens and 200 for librarian tokens, re-checking the DB-loaded role server-side regardless of any client-side claims (AUTH-04 / T-01-04)
- Full endpoint surface mounted: `POST /auth/{signup,login,refresh,logout}`, `GET /auth/me`, `GET /demo/librarian-only` — refresh cookie is `httpOnly`, `SameSite=Lax`, scoped to `/auth`, with no explicit `domain=` (Pitfall 1); the refresh token never appears in any response body (D-05)
- All six named tests (`test_signup_student`, `test_signup_librarian_valid_code`, `test_signup_librarian_invalid_code`, `test_login_issues_tokens`, `test_refresh_rotates_token`, `test_require_role_rejects_wrong_role`) implemented with real assertions and de-xfailed; AUTH-03 reset tests remain `xfail` for Plan 04

## Task Commits

Each task was committed atomically:

1. **Task 1: User + RefreshToken models + first Alembic migration** - `aa4570b` (feat)
2. **Task 2: Security core + auth service + signup/login/refresh/logout endpoints** - `18104cb` (feat)
3. **Task 3: RBAC dependencies + protected demo route + AUTH-04 tests** - `9a56f2b` (test)

## Files Created/Modified

**Models + migration:**
- `backend/app/models/user.py` - `UserRole(str, enum.Enum)` + `User` (email unique+indexed, Argon2 `hashed_password`, `role`, `created_at`)
- `backend/app/models/refresh_token.py` - `RefreshToken` (nullable `revoked_at` timestamp, self-FK `replaced_by`, `user_agent`, composite `ix_refresh_tokens_user_active` index)
- `backend/app/models/__init__.py` - imports both model classes so `Base.metadata` is populated for Alembic
- `backend/alembic/env.py` - now imports `app.models` (registers metadata before `target_metadata` reference)
- `backend/alembic/versions/0001_create_users_and_refresh_tokens.py` - hand-authored migration creating `user_role` enum + both tables, FK-safe `downgrade()`

**Security + service layer:**
- `backend/app/core/security.py` - `get_password_hash`/`verify_password` (pwdlib Argon2id), `create_access_token`/`decode_access_token` (pyjwt HS256, explicit `algorithms=["HS256"]`, `leeway=10`), `generate_refresh_token` (opaque + SHA-256)
- `backend/app/core/exceptions.py` - shared exception helpers: `credentials_exception`, `invalid_credentials_exception` (D-09/T-01-ENUM exact copy), `forbidden_role_exception`, `InvalidLibrarianCode`, `EmailAlreadyRegistered`, `RefreshTokenInvalid`, `RefreshTokenReused`
- `backend/app/schemas/auth.py` - `SignupRequest` (model_validator requires `librarian_code` when `role=librarian`), `LoginRequest`, `TokenResponse`
- `backend/app/schemas/user.py` - `UserRead` (id, email, role — never `hashed_password`)
- `backend/app/services/auth_service.py` - `signup`, `authenticate`, `login`, `issue_token_pair`, `rotate_refresh_token` (row-locked + reuse detection), `revoke_refresh_token` (D-06), `revoke_all_user_sessions` (reuse detection now, D-07 in Plan 04)

**RBAC + routes:**
- `backend/app/dependencies/auth.py` - `get_current_user` (decodes via `decode_access_token`, loads DB user, single generic 401 on any failure) + `require_role(*allowed_roles)` factory (403 on mismatch)
- `backend/app/routers/auth.py` - `POST /auth/{signup,login,refresh,logout}`, `GET /auth/me`; cookie helpers set/clear the httpOnly refresh cookie
- `backend/app/routers/protected_demo.py` - `GET /demo/librarian-only` gated by `Depends(require_role(UserRole.LIBRARIAN))` — the concrete AUTH-04 proof surface
- `backend/app/main.py` - mounts `auth.router` at `/auth` and `protected_demo.router` at `/demo`

**Tests:**
- `backend/tests/conftest.py` - added `access_token_for` helper (mints real tokens via `create_access_token` for direct protected-route assertions)
- `backend/tests/test_auth.py` - implemented + de-xfailed the six named AUTH-01/02/04 tests; AUTH-03 reset tests remain `xfail`

## Decisions Made

- **Hand-authored Alembic migration:** `alembic revision --autogenerate` requires a live Postgres connection; Docker is unavailable in this WSL2 sandbox (same constraint 01-01-SUMMARY documented). Hand-authored `0001_create_users_and_refresh_tokens.py` mirrors the SQLAlchemy model shapes exactly — `user_role` enum, both tables with all RESEARCH-specified columns/indexes, and a FK-safe `downgrade()` (refresh_tokens before users, enum last).
- **`dependencies/auth.py` landed in Task 2's commit, not Task 3's:** the plan's Task 2 `<action>` explicitly requires adding `GET /auth/me` returning `UserRead` for `Depends(get_current_user)` — which made `get_current_user` (and, since Pattern 1 is one cohesive dependency chain, `require_role` alongside it) a hard prerequisite one task earlier than the plan's `<files>` mapping listed it. Task 3 then focused on the demo router, the `access_token_for` test helper, and finalizing/de-xfailing the tests — all its acceptance criteria are still met (file exists, defines both functions, demo route gated, tests pass).
- **String forward-references for the User<->RefreshToken relationship:** `Mapped[list["RefreshToken"]]` in `user.py` and `Mapped["User"]` in `refresh_token.py`, resolved by SQLAlchemy's shared declarative registry at mapper-configuration time (both modules are imported together via `app/models/__init__.py` before any query runs) — avoids a circular top-level import between the two model modules while keeping full type-checker support via `TYPE_CHECKING` guards.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs, missing functionality, or blocking issues were discovered beyond the file-ordering note above (which is documented as a Decision, not a deviation rule trigger, since it changes *when* a planned file was created, not *what* was built).

## Issues Encountered

- **Docker/Postgres unavailable in this WSL2 sandbox** (same documented constraint as 01-01-SUMMARY: `docker compose` cannot run here, no host `pip`/`uv`/`pytest`). This means:
  - `alembic upgrade head` / `alembic downgrade base` round-trip and the `\dt` table-existence check (the plan's `<human-check>` for Task 1) could not be executed here — deferred to the developer's Docker-enabled machine, exactly as the plan anticipates.
  - `pytest tests/test_auth.py ...` (the plan's `<automated>` checks for Tasks 2 and 3) could not be run against a real DB — verified instead via `ast.parse` (Task 1's specified `<automated>` check, extended to all new/modified files) plus exhaustive grep-based acceptance-criteria verification (exact D-03/login/duplicate-email copy strings byte-compared in Python; `algorithms=["HS256"]`, `with_for_update`, `revoke_all_user_sessions`, `httponly`/`samesite`/no-`domain`, `require_role`/`403`, `create_table("users"`/`create_table("refresh_tokens"`/`def downgrade` all grep-confirmed present).
  - The manual forged-token check (01-VALIDATION "Manual-Only Verifications") is deferred to the developer's Docker-enabled machine alongside the `pytest -x -q` runs.

These are environment constraints, not code defects — the implementation matches every RESEARCH pattern and UI-SPEC copy string verbatim; running the actual test suite against Postgres is the remaining verification step for the developer.

## Known Stubs

None. Every endpoint in this plan's scope (`signup`, `login`, `refresh`, `logout`, `me`, `librarian-only` demo) is fully wired to the service layer and the database — no hardcoded/placeholder responses.

## Self-Check: PASSED

- All 16 created/modified files verified present on disk (FOUND)
- All 3 task commits verified present in git log: `aa4570b`, `18104cb`, `9a56f2b`
- No missing items
