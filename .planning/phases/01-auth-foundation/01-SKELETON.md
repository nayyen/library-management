# Walking Skeleton — Library Management System

**Phase:** 1 (Auth Foundation)
**Generated:** 2026-06-08

## Capability Proven End-to-End

A new user can sign up (choosing student, or librarian with a valid `LIBRARIAN_SIGNUP_CODE`), log in, stay logged in across a hard browser refresh (silent refresh via httpOnly cookie), and reach a role-gated dashboard stub — while a wrong-role user is rejected server-side with HTTP 403. This single slice exercises every layer: React UI → axios → FastAPI route → `require_role` dependency → `pwdlib`/`pyjwt` → SQLAlchemy async → PostgreSQL, plus the Alembic migration pipeline and the Docker Compose stack (db + backend + frontend + mailpit) that hosts it all.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI 0.136.x (pin `>=0.115,<0.137`), Python 3.13 in-container | Locked by CLAUDE.md. Async-native, Pydantic-integrated, auto OpenAPI for the typed React contract. |
| ORM / DB toolkit | SQLAlchemy 2.0.x async (`AsyncSession`, `create_async_engine`) + asyncpg | Locked. Modern async standard; `select()` style only — no 1.x `session.query()`. |
| Migrations | Alembic 1.18.x, **sync env.py** using `psycopg` (hybrid: async app, sync Alembic) | Locked by CLAUDE.md. Simpler than `-t async` template; rewrite `postgresql+asyncpg` → `postgresql+psycopg` for the migration URL only (RESEARCH Pattern 6). |
| Database | PostgreSQL 17 (`postgres:17-alpine`) | Locked. Relational integrity for users↔refresh_tokens↔(future) loans. |
| Password hashing | `pwdlib[argon2]` `PasswordHash.recommended()` (Argon2id) | Locked. NOT `passlib` (breaks on 3.13, PEP 594). RESEARCH Pattern 2. |
| Tokens | `pyjwt` HS256 access token (in-memory, ~20 min) + opaque refresh token (SHA-256 hashed in DB, ~30 days, httpOnly cookie, rotated on use with reuse detection) | Locked decisions D-04/D-05/D-06/D-07. NOT `python-jose`. RESEARCH Patterns 3 & 4. |
| Role model | Single `users` table, `role` enum (`student`\|`librarian`); enforcement via `require_role()` FastAPI dependency | Locked by CLAUDE.md. UI gating is cosmetic; server 403 is the enforcement (AUTH-04). |
| Frontend | React 19 + Vite 7 + TypeScript 5.x + TanStack Query 5 + Zustand 5 + React Router 7 + axios | Locked. Access token in Zustand memory only (no `persist`/localStorage, D-05). |
| Styling / components | Tailwind v4 (CSS config via `@tailwindcss/vite`) + shadcn/ui (`new-york` + `slate` + CSS variables) | Per 01-UI-SPEC.md (APPROVED). Do not follow Tailwind v3 tutorials. |
| Email (dev) | `fastapi-mail` + Jinja2 templates → Mailpit (`axllent/mailpit`, SMTP :1025, UI :8025) via `BackgroundTasks` | Locked. NOT synchronous SMTP in request handler; NOT MailHog. RESEARCH Pattern 5. |
| Config | `pydantic-settings` `Settings` class loading `.env` (gitignored); `.env.example` committed | Locked. No plaintext secrets in compose file. |
| Deployment target | Single `docker-compose.yml` (db + backend + frontend + mailpit), Compose v2 (`docker compose`), `pg_isready` healthcheck + `depends_on: condition: service_healthy` | Locked. Documented local full-stack run: `docker compose up`. |
| Directory layout | `backend/app/{main,config,database}.py` + `models/ schemas/ routers/ dependencies/ services/ core/ templates/`; `frontend/src/{api,stores,hooks,components,pages,lib}/` | Per 01-RESEARCH.md "Recommended Project Structure". Becomes the analog for Phases 2-6. |

## Stack Touched in Phase 1

- [x] Project scaffold — backend (uv + pyproject + ruff + pytest), frontend (Vite + TS + Tailwind 4 + shadcn), Docker Compose stack
- [x] Routing — backend `/auth/*` router; frontend React Router 7 routes (`/login`, `/signup`, `/forgot-password`, `/reset-password`, `/` dashboard) with `ProtectedRoute`
- [x] Database — real write (signup inserts `users` + `refresh_tokens` rows) AND real read (login/refresh query them); Alembic migration creates the tables
- [x] UI — interactive login/signup forms wired through axios → FastAPI; silent-refresh-on-load; role-gated dashboard stub
- [x] Deployment — runs via `docker compose up`; backend waits on `db` healthcheck; Mailpit UI at `localhost:8025`

## Out of Scope (Deferred to Later Slices)

Explicit — prevents later phases from re-litigating Phase 1's minimalism:

- **Email verification at signup** — deferred (Claude's Discretion per CONTEXT.md; v1 allows immediate use). Revisit only if abuse patterns emerge.
- **Rate-limiting / anti-automation on login/signup** — flagged by RESEARCH Security Domain (ASVS V2) but not locked in CONTEXT.md. Deferred; add `slowapi` in a later hardening pass if needed.
- **"Manage your sessions" UI** — `refresh_tokens.user_agent` column is captured now (cheap), but no UI consumes it in v1.
- **Timing-attack equalization on forgot-password** — the generic-message enumeration safety (D-09) IS implemented; sub-millisecond timing-side-channel hardening is NOT (RESEARCH A1, LOW risk for an internal tool).
- **Dark mode** — `CSS variables: yes` keeps the door open, but no toggle UI now (01-UI-SPEC).
- **Any catalog / borrowing / loan / notification feature** — Phases 2-6.
- **Production TLS / reverse proxy / secrets vault** — dev Compose only; `secure` cookie flag is environment-driven so prod can flip it on.

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions (it reuses `require_role`, `get_current_user`, the axios client, the Zustand store, and the Alembic pipeline as-is):

- **Phase 2 — Catalog Browse:** student can search/filter and view book + per-copy availability (new `Book`/`Copy` models + read endpoints + catalog UI).
- **Phase 3 — Catalog Management:** librarian CRUD on books and physical copies (write endpoints gated by `require_role("librarian")`).
- **Phase 4 — Borrow Request, Approval & Checkout:** request → approve → handover state machine with concurrency safety (`SELECT … FOR UPDATE`).
- **Phase 5 — Loan Tracking, Returns, Fines & Renewal:** active-loan views, returns, fixed fine policy, single renewal.
- **Phase 6 — Notifications:** approval/rejection/reminder/overdue emails via APScheduler + `notification_log` (not in-request BackgroundTasks for recurring scans).
