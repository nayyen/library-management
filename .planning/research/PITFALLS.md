# Pitfalls Research

**Domain:** University library management system (FastAPI + React + PostgreSQL, request-approval workflow, Docker deployment)
**Researched:** 2026-06-08
**Confidence:** MEDIUM-HIGH (concurrency/locking patterns and FastAPI background-task limitations are well-documented HIGH confidence; fine-calculation and notification specifics are MEDIUM, drawn from ILS vendor docs and community sources)

## Critical Pitfalls

### Pitfall 1: Modeling "the book" and "the copy" as one row (no title/item separation)

**What goes wrong:**
Teams new to library systems model a single `books` table with a `quantity_available` integer column. This collapses two distinct concepts — the *title* (metadata: ISBN, author, genre) and the physical *copy* (a specific, trackable, lendable object with its own status and location) — into one. The result: you cannot answer "which physical copy does student X have?", cannot track condition/loss/damage per item, cannot have two copies of the same title in different states (one borrowed, one available, one lost), and every borrow/return becomes an update to a shared counter rather than a state change on an identifiable row.

**Why it happens:**
A `quantity` column feels simpler and matches how spreadsheets represent "we have 3 copies of Title X." It works fine in a demo with no concurrent borrowers. The need for per-copy identity only becomes obvious once you ask "who has THIS book right now" — which is the system's stated core value.

**How to avoid:**
Model two entities from day one: `book` (catalog metadata — title, author, ISBN, genre, description) and `book_copy` (one row per physical item — barcode/copy number, condition, status enum: available/on_loan/reserved/lost/damaged/withdrawn, FK to `book`). Availability is *derived* (count of copies in `available` status), never stored as a denormalized counter that can drift out of sync. All loan/request records reference a specific `book_copy`, not just a `book`.

**Warning signs:**
- A `quantity` or `copies_available` integer column directly on the `books` table that gets manually incremented/decremented
- Inability to answer "which exact copy is overdue" without ambiguity
- Loan records that reference `book_id` instead of `copy_id`

**Phase to address:**
Phase 1 (data modeling / schema design) — this is foundational; retrofitting copy-level tracking after loans exist is a painful migration (you'd have to backfill copy assignment for historical loan records).

---

### Pitfall 2: Race condition on "is this book available?" between request and approval

**What goes wrong:**
Two students submit borrow requests for the last available copy of a title within milliseconds of each other. Both requests pass an "is a copy available?" check (read), both get inserted as pending requests, and later a librarian approves both — resulting in one physical book promised to two people. Alternatively, naive read-then-write logic ("check available count, then decrement") under concurrent load causes the available count to go negative or two approvals to claim the same copy.

**Why it happens:**
The intuitive implementation is "SELECT to check availability, then INSERT/UPDATE to act on it" — two separate statements with a window between them where another transaction can interleave. This is the classic check-then-act race condition, and it's invisible in manual testing (one user at a time) and only surfaces under concurrent load — exactly the "whole university" scale this system targets.

**How to avoid:**
Wrap the availability check and the state-changing action in a single transaction using row-level locking: `SELECT ... FROM book_copy WHERE book_id = ? AND status = 'available' LIMIT 1 FOR UPDATE SKIP LOCKED`, then update that specific copy's status atomically within the same transaction. `FOR UPDATE SKIP LOCKED` is ideal here — it lets concurrent requests for the same title each grab a *different* available copy without blocking on each other, while still preventing two requests from claiming the same copy. Alternatively, enforce uniqueness with a database constraint (e.g., a partial unique index ensuring only one active loan/reservation per copy) so the database itself rejects the double-claim even if application logic races. Acquire locks as late as possible and keep transactions short to avoid contention/deadlocks at scale.

**Warning signs:**
- Code that does `if available_count > 0:` followed by a separate write statement
- No `FOR UPDATE` / row locking anywhere near the borrow-request or approval code paths
- No database-level constraint preventing two active loans on the same copy — only application-level checks
- Manual QA never tests concurrent submissions (only sequential)

**Phase to address:**
Phase covering the borrow-request and approval flow (core workflow phase). Write a concurrency test (parallel requests for a single-copy title) as part of that phase's acceptance criteria — this is the single highest-value test to write early.

---

### Pitfall 3: Treating fixed loan-period math as "due date = borrow date + N days" with no edge-case handling

**What goes wrong:**
Fine and due-date calculations that look correct in testing produce wrong results in production because of: timezone mismatches (server stores UTC, librarian/student see local time, "due at midnight" becomes ambiguous), off-by-one errors in day-counting (is the due date itself a grace day or a fine day?), double-charging when a book is returned and the return-processing runs the fine calculation more than once, and fines that keep accruing indefinitely with no cap. Real ILS systems have shipped bugs exactly like "a book due Monday 8:00 AM with a grace period until 9:00 AM generated a $2 fine instead of $1 when returned at 9:06" — small interval/rounding mistakes compound into visibly wrong numbers that erode librarian trust in the system.

**Why it happens:**
Date/time arithmetic looks trivial ("just subtract two dates and multiply by a daily rate") but datetime libraries, timezones, and "is this day inclusive or exclusive" decisions are genuinely subtle. Developers test with same-day or next-day scenarios and miss multi-day, cross-timezone, or boundary-exact cases.

**How to avoid:**
Store all timestamps in UTC; convert to a single canonical institutional timezone for display and for "is this overdue" comparisons (a university has one timezone — don't over-engineer for multiple). Define the fine formula explicitly and in writing before coding it (e.g., "fine = max(0, days_late) × daily_rate, where days_late = (return_date − due_date), calculated in whole calendar days, capped at MAX_FINE"). Make fine calculation idempotent — compute it once at return time, store the computed amount on the loan record, and never recompute/re-charge on subsequent reads. Decide explicitly (and document) whether the due date itself counts as a late day, and write a unit test for that exact boundary. Cap fines at a maximum so a long-lost book doesn't generate an absurd, uncollectable charge.

**Warning signs:**
- Date math using naive `datetime.now()` without explicit timezone awareness
- Fine amount recalculated every time the loan record is viewed rather than computed once and stored
- No test covering "returned exactly on the due date" or "returned one minute after midnight"
- No upper bound on accumulated fines

**Phase to address:**
Phase covering loan return / fine calculation. Write the fine formula as a spec/decision record before implementation; cover boundary cases in tests as acceptance criteria.

---

### Pitfall 4: Treating email notifications as "fire and forget" with FastAPI's built-in BackgroundTasks

**What goes wrong:**
Using FastAPI's `BackgroundTasks` to send approval/due-date/overdue emails seems to "just work" in development. In production it silently fails in ways that are hard to detect: tasks have no retry on transient SMTP failure, no visibility into whether they ran or succeeded, no persistence (a server restart or crash mid-task loses the email permanently), and no idempotency guarantee (a retry-on-error could send the same "your book is overdue" email twice, or a slow task could still be running at shutdown and get killed mid-send). For a system whose stated value is "students need to be reachable outside the app," silently-dropped emails directly undermine the core value proposition — and nobody notices until a student complains they "never got the notification."

**Why it happens:**
`BackgroundTasks` is the path of least resistance — it ships with FastAPI, requires no extra infrastructure, and looks identical to a "real" async job system in a demo. The gap only appears under real failure conditions (SMTP provider hiccup, server restart, high load) which don't show up in development.

**How to avoid:**
For due-date reminders and overdue notices specifically (which are *scheduled*, recurring jobs, not request-triggered side effects), you need a real scheduler — `BackgroundTasks` cannot run on a timer at all. Use a proper task queue (Celery with Redis/RabbitMQ, or the lighter-weight ARQ + Redis) for anything that needs retries, scheduling, or delivery confirmation. At minimum: log every notification attempt (sent/failed/retried) to a table so librarians and developers can audit "did student X get notified," make send operations idempotent (track "notification already sent for loan Y, due-date type" to avoid duplicates on retry), and choose a transactional email provider (not raw SMTP) so you get delivery/bounce webhooks. Segment transactional email sending from any future marketing email to protect sender reputation, and set up SPF/DKIM/DMARC for the sending domain — without them, a meaningful fraction of "successfully sent" emails land in spam and the student never sees them regardless of backend correctness.

**Warning signs:**
- `BackgroundTasks` used for due-date reminders (which require a recurring scheduled trigger — something `BackgroundTasks` structurally cannot provide)
- No log/record of notification attempts separate from the "business" event (e.g., no `notification_log` table)
- No domain authentication (SPF/DKIM/DMARC) configured for the sending domain
- Manual testing only checks "did the email function get called," not "did the email arrive in the inbox" (vs. spam)

**Phase to address:**
Phase covering notifications. Decide the job-scheduling mechanism (cron + queue vs. BackgroundTasks) explicitly during architecture/stack decisions — retrofitting a scheduler after the notification code is written around `BackgroundTasks` is a rework, not a tweak.

---

### Pitfall 5: Conflating "authenticated" with "authorized" — role checks scattered or missing on state-changing endpoints

**What goes wrong:**
The student/librarian role split looks simple (only two roles), so teams under-invest in authorization design: role checks get implemented ad hoc per-endpoint (some routes check `current_user.role == "librarian"` inline, others forget to), or — worse — the frontend hides librarian-only UI but the backend trusts the frontend and never re-checks. The predictable failure: a student discovers (via browser devtools or a direct API call) that the "approve request" or "mark returned" endpoint has no server-side role check, and can manipulate loan records, fines, or catalog data directly. Because there's no "admin" role distinct from "librarian" in this system (per scope), librarian endpoints are *highly* privileged — any gap is severe.

**How to avoid:**
Centralize authorization as a reusable FastAPI dependency (e.g., `require_role("librarian")`) injected into every state-changing route — never duplicate the check inline per-handler. Treat the frontend role-based UI as a UX convenience only; every privileged backend operation must independently verify the caller's role from the validated JWT/session, not from any client-supplied value. Additionally, enforce *ownership* checks for student-facing endpoints (a student must only see/cancel *their own* requests and loans — verify `loan.student_id == current_user.id`, don't just check "is a student"). Write integration tests that specifically attempt privileged actions as the wrong role and assert 403, as part of the Definition of Done for every state-changing endpoint.

**Warning signs:**
- Role checks written as inline `if` statements duplicated across route handlers rather than a shared dependency
- Any endpoint that mutates loan/request/catalog state without an explicit role-or-ownership check visible in its dependency list
- No tests that attempt cross-role or cross-user access and assert rejection
- Frontend route guards exist but there's no corresponding backend enforcement for the same action

**Phase to address:**
Phase covering authentication/authorization setup (early — this is foundational and every subsequent feature phase depends on the pattern being right). Re-verify at each subsequent phase that new endpoints follow the established authorization dependency pattern.

---

### Pitfall 6: Designing the schema/queries for "a few hundred rows" and hitting a wall at "thousands of books, thousands of students"

**What goes wrong:**
Catalog search ("search by title, author, genre, ISBN, availability") implemented as naive `LIKE '%term%'` queries with no indexes works fine against a hand-entered demo catalog of 50 books. Against a real university catalog (thousands of titles, tens of thousands of copies, thousands of students each with loan history), the same query becomes a full table scan; combined with N+1 query patterns (e.g., fetching a list of books, then querying copy-availability per book in a loop, then querying author/genre per book in a loop), page loads degrade from milliseconds to seconds, and the system feels broken under real load — exactly the scenario the project explicitly says it must handle.

**Why it happens:**
Performance problems are invisible at small scale and only manifest as data volume and concurrent users grow — by which point the query patterns are baked into many endpoints and require systemic rework, not a quick fix.

**How to avoid:**
From the first schema migration: add indexes on columns used in WHERE/JOIN/ORDER BY for catalog search and loan lookups (title, author, ISBN, status, due_date, student_id, book_id/copy_id foreign keys). Use the ORM's eager-loading (`joinedload`/`selectinload` in SQLAlchemy) explicitly for any list endpoint that needs related data, rather than relying on lazy-loading-in-a-loop. Paginate every list endpoint from day one (catalog browse, loan history, request lists) — never return "all rows." For catalog search specifically, consider PostgreSQL full-text search (`tsvector`/`tsquery` with a GIN index) rather than `LIKE '%...%'`, which cannot use a standard B-tree index efficiently. Load-test with realistic data volume (generate a synthetic catalog of several thousand books and several thousand students) before declaring a phase done — not just the hand-entered demo data.

**Warning signs:**
- Any list/search endpoint with no `LIMIT`/pagination
- `LIKE '%...%'` (leading wildcard) on unindexed text columns for search
- ORM relationship access inside a loop over query results (classic N+1 signature)
- No migration includes index definitions on foreign keys or frequently-filtered columns
- Performance only ever tested against the seed/demo dataset (tens of rows), never a realistic volume

**Phase to address:**
Phase covering catalog browsing/search (where query patterns are first established) and revisited at any phase introducing new list/report views (loan history, overdue lists, etc.). Establish "every list endpoint is paginated and indexed" as a standing Definition-of-Done item across all phases, not a one-time fix.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single `books` table with a `quantity` counter instead of book/copy split | Faster initial schema, fewer joins to write | Cannot identify which physical copy a student holds; major migration to retrofit; undermines the "who has this book" core value | Never — this directly contradicts the stated core value |
| Using `BackgroundTasks` for all email sending (including scheduled reminders) | No extra infrastructure (Redis/Celery) to set up; ships faster | No retry, no scheduling capability, silent failures, duplicate-send risk; due-date reminders structurally cannot be built on `BackgroundTasks` alone | Acceptable only for one-off, non-scheduled, non-critical emails (e.g., "welcome" email on registration) where occasional loss is tolerable — never for due-date/overdue reminders |
| Recomputing fines on every page view instead of storing a computed value | Always "fresh," no extra write | Risk of inconsistent amounts if formula or rates change mid-loan; non-idempotent; harder to audit "what did we actually charge" | Never for the canonical charge amount — fine should be computed once at a defined trigger (return) and stored; display-time "estimated current fine" for an active overdue loan can be computed on the fly as long as it's clearly distinguished from the final charged amount |
| Inline per-route role checks (`if current_user.role != "librarian": raise...`) instead of a shared dependency | Fast to write for the first 2-3 endpoints | Inconsistent enforcement, easy to forget on new endpoints, hard to audit | Acceptable briefly during initial prototyping only; must be refactored to a shared dependency before the phase is considered done |
| Skipping pagination on list endpoints during early development | Simpler endpoint code, fewer query params to handle | Breaks at realistic data volume; requires API contract changes (clients must add pagination params) later, which is a breaking change for any existing frontend code | Acceptable only with an explicit TODO and before any frontend code depends on the unpaginated shape — convert before the catalog/loan-history UI is built against it |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SMTP / transactional email provider | Sending from an unauthenticated domain (no SPF/DKIM/DMARC), mixing transactional and any future bulk/marketing mail on the same sending identity, assuming "sent successfully" means "delivered to inbox" | Configure domain authentication (SPF, DKIM, DMARC) before going live; use a dedicated transactional-email subdomain/stream; treat provider webhooks (bounce/complaint/delivered) as the source of truth for delivery status, not the "send" API call's 200 response |
| PostgreSQL via SQLAlchemy/async ORM | Relying on default lazy-loading for relationships accessed in list views, causing N+1 query storms; not wrapping multi-step state changes (check-then-act) in explicit transactions with row locks | Explicitly choose eager-loading strategy per query; wrap availability-check + claim sequences in `SELECT ... FOR UPDATE [SKIP LOCKED]` within a single transaction |
| Docker / containerized deployment | Running the FastAPI app and a long-running scheduler/worker (for due-date reminder jobs) in the same process/container, so a deploy or crash of the web process also kills scheduled jobs silently | Run the web API and the background worker/scheduler as separate services/containers in the compose setup, so they can be deployed, scaled, and restarted independently and failures are visible per-service |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unindexed `LIKE '%term%'` catalog search | Search feels instant in dev, becomes multi-second once catalog has thousands of titles | Use PostgreSQL full-text search (`tsvector`/GIN index) or trigram indexes (`pg_trgm`) for partial-match search; add B-tree indexes on exact-match filter columns (ISBN, genre, status) | Roughly hundreds to low-thousands of catalog rows, depending on hardware — exactly the scale this project targets |
| N+1 queries on list views (e.g., books + per-book availability + per-book author) | Page load time scales linearly with number of rows displayed; database connection pool exhausts under concurrent users | Use eager loading (`selectinload`/`joinedload`) or a single aggregating query; profile with SQL query logging during development, not just at "it's slow" time | Becomes visible once lists exceed ~50-100 rows per page or under concurrent load — i.e., almost immediately at "whole university" scale |
| No pagination on loan-history / request-list / overdue-list endpoints | Response payloads grow unbounded as loan history accumulates over semesters/years; frontend renders thousands of rows | Cursor or offset pagination on every list endpoint from the first implementation; cap max page size server-side | Breaks gradually as historical data accumulates — a fresh install looks fine, a semester-old install starts to slow down |
| Synchronous email send blocking the request/response cycle | Approval/registration endpoints feel slow (multi-second response times) under load, especially if SMTP provider has latency spikes | Always send notification emails asynchronously via a queue/worker, never inline in the request handler | Becomes noticeable the moment SMTP latency exceeds ~200-500ms or under any concurrent load |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Trusting frontend role-based UI as the only access control | Student crafts direct API requests to librarian-only endpoints (approve request, mark returned, edit catalog) and mutates data they shouldn't be able to touch | Enforce role and ownership checks server-side via a shared FastAPI dependency on every state-changing route; never assume the frontend is the only client |
| Leaking other students' data through loosely-scoped "my loans" endpoints | A student can view or cancel another student's borrow request/loan by guessing/incrementing IDs (IDOR) | Every student-facing query must filter by `current_user.id` server-side, not rely on the client to only request "their own" data |
| Storing plaintext or weakly-hashed passwords for email/password auth | Full account compromise on any data breach; especially damaging since the same students likely reuse passwords across university systems | Use a strong adaptive hash (bcrypt/argon2) via a vetted library; never roll your own; rate-limit login attempts |
| Enumerable user existence via registration/login error messages | Attacker can enumerate valid student emails (useful for phishing/targeted attacks against the university population) | Return identical, generic responses for "email already registered" vs. "invalid credentials" type flows where feasible; rate-limit registration and login endpoints |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing "available" on the catalog page based on stale/cached counts that don't reflect concurrent claims | Student walks to the library for a book that was claimed by someone else seconds ago — directly undermines the stated core value ("students can find out if a book is available before walking to the library") | Compute availability live from copy status at request time (not a cached counter); when a request is approved/rejected, make the catalog reflect the change immediately — and consider showing "X requests pending" so students understand contention |
| Silent request-status changes with no notification trail | Student doesn't know their request was approved/rejected until they happen to check the app — and if email fails silently (Pitfall 4), they may never find out | Always pair a state change (approved/rejected/handed-over/overdue) with both an in-app status update AND a logged notification attempt; surface "notification sent at X" so support can diagnose "I never got an email" complaints |
| Fines that appear suddenly with no warning | Student is surprised/frustrated by a fine they didn't expect, erodes trust in the system | Send due-date reminder emails *before* the due date (not just overdue notices after), and show "X days until due" / "overdue by X days, estimated fine $Y" prominently in the student's loan view |
| Librarian has no way to see *why* a request might be problematic (e.g., student already at max books, or has unpaid fines) | Librarian approves a request that then can't be fulfilled per the system's own rules, creating confusing inconsistent states | Surface borrowing-rule context (current loan count vs. max, outstanding fines) directly in the librarian's approval view, and validate rule compliance server-side at approval time (not just at request time) — state can change between request and approval |

## "Looks Done But Isn't" Checklist

- [ ] **Borrow request flow:** Often missing concurrency protection — verify with a test that fires N simultaneous requests for a single-copy title and confirms exactly one succeeds
- [ ] **Fine calculation:** Often missing boundary-case coverage — verify with explicit tests for "returned exactly on due date," "returned during grace period," "returned after long absence (cap behavior)," and timezone-crossing scenarios
- [ ] **Email notifications:** Often missing delivery confirmation/audit trail — verify there's a queryable log of every notification attempt (sent/failed/retried) and that due-date reminders actually fire on a schedule (not just on-demand triggers), tested by advancing the clock or running the scheduler in a test environment
- [ ] **Role-based access control:** Often missing server-side enforcement on a subset of endpoints — verify by attempting every state-changing action as the wrong role (and as a different user of the same role) and confirming a 403/404, not just checking that the frontend hides the button
- [ ] **Catalog search/list endpoints:** Often missing pagination and indexes — verify by loading a realistic synthetic dataset (thousands of books/students) and measuring response times, not just testing against the seed data
- [ ] **Availability display:** Often shows cached/derived counts that can drift — verify that the displayed "available" status always matches the live count of copies in `available` status, especially immediately after an approval/rejection/return

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Single books table without copy-level tracking discovered late | HIGH | Requires schema migration introducing `book_copy`, backfilling copy assignment for every historical loan record (often requires manual reconciliation against real-world records), and rewriting all loan/request queries to reference copies — budget this as a dedicated migration phase, not a quick patch |
| Race condition causing double-booked copies found in production | MEDIUM | Add `FOR UPDATE SKIP LOCKED` + a database uniqueness constraint preventing two active loans per copy; reconcile any already-double-booked records manually (likely a handful of cases); add a regression test that reproduces the race before considering it fixed |
| Fine calculation bug discovered after charges have been applied to real students | MEDIUM-HIGH | Requires both a code fix AND a data-correction pass (recompute and adjust affected fine records) plus a communication plan to affected students — budget extra time for the human/trust-repair side, not just the technical fix |
| Emails silently failing/landing in spam discovered after students complain | LOW-MEDIUM | Add domain authentication (SPF/DKIM/DMARC), switch to or properly configure a transactional provider, backfill notification log to identify who was missed, and consider a one-time "catch-up" notification batch for affected students |
| Missing server-side authorization checks discovered via security review or incident | MEDIUM | Audit every state-changing endpoint, retrofit the shared role/ownership dependency, add regression tests for every endpoint, and review logs for evidence of exploitation before considering it closed |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Books vs. copies modeling | Phase 1 — Data modeling / catalog schema | Schema review confirms `book` and `book_copy` are separate entities; loan/request records FK to `copy_id`; availability is derived, never stored as a manually-maintained counter |
| Race condition on borrow availability | Phase covering borrow-request & approval workflow | Concurrency test: N parallel requests against a single-copy title results in exactly one approved claim; code review confirms `FOR UPDATE`/locking or equivalent constraint is present |
| Fine calculation edge cases | Phase covering loan return / fines | Written fine-formula spec exists before implementation; unit tests cover due-date boundary, timezone, and cap scenarios; fine amount is computed once and stored, never recomputed on read |
| Email notification reliability | Phase covering notifications | Scheduler mechanism (not bare `BackgroundTasks`) is chosen and documented; notification_log table exists and is populated; domain auth (SPF/DKIM/DMARC) configured; test confirms scheduled reminders fire without manual triggering |
| Auth/role separation | Phase covering authentication & authorization | Shared `require_role`/ownership dependency exists and is used by every state-changing endpoint; tests attempt cross-role and cross-user access and assert rejection |
| Scaling catalog/list queries | Phase covering catalog browse/search (and revisited at each new list view) | Load test against synthetic dataset of thousands of rows shows acceptable response times; every list endpoint is paginated; query plans (EXPLAIN ANALYZE) show index usage, not sequential scans |

## Sources

- [How to Handle Race Conditions in PostgreSQL Functions — OneUptime](https://oneuptime.com/blog/post/2026-01-25-postgresql-race-conditions/view)
- [SELECT FOR UPDATE - Reduce Contention and Avoid Deadlocks — Stormatics](https://stormatics.tech/blogs/select-for-update-in-postgresql)
- [Preventing Postgres SQL Race Conditions with SELECT FOR UPDATE — on-systems.tech](https://on-systems.tech/blog/128-preventing-read-committed-sql-concurrency-errors/)
- [Preventing Race Conditions with SELECT FOR UPDATE in Web Applications — Leapcell](https://leapcell.io/blog/preventing-race-conditions-with-select-for-update-in-web-applications)
- [Background Tasks — FastAPI official docs](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [How to Build Background Task Processing in FastAPI — OneUptime](https://oneuptime.com/blog/post/2026-01-25-background-task-processing-fastapi/view)
- [Managing Background Tasks in FastAPI: BackgroundTasks vs ARQ + Redis — David Muraya](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/)
- [Understanding Pitfalls of Async Task Management in FastAPI Requests — Leapcell](https://leapcell.io/blog/understanding-pitfalls-of-async-task-management-in-fastapi-requests)
- [Fine not being calculated properly when grace period has expired — Ex Libris Knowledge Center](https://knowledge.exlibrisgroup.com/Aleph/Knowledge_Articles/Fine_not_being_calculated_properly_when_grace_period_has_expired)
- [Grace periods (tab16) and overdue jobs — Ex Libris Knowledge Center](https://knowledge.exlibrisgroup.com/Aleph/Knowledge_Articles/Grace_periods_(tab16)_and_overdue_jobs)
- [Overdue fees and fines calculation - things to know — FOLIO Wiki](https://folio-org.atlassian.net/wiki/spaces/FOLIOtips/pages/5672173/Overdue+fees+and+fines+calculation+-+things+to+know)
- [Calculating Overdue Fines — Polaris/III documentation](https://documentation.iii.com/polaris/7.3/PolarisStaffHelp/Patron_Services_Admin/PDPfines/Calculating_Overdue_Fines.htm)
- [Fine Structure and Grace Periods — NC State University Libraries](https://www.lib.ncsu.edu/borrow/fines)
- [Simplifying Approval Process with State Machine: A Practical Guide — Medium](https://medium.com/@wacsk19921002/simplifying-approval-process-with-state-machine-a-practical-guide-part-1-modeling-26d8999002b0)
- [FastAPI RBAC - Full Implementation Tutorial — Permit.io](https://www.permit.io/blog/fastapi-rbac-full-implementation-tutorial)
- [Optimizing Database Queries in FastAPI: Indexing, Caching, and Pagination — Medium](https://medium.com/@maheshwariaditya5555/optimizing-database-queries-in-fastapi-indexing-caching-and-pagination-caad1a320b96)
- [Asynchronous Pagination in FastAPI for Large Result Sets — Medium](https://medium.com/@bhagyarana80/asynchronous-pagination-in-fastapi-for-large-result-sets-62925ceb96a4)
- [SendGrid Emails Going to Spam? Diagnose & Fix Inbox Delivery — MailReach](https://www.mailreach.co/blog/sendgrid-emails-going-to-spam)
- [Why are my transactional emails from Sendgrid being flagged as spam — Suped](https://www.suped.com/learn/email-deliverability/why-are-my-transactional-emails-from-sendgrid-being-flagged-as-spam-in-gmail-and-how-can-i-fix-i)
- [How to design a database for a library management system — Lucid Community](https://community.lucid.co/product-questions-3/how-to-design-a-database-for-a-library-management-system-identified-by-isbn-9835)
- [Creating a Modern Library Database — Medium (Huseyin Danisman)](https://medium.com/@danishman/creating-a-modern-library-database-b7dff4313f28)

---
*Pitfalls research for: University library management system (FastAPI + React + PostgreSQL CRUD/workflow application)*
*Researched: 2026-06-08*
