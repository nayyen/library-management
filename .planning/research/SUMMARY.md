# Project Research Summary

**Project:** Library Management System (university)
**Domain:** Academic library management — catalog/inventory + role-based borrow-request workflow + loan/fine tracking + notifications
**Researched:** 2026-06-08
**Confidence:** HIGH

## Executive Summary

This is a CRUD-and-workflow application in a mature, well-understood domain. Build it as a layered backend (router → service → ORM, organized by aggregate: Book/Copy, BorrowRequest, Loan, Fine) with an explicit state machine owning every transition in the request → approval → checkout → return lifecycle, strict separation between Book (title-level) and Copy (physical-item-level) data, and notification infrastructure that is decoupled from the request/approval workflow itself (designed alongside it, wired up last).

The chosen stack — FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + React/Vite/TanStack Query + Docker — matches 2026 ecosystem conventions exactly and is registry-verified current. Recommended build order follows vertical slices: auth foundation → catalog browse (read-only) → catalog management (librarian CRUD) → borrow-request/approval state machine (highest-risk slice) → loan tracking/returns/fines → notifications.

All four of the project's existing scope decisions (request+approval over self-checkout, fixed borrowing rules, manual catalog entry, email/password auth) are validated by research as sound v1 cuts that won't create scaling problems. One real gap was found: **loan renewal** is missing from scope — it's near-universal in real academic and public libraries, sits directly on top of the loan model already planned, and costs little to add now versus a wave of "why can't I renew" complaints later. The key risks — concurrency races on copy availability, collapsed book/copy data models, fine-calculation edge cases, unreliable scheduled notifications, and authorization gaps — are all well-documented and preventable with established patterns (`SELECT ... FOR UPDATE SKIP LOCKED`, copy-status modeling, idempotent stored fine amounts, APScheduler + notification_log, a shared `require_role` dependency).

## Key Findings

### Recommended Stack

The backend stack is fully converged: FastAPI 0.115+ with SQLAlchemy 2.0 async (`asyncpg` driver), Alembic for migrations, and Pydantic 2.x for schemas. For auth, use `pwdlib[argon2]` + `pyjwt` rather than the commonly-suggested `passlib`/`python-jose` — both of the latter are unmaintained and `passlib` will hard-break on Python 3.13. The frontend stack is React 19 + Vite + TypeScript + TanStack Query (server state) + Zustand (client state) + React Router 7 + shadcn/ui + Tailwind 4 — replacing now-deprecated Create React App and fading Material UI. For email/scheduling, `fastapi-mail` + `APScheduler` + `Mailpit` (for local dev capture) is right-sized for this scale; Celery/Redis would be premature infrastructure.

**Core technologies:**
- FastAPI + SQLAlchemy 2.0 async + asyncpg + Alembic + Pydantic 2.x — converged 2026 standard for async Python web APIs, registry-verified versions
- `pwdlib[argon2]` + `pyjwt` for auth — `passlib`/`python-jose` are unmaintained and `passlib` breaks on Python 3.13
- React 19 + Vite + TanStack Query + Zustand + shadcn/ui + Tailwind 4 — converged 2026 frontend defaults; type-synced to backend via `openapi-typescript`
- `APScheduler` + `fastapi-mail` + `Mailpit` — right-sized for scheduled reminders/overdue scans without Celery-level infrastructure overhead

### Expected Features

The domain is mature with clear consensus on table stakes, differentiators, and anti-features. Research validated the project's existing scope decisions and surfaced one significant gap: loan renewal.

**Must have (table stakes):**
- Catalog search/browse with availability visibility — users expect this
- Borrow request + librarian approval with status visibility — matches the chosen workflow model
- Checkout/loan tracking and return recording — core to "who has what"
- Automatic, visible fine calculation on overdue returns — expected wherever fines exist
- Manual catalog management (CRUD) by librarians — needed from day one given no bulk import
- Email/password registration, login, password reset
- Email notifications for approvals, due dates, overdue items
- **Loan renewal — missing from current scope; near-universal across surveyed institutions (6+ primary sources), low cost to add, sits directly on the planned loan model**

**Should have (competitive):**
- Transparent request-status pipeline for students (pending → approved → ready for pickup → checked out)
- Librarian approval-queue dashboard with batch triage / sort-by-wait-time — prevents human-bottleneck backlogs at semester start
- Modern, mobile-friendly catalog browsing UI

**Defer (v2+):**
- Holds/reservation queues — biggest scope-creep risk in this domain (needs fairness model, position visibility, expiry handling); a lightweight "notify me when available" toggle is a good v1.x bridge
- SSO/university ID integration, faculty-specific rules, configurable borrowing rules, bulk catalog import, in-app payments, SMS notifications — all correctly excluded per existing Out of Scope reasoning

### Architecture Approach

A layered backend (router → service → ORM, no heavy repository layer) organized by domain aggregate, paired with a feature-folder frontend that mirrors it — this alignment matters specifically because the project builds end-to-end vertical slices. A single service module owns the entire borrow-request state machine so every transition is auditable and consistent.

**Major components:**
1. **Catalog/Inventory Service** — Book (title-level) and BookCopy (physical-item-level, with status: available/reserved/checked_out/lost) as separate entities; availability is derived from copy status, never a cached counter
2. **Borrow Workflow Service** — sole owner of the request → approval → checkout → return state machine; all status transitions flow through here for a trustworthy audit trail
3. **Loan/Fine Service** — tracks active loans, computes fines via an idempotent pure function (compute once, store the result, never recompute on view)
4. **Notification Service** — templated, logged (via a `notification_log` table), queued email sending; designed alongside workflow triggers but with delivery stubbed/log-only until workflows are stable
5. **Scheduler** — APScheduler-driven recurring jobs for due-date reminders and overdue scans (FastAPI's `BackgroundTasks` cannot run scheduled/recurring jobs)

### Critical Pitfalls

1. **Collapsing Book and Copy into one row with a quantity counter** — directly contradicts the core value ("who has THIS book"); model them as separate entities from the first schema migration; counters drift, copy-level status doesn't.
2. **Check-then-act race condition on copy availability** — naive "check available, then claim" double-books copies under concurrent load at university scale; fix with `SELECT ... FOR UPDATE SKIP LOCKED` plus a DB-level uniqueness constraint, and write a concurrency test (parallel requests for the last copy of a title) as an explicit acceptance criterion.
3. **Naive fine/date math** — timezone handling, whether the due date itself counts as a fine day, idempotency (don't recompute on every page view), and caps are real sources of bugs even in commercial systems; write a fine-formula spec before coding, store UTC, store the computed amount once, and test boundary cases explicitly.
4. **Relying on FastAPI's `BackgroundTasks` for notifications** — it cannot schedule recurring jobs, has no retries, no persistence, and silently drops on process restart; this is an architecture decision (use APScheduler + `notification_log`), not a later tweak.
5. **Trusting frontend role-gating for librarian-only actions** — with no separate admin role, librarian endpoints are highly privileged; centralize authorization in a shared `require_role()` dependency plus ownership checks, and write 403 tests, rather than relying on hidden UI elements.

## Implications for Roadmap

Based on research, suggested phase structure (vertical MVP slices):

### Phase 1: Auth Foundation
**Rationale:** Every other phase depends on knowing who the user is and what role they have; establishing the shared `require_role` pattern here prevents Pitfall 5 from ever taking root.
**Delivers:** Registration, login, JWT-based sessions, role-gated routes (student/librarian), password reset
**Addresses:** Email/password auth requirement
**Avoids:** Pitfall 5 (ad hoc/frontend-only authorization)

### Phase 2: Catalog Browse (read-only)
**Rationale:** Validates the Book/Copy data model and search/pagination patterns early, before any workflow complexity is layered on top — cheapest point to get the foundational schema right.
**Delivers:** Searchable, paginated catalog with availability visibility (title/author/genre/ISBN/availability filters)
**Uses:** SQLAlchemy 2.0 async models, indexed/paginated queries, React + TanStack Query for server state
**Implements:** Catalog/Inventory Service (Book + BookCopy entities, copy-level status)
**Avoids:** Pitfall 1 (collapsed book/copy model), Pitfall 6-class issues (unindexed search at scale)

### Phase 3: Catalog Management (librarian CRUD)
**Rationale:** Extends the Phase 2 model with write operations; produces realistic test data needed to exercise the borrow workflow meaningfully in Phase 4.
**Delivers:** Librarian-facing add/edit/remove for books and copies
**Implements:** Catalog/Inventory Service write paths, role-gated librarian routes

### Phase 4: Borrow Request → Approval → Checkout
**Rationale:** The highest-risk slice — the state machine is the architectural crux of the whole system and everything downstream depends on getting its transitions and concurrency handling right.
**Delivers:** Student request flow, librarian approval/rejection queue (with batch triage), checkout/handoff recording, full audit trail of status transitions
**Implements:** Borrow Workflow Service (state machine), copy-reservation locking
**Avoids:** Pitfall 2 (availability race conditions) — concurrency test is a required acceptance criterion

### Phase 5: Loan Tracking, Returns, Fines + Renewal
**Rationale:** Derives directly from Phase 4's state machine output; this is also where the validated scope gap (renewal) should be folded in, since it sits on the same data model.
**Delivers:** Active loan views (student + librarian), return recording, automatic idempotent fine calculation, loan renewal
**Implements:** Loan/Fine Service (pure-function fine computation)
**Avoids:** Pitfall 3 (fine/date-math bugs) — requires a written fine-formula spec before implementation; closes the renewal scope gap identified in research

### Phase 6: Notifications
**Rationale:** Triggers are designed alongside Phases 4-5 (so the workflow emits the right events from day one), but delivery infrastructure is finalized last so "does the workflow work" stays decoupled from "does email delivery work."
**Delivers:** Approval/due-date/overdue email notifications, scheduled reminder and overdue-scan jobs
**Uses:** `fastapi-mail`, `APScheduler`, `Mailpit` (dev), `notification_log` table
**Avoids:** Pitfall 4 (unreliable `BackgroundTasks`-only notifications)

### Phase Ordering Rationale

- Auth must come first — it's a hard dependency for every role-differentiated feature in every later phase
- Catalog (browse, then manage) comes before workflow — the Book/Copy data model is the foundation everything else builds on, and it's far cheaper to get right before workflow logic depends on it
- The borrow-request/approval/checkout slice is sequenced as its own phase (not bundled with catalog) because it is the highest-complexity, highest-risk component — the state machine and concurrency handling deserve focused attention and testing
- Loan/fine/renewal follows directly from the workflow phase because loans are *created* by checkout — there's no meaningful way to build loan tracking before the thing that produces loans exists
- Notifications are deliberately last in build order (though designed early) to avoid coupling "workflow correctness" debugging with "email delivery" debugging

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (Borrow Request → Approval → Checkout):** concurrency/locking strategy and state-machine transition design are domain-specific enough to warrant `--research-phase` — get the locking pattern and state model right before writing code
- **Phase 6 (Notifications):** scheduler choice, email deliverability setup (SPF/DKIM/DMARC), and Docker Compose service topology for APScheduler + Mailpit need confirmation closer to implementation

Phases with standard, well-documented patterns (research-phase optional):
- **Phase 1 (Auth):** standard JWT + role-gating pattern, well-documented in FastAPI ecosystem
- **Phase 2 (Catalog Browse):** standard paginated/indexed CRUD-read patterns
- **Phase 3 (Catalog Management):** standard CRUD-write patterns, extends Phase 2
- **Phase 5 (Loans/Fines/Renewal):** standard once the fine-formula spec is written; the spec itself is a product decision, not a research question

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified directly against live PyPI/npm registries and official FastAPI docs via Context7 |
| Features | MEDIUM-HIGH | Cross-verified across multiple ILS vendor docs and primary-source academic library policies (UCLA, UNT, Pitt, Missouri, KCLS, Denver, LAPL, and others) |
| Architecture | HIGH/MEDIUM | Component structure and FastAPI/React conventions are HIGH (multiple independent sources converge); state-machine and notification patterns are MEDIUM (synthesized from general workflow-engine guidance, not library-specific case studies) |
| Pitfalls | MEDIUM-HIGH | Concurrency/locking and BackgroundTasks limitations are HIGH (official docs + well-documented patterns); fine-calculation pitfalls are MEDIUM (corroborated against real vendor-shipped bugs, but vendor configs differ from a from-scratch build) |

**Overall confidence:** HIGH

### Gaps to Address

- **Loan renewal scope decision:** research strongly recommends pulling this into v1 (low cost, high complaint-avoidance value) — reflected as an added Active requirement in REQUIREMENTS.md; confirm during requirements definition
- **Fine formula specifics:** daily rate, cap, and grace-period policy are project-owner/product decisions, not research findings (researched ranges: $0.25–$5/day, 0–7 day grace periods, 7–28 day loan periods vary widely across institutions) — needs a written spec before Phase 5 implementation
- **Librarian approval-queue throughput UX:** validate during Phase 4 that batch-triage/sort-by-wait-time design actually prevents backlog at scale
- **Notification delivery infrastructure:** scheduler mechanism (APScheduler vs. alternatives) and email provider/deliverability setup should be confirmed closer to Phase 6 implementation

## Sources

### Primary (HIGH confidence)
- Context7 official FastAPI documentation — async patterns, BackgroundTasks capabilities/limitations, dependency injection for auth
- Live PyPI/npm registry checks — FastAPI 0.136.x, SQLAlchemy 2.0.50, Alembic 1.18.x, Pydantic 2.13.x, React 19 ecosystem versions
- FastAPI official repo PR #13917 and maintainer discussion #11773 — passlib/python-jose deprecation, pwdlib/pyjwt migration rationale
- Academic library primary-source policies — UCLA, UNT, Pitt, Missouri, KCLS, Denver, LAPL, Cal Poly Pomona, Lorain, URI (loan/renewal/fine policy verification)

### Secondary (MEDIUM confidence)
- Multiple 2025/2026-dated articles on FastAPI layered architecture and React feature-folder organization
- ILS vendor documentation (Ex Libris, FOLIO, Polaris) — real-world fine-calculation edge cases and shipped bugs
- General PostgreSQL concurrency-pattern documentation — `SELECT ... FOR UPDATE SKIP LOCKED`, uniqueness constraints
- Transactional email deliverability best-practice sources (SendGrid-focused, generalizes to other providers)

### Tertiary (LOW confidence)
- WebSearch-sourced ILS architecture/holds-queue design discussions — directionally useful, no single authoritative source reviewed
- APScheduler-vs-Celery scale judgment — reasoned from project scale rather than hard ecosystem consensus

---
*Research completed: 2026-06-08*
*Ready for roadmap: yes*
