---
status: complete
phase: 03-loan-request-approval-workflow
source: 03-SUMMARY.md, 03-01-SUMMARY.md
started: 2026-06-13T15:30:00Z
updated: 2026-06-13T15:50:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Pinjam button on SalinanTable
expected: Login as mahasiswa. Browse to /katalog/{id} with available copies. SalinanTable shows "Pinjam" button (Sage Green) on each 	ersedia row in a "Aksi" column. Non-tersedia rows show no button.
result: pass

### 2. Blocked/Limit Banner & Disabled Pinjam
expected: Login as mahasiswa who is either blocked (is_diblokir=true) or has 5 active loans. The page shows a persistent banner at top (BlockedBanner) — either "Akun Diblokir" (alert-crimson) or "Batas Pinjaman Tercapai" (antique-gold) with body text explaining why. All Pinjam buttons on SalinanTable are disabled.
result: pass

### 3. LoanRequestModal — 3-section form
expected: Clicking "Pinjam" on a tersedia copy opens a modal titled "Formulir Peminjaman" with 3 sections: Buku Terpilih, Informasi Peminjam, Ringkasan Peminjaman. Footer has Batal and Ajukan Peminjaman.
result: pass

### 4. Submit loan request → Toast feedback
expected: Clicking Ajukan Peminjaman submits via POST /api/peminjaman/ajukan. On success: modal closes, success toast appears. Selected copy's status changes to dipesan.
result: pass

### 5. Pinjaman Saya — mahasiswa view
expected: Navigate to /pinjaman as mahasiswa. Shows Pinjaman Saya table with columns: Buku | Status | Tanggal. Each row shows a StatusBadge pill. Empty state: Belum Ada Pinjaman.
result: pass

### 6. Pustakawan Queue — stacked sections
expected: Login as pustakawan. Shows stacked sections: Menunggu Persetujuan (Mahasiswa | Buku | Tanggal Pengajuan | Aksi) and Siap Diambil (Mahasiswa | Buku | Batas Pengambilan | Aksi).
result: pass

### 7. Approve/Reject with ConfirmDialog
expected: Clicking Setujui opens ConfirmDialog. Confirm -> toast and row moves to Siap Diambil. Tolak also opens ConfirmDialog.
result: pass

### 8. Handover with ConfirmDialog
expected: Clicking Serahkan opens ConfirmDialog Tandai Sudah Diserahkan?. Confirm -> toast and row moves to mahasiswa dipinjam list.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
