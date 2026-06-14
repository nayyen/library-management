---
phase: 04-returns-fines-blocking
plan: 03
type: summary
wave: 3
status: completed
completed_at: "2026-06-13"
requirements: [RET-02]
tests_performed:
  test_file: backend/tests/test_peminjaman.py
  count_before: 28
  count_after: 29
  verdict: GREEN
frontend_build: PASS
---

# Summary — Plan 04-03: Mahasiswa Visibility (RET-02)

## Objective

Deliver the mahasiswa-visibility vertical slice: the backend returns `denda_tertunggak` on the mahasiswa GET branch, and "Pinjaman Saya" gains a "Denda" column, a "Terlambat" badge on overdue active loans, and a BlockedBanner personalized with the actual denda amount.

## Files Modified

### Backend

- **`backend/tests/test_peminjaman.py`** — Added `test_list_mahasiswa_denda_tertunggak`: member with two `dikembalikan` loans (5000+0) → `denda_tertunggak==5000`
- **`backend/app/routers/peminjaman.py`** — Mahasiswa GET branch now computes `denda_tertunggak = SUM(total_denda)` over the user's own `dikembalikan` loans (scoped by `id_pengguna == user.id`)

### Frontend

- **`frontend/src/components/BlockedBanner.jsx`** — `blocked.body` changed from static string to `(dendaAmount) => ...` function; component signature changed to `BlockedBanner({ variant, dendaAmount })`; render uses `typeof config.body === 'function'` guard; `limit` variant body remains a plain string (unchanged)
- **`frontend/src/pages/PinjamanPage.jsx`** — Three changes:
  1. BlockedBanner call site wired with `dendaAmount={loanData?.denda_tertunggak ?? 0}`
  2. Mahasiswa "Pinjaman Saya" table: added right-aligned "Denda" `<th>` as 4th header; added `<td>` rendering `Rp {amount}` in crimson for `dikembalikan` loans with `total_denda>0`, `-` otherwise; Status cell swapped to `<StatusBadge status={item.is_terlambat ? 'terlambat' : item.status_peminjaman}>` (D-08)
  3. `SkeletonRows` updated with 4th `<td>` skeleton cell (float-right)

## Key Decisions

- D-07: "Denda" column on Pinjaman Saya — crimson amount for fined rows, `-` otherwise
- D-08: Terlambat badge on the mahasiswa's overdue active loans (same as pustakawan view)
- D-09: BlockedBanner personalized with the actual outstanding denda amount

## Test Results

```
29 passed in 45.09s
```

## Build

```
npm run build → Γ£ô built in 3.01s
```
