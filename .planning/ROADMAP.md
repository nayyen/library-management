# Roadmap: Biblio — Sistem Manajemen Perpustakaan

## Overview

Biblio replaces a manual spreadsheet-based library process with a FastAPI + React + PostgreSQL application, packaged via docker-compose. The build starts by standing up the full stack skeleton — Indonesian-language schema, docker-compose, and JWT auth with bcrypt — so every later phase has a working foundation to add vertical slices onto. From there, the catalog (search/filter for mahasiswa, CRUD for pustakawan) goes live, followed by the core value proposition: the multi-stage loan workflow (request → approval → pickup window → active loan). Returns close the loop with automatic fine calculation, account blocking, and a notification stub. Finally, the librarian dashboard, member management, and mahasiswa loan history surface the data created by the workflow phases, giving both roles a complete operational view. Each phase ships a working end-to-end vertical slice — UI, API, and DB wired together — matching the Biblio design system throughout.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation, Schema & Auth** - Scaffolding, docker-compose, full DB schema, and working registration/login with JWT
- [x] **Phase 2: Book Catalog** - Mahasiswa can search/filter books; pustakawan can manage master books and physical copies
- [x] **Phase 3: Loan Request & Approval Workflow** - Mahasiswa can request loans; pustakawan approves/rejects, manages pickup window and handover
- [ ] **Phase 4: Returns, Fines & Blocking** - Pustakawan processes returns, system calculates fines, blocks accounts, logs overdue notifications, and clears fines
- [ ] **Phase 5: Dashboard, Members & Loan History** - Pustakawan dashboard with stats/queues, member management, and mahasiswa loan history view

## Phase Details

### Phase 1: Foundation, Schema & Auth

**Goal**: The project runs end-to-end via `docker-compose up` with a working database schema, and users can register (mahasiswa) or log in (mahasiswa/pustakawan) with JWT-based sessions, hashed passwords, and protected-route enforcement.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, DEPLOY-01, NFR-01, NFR-02
**Success Criteria** (what must be TRUE):

  1. Running `docker-compose up` starts the backend, frontend, and PostgreSQL containers, and the frontend login page loads in a browser
  2. A new user can register as `mahasiswa` via the UI (email + password), and their password is stored as a bcrypt hash (never plaintext) in `pengguna`
  3. A registered user (mahasiswa, or a seeded pustakawan account) can log in and receive a JWT valid for 1 hour, landing on a role-appropriate authenticated view
  4. Calling a protected API endpoint without a token, or with an expired/invalid token, returns 401 Unauthorized
  5. The login page and authenticated shell render correctly down to 375px width, and a sample API call completes in under 2 seconds

**Plans**: 4 plansPlans:
**Wave 1**

- [x] 01-01-PLAN.md — Backend skeleton: complete schema + Alembic migration + seed + RED auth tests

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Auth API: bcrypt + JWT, registrasi/masuk/saya, 401 enforcement (tests GREEN)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Frontend skeleton: Vite/React/router/Tailwind + auth UI + shell + 401 interceptor

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04-PLAN.md — docker-compose orchestration (DEPLOY-01) + manual smoke (NFR-01, NFR-02)

**UI hint**: yes

### Phase 2: Book Catalog

**Goal**: Mahasiswa can discover books through search and category filters, and pustakawan can fully manage the catalog — both master book records and individual physical copies.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: CAT-01, CAT-02, CAT-03, CAT-04
**Success Criteria** (what must be TRUE):

  1. A logged-in mahasiswa can search the catalog by `judul`, `penulis`, or `isbn` and see matching results
  2. A mahasiswa can filter the catalog by `kategori` and see only books in that category
  3. A logged-in pustakawan can add, edit, and delete a master `buku` record, and the changes are immediately reflected in the catalog view
  4. A pustakawan can add a physical `salinan_buku` copy to a book, specifying `lokasi_rak`, `kondisi`, and `status_ketersediaan`, and the copy appears in that book's detail view

**Plans**: 4 plans

Plans:

**Wave 1**

- [x] 02-01-PLAN.md — Backend catalog read API (search/filter/category/detail) + seed + RED/GREEN tests

**Wave 2** *(blocked on Wave 1)*

- [x] 02-02-PLAN.md — Mahasiswa frontend: browse grid, search/filter, detail view + Salinan table
- [x] 02-03-PLAN.md — Backend pustakawan CRUD (buku create/edit/delete, add salinan) + role-gate/FK tests

**Wave 3** *(blocked on Wave 2)*

- [x] 02-04-PLAN.md — Pustakawan frontend: Kelola tab, add/edit modal, delete confirm, Tambah Salinan form

**UI hint**: yes

### Phase 3: Loan Request & Approval Workflow

**Goal**: A mahasiswa can request to borrow an available book copy, the system enforces loan-limit and block rules, and a pustakawan can approve or reject the request, manage the pickup window, and hand the book over to start the loan.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: LOAN-01, LOAN-02, LOAN-03, LOAN-04, LOAN-05, LOAN-06
**Success Criteria** (what must be TRUE):

  1. A mahasiswa can submit a loan request for an available copy from the catalog UI, creating a `peminjaman` record with `status_peminjaman = menunggu_persetujuan`
  2. A mahasiswa with 5 active loans, or with `is_diblokir = TRUE`, sees their request rejected by the system before it is created
  3. A pustakawan can view pending requests and approve (→ `siap_diambil`, starting the 2x24h pickup timer) or reject (→ `ditolak`) each one, with `salinan_buku.status_ketersediaan` updated to match
  4. A request left in `siap_diambil` past the 2x24h pickup window automatically becomes `dibatalkan` (verifiable by advancing time or via a scheduled/check job)
  5. A pustakawan can mark a `siap_diambil` loan as physically handed over, moving it to `dipinjam` and setting `tanggal_tenggat` to 14 days from handover

**Plans**: 3 plans

**Wave 1**
- [x] 03-01-PLAN.md — Backend peminjaman API: schemas + router + RED/GREEN tests (17 tests, LOAN-01 through LOAN-06)

**Wave 2** *(blocked on Wave 1)*
- [x] 03-02-PLAN.md — Mahasiswa loan-request UI: StatusBadge, BlockedBanner, LoanRequestModal, wired Pinjam on catalog detail, PinjamanPage mahasiswa view

**Wave 3** *(blocked on Wave 2)*
- [x] 03-03-PLAN.md — Pustakawan queue UI: approve/reject/handover actions with ConfirmDialog on PinjamanPage

**UI hint**: yes

### Phase 4: Returns, Fines & Blocking

**Goal**: A pustakawan can process a book return, the system automatically calculates any overdue fine, blocks the mahasiswa's account on late returns with a logged notification, and the pustakawan can clear the fine to unblock the account.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: RET-01, RET-02, RET-03, RET-04
**Success Criteria** (what must be TRUE):

  1. A pustakawan can process a return for a `dipinjam` loan, setting `status_peminjaman = dikembalikan` and recording `tanggal_kembali`
  2. If `tanggal_kembali` is after `tanggal_tenggat`, the system sets `pengguna.is_diblokir = TRUE` and calculates `total_denda` at Rp 1.000 per day overdue, visible to both the mahasiswa and pustakawan
  3. A late return produces a logged overdue-notification entry (stubbed Brevo call) that a pustakawan or developer can inspect
  4. A pustakawan can mark a fine as paid via a "Denda Lunas" action, which clears `is_diblokir` on the mahasiswa's account

**Plans**: TBD
**UI hint**: yes

### Phase 5: Dashboard, Members & Loan History

**Goal**: Pustakawan have a single operational view of pending approvals, overdue loans, basic stats, and the member roster (with block/fine status), while mahasiswa can review their own loan history and due dates.
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03
**Success Criteria** (what must be TRUE):

  1. A pustakawan landing on the dashboard sees pending approval requests, currently overdue loans, and basic catalog/loan stats at a glance
  2. A pustakawan can view a list of mahasiswa members showing each member's blocked status and outstanding fine total
  3. A mahasiswa can view their own loan history, including past and current loans with status and due dates

**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation, Schema & Auth | 4/4 | ✅ Complete | 2026-06-12 |
| 2. Book Catalog | 4/4 | ✅ Complete | 2026-06-13 |
| 3. Loan Request & Approval Workflow | 3/3 | ✅ Complete | 2026-06-13 |
| 4. Returns, Fines & Blocking | 0/TBD | Not started | - |
| 5. Dashboard, Members & Loan History | 0/TBD | Not started | - |
