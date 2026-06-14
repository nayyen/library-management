---
phase: 04-returns-fines-blocking
plan: 02
type: summary
wave: 2
status: completed
completed_at: "2026-06-13"
requirements: [RET-04]
tests_performed:
  test_file: backend/tests/test_peminjaman.py
  count_before: 24
  count_after: 28
  verdict: GREEN
frontend_build: PASS
---

# Summary — Plan 04-02: Unblock Slice (RET-04)

## Objective

Deliver the unblock vertical slice end-to-end: a pustakawan opens the new "Anggota Diblokir" section, sees a card per blocked member with their summed outstanding denda, clicks "Denda Lunas", confirms, and the backend clears `is_diblokir` (leaving historical `total_denda` rows untouched).

## Files Modified

### Backend

- **`backend/tests/test_peminjaman.py`** — Added 4 test functions:
  - `test_lunasi_denda_clears_block`: Pustakawan unblocks a blocked member → 200, `is_diblokir=False`, denda rows unchanged (D-05)
  - `test_lunasi_denda_forbidden_for_mahasiswa`: Mahasiswa token → 403
  - `test_lunasi_denda_404`: Unknown id_pengguna → 404
  - `test_list_pustakawan_anggota_diblokir`: Two dikembalikan loans (16000+4000) → `total_denda==20000`; non-blocked member excluded
- **`backend/app/schemas/peminjaman.py`** — Added `AnggotaDiblokirOut` class with `id_pengguna`, `nama`, `email`, `total_denda`; extended `PeminjamanResponse` with `anggota_diblokir` field and `denda_tertunggak` (for Wave 3)
- **`backend/app/routers/peminjaman.py`** — Added `lunasi_denda` endpoint (`PUT /api/peminjaman/anggota/{id_pengguna}/lunasi_denda`): pustakawan-only, 404 on missing member, sets `is_diblokir=False`, preserves historical denda (D-05). Added `anggota_diblokir` aggregate list in pustakawan GET branch: queries blocked users, computes `SUM(total_denda)` per member over `dikembalikan` loans (D-06)

### Frontend

- **`frontend/src/pages/PinjamanPage.jsx`** — Added `handleLunasiDenda` mutation handler (pattern matches `handleKembalikan`), `anggotaDiblokir` derived const, "Anggota Diblokir" card-list `<section>` (4th pustakawan section) with header, per-card markup (avatar initial, name, email, crimson "Denda Tertunggak" amount, Sage Green "Denda Lunas" button with `lock_open` icon), empty state `Tidak Ada Anggota Diblokir`. Updated skeleton count to 4 sections.

## Key Decisions

- D-04: "Anggota Diblokir" section lists `is_diblokir=true` members as cards with summed denda
- D-05: Clearing the block (`is_diblokir=False`) leaves historical `total_denda` rows untouched
- D-06: Per-member denda = `SUM(total_denda)` over `dikembalikan` loans

## Test Results

```
28 passed in 43.21s
```

## Build

```
npm run build → Γ£ô built in 3.11s
```
