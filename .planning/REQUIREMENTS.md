# Requirements: Library Management System

**Defined:** 2026-06-08
**Core Value:** Librarians can always answer "who has this book and when is it due" without digging through spreadsheets — and students can find out if a book is available before walking to the library.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [ ] **AUTH-01**: User can sign up with email and password (student or librarian)
- [ ] **AUTH-02**: User can log in and stay logged in across browser refresh
- [ ] **AUTH-03**: User can reset their password via an emailed link
- [ ] **AUTH-04**: System enforces role-based access — student and librarian capabilities are kept separate server-side

### Catalog

- [ ] **CAT-01**: Student can search/filter the catalog by title, author, genre/category, ISBN, and availability
- [ ] **CAT-02**: Student can view a book's detail page showing description and current copy availability
- [ ] **CAT-03**: Librarian can add a new book (title, author, ISBN, genre/category) to the catalog
- [ ] **CAT-04**: Librarian can edit or remove an existing book's catalog entry
- [ ] **CAT-05**: Librarian can add, edit, or remove individual physical copies of a book (each copy tracked separately, e.g. available/checked out/lost)

### Borrowing

- [ ] **BORW-01**: Student can submit a request to borrow an available book
- [ ] **BORW-02**: Student can cancel their own pending borrow request before it's approved
- [ ] **BORW-03**: Librarian can view a queue of pending borrow requests and approve or reject each one
- [ ] **BORW-04**: Librarian can record that a specific copy has been handed over (checked out) to a student, completing an approved request
- [ ] **BORW-05**: System enforces a fixed borrowing limit of 5 concurrently active loans per student
- [ ] **BORW-06**: System prevents two students from being approved for the same physical copy at the same time

### Loans & Fines

- [ ] **LOAN-01**: Student can view their active loans with due dates and current request statuses
- [ ] **LOAN-02**: Librarian can view all active loans and who currently holds each copy
- [ ] **LOAN-03**: Librarian can record a book as returned, closing the loan
- [ ] **LOAN-04**: System calculates an overdue fine automatically when a loan is returned late, using a fixed policy: Rp 1.000/day, capped at Rp 50.000, with a 1-day grace period after the due date
- [ ] **LOAN-05**: Student and librarian can view any fines owed on a loan
- [ ] **LOAN-06**: Student can renew an active loan once before its due date, provided no one else is waiting on that title
- [ ] **LOAN-07**: System enforces a fixed loan period of 14 days from checkout

### Notifications

- [ ] **NOTF-01**: Student receives an email when their borrow request is approved or rejected
- [ ] **NOTF-02**: Student receives an email reminder a few days before a loan's due date
- [ ] **NOTF-03**: Student receives an email when a loan becomes overdue

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Discovery & Holds

- **HOLD-01**: Student can place a hold/reservation on a currently-unavailable book and join a wait queue
- **HOLD-02**: Student can opt in to be notified when a held title becomes available

### Access & Administration

- **ADMN-01**: University ID / SSO-based login replaces or supplements email/password
- **ADMN-02**: Bulk import of existing spreadsheet catalog data into the system
- **ADMN-03**: Faculty/staff accounts with different borrowing limits and loan periods than students
- **ADMN-04**: Librarians can configure borrowing rules (limits, loan periods, fine rates) instead of fixed defaults

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| University ID / SSO integration | Adds significant complexity; simple email/password is sufficient for v1 — revisit in v2 (ADMN-01) |
| Self-service checkout (no librarian approval) | Librarian approval keeps the physical handoff and digital records in sync, avoiding inventory desync |
| Bulk import of spreadsheet catalog data | Librarians will (re)enter the catalog manually for v1; import tooling deferred to v2 (ADMN-02) |
| Faculty/staff differentiated borrowing rules | Single student role with fixed rules keeps v1 simple — deferred to v2 (ADMN-03) |
| Separate admin role from librarians | Librarians handle both day-to-day operations and management for v1; no separate admin role needed at this scale |
| Configurable borrowing rules | Fixed defaults (5 books, 14-day loans, Rp 1.000/day fines) are sufficient for v1 — deferred to v2 (ADMN-04) |
| Holds/reservation queues | Requires a fairness/queue model, position visibility, and expiry handling — biggest scope-creep risk in this domain; deferred to v2 (HOLD-01/HOLD-02) |
| In-app payments for fines | Payment processing is a separate concern with its own compliance/security surface; out of scope entirely for now |
| SMS notifications | Email is the agreed notification channel for v1; SMS adds provider/cost complexity without clear v1 need |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | TBD | Pending |
| AUTH-02 | TBD | Pending |
| AUTH-03 | TBD | Pending |
| AUTH-04 | TBD | Pending |
| CAT-01 | TBD | Pending |
| CAT-02 | TBD | Pending |
| CAT-03 | TBD | Pending |
| CAT-04 | TBD | Pending |
| CAT-05 | TBD | Pending |
| BORW-01 | TBD | Pending |
| BORW-02 | TBD | Pending |
| BORW-03 | TBD | Pending |
| BORW-04 | TBD | Pending |
| BORW-05 | TBD | Pending |
| BORW-06 | TBD | Pending |
| LOAN-01 | TBD | Pending |
| LOAN-02 | TBD | Pending |
| LOAN-03 | TBD | Pending |
| LOAN-04 | TBD | Pending |
| LOAN-05 | TBD | Pending |
| LOAN-06 | TBD | Pending |
| LOAN-07 | TBD | Pending |
| NOTF-01 | TBD | Pending |
| NOTF-02 | TBD | Pending |
| NOTF-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 0 (filled in by roadmap creation)
- Unmapped: 25 ⚠️ (expected — roadmapper will populate)

---
*Requirements defined: 2026-06-08*
*Last updated: 2026-06-08 after initial definition*
