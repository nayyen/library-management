# Phase 3 — Loan Request & Approval Workflow — Summary

## Goal

A mahasiswa can request to borrow an available book copy, the system enforces loan-limit and block rules, and a pustakawan can approve or reject the request, manage the pickup window, and hand the book over to start the loan.

## Duration

Started: 2026-06-13
Completed: 2026-06-13

## Plans Executed

| Plan | Wave | Name | Files Changed | Status |
|------|------|------|---------------|--------|
| 03-01 | 1 | Backend peminjaman API | 7 files (4 new + 3 modified) | ✅ Complete |
| 03-02 | 2 | Mahasiswa loan-request UI | 7 files (4 new + 3 modified) | ✅ Complete |
| 03-03 | 3 | Pustakawan queue UI | 1 file (PinjamanPage.jsx) | ✅ Complete |

### Commit Summary

```
d0cc231 feat(03-01): peminjaman API — schemas, router, RED→GREEN tests for all 6 LOAN requirements
98d60e2 feat(03-02): mahasiswa loan-request UI — StatusBadge, BlockedBanner, LoanRequestModal, wired Pinjam on SalinanTable/BukuDetailPage, PinjamanPage + router
3b737a6 feat(03-03): pustakawan approve/reject/handover UI — wired action buttons with ConfirmDialog in PinjamanPage
```

## New Files Created

### Backend (`backend/app/`)
- `schemas/peminjaman.py` — Pydantic v2 schemas (PeminjamanAjukan, PeminjamanItemOut, PeminjamanResponse, PersetujuanBody)
- `routers/peminjaman.py` — 4 endpoints (ajukan, list, persetujuan, serahkan) + lazy sweep + helpers

### Tests (`backend/tests/`)
- `test_peminjaman.py` — 17 RED→GREEN tests covering all LOAN requirements

### Frontend (`frontend/src/`)
- `components/StatusBadge.jsx` — 5-status pill badge (menunggu_persetujuan/siap_diambil/dipinjam/ditolak/dibatalkan)
- `components/BlockedBanner.jsx` — 2-variant persistent banner (limit/blocked)
- `components/LoanRequestModal.jsx` — 3-section loan request confirmation modal
- `pages/PinjamanPage.jsx` — Shared page: mahasiswa Pinjaman Saya table + pustakawan approve/reject/handover queue

## Modified Files

### Backend
- `models/peminjaman.py` — Added SQLAlchemy relationships (pengguna, salinan_buku)
- `models/salinan_buku.py` — Added relationships (buku, peminjaman)
- `models/pengguna.py` — Added relationship (peminjaman)
- `models/buku.py` — Added relationship (salinan)
- `main.py` — Registered peminjaman router

### Frontend
- `components/SalinanTable.jsx` — Added Aksi column with Pinjam button for mahasiswa role
- `pages/BukuDetailPage.jsx` — Wire BlockedBanner, LoanRequestModal, loan-info fetching
- `router.jsx` — Replace ComingSoonPage with PinjamanPage

## Requirements Coverage

| Req | Description | Coverage | Verification |
|-----|-------------|----------|--------------|
| LOAN-01 | Mahasiswa submits loan request | `POST /api/peminjaman/ajukan` + LoanRequestModal UI | test_ajukan_peminjaman_mahasiswa ✅ |
| LOAN-02 | 5-active-loan limit enforced | 400 error on backend, BlockedBanner UI | test_ajukan_rejected_at_loan_limit ✅ |
| LOAN-03 | Blocked account rejected | 400 error on backend, BlockedBanner UI | test_ajukan_rejected_when_blocked ✅ |
| LOAN-04 | Pustakawan approve/reject | `PUT /api/peminjaman/{id}/persetujuan` + ConfirmDialog | test_persetujuan_setujui ✅, test_persetujuan_tolak ✅ |
| LOAN-05 | 2x24h pickup auto-cancellation | Lazy sweep inside GET /api/peminjaman | test_sweep_expired_pickup ✅ |
| LOAN-06 | Handover → dipinjam + 14 day tenggat | `PUT /api/peminjaman/{id}/serahkan` + UI | test_serahkan ✅ |

## Test Results

- All 36 backend tests GREEN (19 existing + 17 new)
- All 3 frontend components lint-clean, build passes

## Key Decisions

- LOAN-05 auto-cancellation: lazy check-on-read (sweep runs on list fetch), no background scheduler
- "Serahkan" button: Ink Blue (`bg-ink-blue`) per D-14
- "Pinjam" button: Sage Green (`bg-sage-green`) per D-13 (keeps Phase 2 intent)
- shadcn: not introduced — all Phase 3 components are hand-built React + Tailwind
- Modal sizing: `LoanRequestModal` uses `max-w-lg` (3-section layout), wider than `BookFormModal`'s `max-w-md`

## Human Checkpoints (Deferred)

1. **Mahasiswa flow**: Login as mahasiswa → browse catalog → request loan → view Pinjaman Saya
2. **Pustakawan flow**: Login as pustakawan → view queue → approve/reject request → handover book
