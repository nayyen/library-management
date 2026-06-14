status: complete
phase: 05-dashboard-members-loan-history
source: 05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md
started: 2026-06-14T12:00:00Z
updated: 2026-06-14T12:10:00Z

## Current Test

[testing complete]

## Tests

### 1. Dashboard Stat Cards
expected: Login as pustakawan, navigate to /dashboard, see 4 stat cards with correct counts and styling
result: pass
evidence: |
  - 7/7 pytest tests GREEN (403 gate, total_buku, peminjaman_aktif, buku_terlambat, denda, pengajuan_preview, empty)
  - Live API returns 200 with all 7 fields: total_buku=11, peminjaman_aktif=0, menunggu_persetujuan_count=3, buku_terlambat=0, total_denda_belum_lunas=16000, jumlah_mahasiswa_denda=1, pengajuan_preview=[3 items]
  - Frontend renders 4 stat cards mapping each API field to correct icon (ink-blue/antique-gold/alert-crimson/sage-green), clickable Buku Terlambat card linked to /pinjaman

### 2. Dashboard Pending Approval Preview
expected: Below stat cards, a section titled "Daftar Pengajuan Peminjaman" with a table showing pending loans (mahasiswa name, book title, tanggal_pengajuan). "Lihat Semua" link on the right navigates to /pinjaman. If none pending, shows empty state.
result: pass
evidence: |
  - Live API pengajuan_preview returns 3 items newest first, each with id/judul/penulis/nama_mahasiswa/tanggal_pengajuan
  - Frontend renders section with "Daftar Pengajuan Peminjaman" title, Mahasiswa/Buku/Tanggal columns, "Lihat Semua" link, and EmptyState when empty

### 3. Dashboard Loading & Error States
expected: While dashboard loads, see pulse-animation skeleton cards. If API fails, see EmptyState with "Gagal Memuat" message and "Coba Lagi" button.
result: pass
evidence: |
  - StatSkeleton component with animate-pulse renders when loading || !data (4 skeleton cards in grid)
  - EmptyState with icon="error_outline", title="Gagal Memuat", actionLabel="Coba Lagi" wired to fetchStats on error

### 4. Dashboard Mahasiswa 403
expected: Login as mahasiswa, navigate to /dashboard. API returns 403, page shows error/gagal memuat state.
result: pass
evidence: |
  - Live API: mahasiswa GET /api/dashboard/stats → 403 "Akses ditolak."
  - pytest: test_dashboard_stats_403_for_mahasiswa PASSED
  - _pustakawan_only gate at top of endpoint before any data processing

### 5. Anggota Page Member Roster
expected: Login as pustakawan, navigate to /anggota. See a 2-column responsive card grid of all registered mahasiswa with avatar/nama/email/StatusBadge/pinjaman_aktif/total_denda.
result: pass
evidence: |
  - 5/5 pytest tests GREEN (403 gate, only_mahasiswa, pinjaman_aktif, total_denda, ordering)
  - Live API returns 13 members sorted by nama with all 6 fields (id_pengguna, nama, email, is_diblokir, pinjaman_aktif, total_denda)
  - Frontend: 2-col grid with avatar (primary-fixed vs alert-crimson/10), StatusBadge (anggota_aktif/anggota_diblokir iconless), info cards, Denda Lunas action row

### 6. Anggota Page Search & Filter
expected: Search input filters cards client-side by name/email. Status filter (Semua/Aktif/Diblokir). Combined filtering. Empty state when no matches.
result: pass
evidence: |
  - Client-side filter via filteredMembers using matchesSearch (nama/email toLowerCase) && matchesStatus (diblokir boolean check)
  - Search input with antique-gold focus ring, placeholder "Cari berdasarkan Nama, Email..."
  - Select dropdown with 3 options (Semua/Aktif/Diblokir), antique-gold focus styling
  - EmptyState "Tidak Ditemukan" with search_off icon when filter yields no results

### 7. Anggota Page Denda Lunas
expected: Denda Lunas confirms via dialog, calls API, shows toast, unblocks member, refreshes roster.
result: pass
evidence: |
  - Live API: PUT /api/peminjaman/anggota/{id}/lunasi_denda → 200 OK, is_diblokir flipped False, historical denda preserved (Rp 16.000)
  - Verified via re-GET that member unblocked and historical denda persists
  - Frontend: ConfirmDialog with amount, Toast success/error, refreshKey triggers re-fetch
  - Button only renders when is_diblokir && total_denda > 0, sage-green with lock_open icon

### 8. PinjamanPage Dikembalikan Date Cell
expected: TanggalCell shows "Dikembalikan {date}" for returned loans.
result: pass
evidence: |
  - Frontend code: TanggalCell line 61-62: if (status === 'dikembalikan') { return <>Dikembalikan {formatDate(item.tanggal_kembali)}</>; }
  - Schema: PeminjamanItemOut includes tanggal_kembali: datetime | None = None
  - Frontend build: 106 modules, 0 errors

### 9. PinjamanPage Anggota Diblokir Section Removed
expected: "Anggota Diblokir" section and handleLunasiDenda function no longer on PinjamanPage.
result: pass
evidence: |
  - grep search confirms: "Anggota Diblokir", "handleLunasiDenda", "anggota_diblokir" all REMOVED
  - Remaining diblokir references are correct (return dialog text, current user's BlockedBanner)

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

