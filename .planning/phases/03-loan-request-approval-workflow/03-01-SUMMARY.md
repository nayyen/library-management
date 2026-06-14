# Plan 03-01 SUMMARY: Peminjaman Backend API

**Phase:** 3 — Loan Request & Approval Workflow
**Plan:** 01
**Status:** ✅ Complete

## What was built

### Files created
- `backend/app/schemas/peminjaman.py` — Pydantic v2 schemas
- `backend/app/routers/peminjaman.py` — All loan endpoints
- `backend/tests/test_peminjaman.py` — 17 RED→GREEN tests

### Files modified
- `backend/app/main.py` — registered `peminjaman.router`
- `backend/app/models/peminjaman.py` — added `pengguna` + `salinan_buku` relationships
- `backend/app/models/salinan_buku.py` — added `buku` + `peminjaman` relationships
- `backend/app/models/pengguna.py` — added `peminjaman` relationship
- `backend/app/models/buku.py` — added `salinan` relationship

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/peminjaman/ajukan` | Mahasiswa requests a loan | Mahasiswa only |
| GET | `/api/peminjaman` | Shared list (role-conditional) | Any authenticated |
| PUT | `/api/peminjaman/{id}/persetujuan` | Approve/reject pending request | Pustakawan only |
| PUT | `/api/peminjaman/{id}/serahkan` | Handover approved loan | Pustakawan only |

### Requirements covered
- **LOAN-01** — Mahasiswa can request to borrow (→ `menunggu_persetujuan`, salinan → `dipesan`)
- **LOAN-02** — 5-active-loan limit enforced (400), using `ACTIVE_STATUSES = [menunggu_persetujuan, siap_diambil, dipinjam]`
- **LOAN-03** — `is_diblokir` check enforced (400); mahasiswa GET response exposes top-level `is_diblokir`
- **LOAN-04** — Pustakawan approve (→ `siap_diambil` + `tanggal_siap_ambil`) / reject (→ `ditolak`, salinan → `tersedia`)
- **LOAN-05** — Lazy 2x24h pickup sweep on every GET (no worker, D-12)
- **LOAN-06** — Handover (→ `dipinjam`, salinan → `dipinjam`, `tanggal_tenggat` = now + 14 days)

### Response shape for mahasiswa GET
```json
{
  "items": [/* PeminjamanItemOut sorted most-recent-first */],
  "total": 2,
  "is_diblokir": false   // ← LOAN-03 banner data source (D-04)
}
```

### Response shape for pustakawan GET
```json
{
  "menunggu_persetujuan": [/* pending items */],
  "siap_diambil": [/* approved-not-yet-handed-over items */]
}
```

### PeminjamanItemOut fields
`id`, `status_peminjaman`, `judul`, `penulis`, `lokasi_rak`, `nama_mahasiswa`, `tanggal_pengajuan`, `tanggal_siap_ambil`, `tanggal_tenggat` (all datetime fields ISO-8601 strings, may include timezone info)

### Test results
- 17 peminjaman tests: ✅ ALL GREEN
- Full backend suite (36 tests): ✅ ALL GREEN (no Phase 1/2 regressions)

### Key implementation decisions
- **Unified response model**: `PeminjamanResponse` has nullable fields for both role branches; the mahasiswa branch populates `items`/`total`/`is_diblokir`, the pustakawan branch populates `menunggu_persetujuan`/`siap_diambil`.
- **ACTIVE_STATUSES**: `[menunggu_persetujuan, siap_diambil, dipinjam]` — these 3 statuses count toward the 5-loan limit.
- **Lazy sweep**: executed at the start of every GET /api/peminjaman (`_sweep_expired_pickups`), using `tanggal_siap_ambil + timedelta(days=2) < now` — timezone-aware comparison with `datetime.now(timezone.utc)`.
