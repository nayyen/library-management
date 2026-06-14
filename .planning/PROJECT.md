# Biblio — Sistem Manajemen Perpustakaan

## What This Is

A digital library management system that replaces a manual, error-prone spreadsheet process. Built with FastAPI (backend), React (frontend), and PostgreSQL (database), packaged for `docker-compose`. Two roles: **mahasiswa** (search the catalog, request loans, track due dates and fines) and **pustakawan** (manage the catalog, approve/reject loan requests, hand books over, process returns, track overdue loans and fines, view a dashboard). The UI follows the "Biblio" design system — a navy/cream academic aesthetic (Playfair Display + Inter) with 6 designed screens: login, book catalog, loan request form, librarian dashboard, member management, and loan history.

## Core Value

The end-to-end loan lifecycle must work correctly: a mahasiswa can find a book and request to borrow it, a pustakawan can approve/reject and hand it over, and the system tracks the due date through to return — automatically calculating fines (Rp 1.000/day) and blocking the mahasiswa's account on late returns.

## Requirements

### Validated

**Authentication**
- [x] User can register as `mahasiswa` with email + password (pustakawan accounts are seeded, not self-registered)
- [x] User can log in and receive a JWT valid for 1 hour
- [x] Passwords are hashed with bcrypt
- [x] Protected endpoints reject requests with missing/expired tokens (401)

### Active

**Catalog**
- [ ] Mahasiswa can search the catalog by `judul`, `penulis`, or `isbn`
- [ ] Mahasiswa can filter the catalog by `kategori`
- [ ] Pustakawan can add, edit, and delete master `buku` records
- [ ] Pustakawan can add physical `salinan_buku` copies (lokasi_rak, kondisi, status_ketersediaan)

**Loan Requests & Approval**
- [ ] Mahasiswa can request to borrow an available book (`status_peminjaman` → `menunggu_persetujuan`)
- [ ] System rejects a loan request if the mahasiswa already has 5 active loans
- [ ] System rejects a loan request if `pengguna.is_diblokir = TRUE`
- [ ] Pustakawan can approve (→ `siap_diambil`) or reject (→ `ditolak`) a pending request, syncing `salinan_buku.status_ketersediaan`
- [ ] Approval starts a 2x24h pickup window; if not picked up in time, status auto-becomes `dibatalkan`
- [ ] Pustakawan can mark a book as physically handed over (→ `dipinjam`), starting the 14-day due date (`tanggal_tenggat`)

**Returns & Fines**
- [ ] Pustakawan can process a return (→ `dikembalikan`), comparing `tanggal_kembali` to `tanggal_tenggat`
- [ ] Late returns set `is_diblokir = TRUE` and calculate `total_denda` at Rp 1.000/day overdue
- [ ] A late return triggers an overdue-notification email via the notification service (Brevo integration stubbed/logged in v1)
- [ ] Pustakawan can mark a fine as paid ("Denda Lunas"), clearing `is_diblokir`

**Librarian Dashboard & Member Management**
- [ ] Pustakawan dashboard shows pending approval requests, overdue loans, and basic stats
- [ ] Pustakawan can view the list of mahasiswa members, including blocked status and outstanding fines
- [ ] Mahasiswa can view their own loan history and current due dates

**Deployment**
- [ ] `docker-compose up` runs backend, frontend, and PostgreSQL together for local/demo use

**Non-Functional**
- [ ] API responses complete in under 2 seconds under normal load
- [ ] Frontend is responsive from 375px width upward

### Out of Scope

- Loan renewal (`perpanjangan`) — PRD explicitly fixes the loan period at 14 days with no extension
- Online fine payment — fines are paid in cash to the librarian; the system only tracks status via the "Denda Lunas" action
- Real Brevo API integration — v1 stubs/logs the notification payload; real API wiring is a fast-follow once a Brevo key is available
- OAuth / social login — email + password only, per PRD
- Native mobile app — web frontend only, responsive down to 375px
- Public self-registration for `pustakawan` — librarian accounts are seeded/admin-created only

## Context

- **Course project:** 4-week, 4-person student team (PSI course, post-UTS milestone). The PRD (`docs/PRD.md`) was provided as the assignment brief — table/column names in the Postgres schema are in Bahasa Indonesia per the PRD's explicit note, and this should carry through to the actual schema and likely API payload field names.
- **Design assets exist:** `docs/design/stitch_botanical_scholar_library/` contains a full Stitch-generated design system (`biblio_design_system/DESIGN.md`) plus 6 page mockups with `code.html` reference markup and screenshots: login, katalog_buku, dashboard_pustakawan, form_pengajuan_pinjam, manajemen_anggota, riwayat_peminjaman.
- **Repo state:** `backend/` and `frontend/` directories exist but are currently empty — this is a greenfield build on top of the provided docs.
- **Custom ENUM types** already defined in the PRD: `PERAN_PENGGUNA`, `KONDISI_BUKU`, `STATUS_SALINAN`, `STATUS_PEMINJAMAN` — these drive both the DB schema and the state machine for the loan workflow.

## Constraints

- **Tech stack**: FastAPI + React + PostgreSQL + Docker — fixed by the course PRD, not open for substitution
- **Timeline**: 4 weeks total, 4-person student team — favors a phased build that gets a working vertical slice early
- **Auth**: bcrypt password hashing, JWT sessions with 1-hour expiry (NF02)
- **Performance**: All API responses under 2 seconds under normal load (NF01)
- **Responsiveness**: React frontend must work at 375px width and up (NF03)
- **Schema language**: DB table/column names use Bahasa Indonesia, as specified in the PRD
- **Design system**: UI must follow the Biblio design system (colors, typography, spacing, component styles) defined in `docs/design/stitch_botanical_scholar_library/biblio_design_system/DESIGN.md`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Brevo email integration stubbed (logged) in v1, real API deferred | 4-week timeline; avoids blocking on third-party account/API key setup | — Pending |
| Full `docker-compose` (backend + frontend + db) included in v1 | Needed for reproducible grading/demo | — Pending |
| All 6 Stitch mockup pages in v1 scope | Matches PRD functional requirements; design already exists, no reason to defer | — Pending |
| Pustakawan accounts are seeded only; public registration is mahasiswa-only | Avoids unauthorized librarian self-signup, simpler auth flow | — Pending |
| No loan renewal feature | Explicit in PRD: 14-day period, "tanpa perpanjangan" | — Pending |
| Fines tracked via "Denda Lunas" button, paid in cash | No payment gateway integration needed for a campus library | — Pending |

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
*Last updated: 2026-06-12 after initialization*
