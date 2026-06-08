# Library Management System

## What This Is

A digital library management system for a university, replacing spreadsheet-based tracking. Students search the catalog and request books online; librarians approve requests, hand over books, record returns, and track who has what — all in one system instead of scattered spreadsheets.

## Core Value

Librarians can always answer "who has this book and when is it due" without digging through spreadsheets — and students can find out if a book is available before walking to the library.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Student can search/browse the catalog by title, author, genre/category, ISBN, and availability
- [ ] Student can request to borrow an available book
- [ ] Librarian can approve or reject a borrow request
- [ ] Librarian can mark a book as handed over (checked out) to a student
- [ ] Student can view their current loans, due dates, and request status
- [ ] Librarian can record a book as returned
- [ ] System enforces simple fixed borrowing rules (max books per student, fixed loan duration)
- [ ] System calculates overdue fines automatically when a book is returned late
- [ ] Librarian can manually add, edit, and remove books and copies in the catalog
- [ ] Students and librarians can register and log in via email/password
- [ ] System sends email notifications for request approvals, due-date reminders, and overdue books

### Out of Scope

- University ID / SSO integration — adds significant complexity; simple email/password is sufficient for v1
- Self-service checkout (student marks book borrowed without librarian) — librarian approval keeps physical handoff and records in sync
- Bulk import of existing spreadsheet catalog data — librarians will (re)enter catalog manually for v1; import tooling can come later
- Faculty/staff differentiated borrowing rules — single student role with fixed rules keeps v1 simple
- Admin role separate from librarians — librarians handle both day-to-day operations and management for v1

## Context

- Target users: university students (search/borrow) and librarians (catalog/loan management)
- Scale: whole-university library — thousands of books, hundreds/thousands of student accounts; needs to handle real load, not a toy dataset
- Current process is entirely spreadsheet-based; no existing digital system to migrate from or integrate with
- Borrowing is a request → librarian-approval → physical handoff flow, not self-checkout — the system mirrors and digitizes this existing physical process
- Notifications are email-based (approvals, due dates, overdue) — students need to be reachable outside the app

## Constraints

- **Tech stack**: Backend in Python (FastAPI), frontend in React, database PostgreSQL — user-specified, non-negotiable
- **Deployment**: Must run in Docker — user-specified for portability/ease of deployment
- **Scale**: Must handle whole-university load (thousands of books, large student body) — informs schema and query design from the start

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Borrow flow is request + librarian approval, not self-service | Mirrors existing physical handoff process; keeps librarian in the loop and avoids inventory desync | — Pending |
| Fixed (non-configurable) borrowing rules for v1 | Keeps scope small; sensible defaults (e.g., max N books, fixed loan period) cover the common case | — Pending |
| Librarians manage catalog manually, no bulk import for v1 | Avoids building import tooling for messy spreadsheet data up front; can be added later if painful | — Pending |
| Email/password auth, no university SSO | SSO integration is high-effort and out of scope for a v1; simple auth unblocks everything else | — Pending |
| Email notifications for approvals/due dates/overdue | Students need to be reachable outside the app; this is the most requested touchpoint | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-08 after initialization*
