# Requirements: Biblio — Sistem Manajemen Perpustakaan

**Defined:** 2026-06-12
**Core Value:** A mahasiswa can find a book and request to borrow it, a pustakawan can approve/hand it over, and the system tracks the loan through to return — automatically calculating fines on late returns.

## v1 Requirements

### Authentication

- [ ] **AUTH-01**: User can register as `mahasiswa` with email + password (pustakawan accounts are seeded, not self-registered)
- [ ] **AUTH-02**: User can log in and receive a JWT valid for 1 hour
- [ ] **AUTH-03**: Passwords are hashed with bcrypt before storage
- [ ] **AUTH-04**: Protected endpoints reject requests with missing/expired tokens (401 Unauthorized)

### Catalog

- [ ] **CAT-01**: Mahasiswa can search the book catalog by `judul`, `penulis`, or `isbn`
- [ ] **CAT-02**: Mahasiswa can filter the catalog by `kategori`
- [ ] **CAT-03**: Pustakawan can add, edit, and delete master `buku` records
- [ ] **CAT-04**: Pustakawan can add physical `salinan_buku` copies with `lokasi_rak`, `kondisi`, and `status_ketersediaan`

### Loan Requests & Approval

- [ ] **LOAN-01**: Mahasiswa can request to borrow an available book copy (`status_peminjaman` → `menunggu_persetujuan`)
- [ ] **LOAN-02**: System rejects a loan request if the mahasiswa already has 5 active loans
- [ ] **LOAN-03**: System rejects a loan request if `pengguna.is_diblokir = TRUE`
- [ ] **LOAN-04**: Pustakawan can approve (→ `siap_diambil`) or reject (→ `ditolak`) a pending request, syncing `salinan_buku.status_ketersediaan`
- [ ] **LOAN-05**: Approval starts a 2x24h pickup window; if not picked up in time, status auto-becomes `dibatalkan`
- [ ] **LOAN-06**: Pustakawan can mark a book as physically handed over (→ `dipinjam`), starting the 14-day due date (`tanggal_tenggat`)

### Returns & Fines

- [ ] **RET-01**: Pustakawan can process a return (→ `dikembalikan`), comparing `tanggal_kembali` to `tanggal_tenggat`
- [ ] **RET-02**: Late returns set `is_diblokir = TRUE` and calculate `total_denda` at Rp 1.000/day overdue
- [ ] **RET-03**: A late return triggers an overdue-notification via the notification service (Brevo call stubbed/logged in v1)
- [ ] **RET-04**: Pustakawan can mark a fine as paid ("Denda Lunas"), clearing `is_diblokir`

### Dashboard & Members

- [ ] **DASH-01**: Pustakawan dashboard shows pending approval requests, overdue loans, and basic stats
- [ ] **DASH-02**: Pustakawan can view the list of mahasiswa members, including blocked status and outstanding fines
- [ ] **DASH-03**: Mahasiswa can view their own loan history and current due dates

### Deployment

- [ ] **DEPLOY-01**: `docker-compose up` runs backend, frontend, and PostgreSQL together for local/demo use

### Non-Functional

- [ ] **NFR-01**: All API responses complete in under 2 seconds under normal load
- [ ] **NFR-02**: Frontend is responsive from 375px width and up

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
| AUTH-01 | TBD | Pending |
| AUTH-02 | TBD | Pending |
| AUTH-03 | TBD | Pending |
| AUTH-04 | TBD | Pending |
| CAT-01 | TBD | Pending |
| CAT-02 | TBD | Pending |
| CAT-03 | TBD | Pending |
| CAT-04 | TBD | Pending |
| LOAN-01 | TBD | Pending |
| LOAN-02 | TBD | Pending |
| LOAN-03 | TBD | Pending |
| LOAN-04 | TBD | Pending |
| LOAN-05 | TBD | Pending |
| LOAN-06 | TBD | Pending |
| RET-01 | TBD | Pending |
| RET-02 | TBD | Pending |
| RET-03 | TBD | Pending |
| RET-04 | TBD | Pending |
| DASH-01 | TBD | Pending |
| DASH-02 | TBD | Pending |
| DASH-03 | TBD | Pending |
| DEPLOY-01 | TBD | Pending |
| NFR-01 | TBD | Pending |
| NFR-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 0
- Unmapped: 24 ⚠️ (mapped during roadmap creation)

---
*Requirements defined: 2026-06-12*
*Last updated: 2026-06-12 after initial definition*
