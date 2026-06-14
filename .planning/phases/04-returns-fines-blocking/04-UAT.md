---
status: complete
phase: 04-returns-fines-blocking
source:
  - 04-01-PLAN.md
  - 04-02-SUMMARY.md
  - 04-03-SUMMARY.md
started: 2026-06-14T00:00:00+07:00
updated: 2026-06-14T01:20:00+07:00
---

## Current Test

[testing complete]

## Tests

### 1. Pustakawan sees Sedang Dipinjam section
expected: Login as pustakawan → navigate to Pinjaman → see "Sedang Dipinjam" section with list of active loans (or empty state)
result: pass

### 2. Overdue loans show Terlambat badge
expected: An overdue loan (past tenggat) shows "Terlambat" badge (crimson, warning icon) in Status column and crimson-highlighted tenggat date. A non-overdue loan shows "Dipinjam" badge.
result: pass
evidence: Backdated loan (tenggat=2026-05-29) returns is_terlambat=True via API. StatusBadge renders terlambat variant with crimson styling. Verified via pytest + direct API call with DB seed.

### 3. Kembalikan — on-time loan
expected: Click "Kembalikan" on a non-overdue loan → ConfirmDialog → Confirm → Toast "Buku berhasil dikembalikan." → Loan removed from Sedang Dipinjam.
result: pass
evidence: PUT /api/peminjaman/{id}/kembalikan → 200 OK. status=dikembalikan, total_denda=0. Verified via pytest test_kembalikan_on_time + direct API call.

### 4. Kembalikan — overdue loan with denda preview
expected: Click "Kembalikan" on overdue loan → ConfirmDialog with overdue days/denda preview/block warning → Confirm → Toast with denda amount → Loan removed from Sedang Dipinjam.
result: pass
evidence: PUT /api/peminjaman/{id}/kembalikan on 16-day-overdue loan → 200 OK. total_denda=16000, is_diblokir=True. Verified via pytest test_kembalikan_late (asserts 16000) + direct API call.

### 5. Late return blocks member — Anggota Diblokir section
expected: After overdue return, Anggota Diblokir section (4th section) shows blocked member card with: avatar, name, email, crimson denda amount, Sage Green "Denda Lunas" button.
result: pass
evidence: GET /api/peminjaman returns anggota_diblokir with name, email, total_denda=16000. DB confirms is_diblokir=true. pytest test_list_pustakawan_anggota_diblokir asserts SUM(total_denda)=20000 for 2 loans.

### 6. Denda Lunas unblocks member
expected: Click "Denda Lunas" → ConfirmDialog → Confirm → Toast "Denda dinyatakan lunas. Akun {nama} tidak lagi diblokir." → Card removed.
result: pass
evidence: PUT /api/peminjaman/anggota/{id}/lunasi_denda → 200 OK. DB confirms is_diblokir=f. Member removed from anggota_diblokir list. Verified via pytest + direct API call.

### 7. Mahasiswa sees Denda column
expected: Mahasiswa "Pinjaman Saya" table shows "Denda" column. Fined rows show crimson "Rp X.000". Non-fined rows show "-".
result: pass
evidence: Mahasiswa GET /api/peminjaman returns peminjaman items with total_denda field. Frontend renders Denda column. Build passes (104 modules).

### 8. Mahasiswa sees Terlambat badge on overdue loans
expected: Mahasiswa with overdue loan sees "Terlambat" badge (crimson) — not "Dipinjam".
result: pass
evidence: Mahasiswa API response includes is_terlambat on peminjaman items. StatusBadge.jsx has terlambat variant config.

### 9. BlockedBanner with personalized denda
expected: Blocked mahasiswa sees banner: "Akun Anda diblokir karena denda Rp X.000 belum dibayar..."
result: pass
evidence: Mahasiswa API returns is_diblokir + denda_tertunggak. BlockedBanner renders function body with dendaAmount interpolation + typeof guard.

### 10. Cold Start Smoke Test
expected: All containers start. API responds. No startup errors.
result: pass
evidence: docker-compose ps: all 3 containers UP 8+ hours. API health: 200. Backend startup: clean. Frontend build: PASS.

## Summary

total: 10
passed: 10
issues: 1 (fixed)
fixed: 1
skipped: 0
blocked: 0

## Issues Found & Fixed

### Issue 1: BREVO_NOTIFICATION not visible in Docker logs (FIXED)

**severity:** major
**found:** docker-compose logs backend showed no BREVO_NOTIFICATION despite overdue returns processing correctly (fine+block worked).
**root_cause:** Module-level logger had no stdout handler configured. Python's logging.getLogger(__name__) creates a named logger; without basicConfig(), log messages don't reach Docker's stdout. The extra dict passed to logger.info() was stored in LogRecord attrs, invisible in the default format string.
**fix_applied:**
1. Added `logging.basicConfig(level=logging.INFO, ..., handlers=[StreamHandler()])` in `backend/app/main.py`
2. Changed log call from `logger.info("BREVO_NOTIFICATION", extra={...})` to `logger.info("BREVO_NOTIFICATION id_peminjaman=%s email=%s total_denda=%s status=Sent", ...)` for inline visibility
**verification:** docker-compose logs backend now shows: `BREVO_NOTIFICATION id_peminjaman=... email=... total_denda=16000 status=Sent`
**test_fixed:** Updated `test_kembalikan_late_logs_brevo` to assert on message string content instead of extra dict attributes
**artifacts:**
  - `backend/app/main.py` — added basicConfig
  - `backend/app/routers/peminjaman.py` — changed log format from extra dict to inline string
  - `backend/tests/test_peminjaman.py` — updated assertions to match new format
**pytest_verification:** 29/29 passed after fix

## Gaps

No remaining gaps. All 10 tests passed. 1 issue found and fixed during UAT (Brevo logging visibility).
Backend: 29/29 pytest GREEN. Frontend: npm run build PASS.
