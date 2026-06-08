# Phase 1: Auth Foundation - Research

**Researched:** 2026-06-08
**Domain:** FastAPI + SQLAlchemy 2.0 async authentication (JWT access/refresh, RBAC, password reset) + greenfield project scaffolding (Docker Compose, Alembic, React 19/Vite)
**Confidence:** MEDIUM-HIGH

## Summary

This phase is both the project's Walking Skeleton (first-ever code, full Docker Compose stack scaffold) and the security foundation every later phase depends on. The locked stack (FastAPI + SQLAlchemy 2.0 async + asyncpg + Alembic + PostgreSQL; pwdlib[argon2]; pyjwt; fastapi-mail + Mailpit; React 19 + Vite + TanStack Query + Zustand + React Router 7) is current, well-documented, and the combination is a common, well-trodden pattern as of mid-2026 — multiple independent boilerplates and the official FastAPI docs (post-PR #13917) now use exactly this pwdlib+Argon2 / pyjwt combination, replacing the older passlib/python-jose stack that CLAUDE.md correctly avoids.

The riskiest technical surface is **not** any single library — it's the *interaction* between three things: (1) the async-app/sync-Alembic hybrid migration setup, (2) httpOnly-cookie + CORS configuration across two different localhost ports in dev, and (3) refresh-token rotation race conditions (concurrent tabs/requests racing to rotate the same token). All three have well-known, documented solutions, but each is a classic place where teams lose a day to a subtle misconfiguration. This research documents the exact patterns to avoid each.

**Primary recommendation:** Scaffold the project structure first (routers/models/schemas/dependencies skeleton + Docker Compose + Alembic with the async-engine-in-sync-env.py pattern), get `alembic upgrade head` running green against Postgres in Compose, THEN build the auth vertical slice (signup → hash → login → issue tokens → require_role → refresh rotation → reset flow) on top of a working skeleton. Don't try to design the "perfect" user/token schema before the migration pipeline works end-to-end — that's how teams end up hand-editing migration files.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Password hashing & verification | API/Backend | — | Security-critical; must never touch the client. `pwdlib[argon2]` lives in backend service layer. |
| JWT issuance & verification | API/Backend | — | Signing key (`SECRET_KEY`) must never leave the server; access-token validation happens on every protected request via FastAPI dependency. |
| Role enforcement (`require_role`) | API/Backend | — | D-NOTE: the explicit success criterion #4 ("rejected server-side regardless of what UI shows") makes this non-negotiable as a backend-owned concern; UI role-gating is cosmetic only. |
| Refresh-token storage & rotation | API/Backend + Database | — | Refresh-token table is the source of truth for session validity/revocation; rotation logic must be transactional at the DB layer to avoid race conditions. |
| httpOnly refresh cookie | Frontend Server (browser-set, backend-issued) | Browser/Client | Cookie is set by the FastAPI response (`Set-Cookie`) and stored by the browser; JS never reads it — this is the entire point of httpOnly. |
| Access token storage (in-memory) | Browser/Client | — | Zustand store, cleared on tab close; never persisted to localStorage (XSS mitigation per D-05). |
| Silent refresh on page load | Browser/Client | API/Backend | Client triggers `/auth/refresh` on app mount; backend validates the httpOnly cookie and issues a new access token. |
| Role-gated route components | Browser/Client | API/Backend | UI-level gating is UX convenience only (hide links/pages) — the *enforcement* is server-side (AUTH-04); client-side gating that isn't backed by a 403 is a security theater anti-pattern. |
| Password-reset email delivery | API/Backend | — | `fastapi-mail` + `BackgroundTasks`, fire-and-forget from the request handler; SMTP round-trip must never block the HTTP response. |
| Email template rendering | API/Backend | — | Jinja2 templates rendered server-side and handed to `fastapi-mail`. |
| Database schema / migrations | Database | API/Backend (Alembic runs from backend container/CLI) | Alembic owns schema evolution; SQLAlchemy models are the source of truth that autogenerate reads from. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.136.3 | Backend API framework | Verified current on PyPI `[VERIFIED: PyPI registry]`. Matches CLAUDE.md pin range `>=0.115,<0.137`. |
| sqlalchemy | 2.0.50 | Async ORM | Verified current on PyPI `[VERIFIED: PyPI registry]`. 2.0 async (`AsyncSession`, `create_async_engine`) is the modern standard for FastAPI. |
| alembic | 1.18.4 | Migrations | Verified current on PyPI `[VERIFIED: PyPI registry]`. First-class support for async-engine env.py patterns since 1.13+. |
| pydantic | 2.13.4 | Validation/schemas | Verified current on PyPI `[VERIFIED: PyPI registry]`. |
| pwdlib[argon2] | 0.3.0 | Password hashing | Verified current on PyPI `[VERIFIED: PyPI registry]`. **Official FastAPI tutorial migration target** — confirmed via [fastapi/fastapi PR #13917](https://github.com/fastapi/fastapi/pull/13917) `[CITED: github.com/fastapi/fastapi/pull/13917]`. Replaces `passlib` (broken on Python 3.13 per PEP 594 `crypt` removal). |
| pyjwt | 2.13.0 | JWT encode/decode | Verified current on PyPI `[VERIFIED: PyPI registry]`. Actively maintained (55 releases since 2015); `python-jose` has had no release since 2021. |
| asyncpg | 0.31.0 | Async Postgres driver | Verified current on PyPI `[VERIFIED: PyPI registry]`. Standard async driver for `postgresql+asyncpg://`. |
| psycopg[binary] | 3.3.4 | Sync Postgres driver (Alembic) | Verified current on PyPI `[VERIFIED: PyPI registry]`. CLAUDE.md recommends sync-Alembic + async-app hybrid as the simplest, most-documented combination — this is psycopg's role. |
| python-multipart | 0.0.32 | OAuth2 password-flow form parsing | Verified current on PyPI `[VERIFIED: PyPI registry]`. Required by FastAPI's `OAuth2PasswordRequestForm`. |
| pydantic-settings | 2.14.1 | Typed env config | Verified current on PyPI `[VERIFIED: PyPI registry]`. Standard `.env` → `Settings` pattern. |
| fastapi-mail | 1.6.4 | Email sending | Verified current on PyPI `[VERIFIED: PyPI registry]`. Async, Jinja2-templated, built on `aiosmtplib`. 97 releases — mature. |
| jinja2 | 3.1.6 | Email templating | Verified current on PyPI `[VERIFIED: PyPI registry]`. Dependency of fastapi-mail. |
| react | 19.2.7 | Frontend UI | Verified current on npm `[VERIFIED: npm registry]`. |
| vite | 7.x recommended (8.0.16 latest, "very new" per CLAUDE.md) | Build tool/dev server | Latest is 8.0.16 `[VERIFIED: npm registry]` but CLAUDE.md explicitly recommends 6.x/7.x for stability since v8 (Rolldown-based) is bleeding-edge. **Use Vite 7.x** — the `npm create vite@latest` scaffolder will offer a stable major; pin explicitly if it defaults to 8. |
| @tanstack/react-query | 5.101.0 | Server-state mgmt | Verified current on npm `[VERIFIED: npm registry]`. |
| zustand | 5.0.14 | Client-state mgmt | Verified current on npm `[VERIFIED: npm registry]`. |
| react-router-dom | 7.17.0 | Routing | Verified current on npm `[VERIFIED: npm registry]`. |
| axios | 1.17.0 | HTTP client | Verified current on npm `[VERIFIED: npm registry]`. |
| typescript | 6.0.3 (latest); 5.x per CLAUDE.md | Frontend language | **Mismatch flag:** npm shows TS 6.0.3 as latest `[VERIFIED: npm registry]`, but CLAUDE.md pins "5.x". TS 6 may be very recent — verify it's stable before adopting; 5.x remains a safe, well-supported choice. Recommend planner pin to latest 5.x unless TS 6 compatibility with the rest of the toolchain (Vite, RTL, etc.) is separately confirmed. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-hook-form | 7.78.0 | Form handling | Login/signup/reset forms — verified current `[VERIFIED: npm registry]`. |
| zod | 4.4.3 | Schema validation | Pairs with react-hook-form via `@hookform/resolvers/zod` — verified current `[VERIFIED: npm registry]`. Note: zod 4 is a major version bump from the 3.x many tutorials reference; check `@hookform/resolvers` compatibility. |
| tailwindcss | 4.3.0 | Styling | Verified current `[VERIFIED: npm registry]`. v4 uses CSS-based config (`@tailwindcss/vite` plugin), not `tailwind.config.js` — don't follow v3 tutorials. |
| openapi-typescript / openapi-fetch | 7.13.0 / 0.17.0 | Typed API client gen | Verified current `[VERIFIED: npm registry]`. Generates TS types from FastAPI `/openapi.json` (OpenAPI 3.1). |
| vitest / @testing-library/react | 4.1.8 / 16.3.2 | Frontend testing | Verified current `[VERIFIED: npm registry]`. |
| pytest / pytest-asyncio / httpx | 9.0.3 / — / 0.28.1 | Backend testing | pytest and httpx verified current on PyPI `[VERIFIED: PyPI registry]`. `pytest-asyncio` not independently checked — `[ASSUMED]` still required and compatible (it's the standard pairing). |
| ruff | 0.15.16 | Lint/format | Verified current on PyPI `[VERIFIED: PyPI registry]`. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom ~150-line auth module | `fastapi-users` | Batteries-included but heavier abstraction; CLAUDE.md already decided against it for this project's two simple roles — don't revisit. |
| Refresh token in httpOnly cookie | Refresh token in localStorage | Locked decision (D-05) — localStorage is XSS-exposed; do not reconsider. |
| Sync-Alembic + async-app hybrid | Fully async Alembic (`-t async` template) | Hybrid is simpler and more documented; async-only saves one dependency (`psycopg`) but adds `run_sync` boilerplate in `env.py`. CLAUDE.md already locked the hybrid — follow it. |
| `APScheduler` in-process | Celery + Redis | Overkill for v1's "send a few emails" scope; CLAUDE.md already locked APScheduler for Phase 6 — not relevant to Phase 1 directly but confirms the project's "lightweight first" philosophy. |

**Installation:**
```bash
# Backend (uv recommended per CLAUDE.md)
uv add fastapi "sqlalchemy>=2.0.30" alembic "pydantic>=2.10" "pwdlib[argon2]" pyjwt asyncpg "psycopg[binary]" python-multipart pydantic-settings fastapi-mail jinja2 "uvicorn[standard]"
uv add --dev pytest pytest-asyncio httpx ruff mypy

# Frontend
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query zustand react-router-dom react-hook-form zod @hookform/resolvers axios
npm install -D tailwindcss @tailwindcss/vite openapi-typescript openapi-fetch vitest @testing-library/react @testing-library/jest-dom
npx shadcn@latest init
```

## Package Legitimacy Audit

> slopcheck could not be installed in this environment (no `pip`/`pip3` binary present in the sandbox — Python 3.10.12 has no `pip` module). Per the graceful-degradation protocol, all packages below are cross-checked against PyPI/npm registry metadata directly, but **none carry a slopcheck `[OK]` verdict**. The planner should gate first-time installs of the less-mainstream entries (`pwdlib`, `fastapi-mail`) behind a quick human sanity check (e.g., "does `uv add pwdlib[argon2]` succeed and does `from pwdlib import PasswordHash` import cleanly") rather than a heavyweight `checkpoint:human-verify`, since these are also the packages CLAUDE.md and the official FastAPI docs explicitly name.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| fastapi | PyPI | ~7 yrs (since 2018) | very high | github.com/fastapi/fastapi | N/A — not run | Approved (named in CLAUDE.md, official) |
| sqlalchemy | PyPI | ~20 yrs | very high | github.com/sqlalchemy/sqlalchemy | N/A | Approved |
| alembic | PyPI | ~12 yrs | high | github.com/sqlalchemy/alembic | N/A | Approved |
| pydantic | PyPI | ~10 yrs | very high | github.com/pydantic/pydantic | N/A | Approved |
| pwdlib | PyPI | ~2 yrs (first release 0.1.0; 4 total releases) | moderate | github.com/frankie567/pwdlib | N/A — `[ASSUMED]` per gate | Approved with note — newer/smaller project (4 releases since v0.1.0), but it is the package the **official FastAPI repo migrated its tutorial to** ([PR #13917](https://github.com/fastapi/fastapi/pull/13917)), authored by `frankie567` (maintainer of `fastapi-users`, a high-reputation FastAPI ecosystem contributor). Cite: `[CITED: github.com/fastapi/fastapi/pull/13917]`. |
| pyjwt | PyPI | ~11 yrs (55 releases) | very high | github.com/jpadilla/pyjwt | N/A | Approved |
| asyncpg | PyPI | ~9 yrs | high | github.com/MagicStack/asyncpg | N/A | Approved |
| psycopg | PyPI | mature (psycopg3 ~5 yrs) | high | github.com/psycopg/psycopg | N/A | Approved |
| fastapi-mail | PyPI | ~6 yrs (97 releases) | moderate-high | github.com/sabuhish/fastapi-mail | N/A | Approved |
| jinja2 | PyPI | ~17 yrs | very high | github.com/pallets/jinja | N/A | Approved |
| python-multipart | PyPI | ~10 yrs | high | github.com/Kludex/python-multipart | N/A | Approved |
| pydantic-settings | PyPI | ~4 yrs | high | github.com/pydantic/pydantic-settings | N/A | Approved |
| react, vite, @tanstack/react-query, zustand, react-router-dom, react-hook-form, zod, axios, tailwindcss, typescript | npm | all multi-year, mainstream | very high | well-known org repos | N/A — checked `scripts.postinstall` for axios/zustand/fastapi-mail equiv; none found suspicious | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none — `pwdlib` is flagged only as "newer, smaller" (not suspicious) and is independently corroborated by the official FastAPI repo's own migration PR, which raises it above a bare registry-existence check.

*slopcheck was unavailable at research time (no pip in environment). All packages are nonetheless backed by either (a) long registry history + high download volume, or (b) official-repo citation (pwdlib via FastAPI PR #13917). The planner should still treat first-time `uv add`/`npm install` of `pwdlib` and `fastapi-mail` as a quick checkpoint (run the install, confirm import succeeds) rather than blind trust — this is lighter than a full `checkpoint:human-verify` but maintains the spirit of the gate.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────┐         ┌──────────────────────────────────────────────┐
│   Browser   │         │              FastAPI Backend                  │
│  (React 19) │         │                                                │
│             │         │  ┌──────────┐   ┌──────────────┐             │
│ Zustand:    │ 1. POST │  │  /auth   │──▶│ require_role │──▶ Protected │
│ access_token│ /login  │  │  router  │   │  dependency  │    routes    │
│ (in-memory) │────────▶│  └────┬─────┘   └──────────────┘             │
│             │         │       │                                       │
│ axios       │ 2. Set- │       ▼                                       │
│ interceptor │ Cookie: │  ┌──────────────┐    ┌─────────────────┐    │
│ (attach JWT,│ refresh_│  │ pwdlib verify │   │ pyjwt encode/   │    │
│  catch 401) │ token   │  │ (argon2 hash) │   │ decode (HS256)  │    │
│             │ httpOnly│  └──────┬───────┘    └────────┬────────┘    │
│ TanStack    │◀────────│         │                     │              │
│ Query       │ 3. body:│         ▼                     ▼              │
│ (server     │ {access_│  ┌──────────────────────────────────┐       │
│  state)     │  token} │  │   AsyncSession (SQLAlchemy 2.0)   │       │
└──────┬──────┘         │  │   - users table                   │       │
       │                │  │   - refresh_tokens table          │       │
       │ 4. on page     │  └────────────────┬──────────────────┘       │
       │    load:       │                   │                          │
       │ POST /auth/    │                   ▼                          │
       │ refresh        │            ┌─────────────┐                  │
       │ (cookie sent   │            │ PostgreSQL  │                  │
       │  automatically)│            └─────────────┘                  │
       │───────────────▶│                                              │
       │                │  ┌──────────────────────────────────┐       │
       │ 5. password    │  │  /auth/forgot-password           │       │
       │    reset flow  │  │  → BackgroundTasks.add_task(     │       │
       │───────────────▶│  │      send_reset_email)           │       │
       │                │  │  → fastapi-mail + Jinja2 template│       │
       │                │  │  → SMTP to Mailpit (dev)         │       │
       │                │  └──────────────────────────────────┘       │
       │                │              │                               │
       │                │              ▼                               │
       │                │       ┌─────────────┐                        │
       │                │       │   Mailpit   │ (localhost:8025 web UI)│
       │                │       └─────────────┘                        │
       └────────────────┴──────────────────────────────────────────────┘
```

**Primary use case trace (signup → protected route):**
1. Browser POSTs `{email, password, role, librarian_code?}` to `/auth/signup`
2. Backend validates librarian_code (if role=librarian) against `LIBRARIAN_SIGNUP_CODE` env var, hashes password with `pwdlib` (Argon2), inserts into `users`
3. Backend issues access token (pyjwt, short TTL) + refresh token (random string, hashed + stored in `refresh_tokens` table, raw value set as httpOnly cookie)
4. Browser stores access token in Zustand (memory only); axios interceptor attaches it as `Authorization: Bearer <token>` on every request
5. Protected route hits `require_role("librarian")` dependency → decodes JWT → loads user → checks role → 200 or 403
6. On page refresh: Zustand is empty → frontend calls `/auth/refresh` (browser auto-sends httpOnly cookie) → backend validates+rotates refresh token → issues new access token → Zustand repopulated

### Recommended Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI() app, CORS middleware, router includes
│   ├── config.py            # pydantic-settings Settings class (.env)
│   ├── database.py          # async_engine, async_sessionmaker, get_db dependency
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py          # DeclarativeBase
│   │   ├── user.py          # User model (role enum)
│   │   └── refresh_token.py # RefreshToken model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py          # SignupRequest, LoginRequest, TokenResponse, etc.
│   │   └── user.py          # UserRead, UserCreate (Pydantic)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py          # /auth/signup, /login, /refresh, /logout, /forgot-password, /reset-password
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py          # get_current_user, require_role
│   │   └── db.py            # get_db (re-export or define here)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py  # token issuance, rotation, hashing orchestration
│   │   └── email_service.py # fastapi-mail wrapper + Jinja2 templates
│   ├── core/
│   │   ├── security.py      # pwdlib PasswordHash instance, pyjwt encode/decode helpers
│   │   └── exceptions.py    # custom exception classes
│   └── templates/
│       └── email/
│           └── password_reset.html
├── alembic/
│   ├── env.py               # async-engine-in-sync-context pattern
│   └── versions/
├── alembic.ini
├── tests/
│   ├── conftest.py          # AsyncClient + test DB fixtures
│   └── test_auth.py
├── pyproject.toml
└── Dockerfile

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx              # Router setup
│   ├── api/
│   │   ├── client.ts        # axios instance + interceptors
│   │   └── generated/       # openapi-typescript output
│   ├── stores/
│   │   └── authStore.ts     # Zustand: { accessToken, user, setAuth, clearAuth }
│   ├── hooks/
│   │   ├── useLogin.ts      # TanStack Query mutation
│   │   └── useSilentRefresh.ts
│   ├── components/
│   │   └── ProtectedRoute.tsx  # role-gated route wrapper
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── SignupPage.tsx
│   │   ├── ForgotPasswordPage.tsx
│   │   └── ResetPasswordPage.tsx
│   └── lib/
│       └── queryClient.ts
├── vite.config.ts
├── package.json
└── Dockerfile

docker-compose.yml
.env / .env.example
```

### Pattern 1: `get_current_user` + `require_role` dependency chain

**What:** Layered FastAPI dependencies — `get_current_user` decodes the JWT and loads the user; `require_role(*roles)` wraps it and raises 403 if the role doesn't match.
**When to use:** Every protected route in every future phase (catalog management, borrow approval, etc.) depends on this exact pattern — get it right here.
**Example:**
```python
# Source: pattern synthesized from FastAPI official OAuth2-JWT tutorial
# (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) + community RBAC examples
# (https://medium.com/@bhagyarana80/how-i-built-a-role-based-access-control-system-with-fastapi-and-pydantic-2c49e967efb0)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: UserRole):
    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user
    return _checker

# Usage:
# @router.post("/books", dependencies=[Depends(require_role(UserRole.LIBRARIAN))])
# async def create_book(...): ...
```

### Pattern 2: pwdlib Argon2 hashing (replaces passlib)

**What:** `PasswordHash.recommended()` gives a pre-configured Argon2id hasher; `.hash()` / `.verify()` are the only two calls needed.
**When to use:** Signup (hash) and login (verify).
**Example:**
```python
# Source: official FastAPI tutorial migration — fastapi/fastapi PR #13917
# https://github.com/fastapi/fastapi/pull/13917
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()  # Argon2id with secure defaults

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)
```
Resulting hash format: `$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>` — confirms Argon2id with memory=64MB, time_cost=3, parallelism=4 (pwdlib's "recommended" defaults). These are sane for a university-scale app; no manual tuning needed for v1.

### Pattern 3: pyjwt access + refresh token issuance

**What:** Separate short-lived access tokens (JWT, stateless, contains `sub`, `role`, `exp`) from long-lived refresh tokens (random opaque string, stored hashed in DB — NOT a JWT, so it can be revoked server-side).
**When to use:** Login, refresh, signup (issue both on first auth).
**Example:**
```python
# Source: pattern synthesized from FastAPI official docs +
# https://medium.com/@jagan_reddy/jwt-in-fastapi-the-secure-way-refresh-tokens-explained-f7d2d17b1d17
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

ACCESS_TOKEN_EXPIRE_MINUTES = 20   # within locked 15-30 min range
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token_for_cookie, sha256_hash_for_db_storage)."""
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed
```
**Important:** the refresh token is *not* a JWT — it's a random opaque string, hashed (SHA-256 is sufficient here; it's a high-entropy random token, not a low-entropy password — Argon2 would be wasteful) and stored in the `refresh_tokens` table. This is what makes per-session revocation (D-06/D-07) possible: you can delete a row, but you can't "delete" a stateless JWT. Only the access token is a JWT (stateless, short-lived, never stored).

### Pattern 4: Refresh-token rotation with reuse detection

**What:** On every `/auth/refresh` call: look up the hashed token, verify not expired/revoked, issue a new pair, mark the old row revoked (don't delete — keep for reuse-detection audit), and atomically swap.
**When to use:** Implements D-04 (rotation-on-use) and the security property that a stolen-then-used refresh token gets detected.
**Example:**
```python
# Source: pattern synthesized from
# https://medium.com/@backendwithali/race-conditions-in-jwt-refresh-token-rotation
# and https://blog.hanchon.live/guides/jwt-tokens-and-fastapi/
async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[str, str, User]:
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()

    # SELECT ... FOR UPDATE locks the row for the duration of this transaction —
    # prevents two concurrent refresh calls from both succeeding on the same token
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == hashed)
        .with_for_update()
    )
    result = await db.execute(stmt)
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise HTTPException(401, "Invalid refresh token")

    if token_row.revoked_at is not None:
        # REUSE DETECTED — someone replayed an already-rotated token.
        # Treat as compromise: revoke the entire session family.
        await revoke_all_user_sessions(db, token_row.user_id)
        raise HTTPException(401, "Token reuse detected — all sessions revoked")

    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token expired")

    # Rotate: mark old as revoked, create new row, link via replaced_by
    token_row.revoked_at = datetime.now(timezone.utc)
    new_raw, new_hashed = generate_refresh_token()
    new_row = RefreshToken(
        user_id=token_row.user_id,
        token_hash=new_hashed,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        replaced_by=None,
    )
    db.add(new_row)
    await db.flush()
    token_row.replaced_by = new_row.id
    await db.commit()

    user = await db.get(User, token_row.user_id)
    new_access = create_access_token(user.id, user.role)
    return new_access, new_raw, user
```
`with_for_update()` (translates to `SELECT ... FOR UPDATE` in Postgres) is the key mechanism that prevents the race condition where two near-simultaneous refresh calls (e.g., two browser tabs both detecting an expired access token) both read the "not yet revoked" state and both try to rotate — the second transaction blocks until the first commits, then sees `revoked_at IS NOT NULL` and correctly triggers reuse-detection-or-graceful-retry logic. **Without this lock, you get a race where both succeed, one client ends up with an invalidated token, and you get spurious "session expired" bug reports.**

### Pattern 5: fastapi-mail + Jinja2 + BackgroundTasks for password reset

**What:** Render a Jinja2 HTML template, hand it to `FastMail.send_message()`, fire via `BackgroundTasks.add_task()` so the HTTP response returns immediately.
**When to use:** `/auth/forgot-password` endpoint.
**Example:**
```python
# Source: FastAPI-Mail official docs (https://sabuhish.github.io/fastapi-mail/)
# + https://github.com/maxwellwachira/FastAPI-Mail
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi import BackgroundTasks

conf = ConnectionConfig(
    MAIL_USERNAME="",
    MAIL_PASSWORD="",
    MAIL_FROM="noreply@library.local",
    MAIL_PORT=1025,           # Mailpit SMTP port
    MAIL_SERVER="mailpit",    # Compose service name
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates" / "email",
)

async def send_reset_email(email: str, reset_link: str):
    message = MessageSchema(
        subject="Reset your library account password",
        recipients=[email],
        template_body={"reset_link": reset_link, "expires_in": "1 hour"},
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")

# In the route:
@router.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    user = await get_user_by_email(db, req.email)
    if user is not None:
        token = generate_reset_token()
        await store_reset_token(db, user.id, token)  # 1-hour TTL, single-use
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(send_reset_email, user.email, link)
    # ALWAYS return the same generic response — enumeration-safe (D-09)
    return {"message": "If that email is registered, you'll receive a reset link shortly."}
```
**Critical for D-09 (enumeration safety):** the generic response must be returned in *both* branches (user found / not found), and — subtler — must take roughly the same amount of time either way, otherwise a timing attack reveals which emails are registered. Doing the DB lookup unconditionally (even if you discard the result) and always calling `background_tasks.add_task` (with a no-op task if user is None) helps equalize timing. This is a MEDIUM-confidence recommendation — `[ASSUMED]` that timing-attack resistance matters at this scale; flag for the planner to decide if this level of rigor is warranted for a university-internal tool.

### Pattern 6: Alembic async-engine-in-sync-env.py

**What:** Alembic's migration runner is fundamentally synchronous; the standard pattern wraps an async engine connection with `run_sync` so `context.configure` + `context.run_migrations` (sync APIs) can execute against it — OR (CLAUDE.md's recommended simpler path) just use a fully separate sync engine (`psycopg`) for Alembic only, and never touch the async engine from migrations at all.
**When to use:** Project scaffolding — set this up before writing the first model.
**Example (CLAUDE.md's recommended hybrid — sync Alembic, async app):**
```python
# alembic/env.py
# Source: pattern synthesized from
# https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/
# and Alembic Cookbook: https://alembic.sqlalchemy.org/en/latest/cookbook.html
from sqlalchemy import engine_from_config, pool
from app.models.base import Base
from app.config import settings

config = context.config

# Build a SYNC URL (psycopg, not asyncpg) for Alembic only —
# .replace("%", "%%") guards against ConfigParser interpolation
# choking on URL-encoded special characters in the password
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg")
config.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))

target_metadata = Base.metadata  # MUST import all models first or this is empty!

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pooling needed for one-shot migration runs
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```
This is simpler than the `-t async` template (no `run_sync` wrapper boilerplate) and matches CLAUDE.md's explicit recommendation: "sync Alembic + `psycopg`, async app + `asyncpg`."

### Pattern 7: React — axios interceptor + Zustand + silent refresh

**What:** A request interceptor attaches the in-memory access token; a response interceptor catches 401s, calls `/auth/refresh` (browser sends httpOnly cookie automatically via `withCredentials: true`), updates Zustand, and retries the original request — with a "failed queue" to prevent duplicate refresh calls when multiple requests 401 simultaneously.
**When to use:** App-wide axios instance setup; this is the backbone every future API call rides on.
**Example:**
```typescript
// Source: pattern synthesized from
// https://dev.to/hkarimi/building-a-production-grade-react-auth-starter-jwt-refresh-tokens-zustand-tanstack-query-3pk3
// and https://medium.com/@kirankumal714/implementing-refresh-token-in-react-using-axios-zustand-and-react-query-a5dbac2944b6
import axios from "axios";
import { useAuthStore } from "@/stores/authStore";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true, // REQUIRED — sends httpOnly refresh cookie cross-origin
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token!)));
  failedQueue = [];
};

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // queue this request until the in-flight refresh completes
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { data } = await apiClient.post("/auth/refresh"); // cookie sent automatically
        useAuthStore.getState().setAccessToken(data.access_token);
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().clearAuth();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
```
The `isRefreshing` + `failedQueue` pair is the documented fix for the "multiple simultaneous 401s trigger multiple refresh calls" race condition `[CITED: dev.to/hkarimi/...3pk3]`.

### Anti-Patterns to Avoid
- **Storing the access OR refresh token in localStorage:** Locked decision D-05 forbids this (XSS exposure). Access token = Zustand memory only; refresh token = httpOnly cookie only.
- **Synchronous SMTP send inside the request handler:** CLAUDE.md explicitly calls this out — blocks the response on mail-server latency. Always `BackgroundTasks.add_task`.
- **`session.query(...)` (SQLAlchemy 1.x style):** CLAUDE.md forbids this. Use `select()` + `AsyncSession.execute()`.
- **Client-side-only role gating:** A `<ProtectedRoute requiredRole="librarian">` that merely hides UI is not security — success criterion #4 requires the *server* to return 403. Always pair UI gating with `require_role` on the backend; never trust the frontend's role claim.
- **Deleting refresh tokens on rotation instead of marking revoked:** Deleting destroys the audit trail needed for reuse-detection (Pattern 4). Mark `revoked_at` + `replaced_by`, prune via a periodic job later if storage becomes a concern.
- **Wildcard CORS origins with `allow_credentials=True`:** FastAPI/Starlette will reject this combination outright (browsers refuse wildcard+credentials) — must explicitly list `["http://localhost:5173"]` (or whatever the Vite dev port is).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom PBKDF2/bcrypt wrapper | `pwdlib[argon2]` `.recommended()` | Argon2 parameter tuning (memory cost, parallelism, salt generation) is a cryptographic minefield; `pwdlib` ships vetted defaults and is the package the official FastAPI docs migrated to. |
| JWT encode/decode + signature verification | Custom base64+HMAC scheme | `pyjwt` | Token format, claim validation (`exp`, `nbf`, `iat`), algorithm confusion attacks (`alg: none`) are all handled correctly by a maintained library; rolling your own is a classic source of auth bypass CVEs. |
| CSRF/cookie security flags | Manual `Set-Cookie` string construction | FastAPI `Response.set_cookie(httponly=True, secure=..., samesite="lax")` | Cookie attribute combinations (especially `SameSite` + cross-port dev setups) are notoriously easy to get subtly wrong; the framework's typed API prevents malformed headers. |
| Email sending with retries/templating | Raw `smtplib` calls in request handlers | `fastapi-mail` + `BackgroundTasks` | Async SMTP, connection pooling, Jinja2 template rendering, and attachment handling are all solved problems; hand-rolling re-introduces the "blocks the request" anti-pattern CLAUDE.md explicitly warns against. |
| Form validation (signup/login/reset) | Manual `if not email or "@" not in email` checks | Pydantic schemas (backend) + Zod + react-hook-form (frontend) | Email format, password strength rules, and cross-field validation (e.g., "librarian code required if role=librarian") are exactly what schema libraries are for — and keeping both layers in sync via generated types (`openapi-typescript`) prevents drift. |
| Database connection pooling / retry-on-startup | Custom `while True: try connect except: sleep` loops | SQLAlchemy `create_async_engine(pool_size=..., pool_pre_ping=True)` + Compose healthcheck (`pg_isready` + `condition: service_healthy`) | The framework + orchestration layer combination already solves "wait for Postgres to be ready" — reinventing it in app code duplicates effort and is a common source of "works on my machine" bugs. |

**Key insight:** Every item in this table is a place where "just write 20 lines to do X" feels faster but is actually where security CVEs and 2am production bugs come from. The entire point of the locked stack (CLAUDE.md) is that these problems are *already solved* by widely-audited libraries — the work in this phase is wiring them together correctly, not reimplementing them.

## Common Pitfalls

### Pitfall 1: `localhost` vs `127.0.0.1` cookie/CORS mismatch
**What goes wrong:** The browser treats `http://localhost:5173` and `http://127.0.0.1:5173` as different origins. If the frontend dev server binds to one and the backend's CORS `allow_origins` lists the other (or the cookie's domain doesn't match what the browser used to reach the API), the httpOnly refresh cookie silently fails to be set or sent — login appears to work but refresh-on-reload fails with no obvious error.
**Why it happens:** Vite/uvicorn defaults, `.env` values, and what the developer types into the browser address bar can all disagree.
**How to avoid:** Pick ONE hostname (`localhost` is the conventional choice) and use it consistently in: Vite dev server config, FastAPI CORS `allow_origins`, the cookie's implicit domain (don't set an explicit `domain=` attribute in dev — let it default to the issuing host), and `VITE_API_URL`. Document this in `.env.example`.
**Warning signs:** Login succeeds, but a page refresh logs the user out; `document.cookie` shows nothing (expected for httpOnly) but Network tab shows no `Cookie` header on the `/auth/refresh` request.
`[CITED: sqlpey.com/javascript/cors-cookie-fastapi-react-fix + fastapi.tiangolo.com/tutorial/cors]`

### Pitfall 2: `allow_credentials=True` + wildcard origins
**What goes wrong:** Setting `allow_origins=["*"]` together with `allow_credentials=True` either raises a config error or — worse — the browser silently refuses to send/accept the cookie, and the dev sees "CORS error" messages that seem to contradict the CORS config being "correct."
**Why it happens:** The CORS spec forbids combining wildcard origins with credentialed requests (a security measure); FastAPI/Starlette enforces this, but the error surfaces as a confusing browser-side rejection rather than a clear backend startup error.
**How to avoid:** When `allow_credentials=True`, explicitly enumerate `allow_origins=["http://localhost:5173"]` (and add the production origin later) — never use `"*"` for any of `allow_origins`, `allow_methods`, `allow_headers` once credentials are involved.
**Warning signs:** Browser console shows "CORS policy: The value of the 'Access-Control-Allow-Origin' header... must not be the wildcard '*' when the request's credentials mode is 'include'".
`[CITED: fastapi.tiangolo.com/tutorial/cors]`

### Pitfall 3: Empty Alembic autogenerate (forgot to import models)
**What goes wrong:** Running `alembic revision --autogenerate` produces an empty migration (no `op.create_table` statements) even though models clearly exist.
**Why it happens:** `Base.metadata` is populated by the act of *importing* model modules (SQLAlchemy's declarative registry side-effect). If `env.py` only imports `Base` and not the individual model files, `Base.metadata.tables` is empty at autogenerate time.
**How to avoid:** In `env.py` (or in `app/models/__init__.py`, imported by `env.py`), explicitly import every model module before referencing `target_metadata = Base.metadata`. A common pattern: `from app.models import user, refresh_token  # noqa: F401`.
**Warning signs:** `alembic revision --autogenerate -m "create users table"` generates a migration file with empty `upgrade()`/`downgrade()` bodies.
`[CITED: berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker]`

### Pitfall 4: ConfigParser `%` interpolation breaking DB URLs with special characters
**What goes wrong:** If the Postgres password (or any part of `DATABASE_URL`) contains a `%` (e.g., from URL-encoding a special character), `config.set_main_option("sqlalchemy.url", url)` raises a cryptic `InterpolationSyntaxError` because Alembic's config layer uses Python's `ConfigParser`, which treats `%` as an interpolation marker.
**Why it happens:** `ConfigParser` (used internally by `alembic.ini` parsing) performs `%`-style string interpolation; a literal `%` in a value must be escaped as `%%`.
**How to avoid:** Always call `.replace("%", "%%")` on the URL string before passing it to `config.set_main_option()`. (Generated dev passwords are unlikely to contain `%`, but production secrets manager output sometimes does — cheap to guard against now.)
**Warning signs:** `alembic upgrade head` fails with `configparser.InterpolationSyntaxError: '%' must be followed by '%' or '('...` despite the URL looking correct when printed.
`[CITED: WebSearch synthesis of alembic env.py setup guides — MEDIUM confidence, single clear source]`

### Pitfall 5: Refresh-token rotation race conditions across concurrent requests
**What goes wrong:** Two near-simultaneous requests (e.g., two browser tabs, or a request retry) both present the same refresh token to `/auth/refresh`. Without locking, both read "not yet rotated," both rotate, and one ends up holding an invalidated token — manifesting as a spurious "please log in again."
**Why it happens:** Classic read-then-write race condition; the rotation logic (read row → check valid → write new row → mark old revoked) is not atomic without explicit locking.
**How to avoid:** Use `SELECT ... FOR UPDATE` (`.with_for_update()` in SQLAlchemy) to lock the refresh-token row for the duration of the rotation transaction — see Pattern 4. Alternatively (more lenient), implement a short "grace period" where the immediately-prior token is still accepted for N seconds after rotation — but this adds complexity CLAUDE.md/CONTEXT.md don't ask for; prefer the simpler row-lock approach for v1.
**Warning signs:** Intermittent, hard-to-reproduce "session expired" errors that correlate with multi-tab usage or flaky network retries.
`[CITED: medium.com/@backendwithali/race-conditions-in-jwt-refresh-token-rotation]`

### Pitfall 6: `passlib`/`python-jose` appearing in copy-pasted tutorial code
**What goes wrong:** The overwhelming majority of FastAPI auth tutorials online (as of this research) still show `passlib.context.CryptContext` and `python-jose`, because the official docs only migrated in PR #13917 (recent). A developer following an older/popular tutorial will install the wrong packages.
**Why it happens:** Tutorial content lags behind library ecosystem shifts; `passlib`+`python-jose` was the standard for years.
**How to avoid:** Use the exact import patterns in Pattern 2 and Pattern 3 above (`from pwdlib import PasswordHash`, `import jwt` from `pyjwt`). If consulting external tutorials, mentally substitute `CryptContext(schemes=["bcrypt"])` → `PasswordHash.recommended()` and `from jose import jwt` → `import jwt` (pyjwt has a near-identical `encode`/`decode` API, easing the swap).
**Warning signs:** `pip install passlib` or `pip install python-jose` appearing in any generated `pyproject.toml`/requirements — both are explicitly forbidden by CLAUDE.md.
`[CITED: github.com/fastapi/fastapi/pull/13917 + github.com/fastapi/fastapi/discussions/11773]`

### Pitfall 7: JWT clock skew between containers
**What goes wrong:** If the backend container's clock drifts even slightly from "real" time (common in some Docker/WSL2 setups, or across multiple backend replicas), a freshly-issued token can appear "not yet valid" (`iat`/`nbf` in the future) or expire earlier/later than intended, causing intermittent 401s right after login.
**Why it happens:** `pyjwt` validates `exp`/`iat`/`nbf` against the *verifying* machine's clock; container clocks can drift from host clocks, especially in WSL2 environments (noted in this project's own platform: `Linux 5.15.167.4-microsoft-standard-WSL2`).
**How to avoid:** (a) Don't set `nbf` (not-before) claims unless you need them — they're the most sensitive to skew; (b) `pyjwt.decode()` accepts a `leeway` parameter (e.g., `leeway=10` seconds) to tolerate small clock differences; (c) for a single-container dev setup this is a low-probability issue, but worth a one-line `leeway=10` as cheap insurance.
**Warning signs:** Login works, but the very next authenticated request returns 401 "token not yet valid" or "token expired" despite the token being freshly issued.
`[ASSUMED — synthesized from general pyjwt clock-validation behavior + WSL2 clock-drift being a known class of issue; not verified against this specific environment's clock behavior]`

## Code Examples

### User & RefreshToken SQLAlchemy 2.0 models
```python
# Source: pattern synthesized from SQLAlchemy 2.0 declarative mapping docs
# + refresh-token schema research (caduh.com/blog/jwts-expiration-rotation-revocation)
import enum
from datetime import datetime
from sqlalchemy import String, Enum, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    LIBRARIAN = "librarian"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # sha256 hex
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[int | None] = mapped_column(ForeignKey("refresh_tokens.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)  # optional metadata (Claude's discretion D-CONTEXT)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_active", "user_id", "revoked_at"),
    )
```
**Schema design rationale:**
- `token_hash` not `token` — never store the raw refresh token (it's a bearer credential; a DB leak shouldn't be a session-hijack vector). SHA-256 hex digest (64 chars) is sufficient for a high-entropy random token (unlike passwords, no need for slow/salted hashing).
- `revoked_at` (nullable timestamp) instead of a boolean `is_revoked` — preserves *when* revocation happened, useful for audit/debugging and for the reuse-detection check in Pattern 4.
- `replaced_by` self-referencing FK — builds the rotation chain, enabling "was this token already rotated, and into what?" forensics.
- Composite index on `(user_id, revoked_at)` — supports both "find all active sessions for user X" (D-06 logout, D-07 reset-completion mass-revocation) and "find all sessions to revoke."
- `user_agent` — included per CONTEXT.md's "Claude's Discretion" note that this is optional but useful for a future "manage your sessions" view; cheap to add now, expensive to backfill later.

### Zustand auth store
```typescript
// Source: pattern synthesized from
// https://dev.to/hkarimi/building-a-production-grade-react-auth-starter-jwt-refresh-tokens-zustand-tanstack-query-3pk3
import { create } from "zustand";

interface User {
  id: number;
  email: string;
  role: "student" | "librarian";
}

interface AuthState {
  accessToken: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  setAccessToken: (token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAuth: (accessToken, user) => set({ accessToken, user }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clearAuth: () => set({ accessToken: null, user: null }),
}));
// Deliberately NOT using zustand's `persist` middleware — that would write to
// localStorage, which is exactly what D-05 forbids for the access token.
```

### Role-gated route component
```typescript
// Source: pattern synthesized from React Router 7 + Zustand role-gating examples
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export function ProtectedRoute({ requiredRole }: { requiredRole?: "student" | "librarian" }) {
  const { user, accessToken } = useAuthStore();

  if (!accessToken || !user) return <Navigate to="/login" replace />;
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" replace />;

  return <Outlet />;
}
// REMINDER: this is UX convenience only. The *enforcement* is the backend's
// require_role() dependency (Pattern 1) returning 403 — this component merely
// avoids showing a librarian-only page to a student who'd get a 403 anyway.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `passlib.context.CryptContext(schemes=["bcrypt"])` | `pwdlib.PasswordHash.recommended()` (Argon2id) | Official FastAPI docs migrated via PR #13917 (recent, exact date not in PR metadata fetched) | `passlib` is unmaintained and breaks on Python 3.13 (`crypt` module removal, PEP 594); `pwdlib` is the FastAPI-blessed replacement |
| `from jose import jwt` (`python-jose`) | `import jwt` (`pyjwt`) | `python-jose` last released 2021 | `pyjwt` actively maintained, simpler API, fewer CVE concerns |
| MailHog for dev SMTP capture | Mailpit (`axllent/mailpit`) | MailHog archived/unmaintained | Mailpit is the actively-maintained drop-in successor (CLAUDE.md already locks this) |
| Create React App | Vite | CRA officially deprecated Feb 2025 | CLAUDE.md already locks Vite; not a concern for this phase beyond initial scaffold |
| Tailwind v3 `tailwind.config.js` | Tailwind v4 CSS-based config (`@tailwindcss/vite`) | Tailwind 4.0 release | Don't follow v3 tutorials for setup — config model changed entirely |

**Deprecated/outdated:**
- `passlib`: unmaintained, hard-breaks on Python 3.13. Already excluded by CLAUDE.md.
- `python-jose`: no releases since 2021, CVE history. Already excluded by CLAUDE.md.
- MailHog: archived. Already excluded by CLAUDE.md (Mailpit locked).
- Tailwind v3 config patterns: superseded by v4's CSS-first config — relevant because many "shadcn/ui setup" tutorials still show v3 instructions.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Timing-attack resistance matters for the enumeration-safe password-reset response (D-09) | Pattern 5 / Code Examples | LOW — if wrong, the "generic response" is still enumeration-safe against the obvious vector (different message text); only a sophisticated timing-side-channel attack would be missed. For a university-internal tool this is likely over-engineering; flag for planner to descope if desired. |
| A2 | JWT clock-skew (`leeway`) is worth guarding against in this specific WSL2/Docker dev environment | Pitfall 7 | LOW — adding `leeway=10` to `jwt.decode()` is a one-line, harmless safety margin even if clock drift never actually occurs here. Risk of NOT adding it: rare, hard-to-reproduce 401s that waste debugging time. |
| A3 | TypeScript 6.0.3 (npm "latest") may not yet be the right choice vs. CLAUDE.md's pinned "5.x" | Standard Stack table | MEDIUM — if the planner blindly takes "latest," the project may hit compatibility friction with Vite/RTL/shadcn tooling that hasn't caught up to TS 6 yet. Recommend pinning to latest 5.x explicitly in `package.json` unless TS 6 compatibility is separately verified. |
| A4 | `pytest-asyncio` version compatibility with pytest 9.x (not independently checked on PyPI) | Standard Stack — Supporting table | LOW — `pytest-asyncio` is the standard, near-universal pairing; if there's a version mismatch, `uv add` will surface it immediately at install time (fail-fast, not a silent landmine). |
| A5 | `replace_all`-style `.replace("%", "%%")` guard for Alembic `sqlalchemy.url` — single WebSearch source, not cross-verified against Alembic's own docs in this session | Pitfall 4 | LOW — the fix is a no-op (harmless) if the URL never contains `%`; adding it costs nothing and prevents a real, documented failure mode if it ever does. |

**If empty:** N/A — see table above; 5 assumptions logged, all LOW-MEDIUM risk with cheap mitigations.

## Open Questions

1. **Exact access/refresh token lifetimes within the locked ranges**
   - What we know: CONTEXT.md locks ~15-30 min access / ~30 day refresh, explicitly leaving exact values to "Claude's Discretion."
   - What's unclear: Whether 15 min (tighter security, more refresh calls) or 30 min (fewer refresh calls, slightly larger compromise window) better fits this university's usage pattern (e.g., librarians keeping a tab open all day vs. students checking in briefly).
   - Recommendation: Default to 20 min access / 30 day refresh (values used in Pattern 3's example) — a reasonable midpoint. Document the constants in `config.py` as named settings so they're trivially adjustable without code changes later.

2. **Email verification at signup**
   - What we know: CONTEXT.md flags this as "Claude's Discretion... a reasonable default for v1 is to allow immediate use without mandatory email verification."
   - What's unclear: Whether the university's IT/security policy has an implicit expectation here that wasn't surfaced in discussion.
   - Recommendation: Skip mandatory email verification for v1 (matches CONTEXT.md's suggested default and keeps the walking-skeleton phase scoped). Note it explicitly in the plan as a "deferred enhancement" so it's easy to revisit if abuse patterns emerge (e.g., fake signups).

3. **Reset-token storage mechanism — separate table vs. column on `users`**
   - What we know: D-08 requires 1-hour, single-use reset links; D-07 requires reset-completion to revoke all sessions.
   - What's unclear: Whether to add a `password_reset_tokens` table (mirroring `refresh_tokens`'s pattern — hashed token, expiry, used_at) or simpler columns directly on `users` (`reset_token_hash`, `reset_token_expires_at`).
   - Recommendation: Use a small dedicated table (`password_reset_tokens`: id, user_id FK, token_hash, expires_at, used_at) — mirrors the `refresh_tokens` pattern the team will already be building, supports multiple-in-flight-requests gracefully (old links simply become invalid when a newer one is requested), and keeps `users` lean. This is a LOW-stakes schema choice either way; the table approach is marginally more consistent with the rest of this phase's design.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker / Docker Compose | Entire stack orchestration (locked requirement) | ✗ | — | **No viable fallback for actually running the stack** — Docker Desktop WSL2 integration is not active in this sandbox (`docker` command not found, WSL2 detected). The plan must include a setup/verification step for the developer to confirm Docker availability on their actual machine before `docker compose up` tasks; planning and code-writing can proceed without it, but execution/verification tasks that require running containers will need Docker enabled. |
| Node.js | Frontend scaffolding, npm installs | ✓ | v20.20.2 | — |
| npm | Frontend package management | ✓ | 10.8.2 | — |
| Python 3 | Backend runtime reference | ✓ | 3.10.12 | CLAUDE.md recommends 3.12/3.13 — the actual backend will run *inside* the Docker container (per locked deployment constraint), so the host's 3.10 is irrelevant to runtime; only relevant if someone tries to run the backend natively outside Docker. |
| pip / uv | Python package management (host-level) | ✗ | — | Neither `pip` nor `uv` present on host. Not blocking — CLAUDE.md specifies `uv` for dependency management *inside* the Docker build process (Dockerfile), and the project is Docker-first per locked constraints. The planner should ensure the Dockerfile installs `uv` itself (e.g., via the official `uv` install script or a `ghcr.io/astral-sh/uv` base-image layer) rather than assuming host tooling. |
| ctx7 (Context7 CLI) | Documentation lookups during research | ✗ | — | Not available; this research relied on WebSearch + official doc fetches + PyPI/npm registry verification instead. No impact on plan quality — all critical claims were cross-verified against authoritative sources (PyPI, official GitHub repos, FastAPI's own PR). |

**Missing dependencies with no fallback:**
- Docker / Docker Compose — the locked deployment mechanism cannot be verified end-to-end in this research session. The plan MUST include an early "verify Docker is running" checkpoint before any container-dependent tasks, and should not assume `docker compose up` succeeds silently.

**Missing dependencies with fallback:**
- pip/uv on host — irrelevant given the Docker-first architecture; the Dockerfile is responsible for installing its own toolchain.
- Python 3.12/3.13 on host — irrelevant; runtime is containerized.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x + pytest-asyncio (backend); vitest 4.x + @testing-library/react 16.x (frontend) — none yet installed (greenfield) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_auth.py -x -q` (backend); `npx vitest run src/components/ProtectedRoute.test.tsx` (frontend) |
| Full suite command | `pytest -q` (backend); `npx vitest run` (frontend) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | Signup creates user with correct role; librarian signup requires valid invite code; wrong code rejected with clear error | integration | `pytest tests/test_auth.py::test_signup_student tests/test_auth.py::test_signup_librarian_valid_code tests/test_auth.py::test_signup_librarian_invalid_code -x -q` | ❌ Wave 0 |
| AUTH-02 | Login issues access+refresh tokens; silent refresh on page load restores session; access token never persisted to localStorage | integration (backend) + component (frontend) | `pytest tests/test_auth.py::test_login_issues_tokens tests/test_auth.py::test_refresh_rotates_token -x -q` + `npx vitest run src/hooks/useSilentRefresh.test.ts` | ❌ Wave 0 |
| AUTH-03 | Forgot-password returns generic response regardless of email validity; reset link is single-use, 1-hour TTL; completing reset revokes all sessions and auto-logs-in | integration | `pytest tests/test_auth.py::test_forgot_password_enumeration_safe tests/test_auth.py::test_reset_password_single_use tests/test_auth.py::test_reset_revokes_all_sessions -x -q` | ❌ Wave 0 |
| AUTH-04 | `require_role("librarian")` returns 403 for student tokens and vice versa, on at least one real protected route | integration | `pytest tests/test_auth.py::test_require_role_rejects_wrong_role -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_auth.py -x -q` (backend); `npx vitest run` for touched frontend files
- **Per wave merge:** `pytest -q` (full backend suite) + `npx vitest run` (full frontend suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/conftest.py` — async test client fixture (`httpx.AsyncClient` against the FastAPI app), test-database fixture (separate Postgres schema or transactional rollback per test), factory helpers for creating test users
- [ ] `backend/tests/test_auth.py` — covers AUTH-01 through AUTH-04 (see map above)
- [ ] `backend/pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — `asyncio_mode = "auto"` for pytest-asyncio
- [ ] `frontend/vitest.config.ts` — Vite-native test config (shares config with `vite.config.ts`)
- [ ] `frontend/src/test/setup.ts` — RTL + jest-dom matchers setup
- [ ] Framework install: `uv add --dev pytest pytest-asyncio httpx` (backend); `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom` (frontend)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | `pwdlib[argon2]` for password storage; `pyjwt` for token-based session auth; rate-limiting on login/signup endpoints recommended (not explicitly locked — flag for planner) |
| V3 Session Management | yes | Refresh-token table with rotation-on-use + reuse detection (Pattern 4); httpOnly+Secure+SameSite cookie attributes; short-lived access tokens |
| V4 Access Control | yes | `require_role()` FastAPI dependency (Pattern 1) enforced server-side on every protected route — directly satisfies AUTH-04 / success criterion #4 |
| V5 Input Validation | yes | Pydantic schemas (backend) — `EmailStr` for email fields, length/complexity constraints on passwords; Zod + react-hook-form (frontend, defense-in-depth, not a substitute for backend validation) |
| V6 Cryptography | yes | Never hand-roll: `pwdlib` (Argon2id) for password hashing, `pyjwt` (HS256, or consider RS256 if multi-service signing verification is ever needed) for JWT signing, `secrets.token_urlsafe()` + SHA-256 for refresh-token generation/storage |

### Known Threat Patterns for FastAPI + React + JWT stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Account enumeration via signup/login/reset error messages | Information Disclosure | Generic responses for password-reset (D-09, locked); consider whether login error messages ("user not found" vs. "wrong password") leak the same info — recommend a single generic "Invalid email or password" for login too |
| Refresh-token theft + replay | Spoofing / Elevation of Privilege | httpOnly+Secure+SameSite cookie (D-05); rotation-on-use + reuse detection (Pattern 4); per-session revocation table (D-06) |
| Session fixation after password reset | Elevation of Privilege | D-07's "revoke all sessions on reset completion" directly mitigates this — a freshly-reset account starts with exactly one valid session |
| JWT algorithm confusion (`alg: none` / RS256↔HS256 substitution) | Tampering | `pyjwt.decode(..., algorithms=["HS256"])` — ALWAYS pass an explicit allowed-algorithms list; never accept the algorithm from the token's own header. This is the single most common JWT library misuse vector. `[CITED: general pyjwt security guidance — verify the explicit `algorithms=` parameter is present in every `jwt.decode()` call during code review]` |
| CSRF on cookie-authenticated endpoints | Tampering | `SameSite=Lax` (or `Strict`) on the refresh cookie significantly mitigates CSRF for the refresh endpoint; since the access token is sent via `Authorization` header (not a cookie), the bulk of the API surface is naturally CSRF-resistant (custom headers aren't auto-attached cross-site) |
| Brute-force login/signup attempts | Denial of Service / Spoofing | Not explicitly locked in CONTEXT.md — recommend the planner add basic rate-limiting (e.g., `slowapi` or a simple per-IP counter) as at minimum a "Claude's Discretion, flag for confirmation" item; ASVS V2 expects *some* anti-automation control |

## Sources

### Primary (HIGH confidence)
- PyPI registry (live JSON API queries, 2026-06-08) — verified current versions: fastapi 0.136.3, sqlalchemy 2.0.50, alembic 1.18.4, pydantic 2.13.4, pwdlib 0.3.0, pyjwt 2.13.0, fastapi-mail 1.6.4, asyncpg 0.31.0, psycopg 3.3.4, python-multipart 0.0.32, pydantic-settings 2.14.1, jinja2 3.1.6, pytest 9.0.3, httpx 0.28.1, ruff 0.15.16, apscheduler 3.11.2
- npm registry (live queries, 2026-06-08) — verified current versions: react 19.2.7, vite 8.0.16, @tanstack/react-query 5.101.0, zustand 5.0.14, react-router-dom 7.17.0, react-hook-form 7.78.0, zod 4.4.3, axios 1.17.0, tailwindcss 4.3.0, typescript 6.0.3, openapi-typescript 7.13.0, openapi-fetch 0.17.0, vitest 4.1.8, @testing-library/react 16.3.2
- [fastapi/fastapi PR #13917](https://github.com/fastapi/fastapi/pull/13917) — official tutorial migration from `passlib` to `pwdlib` + Argon2; exact import/usage patterns (`PasswordHash.recommended()`, `.hash()`, `.verify()`)
- [FastAPI official OAuth2-JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — `OAuth2PasswordBearer`, `get_current_user` dependency pattern
- [FastAPI official CORS docs](https://fastapi.tiangolo.com/tutorial/cors/) — `allow_credentials` + wildcard origin incompatibility, `CORSMiddleware` configuration

### Secondary (MEDIUM confidence)
- [berkkaraal.com — Setup FastAPI Project with Async SQLAlchemy 2, Alembic, PostgreSQL and Docker](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) — async-engine env.py pattern, model-import gotcha, NullPool rationale
- [Alembic Cookbook (official docs)](https://alembic.sqlalchemy.org/en/latest/cookbook.html) — async migration patterns
- [dev.to — Building a Production-Grade React Auth Starter (JWT, Refresh Tokens, Zustand, TanStack Query)](https://dev.to/hkarimi/building-a-production-grade-react-auth-starter-jwt-refresh-tokens-zustand-tanstack-query-3pk3) — axios interceptor + failed-queue pattern, Zustand store shape
- [medium.com/@backendwithali — Race Conditions in JWT Refresh Token Rotation](https://medium.com/@backendwithali/race-conditions-in-jwt-refresh-token-rotation-%EF%B8%8F-%EF%B8%8F-5293056146af) — `SELECT ... FOR UPDATE` locking rationale, reuse-detection pattern
- [blog.hanchon.live — Blacklist and Refresh Tokens (JWT) and FastAPI (Part 3)](https://blog.hanchon.live/guides/jwt-tokens-and-fastapi/) — token rotation/deletion-vs-revocation patterns
- [sqlpey.com — Fixing CORS and Cookie Issues Between FastAPI Backend and React Frontend](https://sqlpey.com/javascript/cors-cookie-fastapi-react-fix/) — localhost vs 127.0.0.1 origin mismatch pitfall
- [sabuhish.github.io/fastapi-mail — official docs](https://sabuhish.github.io/fastapi-mail/) — Jinja2 template configuration, `ConnectionConfig`, `FastMail.send_message`
- [medium.com/@bhagyarana80 — How I Built a Role-Based Access Control System with FastAPI and Pydantic](https://medium.com/@bhagyarana80/how-i-built-a-role-based-access-control-system-with-fastapi-and-pydantic-2c49e967efb0) — `require_role` dependency factory pattern

### Tertiary (LOW confidence)
- WebSearch synthesis on ConfigParser `%`-interpolation Alembic gotcha — single clear mention across multiple search-aggregated sources, not independently verified against Alembic's own issue tracker in this session (Pitfall 4, marked `[CITED: WebSearch synthesis]` with explicit confidence note)
- General `pyjwt` clock-skew/`leeway` guidance (Pitfall 7) — synthesized from training knowledge of `pyjwt`'s `decode()` API + WSL2 clock-drift being a known general class of issue; not verified against this specific environment's actual clock behavior — flagged `[ASSUMED]` (A2 in Assumptions Log)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every package version was verified live against PyPI/npm registries (authoritative sources), and the pwdlib/pyjwt choice is corroborated by the official FastAPI repo's own migration PR (not just CLAUDE.md's say-so)
- Architecture: MEDIUM-HIGH — the require_role/get_current_user pattern, refresh-token rotation pattern, and Compose layout are all extremely common, multiply-corroborated patterns; the exact schema column choices (Pattern 4's models) are this researcher's synthesis from multiple sources rather than a single canonical reference, hence MEDIUM rather than HIGH
- Pitfalls: MEDIUM — most pitfalls are corroborated by 2+ independent sources (CORS/cookie issues, model-import autogenerate gotcha, refresh-token races); two (Pitfall 4's ConfigParser `%` issue, Pitfall 7's clock-skew) rest on thinner single-source or synthesized evidence and are explicitly flagged as such

**Research date:** 2026-06-08
**Valid until:** ~30 days for the architecture/pattern guidance (stable, well-established patterns); package version pins should be re-verified at planning/implementation time if more than ~2 weeks elapse, since this is a fast-moving ecosystem (note: npm shows TypeScript 6.0.3 and Vite 8.0.16 as "latest" — both flagged in this research as potentially too-bleeding-edge; re-check their stability status before locking final versions)
