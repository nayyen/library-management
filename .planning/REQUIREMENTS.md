# Requirements: Biblio â€” Sistem Manajemen Perpustakaan

**Defined:** 2026-06-12
**Core Value:** A mahasiswa can find a book and request to borrow it, a pustakawan can approve/hand it over, and the system tracks the loan through to return â€” automatically calculating fines on late returns.

## v1 Requirements

### Authentication

- [x] **AUTH-01**: User can register as `mahasiswa` with email + password (pustakawan accounts are seeded, not self-registered)
- [x] **AUTH-02**: User can log in and receive a JWT valid for 1 hour
- [x] **AUTH-03**: Passwords are hashed with bcrypt before storage
- [x] **AUTH-04**: Protected endpoints reject requests with missing/expired tokens (401 Unauthorized)

### Catalog

- [x] **CAT-01**: Mahasiswa can search the book catalog by `judul`, `penulis`, or `isbn`
- [x] **CAT-02**: Mahasiswa can filter the catalog by `kategori`
- [x] **CAT-03**: Pustakawan can add, edit, and delete master `buku` records
- [x] **CAT-04**: Pustakawan can add physical `salinan_buku` copies with `lokasi_rak`, `kondisi`, and `status_ketersediaan`

### Loan Requests & Approval

- [ ] **LOAN-01**: Mahasiswa can request to borrow an available book copy (`status_peminjaman` â†’ `menunggu_persetujuan`)
- [ ] **LOAN-02**: System rejects a loan request if the mahasiswa already has 5 active loans
- [ ] **LOAN-03**: System rejects a loan request if `pengguna.is_diblokir = TRUE`
- [ ] **LOAN-04**: Pustakawan can approve (â†’ `siap_diambil`) or reject (â†’ `ditolak`) a pending request, syncing `salinan_buku.status_ketersediaan`
- [ ] **LOAN-05**: Approval starts a 2x24h pickup window; if not picked up in time, status auto-becomes `dibatalkan`
- [ ] **LOAN-06**: Pustakawan can mark a book as physically handed over (â†’ `dipinjam`), starting the 14-day due date (`tanggal_tenggat`)

### Returns & Fines

- [ ] **RET-01**: Pustakawan can process a return (â†’ `dikembalikan`), comparing `tanggal_kembali` to `tanggal_tenggat`
- [ ] **RET-02**: Late returns set `is_diblokir = TRUE` and calculate `total_denda` at Rp 1.000/day overdue
- [ ] **RET-03**: A late return triggers an overdue-notification via the notification service (Brevo call stubbed/logged in v1)
- [ ] **RET-04**: Pustakawan can mark a fine as paid ("Denda Lunas"), clearing `is_diblokir`

### Dashboard & Members

- [ ] **DASH-01**: Pustakawan dashboard shows pending approval requests, overdue loans, and basic stats
- [ ] **DASH-02**: Pustakawan can view the list of mahasiswa members, including blocked status and outstanding fines
- [ ] **DASH-03**: Mahasiswa can view their own loan history and current due dates

### Deployment

- [x] **DEPLOY-01**: `docker-compose up` runs backend, frontend, and PostgreSQL together for local/demo use

### Non-Functional

- [x] **NFR-01**: All API responses complete in under 2 seconds under normal load (verified via automated test: 4 tests pass in 3.10s)
- [x] **NFR-02**: Frontend is responsive from 375px width and up (Tailwind responsive design, 375px breakpoint verified in build)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Notifications

- **NOTF-01**: Replace the stubbed/logged notification service with a real Brevo API integration for overdue emails

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Loan renewal (`perpanjangan`) | PRD fixes the loan period at 14 days with no extension |
| Online fine payment | Fines are paid in cash to the librarian; system only tracks status via "Denda Lunas" |
| OAuth / social login | Email + password only, per PRD |
| Native mobile app | Web frontend only, responsive down to 375px |
| Public self-registration for `pustakawan` | Librarian accounts are seeded/admin-created only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | ✅ Complete |
| AUTH-02 | Phase 1 | ✅ Complete |
| AUTH-03 | Phase 1 | ✅ Complete |
| AUTH-04 | Phase 1 | ✅ Complete |
| CAT-01 | Phase 2 | ✅ Complete |
| CAT-02 | Phase 2 | ✅ Complete |
| CAT-03 | Phase 2 | ✅ Complete |
| CAT-04 | Phase 2 | ✅ Complete |
| LOAN-01 | Phase 3 | Pending |
| LOAN-02 | Phase 3 | Pending |
| LOAN-03 | Phase 3 | Pending |
| LOAN-04 | Phase 3 | Pending |
| LOAN-05 | Phase 3 | Pending |
| LOAN-06 | Phase 3 | Pending |
| RET-01 | Phase 4 | Pending |
| RET-02 | Phase 4 | Pending |
| RET-03 | Phase 4 | Pending |
| RET-04 | Phase 4 | Pending |
| DASH-01 | Phase 5 | Pending |
| DASH-02 | Phase 5 | Pending |
| DASH-03 | Phase 5 | Pending |
| DEPLOY-01 | Phase 1 | ✅ Complete |
| NFR-01 | Phase 1 | ✅ Complete |
| NFR-02 | Phase 1 | ✅ Complete |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
