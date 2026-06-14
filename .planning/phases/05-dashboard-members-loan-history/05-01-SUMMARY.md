# Plan 05-01 Summary — Dashboard (DASH-01)

**Completed:** 2026-06-14

## Artifacts Created

### Backend
- `backend/app/schemas/dashboard.py` — `DashboardStatsOut` with 7 fields (total_buku, peminjaman_aktif, menunggu_persetujuan_count, buku_terlambat, total_denda_belum_lunas, jumlah_mahasiswa_denda, pengajuan_preview)
- `backend/app/routers/dashboard.py` — `GET /api/dashboard/stats` aggregation endpoint, pustakawan-gated, with `_pustakawan_only`, `_is_terlambat`, `_sweep_expired_pickups`, `_build_item_out` helpers
- `backend/tests/test_dashboard.py` — 7 tests covering: 403 gate, Total Buku, Peminjaman Aktif (siap_diambil + dipinjam only), Buku Terlambat (via `_is_terlambat`), Total Denda Belum Lunas + jumlah_mahasiswa, Pengajuan Preview (max 5 newest first), empty state

### Frontend
- `frontend/src/pages/DashboardPage.jsx` — 4 stat cards (Total Buku ink-blue, Peminjaman Aktif antique-gold with sub-stat, Buku Terlambat alert-crimson clickable card with border-l to /pinjaman, Total Denda Belum Lunas sage-green with sub-stat) + read-only pending-approval preview table with "Lihat Semua" link + loading skeleton + error EmptyState

### Modified
- `backend/app/main.py` — added `dashboard` to imports and `app.include_router(dashboard.router)`
- `frontend/src/router.jsx` — replaced `ComingSoonPage` placeholder with `<DashboardPage />`

## Tests
- Backend: 7/7 dashboard tests GREEN
- Full backend suite: 55/55 GREEN
- Frontend build: PASS

## Fixes
- `_sweep_expired_pickups` uses cutoff comparison (`tanggal_siap_ambil < cutoff` instead of `tanggal_siap_ambil + timedelta(days=2) < now`) for SQLite compatibility
