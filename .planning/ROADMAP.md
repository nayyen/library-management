# Roadmap: Library Management System

## Overview

This roadmap delivers the library management system as six end-to-end vertical slices. It starts with authentication and role-based access (the foundation every other capability depends on), then builds the catalog data model first as a read-only browse experience and then as librarian-managed inventory, before tackling the highest-risk slice — the borrow request → approval → checkout state machine with its concurrency guarantees. Loan tracking, returns, fines, and renewal follow directly since loans are produced by checkout, and email notifications are wired up last so workflow correctness can be verified independently of delivery infrastructure. By the end, librarians can answer "who has this book and when is it due" from the system, and students can check availability and manage their borrowing entirely online.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Auth Foundation** - Students and librarians can register, log in, reset passwords, and the system enforces role-separated access server-side (completed 2026-06-09)
- [ ] **Phase 2: Catalog Browse** - Students can search, filter, and view book/copy availability in the catalog
- [ ] **Phase 3: Catalog Management** - Librarians can add, edit, and remove books and individual physical copies
- [ ] **Phase 4: Borrow Request, Approval & Checkout** - Students can request books and librarians can approve/reject and check them out, with limits and concurrency safety enforced
- [ ] **Phase 5: Loan Tracking, Returns, Fines & Renewal** - Students and librarians can track active loans, record returns, see automatically calculated fines, and renew loans
- [ ] **Phase 6: Notifications** - Students receive timely email notifications for approvals/rejections, due-date reminders, and overdue loans

## Phase Details

### Phase 1: Auth Foundation

**Goal**: Students and librarians can securely register, log in, recover access, and the system enforces role separation server-side for every later feature
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):

  1. A new user can sign up with email and password, choosing or being assigned a student or librarian role
  2. A user can log in and remains logged in across a browser refresh
  3. A user who forgets their password can request and use an emailed reset link to regain access
  4. Librarian-only and student-only actions are rejected server-side (403) when attempted by the wrong role, regardless of what the UI shows

**Plans**: 4 plans (Walking Skeleton — also produces 01-SKELETON.md)

  - [x] 01-01-PLAN.md — Scaffold: Docker Compose stack + FastAPI/Alembic + Vite/Tailwind/shadcn + Wave 0 test infra
  - [x] 01-02-PLAN.md — Backend auth slice: models + migration + JWT/refresh rotation + signup/login/refresh + require_role (AUTH-01/02/04)
  - [x] 01-03-PLAN.md — Frontend auth slice: Zustand + axios interceptor + silent refresh + login/signup + role-gated dashboard (AUTH-01/02/04)
  - [x] 01-04-PLAN.md — Password reset slice: reset-token table + Mailpit email + forgot/reset + session-wipe + auto-login (AUTH-03)

### Phase 2: Catalog Browse

**Goal**: Students can find out whether a book is available before walking to the library, by searching and browsing a real catalog
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CAT-01, CAT-02
**Success Criteria** (what must be TRUE):

  1. A student can search/filter the catalog by title, author, genre/category, ISBN, and availability and get accurate, paginated results
  2. A student can open a book's detail page and see its description plus current per-copy availability (e.g., how many copies are available vs. checked out)
  3. Search and availability results reflect real Book/Copy data modeled as separate entities (not a collapsed quantity counter)

**Plans**: TBD
**UI hint**: yes

### Phase 3: Catalog Management

**Goal**: Librarians can build and maintain the catalog themselves, entirely within the system, with no manual spreadsheet work
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: CAT-03, CAT-04, CAT-05
**Success Criteria** (what must be TRUE):

  1. A librarian can add a new book with title, author, ISBN, and genre/category, and it immediately appears in student search results
  2. A librarian can edit or remove an existing book's catalog entry
  3. A librarian can add, edit, or remove individual physical copies of a book, each tracked separately with its own status (available/checked out/lost)
  4. Catalog write actions are restricted to librarians; student attempts are rejected server-side

**Plans**: TBD
**UI hint**: yes

### Phase 4: Borrow Request, Approval & Checkout

**Goal**: The request → approval → handoff workflow mirrors the library's physical process end-to-end, safely and without double-booking copies
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: BORW-01, BORW-02, BORW-03, BORW-04, BORW-05, BORW-06
**Success Criteria** (what must be TRUE):

  1. A student can submit a borrow request for an available book and cancel it later if it's still pending
  2. A librarian can see a queue of pending requests and approve or reject each one
  3. A librarian can record handover of a specific physical copy to a student, completing an approved request and updating that copy's status
  4. A student cannot have more than 5 concurrently active loans — the system blocks a 6th request/approval
  5. When two students race for the last copy of a title, only one is ever approved for it — concurrent requests cannot double-book the same physical copy

**Plans**: TBD

### Phase 5: Loan Tracking, Returns, Fines & Renewal

**Goal**: Librarians can always answer "who has this book and when is it due," and students can see what they owe and renew when eligible
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: LOAN-01, LOAN-02, LOAN-03, LOAN-04, LOAN-05, LOAN-06, LOAN-07
**Success Criteria** (what must be TRUE):

  1. A student can view their active loans, due dates (14 days from checkout), and current request statuses in one place
  2. A librarian can view all active loans system-wide and see who currently holds each copy
  3. A librarian can record a book as returned, which closes the loan and frees the copy for the next request
  4. When a loan is returned late, the system automatically calculates and stores a fine using the fixed policy (Rp 1.000/day, capped at Rp 50.000, 1-day grace period) — computed once, not recalculated on every view
  5. Both the student and the librarian can view any fines owed on a loan
  6. A student can renew an active loan once before its due date, but only if no one else is waiting on that title; the system blocks a second renewal or a renewal with a pending request from someone else

**Plans**: TBD

### Phase 6: Notifications

**Goal**: Students stay informed about their borrowing activity by email, without needing to check the app proactively
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: NOTF-01, NOTF-02, NOTF-03
**Success Criteria** (what must be TRUE):

  1. A student receives an email when their borrow request is approved or rejected
  2. A student receives an email reminder a few days before their loan's due date
  3. A student receives an email when their loan becomes overdue
  4. Notification sends are logged and scheduled reliably (recurring reminder/overdue scans survive process restarts), not dependent on a single in-request background task

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth Foundation | 4/4 | Complete   | 2026-06-09 |
| 2. Catalog Browse | 0/TBD | Not started | - |
| 3. Catalog Management | 0/TBD | Not started | - |
| 4. Borrow Request, Approval & Checkout | 0/TBD | Not started | - |
| 5. Loan Tracking, Returns, Fines & Renewal | 0/TBD | Not started | - |
| 6. Notifications | 0/TBD | Not started | - |
</content>
</invoke>
