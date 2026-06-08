# Architecture Research

**Domain:** University library management system (catalog/inventory + role-based borrow-request workflow + loan/fine tracking + email notifications)
**Researched:** 2026-06-08
**Confidence:** HIGH (component structure, FastAPI/React conventions) / MEDIUM (state machine and notification patterns — synthesized from general workflow-engine and FastAPI background-task guidance, not library-specific case studies)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT (React SPA)                           │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │  Catalog   │  │   Auth /   │  │  My Loans / │  │   Librarian   │  │
│  │  Browse    │  │  Account   │  │  Requests   │  │   Dashboard   │  │
│  │  (student) │  │            │  │  (student)  │  │ (catalog,     │  │
│  │            │  │            │  │             │  │  approvals,   │  │
│  │            │  │            │  │             │  │  checkout/    │  │
│  │            │  │            │  │             │  │  returns)     │  │
│  └─────┬──────┘  └─────┬──────┘  └──────┬──────┘  └───────┬───────┘  │
│        │               │                │                 │          │
│        └───────────────┴────────────────┴─────────────────┘          │
│                          TanStack Query + fetch client                │
├──────────────────────────────────────────────────────────────────────┤
│                      HTTP/JSON (REST, JWT bearer)                     │
├──────────────────────────────────────────────────────────────────────┤
│                       API LAYER (FastAPI routers)                     │
│  /auth   /books   /copies   /requests   /loans   /fines   /users     │
├──────────────────────────────────────────────────────────────────────┤
│                    SERVICE LAYER (business logic)                     │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌─────────────────┐ │
│  │  Catalog   │ │   Auth /   │ │   Borrow     │ │  Loan / Fine    │ │
│  │  Service   │ │   User     │ │   Workflow   │ │   Service       │ │
│  │            │ │   Service  │ │   Service    │ │  (checkout,     │ │
│  │ (search,   │ │ (register, │ │ (state       │ │   return, fine  │ │
│  │  CRUD,     │ │  login,    │ │  machine:    │ │   calc)         │ │
│  │  copy mgmt)│ │  JWT, RBAC)│ │  request →   │ │                 │ │
│  │            │ │            │ │  approve/    │ │                 │ │
│  │            │ │            │ │  reject →    │ │                 │ │
│  │            │ │            │ │  checkout)   │ │                 │ │
│  └─────┬──────┘ └─────┬──────┘ └──────┬───────┘ └────────┬────────┘ │
│        │              │               │                  │           │
│        └──────────────┴───────┬───────┴──────────────────┘           │
│                                │                                       │
│                       ┌────────▼─────────┐                            │
│                       │  Notification    │                            │
│                       │  Service         │── triggers on state ──────┤
│                       │ (email queue,    │   transitions / due-date  │
│                       │  templates)      │   crons                   │
│                       └────────┬─────────┘                            │
├────────────────────────────────┼──────────────────────────────────────┤
│                       REPOSITORY / ORM LAYER                          │
│              SQLAlchemy models + sessions (async)                     │
├────────────────────────────────┼──────────────────────────────────────┤
│         PostgreSQL              │            SMTP / Email Provider     │
│  (books, copies, users,         │         (transactional email API,    │
│   requests, loans, fines,       └────────►  e.g. SES/Mailgun/SMTP      │
│   notification_log)                         relay in dev = MailHog)    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Catalog/Inventory Service | Book metadata CRUD, copy-level inventory (each physical copy has its own status), search/filter/availability queries | SQLAlchemy models `Book` (1) ↔ `BookCopy` (many); full-text/trigram search on title/author; computed "available count" via copy status, not a cached counter |
| Auth/User Service | Registration, login, password hashing, JWT issuance/refresh, role resolution (student/librarian) | `fastapi-users` or hand-rolled with `passlib`/`python-jose`; role stored on `User` row; dependency-injected `get_current_user` / `require_role()` guards |
| Borrow Workflow Service | Owns the request lifecycle state machine; validates transitions; enforces business rules (max books, availability) at transition time | Explicit `BorrowRequest` table with `status` enum column + `status_history`/audit table; service-layer functions per transition (`submit`, `approve`, `reject`, `checkout`, `return`) that wrap DB writes in a transaction and call the notification service |
| Loan/Fine Service | Tracks active loans, due dates, returns, computes overdue fines on return (or via scheduled job for "overdue" status) | `Loan` table derived from an approved+checked-out request; fine calculation as a pure function (days late × rate, capped); `Fine` table linked to loan |
| Notification Service | Sends transactional emails on workflow events (approval, rejection, due-date reminder, overdue) and logs what was sent | Thin wrapper around an email-sending function, invoked via FastAPI `BackgroundTasks` initially; templated messages (Jinja2 strings); `notification_log` table to prevent duplicate sends and support debugging |
| Scheduler (cron-like) | Periodic jobs: due-date reminders (N days before due), overdue detection/fine accrual | APScheduler running in the same container, or a simple periodic task — NOT Celery Beat at this scale |

## Recommended Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, router registration, middleware
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings, env vars)
│   │   ├── security.py          # JWT, password hashing
│   │   └── database.py          # Async engine, session factory, Base
│   ├── models/                  # SQLAlchemy ORM models (one file per aggregate)
│   │   ├── user.py
│   │   ├── book.py              # Book + BookCopy
│   │   ├── borrow_request.py    # BorrowRequest + status enum + history
│   │   ├── loan.py
│   │   └── fine.py
│   ├── schemas/                 # Pydantic request/response DTOs, mirrors models/
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── borrow_request.py
│   │   └── loan.py
│   ├── routers/                 # Thin HTTP layer — one file per resource
│   │   ├── auth.py
│   │   ├── books.py
│   │   ├── requests.py
│   │   ├── loans.py
│   │   └── fines.py
│   ├── services/                # Business logic, the heart of the app
│   │   ├── catalog_service.py
│   │   ├── auth_service.py
│   │   ├── borrow_workflow_service.py   # state machine lives here
│   │   ├── loan_fine_service.py
│   │   └── notification_service.py
│   ├── repositories/            # (optional for v1) DB query layer if services grow complex
│   ├── notifications/
│   │   ├── templates/           # email templates (Jinja2 strings or .html)
│   │   └── email_client.py      # SMTP/provider adapter
│   ├── scheduler/
│   │   └── jobs.py              # due-date reminder + overdue scan jobs
│   └── dependencies.py          # get_db, get_current_user, require_role
├── alembic/                     # migrations
├── tests/
│   ├── unit/                    # service-layer + state machine tests (no DB)
│   └── integration/             # router + DB tests (testcontainers or pytest-postgresql)
└── docker-compose.yml

frontend/
├── src/
│   ├── api/                     # generated/typed client + fetch wrappers
│   ├── features/                # feature-folder organization (not by layer)
│   │   ├── catalog/             # browse/search components, hooks, queries
│   │   ├── auth/                # login/register forms, auth context
│   │   ├── requests/            # student: my requests, request button/modal
│   │   ├── loans/               # student: my loans, due dates
│   │   └── librarian/           # catalog mgmt, approval queue, checkout/return UI
│   ├── components/              # shared UI primitives (Button, Table, Modal…)
│   ├── routes/ or pages/        # route-level composition (React Router)
│   ├── lib/                     # query client, auth token storage, utils
│   └── App.tsx
└── vite.config.ts
```

### Structure Rationale

- **Backend: layered (router → service → ORM), NOT repository-pattern-heavy for v1.** With one DB and a small team, a repository layer is an extra abstraction that mostly adds indirection. Put query logic directly in services; extract a repository layer later only if services get noisy or you need to swap persistence (unlikely here). [Source: layered architecture is described as "essential" but the repository pattern is explicitly called optional/incremental — refactor into it only when routers exceed a few hundred lines.]
- **Models grouped by aggregate, not by table.** `Book`+`BookCopy` live together because they're always reasoned about as a unit; same for `BorrowRequest`+its status history.
- **`borrow_workflow_service.py` is the single owner of state transitions.** This is the most important boundary in the whole system — every status change (submit/approve/reject/checkout/return) must go through this module so that validation, history logging, and notification triggers can never be bypassed by a router calling the ORM directly.
- **Frontend organized by feature, not by type** (no global `hooks/`, `components/` dumping ground for feature-specific code). This mirrors how the backend is organized by domain (catalog, requests, loans) and keeps a vertical slice's frontend + backend code conceptually aligned, which matters because you're building end-to-end vertical slices. [Source: "Group by feature/domain often works well in FastAPI... splitting by layers results in jumping across folders to understand a single feature" — same logic applies to React.]
- **`notifications/` and `scheduler/` are separate from `services/`** because they're cross-cutting infrastructure (could be swapped — e.g., SMTP → SES, BackgroundTasks → Celery — without touching business logic). Services call an injected `NotificationService` interface; they don't know how email is actually sent.

## Architectural Patterns

### Pattern 1: Explicit State Machine for Borrow Requests

**What:** Model the request lifecycle as an explicit enum with a small, closed set of valid transitions, enforced in one service module — not scattered `if status == "approved"` checks across routers.

**States:** `pending → approved → checked_out → returned` (terminal), with `pending → rejected` (terminal) as the alternate branch. Optionally `approved → cancelled` if students can withdraw a request before pickup.

**When to use:** Any time a domain entity has a lifecycle with rules about what can happen next (this is exactly the request → approval → handoff → return flow described in the project).

**Trade-offs:**
- Pro: transitions are testable in isolation (pure function: `(current_status, action, actor_role) → new_status | error`), impossible to skip steps, audit trail falls out naturally.
- Con: more upfront modeling than just mutating a status string; requires discipline that *all* status changes go through the service, not direct ORM updates.

**Example:**
```python
# services/borrow_workflow_service.py
class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHECKED_OUT = "checked_out"
    RETURNED = "returned"
    CANCELLED = "cancelled"

VALID_TRANSITIONS = {
    RequestStatus.PENDING:    {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED},
    RequestStatus.APPROVED:   {RequestStatus.CHECKED_OUT, RequestStatus.CANCELLED},
    RequestStatus.CHECKED_OUT:{RequestStatus.RETURNED},
}

async def transition(db, request: BorrowRequest, to: RequestStatus, actor: User) -> BorrowRequest:
    if to not in VALID_TRANSITIONS.get(request.status, set()):
        raise InvalidTransitionError(request.status, to)
    # role checks (e.g., only librarian can approve), side effects (decrement available copies,
    # create Loan row on checkout), history row, then commit
    ...
    await notification_service.notify_status_change(request, to)
    return request
```

### Pattern 2: Copy-Level Inventory with Status, Not a Cached Counter

**What:** Track availability by giving each physical `BookCopy` a status (`available`, `requested`/`reserved`, `checked_out`, `lost`/`retired`) rather than maintaining a denormalized `available_count` integer on `Book`.

**When to use:** Whenever "is this in stock" must stay consistent with "who has which physical item" — exactly this domain, where the librarian needs to answer "who has this book."

**Trade-offs:**
- Pro: availability is always derivable by querying copy status (`SELECT count(*) FROM book_copies WHERE book_id=? AND status='available'`), no risk of counter drift; also gives you "which exact copy did this student take" for free.
- Con: slightly more complex queries than reading an integer column; needs an index on `(book_id, status)` for catalog browse performance at scale (thousands of books).
- **Concurrency note:** Two students requesting the "last available copy" simultaneously is a real race. Handle it at approval/checkout time (not request time) with a transaction that re-checks copy availability and uses `SELECT ... FOR UPDATE` or an optimistic check-and-update — since the actual handoff is physical and librarian-mediated, the request itself doesn't need to lock a copy; only the *approval* (which should pick and reserve a specific copy) does.

### Pattern 3: Notification as a Side Effect of State Transitions, Decoupled via a Thin Service Interface

**What:** The workflow/loan services call `notification_service.notify_x(...)` after a successful DB commit; the notification service decides *how* to send (BackgroundTasks now, queue later) and logs what was sent.

**When to use:** Any transactional email tied to domain events (approval, rejection, due-date reminder, overdue notice) — exactly the three notification types in scope.

**Trade-offs:**
- Pro: business logic stays testable without mocking SMTP; swapping BackgroundTasks → Celery later requires changing only `notification_service.py`, not callers.
- Con: `BackgroundTasks` (FastAPI's built-in) runs in-process and is lost on crash/restart — acceptable for v1 at university scale, but means a crashed server can silently drop a queued email. Mitigate with a `notification_log` table written *before* the send attempt, so a periodic job can detect and retry "logged but not sent" rows. [Source: FastAPI docs and multiple comparisons converge — start with `BackgroundTasks` for "quick tasks... sending emails," graduate to Celery only if you need persistence/retries/horizontal scale, which this project does not at its stated scale.]

**Example:**
```python
# routers/requests.py
@router.post("/{id}/approve")
async def approve_request(id: int, current_user=Depends(require_role("librarian")),
                          background_tasks: BackgroundTasks, db=Depends(get_db)):
    request = await borrow_workflow_service.transition(db, request, RequestStatus.APPROVED, current_user)
    background_tasks.add_task(notification_service.send_approval_email, request.student_email, request)
    return request
```

## Data Flow

### Request Flow (Borrow → Approval → Checkout → Return → Fine)

```
1. SUBMIT
[Student clicks "Request"] → POST /requests
    → borrow_workflow_service.submit()
        - validates: book has an available copy, student under max-books limit
        - creates BorrowRequest{status=pending}
    → notification_service.notify_submitted()  (optional confirmation email)
    → 201 response → student's "My Requests" list updates (TanStack Query invalidate)

2. APPROVE / REJECT
[Librarian opens approval queue] → GET /requests?status=pending
[Librarian clicks Approve] → POST /requests/{id}/approve
    → borrow_workflow_service.transition(pending → approved)
        - selects & reserves a specific available BookCopy (status → reserved)
        - writes status_history row
    → notification_service.notify_approved()  → email queued via BackgroundTasks
    → student sees status change to "Approved — pick up at the desk"

3. CHECKOUT (physical handoff recorded)
[Librarian marks handed over] → POST /requests/{id}/checkout
    → borrow_workflow_service.transition(approved → checked_out)
        - BookCopy.status → checked_out
        - creates Loan{borrow_request_id, copy_id, checkout_date, due_date = checkout_date + fixed_period}
    → notification_service.notify_checkout()  (optional — due-date confirmation)

4. ONGOING — Reminders & Overdue Detection (scheduled job, not user-triggered)
[Scheduler runs daily] → loan_fine_service.scan_due_dates()
    - loans due in N days → notify_due_soon()
    - loans past due_date and not returned → mark overdue (status flag or computed),
      → notify_overdue()
    (writes to notification_log to avoid duplicate sends per loan per day)

5. RETURN & FINE CALCULATION
[Librarian marks returned] → POST /loans/{id}/return
    → loan_fine_service.process_return()
        - Loan.return_date = today; BookCopy.status → available
        - if return_date > due_date: fine = (days_late × daily_rate), capped
        - creates Fine{loan_id, amount, reason} if applicable
    → borrow_workflow_service.transition(checked_out → returned)
    → notification_service.notify_returned() / notify_fine_issued()
    → student's loan list & librarian's "who has this book" view both refresh
```

### State Management (Frontend)

```
Server state (books, requests, loans, fines)
    ↓ (TanStack Query — cache, refetch, invalidation)
[Feature components] ←→ [useQuery / useMutation hooks in features/*/queries.ts]
    ↓ (mutation success → invalidate related query keys, e.g. approving a
       request invalidates both the librarian queue AND the student's loan list)
[Auth/session state] → React Context or lightweight store (Zustand) — token + role only,
                        NOT server data (avoid duplicating what TanStack Query already caches)
```

### Key Data Flows

1. **Catalog → Request:** Browsing reads `Book`+`BookCopy` aggregated availability; submitting a request reads current availability again at write time (don't trust stale client-side state) and writes a new `BorrowRequest` row — the read-then-write must happen inside the service, server-side.
2. **Workflow → Notification (fire-and-forget but logged):** Every status transition that matters to a human (approved, rejected, overdue) flows through `notification_service`, which both sends the email (async/background) and writes a `notification_log` row in the same DB transaction as the status change — so "did we tell the student?" is always answerable even if the email itself fails.
3. **Loan → Fine (derived, not independently entered):** Fines are never created directly by a librarian; they are *computed* by the loan service as a pure function of `(due_date, return_date, daily_rate)` at the moment of return (or by the scheduled overdue scan). This keeps "who owes what and why" auditable and prevents manual entry drift.
4. **Cross-cutting "who has this book" query:** This is the core value statement from PROJECT.md — it must be answerable with a single efficient query joining `BookCopy → Loan (active) → User`, which argues strongly for the copy-level status model over a counter.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Pilot / single department (hundreds of users, low thousands of books) | Single FastAPI container + single Postgres instance + BackgroundTasks for email. Everything in one docker-compose stack. This is sufficient — don't add Celery/Redis/queues preemptively. |
| Whole-university (thousands of books, thousands of students) — the stated target | Add DB indexes on hot paths (`book_copies(book_id, status)`, `borrow_requests(status, student_id)`, `loans(due_date)` for the scheduler scan); add pagination everywhere on catalog/list endpoints; consider read-replica only if reporting queries start contending with transactional load (unlikely at this size). BackgroundTasks remains fine for email volume in this range (low hundreds/day). |
| Hypothetical multi-campus / 100k+ users (explicitly out of current scope) | This is where you'd introduce Celery + Redis for guaranteed-delivery email, partition/shard catalog data, and consider splitting notification/scheduler into a separate service. Not relevant to v1 — noting only so the team doesn't over-build now. |

### Scaling Priorities

1. **First likely bottleneck: catalog search/browse at "thousands of books."** Mitigate with proper indexing (btree on title/author/ISBN, `pg_trgm` for fuzzy search if needed) and pagination from day one — this is cheap to do correctly upfront and expensive to retrofit.
2. **Second: the approval queue and "who has this book" queries as loan volume grows.** Mitigate with indexes on `status` columns and `due_date`, and by ensuring the scheduled overdue/reminder scan is a single indexed query, not N+1 per loan.

## Anti-Patterns

### Anti-Pattern 1: Letting Routers Mutate Status Directly

**What people do:** A router handler does `request.status = "approved"; db.commit()` directly, maybe in two or three different endpoints, with slightly different side-effect logic each time.
**Why it's wrong:** Status changes stop being auditable or testable as a unit; it becomes possible to skip steps (e.g., go straight from `pending` to `checked_out`), forget to decrement copy availability, or forget to trigger a notification — and these bugs are exactly the kind that erode trust in "who has this book."
**Instead:** All status changes go through `borrow_workflow_service.transition()`, which is the single place that validates the transition, applies side effects (copy reservation, loan creation), writes history, and triggers notifications — atomically, in one DB transaction.

### Anti-Pattern 2: Cached Availability Counters That Drift From Reality

**What people do:** Store `available_copies: int` on the `Book` row and increment/decrement it on every borrow/return.
**Why it's wrong:** Counters drift the moment any code path forgets to update them (a failed transaction, a manual DB fix, a bug in one of several mutation points) — and once they drift, "is this book available" becomes a lie the system tells confidently. This is a classic library-system failure mode.
**Instead:** Derive availability by querying `BookCopy` status directly (indexed query, cheap at this scale). If a cached count is needed for catalog list performance later, make it a materialized/derived value recomputed from the source of truth, never an independently-mutated counter.

### Anti-Pattern 3: Treating Email Sending as Synchronous and Blocking

**What people do:** Call the SMTP client inline inside the request handler (`send_email(...)` before `return response`), so a slow mail server makes the approval endpoint feel slow or time out.
**Why it's wrong:** Couples user-facing latency to a third-party service's reliability; a flaky SMTP provider degrades the whole app's perceived performance, and failures there can roll back unrelated DB work if not isolated.
**Instead:** Commit the DB transaction first, then hand off the email to `BackgroundTasks` (or later, a queue). Log the notification attempt in `notification_log` so failures are visible and retriable without blocking the user-facing action.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Email/SMTP provider (e.g., SES, Mailgun, SMTP relay) | Adapter module (`notifications/email_client.py`) behind the `NotificationService` interface; configured via env vars | In dev/docker-compose, run a fake SMTP catcher (e.g., MailHog/Mailpit) so emails are inspectable without real delivery — avoids accidentally spamming real student addresses during development |
| (None other in scope) | — | Out-of-scope items (SSO, bulk import) mean there are no other external integrations for v1 — keep it that way; resist the temptation to "future proof" for integrations that aren't planned |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Router ↔ Service | Direct function calls, dependency-injected DB session | Routers do request/response shaping (Pydantic schemas) and auth checks only; all business logic lives in services |
| Borrow Workflow Service ↔ Catalog Service | Direct call (same process) — workflow service asks catalog service "reserve a copy of book X" | Keep this a clean function-call interface even though both live in-process; it's the seam you'd split first if this ever became two services (it won't need to at this scale) |
| Workflow/Loan Services ↔ Notification Service | Direct call after successful DB commit, wrapped in `BackgroundTasks` | Notification service is the only thing that knows about email; services only know "notify X happened" |
| Scheduler ↔ Loan/Fine Service | Scheduler invokes service functions on a timer (APScheduler job) | Scheduler is infrastructure, not business logic — it should call the same service functions a router would call, ensuring one code path for "what happens when a loan becomes overdue" regardless of whether a human or a clock triggered it |
| Frontend ↔ Backend | REST/JSON over HTTPS, JWT bearer tokens, OpenAPI-generated types (FastAPI auto-generates schema; consider `openapi-typescript` for the frontend) | Keeps the contract explicit and typed end-to-end; reduces drift between what the API returns and what the frontend expects |

## Suggested Build Order (Vertical Slices)

Given the project will be built as end-to-end vertical slices (catalog browse → borrow request/approval → loan tracking/returns/fines), the architecture above naturally supports this sequencing because each slice's backend and frontend pieces are organized by the same feature boundary:

1. **Slice 0 — Auth foundation (cuts across everything):** `User` model, register/login, JWT, role-based route guards (both backend `require_role` and frontend route protection). Nothing else works without this, but keep it minimal — email/password only, two roles.
2. **Slice 1 — Catalog browse (read-only):** `Book`+`BookCopy` models, search/filter/availability endpoints, catalog browse UI. This validates the data model for inventory (the copy-level status pattern) before anything depends on it, and gives librarians a reason to start entering real data early.
3. **Slice 1.5 — Catalog management (librarian CRUD):** add/edit/remove books and copies — needed before request/approval slice can be meaningfully tested with real data, and it's a natural extension of the catalog model from Slice 1.
4. **Slice 2 — Borrow request → approval → checkout (the core workflow):** `BorrowRequest` + state machine service, request submission UI, librarian approval queue UI, checkout recording. This is the highest-risk slice — the state machine and copy-reservation logic are the architectural crux of the whole system — build and test it thoroughly before layering loans/fines on top.
5. **Slice 3 — Loan tracking, returns, fines:** `Loan`+`Fine` models derived from completed checkouts, return recording, fine calculation, "my loans"/"who has this book" views. Depends entirely on Slice 2's state machine producing well-formed `checked_out` records.
6. **Slice 4 — Notifications (threaded through, finalized last):** while the *triggers* for notifications are designed alongside each workflow transition (Slices 2–3), the actual email-sending infrastructure (SMTP adapter, templates, `notification_log`, scheduled due-date/overdue scan) can be stubbed early (log-only) and wired to real delivery once the workflows it depends on are stable — this avoids debugging "why didn't I get an email" at the same time as debugging the state machine itself.

**Build-order rationale:** Each slice depends on the data model and service boundary established by the previous one — catalog must exist before requests can reference books; requests must exist and transition correctly before loans can be derived from them; loans must exist before fines can be computed from them. Notifications are designed early (as part of the state machine's side effects) but can be *stubbed* until the workflows generating them are trustworthy, decoupling "does the workflow work" from "does email delivery work" as separate debugging concerns.

## Sources

- [Building Production-Ready FastAPI Applications with Service Layer Architecture in 2025](https://medium.com/@abhinav.dobhal/building-production-ready-fastapi-applications-with-service-layer-architecture-in-2025-f3af8a6ac563) — MEDIUM confidence (community article, but consistent with multiple other sources on layered architecture)
- [Practical FastAPI × Clean Architecture Guide (router splitting, service layer, repository pattern)](https://blog.greeden.me/en/2025/12/23/practical-fastapi-x-clean-architecture-guide-growing-a-maintainable-api-with-router-splitting-a-service-layer-and-the-repository-pattern/) — MEDIUM confidence
- [FastAPI official docs — Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) — HIGH confidence (official documentation)
- [FastAPI Scheduling & Background Tasks: BackgroundTasks vs APScheduler vs Celery](https://medium.com/@rasifrazak123/fastapi-scheduling-background-tasks-backgroundtasks-vs-apscheduler-vs-celery-complete-guide-ff90d6be524b) — MEDIUM confidence, corroborated by FastAPI docs and multiple independent comparison articles converging on the same recommendation (start with BackgroundTasks, graduate to Celery only when persistence/retry/scale demands it)
- [Workflow Management Database Design — Budibase](https://budibase.com/blog/data/workflow-management-database-design/) — MEDIUM confidence (general workflow-engine pattern, not library-specific, but directly applicable to the request/approval state machine)
- [Designing a Workflow Engine Database Part 4: States and Transitions](https://exceptionnotfound.net/designing-a-workflow-engine-database-part-4-states-and-transitions/) — MEDIUM confidence
- [Creating a Relational Database and ERD for E-Libraries](https://medium.com/@dinantio/creating-a-relational-database-and-constructing-an-entity-relationship-diagram-for-e-libraries-9a6bb1375c40) — MEDIUM confidence (corroborates the `Book`/`BookCopy` separation pattern as standard for library schemas)
- [System Design for Library Management — GeeksforGeeks](https://www.geeksforgeeks.org/system-design/system-design-for-library-management/) — MEDIUM confidence
- [How do you typically structure your project if it includes both frontend and FastAPI? — fastapi/fastapi Discussion #4344](https://github.com/fastapi/fastapi/discussions/4344) — MEDIUM confidence (maintainer/community discussion)
- [TanStack Query — Project structure suggestions, Discussion #3017](https://github.com/TanStack/query/discussions/3017) — MEDIUM confidence
- General domain knowledge of REST/JWT auth patterns, race-condition handling (`SELECT ... FOR UPDATE`), and pure-function fine calculation — HIGH confidence (standard, well-established patterns; not domain-specific to libraries)

---
*Architecture research for: University library management system (FastAPI + React + PostgreSQL)*
*Researched: 2026-06-08*
