<!-- GSD:project-start source:PROJECT.md -->

## Project

**Library Management System**

A digital library management system for a university, replacing spreadsheet-based tracking. Students search the catalog and request books online; librarians approve requests, hand over books, record returns, and track who has what — all in one system instead of scattered spreadsheets.

**Core Value:** Librarians can always answer "who has this book and when is it due" without digging through spreadsheets — and students can find out if a book is available before walking to the library.

### Constraints

- **Tech stack**: Backend in Python (FastAPI), frontend in React, database PostgreSQL — user-specified, non-negotiable
- **Deployment**: Must run in Docker — user-specified for portability/ease of deployment
- **Scale**: Must handle whole-university load (thousands of books, large student body) — informs schema and query design from the start

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.136.x (pin `>=0.115,<0.137`) | Backend API framework | User-specified. Async-native, Pydantic-integrated, auto-generates OpenAPI docs — critical for a React frontend that needs a typed contract. Verified current release via PyPI. |
| Python | 3.12 or 3.13 | Runtime | 3.12/3.13 are the sweet spot in 2026: mature async perf improvements, broad library support. Avoid 3.13 only if a dependency (rare now) lags; otherwise prefer 3.13 for perf. |
| SQLAlchemy | 2.0.x (`>=2.0.30`) | ORM / database toolkit | The 2.0 async API (`AsyncSession`, `async_engine`) is the modern standard paired with FastAPI's async routes. Avoid SQLAlchemy 1.x — different (legacy) query API, no first-class async. |
| Alembic | 1.18.x | Database migrations | The de facto migration tool for SQLAlchemy. A library catalog (books, copies, loans, fines) WILL evolve its schema — migrations from day one are non-negotiable, not optional polish. |
| Pydantic | 2.x (`>=2.10`) | Data validation / schemas | Ships with FastAPI; v2's Rust core (`pydantic-core`) is materially faster than v1. Use `pydantic-settings` 2.x for typed environment config (`.env` → `Settings` class). |
| PostgreSQL | 16 or 17 | Database | User-specified. Use the official `postgres:16-alpine` or `postgres:17-alpine` Docker image. Strong relational fit for this domain: books↔copies↔loans↔fines is inherently relational with FK integrity (a copy can't be loaned to two students at once — exactly what RDBMS constraints are for). |
| React | 19.x | Frontend UI library | User-specified. React 19 is current stable; Create React App is officially deprecated (Feb 2025) — do not use it. |
| Vite | 6.x or 7.x (latest 8.x is very new — prefer 6/7 for stability) | Frontend build tool / dev server | The standard React tooling in 2026, replacing CRA entirely. Fast HMR, native TS support, minimal config. Note: Vite 8 (Rolldown-based) is bleeding-edge as of mid-2026 — prefer Vite 6/7 unless you want to be an early adopter of the new Rust bundler. |
| TypeScript | 5.x | Frontend language | Not optional for a project this size with role-based UI branching (student vs. librarian views) and an API contract to keep in sync. Generate types from FastAPI's OpenAPI schema (see `openapi-typescript` below) to keep frontend/backend in lockstep. |
| Docker + Docker Compose | Compose v2 (`docker compose`, not `docker-compose`) | Containerization & orchestration | User-specified. Compose is the standard for multi-service local/dev orchestration (web + db + mail-catcher). For production, the same Compose file (or a derived one) can run on a single VM — appropriate for a university-scale deployment that doesn't need Kubernetes. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `uvicorn[standard]` | 0.34+ | ASGI server | Run FastAPI in Docker. Use `uvicorn` directly (with `--workers`) rather than gunicorn+uvicorn workers for simplicity at this scale; revisit only if you need process-level fault isolation. |
| `asyncpg` | 0.30+ | Async PostgreSQL driver | Pair with SQLAlchemy's async engine (`postgresql+asyncpg://...`). Significantly faster than `psycopg2` for async workloads — the standard async driver choice for FastAPI+Postgres. |
| `psycopg[binary]` | 3.2+ | Sync PostgreSQL driver | Only needed for Alembic migrations if you keep them sync (common pattern: async app, sync Alembic env using `psycopg`). Alternatively run Alembic in async mode with `asyncpg` — more setup, marginal benefit at this scale. **Recommendation: sync Alembic + `psycopg`, async app + `asyncpg`** — simplest, most-documented combination. |
| `pydantic-settings` | 2.6+ | Typed environment configuration | Load `DATABASE_URL`, `SECRET_KEY`, SMTP settings, etc. from environment/`.env` into a validated `Settings` class. Standard FastAPI config pattern — avoids scattered `os.environ.get()` calls. |
| `pwdlib[argon2]` | 0.2+ | Password hashing | **Use this, not `passlib`.** `passlib` is unmaintained and breaks on Python 3.13 (relies on the removed `crypt` module per PEP 594). FastAPI's own docs are migrating examples to `pwdlib` + Argon2 (see fastapi/fastapi#13917). Argon2 is the current recommended algorithm — GPU-crack-resistant, memory-hard. |
| `pyjwt` | 2.9+ | JWT encode/decode | **Use this, not `python-jose`.** `python-jose` has had no release since 2021 and has known CVEs in its ecosystem; `pyjwt` is actively maintained with a simpler, more focused API. Use for issuing/verifying access (and optionally refresh) tokens. |
| `python-multipart` | 0.0.12+ | Form data parsing | Required by FastAPI for OAuth2 password-flow login forms (`OAuth2PasswordRequestForm`) and any file upload (e.g., book cover images, if added later). |
| `fastapi-mail` | 1.4+ | Email sending | Async, Jinja2-templated email (approval notices, due-date reminders, overdue alerts — exactly this domain's needs). Built on `aiosmtplib`. Pairs cleanly with FastAPI's `BackgroundTasks` for fire-and-forget sending without blocking the request. |
| `jinja2` | 3.1+ | Email/HTML templating | Dependency of `fastapi-mail` for templated emails; also useful if you ever need server-rendered fragments. |
| `apscheduler` | 3.10+ (or `celery` + `celery-beat` — see note) | Scheduled jobs | **This domain needs scheduled jobs**: due-date reminder emails and overdue-fine calculation must run on a recurring basis (e.g., nightly), not just react to user requests. `APScheduler` running inside the FastAPI app (or a small sidecar worker) is the lightweight choice for this scale. Reach for Celery + Redis only if you anticipate heavy async workloads beyond email/cron — likely overkill for v1. |
| `httpx` | 0.27+ | Async HTTP client | Use in tests (`AsyncClient` against the FastAPI app) and for any outbound API calls. The modern replacement for `requests` in async contexts; FastAPI's own test docs recommend it. |
| `pytest` + `pytest-asyncio` | pytest 8.x / pytest-asyncio 0.24+ | Backend testing | Standard Python testing stack. `pytest-asyncio` for testing async route handlers and DB session fixtures. |
| `factory-boy` or plain fixtures | latest | Test data generation | Generating realistic catalog/loan test data (books, copies, students, loans in various states) — useful given the domain's many state combinations (available/requested/loaned/overdue/returned). |
| Alembic | (see core) | — | — |
| `python-dotenv` | bundled via `pydantic-settings` | — | Not needed standalone; `pydantic-settings` handles `.env` loading. |

### Frontend Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@tanstack/react-query` | 5.x | Server-state management (data fetching, caching, mutations) | **The standard for talking to a FastAPI backend from React in 2026.** Handles loading/error/stale states, cache invalidation after mutations (e.g., re-fetch catalog after a librarian edits a book), and background refetch — replaces hand-rolled `useEffect` fetch logic. |
| `zustand` | 5.x | Client-state management (UI state only) | Use for ephemeral UI state (modal open/closed, selected filters, sidebar state) — **not** for server data (that's React Query's job). Minimal boilerplate vs. Redux; the 2026 default for lightweight client state. |
| `react-router-dom` | 7.x | Routing | Mature, well-documented, large ecosystem — appropriate default for a CRUD-heavy app with role-gated routes (student routes vs. librarian routes). `@tanstack/react-router` is a strong type-safe alternative if the team wants stricter route-param typing, but adds a steeper learning curve; React Router 7 is the safer, more conventional choole here. |
| `react-hook-form` | 7.x | Form handling | Standard for forms with validation (book entry forms, registration, login, request forms). Minimal re-renders, good DX. |
| `zod` | 4.x | Schema validation | Pairs with `react-hook-form` (`@hookform/resolvers/zod`) for client-side validation. Optionally generate Zod schemas from the OpenAPI spec to mirror backend Pydantic validation — keeps client/server validation rules consistent. |
| `axios` | 1.x | HTTP client | Use as the fetcher under React Query. Handles request/response interceptors well (e.g., attaching JWT to every request, handling 401 → redirect to login centrally) — cleaner than raw `fetch` for an app with auth on every call. |
| `tailwindcss` | 4.x | Styling | Utility-first CSS; the dominant choice paired with shadcn/ui. Fast to build consistent UI for catalog grids, tables, forms. |
| `shadcn/ui` | latest (CLI-installed, not an npm dependency) | UI component primitives | Accessible, unstyled-then-themed components (tables, dialogs, dropdowns, forms) copied into your codebase rather than installed as an opaque dependency — you own and can modify the code. Has overtaken Material UI as the 2025/2026 default for new React projects. Strong fit for data-heavy admin-style UIs (librarian dashboards, loan tables). |
| `openapi-typescript` + `openapi-fetch` | latest | Typed API client generation | Generates TypeScript types directly from FastAPI's `/openapi.json`. Keeps frontend types in sync with backend Pydantic schemas automatically — eliminates a whole class of "frontend expects a field the backend renamed" bugs. Re-run on backend schema changes (can be a Make/npm script). |
| `vitest` + `@testing-library/react` | vitest 2.x / RTL 16.x | Frontend testing | Vite-native test runner (shares config with Vite, fast). RTL for component/interaction testing. The standard pairing for Vite-based React projects, replacing Jest. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `ruff` | Python linting + formatting | Replaces `flake8` + `black` + `isort` in one fast Rust-based tool. The 2025/2026 Python tooling default. Configure in `pyproject.toml`. |
| `mypy` (optional but recommended) | Static type checking | Pairs well with Pydantic's type-driven design; catches schema/type drift early. Run in CI, not necessarily blocking local dev. |
| `uv` | Python package/dependency management | Significantly faster than `pip`/`poetry` for installs and lockfile resolution; increasingly the 2026 default for new Python projects (used in several current FastAPI boilerplates researched, e.g. `ferdinandbracho/bp_fastAPI-sqlalchemy-alembic-docker_uv`). Generates a lockfile for reproducible Docker builds. Alternative: Poetry — fine if the team already knows it, but `uv` is faster and simpler. |
| `pre-commit` | Git hooks | Run `ruff`, `mypy`, and frontend lint/format checks before commit. Standard practice to keep a multi-stack repo consistent. |
| ESLint + Prettier (or Biome) | Frontend linting/formatting | `Biome` is a faster Rust-based alternative gaining traction (analogous to `ruff` for JS/TS) — either is fine; ESLint+Prettier remains the safer, more battle-tested default for a team unfamiliar with Biome. |
| `Mailpit` (Docker image `axllent/mailpit`) | Dev/test email catcher | **Add this to `docker-compose.yml` for local dev.** Captures all outgoing SMTP mail in a web UI (`localhost:8025`) instead of sending real emails — essential for testing the approval/reminder/overdue email flows without spamming real student inboxes. Successor to MailHog (which is now unmaintained); Mailpit is the current standard. |
| Docker Compose Watch (`develop.watch`) | Live-reload in containers | Compose v2's built-in file-sync/rebuild-on-change — avoids needing separate volume-mount + nodemon/uvicorn-reload juggling tricks. Use for both the FastAPI (`--reload`) and Vite dev servers inside Compose. |

## Installation

# --- Backend (using uv) ---

# --- Frontend (using Vite + React + TS template) ---

# shadcn/ui is added via its CLI (copies component source into your repo):

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `pyjwt` + custom auth dependency | `fastapi-users` | If you want a fully batteries-included user-management package (registration, password reset, email verification flows pre-built). For this project's two simple roles (student/librarian) and explicitly-scoped-out SSO, a custom ~150-line auth module is easier to understand, debug, and extend than learning `fastapi-users`' abstractions. Reconsider `fastapi-users` only if auth requirements grow significantly (social login, multi-tenant, etc.). |
| `asyncpg` (async) + `psycopg` (sync, for Alembic) | Fully async Alembic with `asyncpg` | If the team is comfortable with async migration env setup and wants one driver only. Adds boilerplate (`run_sync` wrappers in `env.py`) for marginal benefit at this scale — the hybrid sync-Alembic/async-app pattern is the most common, most-documented approach in current FastAPI+Postgres boilerplates researched. |
| `APScheduler` for cron-like jobs | Celery + Redis/RabbitMQ + Celery Beat | If the system grows to need heavy background processing (bulk imports, report generation, high email volume) beyond "send a few emails nightly." Celery adds operational complexity (broker, worker processes, monitoring) that is unjustified for v1's modest scheduled-job needs (overdue checks, reminders). |
| `react-router-dom` v7 | `@tanstack/react-router` | If the team values fully type-safe route params/search-params and is willing to invest in a steeper learning curve. React Router remains the more conventional, widely-documented choice — lower risk for a team that may include less frontend-specialized devs (librarian-facing CRUD apps tend to be maintained by generalist teams). |
| `shadcn/ui` + Tailwind | Material UI (MUI), Ant Design, Chakra | If the team strongly prefers a traditional installed component library with less setup. shadcn/ui has overtaken MUI in 2025/2026 popularity and gives more design control, but MUI/Ant remain perfectly viable, especially for admin-heavy UIs (Ant Design in particular is strong for data tables — a good fit for librarian dashboards if the team prefers it). |
| Single Docker Compose stack (web + db + mailpit) | Separate dev/prod Compose files, or Kubernetes | Kubernetes is overkill for a single-university deployment. A Compose-based deployment (possibly with a reverse proxy like Caddy/Traefik for TLS) is the right-sized choice; revisit only if the system needs to scale across multiple institutions/regions. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Create React App (`create-react-app`) | Officially deprecated by the React team (Feb 2025); no longer maintained, slow builds, outdated tooling. | Vite (`npm create vite@latest -- --template react-ts`) |
| `passlib` | Unmaintained; depends on Python's `crypt` module, which is removed in Python 3.13 (PEP 594) — will hard-break on upgrade. FastAPI's own docs are actively migrating away from it. | `pwdlib[argon2]` |
| `python-jose` | No releases since 2021; maintenance concerns and known CVE history in the broader `jose`-for-Python ecosystem. | `pyjwt` |
| SQLAlchemy 1.x query style (`session.query(...)`) | Legacy API; no native async support; FastAPI's official docs and current boilerplates use the 2.0 `select()`/`AsyncSession` style exclusively. | SQLAlchemy 2.0 async ORM (`AsyncSession`, `select(Model)`) |
| MailHog for dev email capture | Project is unmaintained/archived (no commits in years); known to have minor security issues left unpatched. | Mailpit (`axllent/mailpit`) — actively maintained drop-in successor with a near-identical UI |
| Storing plaintext SMTP credentials / `SECRET_KEY` in `docker-compose.yml` directly | Leaks secrets into version control and shell history; a common rookie mistake that causes painful cleanup later. | `.env` files (gitignored) loaded via `pydantic-settings` + Compose's `env_file:` directive; use Docker secrets or a vault for actual production deployment |
| Building the email/reminder system as "send synchronously inside the request handler" | Blocks the HTTP response on SMTP round-trip latency; a slow mail server makes "approve request" feel broken to the librarian. | FastAPI `BackgroundTasks` for one-off sends (approval emails); `APScheduler` for recurring batch jobs (nightly due-date/overdue scans) |
| Polling the database from the frontend with `setInterval` + raw `fetch` | Reinvents caching/loading/error state badly; causes unnecessary load and jank. | TanStack React Query with `refetchInterval` where live-ish data is genuinely needed (e.g., catalog availability) |

## Stack Patterns by Variant

- Use a single `users` table with a `role` enum column (`student` | `librarian`), not separate tables per role — simplest schema that satisfies "no admin role separate from librarians" per the project's scope.
- Issue short-lived JWT access tokens (`pyjwt`) + a longer-lived refresh token (httpOnly cookie or rotated refresh token in DB) — avoids the common pitfall of long-lived access tokens that can't be revoked.
- Gate routes by role via a FastAPI dependency (`require_role("librarian")`) — keep authorization logic in dependencies, not scattered in route bodies.
- Model `Book` (catalog metadata) separately from `Copy` (physical instances with status: available/requested/loaned/lost) — a classic library-domain pattern. This is what makes "who has this book and when is it due" answerable: you query `Copy` + `Loan`, not `Book`.
- Model the request→approval→handoff→return lifecycle as an explicit `Loan` (or `BorrowRequest`) state machine with a status enum (`requested`, `approved`, `rejected`, `active`, `returned`, `overdue`) and timestamps for each transition — gives you a clean audit trail "for free" and makes fine calculation (return date vs. due date) a pure function of stored data.
- Use PostgreSQL `CHECK` constraints and unique partial indexes (e.g., "a `Copy` can have at most one active `Loan`") to enforce invariants at the DB layer — don't rely solely on application logic, which is exactly where double-booking bugs creep in under concurrent requests.
- Add indexes on the columns the catalog search will filter/sort by from day one: `title`, `author`, `isbn`, `category`, and a composite/availability index on `Copy.status`. Consider PostgreSQL full-text search (`tsvector`/`pg_trgm`) for title/author search — avoids needing a separate search engine (Elasticsearch/Meilisearch) at this scale.
- Use SQLAlchemy's async session with connection pooling (`pool_size`, `max_overflow` tuned to expected concurrency) — default pool sizes are conservative and may need adjustment for "whole university" concurrent load.
- Paginate all list endpoints (catalog browse, loan history, librarian dashboards) from the start — "thousands of books" returned unpaginated will be the first performance complaint.
- Single `docker-compose.yml` with services: `db` (postgres:16-alpine), `backend` (FastAPI + `--reload`, volume-mounted source), `frontend` (Vite dev server), `mailpit` (SMTP catcher + web UI on :8025). Add a `db-init`/migration step (`alembic upgrade head`) as a one-shot service or backend entrypoint script.
- Use Compose health checks on `db` (`pg_isready`) so `backend` waits for Postgres to be ready — a very common source of "works on my machine, fails in CI/fresh clone" bugs.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.115+ | Pydantic 2.x, Python 3.9–3.13 | FastAPI 0.115+ has dropped meaningful Pydantic v1 support paths in practice; always pair with Pydantic 2.x. |
| SQLAlchemy 2.0.x | `asyncpg` 0.29+, `psycopg` 3.x, Alembic 1.13+ | Alembic 1.13+ has first-class support for SQLAlchemy 2.0's async engine patterns in `env.py` templates. |
| `pwdlib[argon2]` | Python 3.9+ | No `crypt`-module dependency — safe across the Python 3.13 boundary where `passlib` breaks. |
| React 19 | Vite 5/6/7, TypeScript 5.x, React Router 7, TanStack Query 5 | React 19's new features (Actions, `use()`) are optional — existing patterns from React 18 still work, so no forced rewrite of familiar idioms. |
| Tailwind CSS 4.x | Vite via `@tailwindcss/vite` plugin | Tailwind 4 changed its config model (CSS-based config, no `tailwind.config.js` required) — follow the v4 setup docs, not older v3 tutorials, to avoid config-format confusion. |
| `openapi-typescript` | FastAPI's generated `/openapi.json` (OpenAPI 3.1) | FastAPI 0.100+ generates OpenAPI 3.1 schemas; ensure `openapi-typescript` version supports 3.1 (current versions do). |

## Sources

- Context7 `/fastapi/fastapi` — async SQLAlchemy session dependency patterns, `dependencies-with-yield` examples (HIGH confidence, official docs)
- Context7 library search — confirmed current FastAPI boilerplate ecosystem (`benavlabs/FastAPI-boilerplate`: Pydantic v2 + SQLAlchemy 2.0 + Postgres + Docker; `ferdinandbracho/...uv` template) (MEDIUM-HIGH, community-maintained but high-reputation)
- PyPI registry queries (live, 2026-06-08) — verified current stable versions for FastAPI (0.136.x), SQLAlchemy (2.0.50), Alembic (1.18.x), Pydantic (2.13.x), pwdlib (0.3.x), pyjwt (2.13.x), fastapi-mail (1.6.x), uvicorn, asyncpg, psycopg, pytest, httpx, ruff (HIGH — direct registry data)
- npm registry queries (live, 2026-06-08) — verified current stable versions for React (19.2.x), Vite (8.x, with note that 6/7 are the stable mainstream choice), TanStack Query (5.101.x), React Router (7.17.x), Zustand (5.0.x), Tailwind (4.3.x), TypeScript (6.0.x), React Hook Form, Zod, Vitest (HIGH — direct registry data)
- [fastapi/fastapi PR #13917](https://github.com/fastapi/fastapi/pull/13917) — official FastAPI docs migration from `passlib` to `pwdlib`+Argon2 (HIGH, official repo)
- [fastapi/fastapi Discussion #11773](https://github.com/fastapi/fastapi/discussions/11773) — community/maintainer consensus that `passlib` is unmaintained (MEDIUM-HIGH)
- [frankie567/pwdlib Discussion #1](https://github.com/frankie567/pwdlib/discussions/1) — rationale for `pwdlib` as modern password-hash helper (MEDIUM, author's own announcement)
- [fastapi-users/fastapi-users Discussion #1372 (v13.0.0 release)](https://github.com/fastapi-users/fastapi-users/discussions/1372) — confirms ecosystem-wide adoption of `pwdlib`+Argon2 (MEDIUM)
- [k4black/fastapi-jwt Issue #40](https://github.com/k4black/fastapi-jwt/issues/40) — community discussion on `python-jose` maintenance concerns vs. alternatives (MEDIUM, single-source corroborated by general `pyjwt` adoption trend)
- WebSearch: "FastAPI React PostgreSQL Docker boilerplate" — cross-referenced multiple current (2024-2025-dated) boilerplate repos confirming SQLAlchemy 2.0 async + Alembic + Docker as the standard combination (MEDIUM, multiple independent sources agree)
- WebSearch: Mailpit vs MailHog — Mailpit (`axllent/mailpit`) confirmed as the actively-maintained successor to the now-stale MailHog project (MEDIUM, cross-referenced GitHub repo activity)
- WebSearch: "React 2026 standard stack" — multiple sources (thetshaped.dev, onebyzero.substack.com, patterns.dev) converge on Vite + TanStack Query + Zustand + shadcn/ui + Tailwind as the 2026 default React stack, CRA deprecation confirmed (MEDIUM-HIGH, strong cross-source agreement)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
