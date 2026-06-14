---
status: complete
phase: 02-book-catalog
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
  - 02-04-SUMMARY.md
started: 2026-06-13T10:00:00+07:00
updated: 2026-06-13T10:30:00+07:00
---

## Current Test

[testing complete]

## Tests

### 1. Search catalog by judul, penulis, or isbn
expected: Typing in search bar filters book grid (debounced ~300ms). Searching "Gadis" shows matching results. Non-existent term shows "Buku Tidak Ditemukan" empty state. Clearing search restores full catalog.
result: pass

### 2. Filter catalog by kategori
expected: Category filter sidebar shows Fiksi, Non-Fiksi, Referensi checkboxes. Selecting one filters accordingly. Multi-select combines with OR. Deselecting all restores full catalog. Filter + search work together.
result: pass

### 3. Book detail page
expected: Clicking a book card navigates to `/katalog/{id}` showing cover placeholder, title, author, metadata (Kategori, ISBN, Tahun Terbit), availability badge, and Salinan Buku table with rak/kondisi/status per copy. "Kembali ke Katalog" navigates back. Books with no available copies show "Tidak Tersedia".
result: pass

### 4. Pustakawan tab toggle (Jelajah/Kelola)
expected: Pustakawan sees Jelajah/Kelola tab toggle on catalog page. Jelajah is default (browse grid). Kelola shows admin table with columns Judul, Penulis, ISBN, Kategori, Tahun Terbit, Ketersediaan, Aksi + "Tambah Buku" button. Mahasiswa does NOT see the toggle.
result: pass

### 5. Pustakawan add/edit/delete buku
expected: "Tambah Buku" opens modal with judul/penulis/isbn/kategori/tahun_terbit fields. Saving adds to table. Edit icon re-opens modal pre-filled; saving updates row. Delete icon shows "Hapus Buku?" confirmation; confirming removes the book from table.
result: pass

### 6. FK-safe delete block + Tambah Salinan
expected: Deleting a book with existing copies shows "Tidak Dapat Dihapus" dialog with "Buku masih memiliki N salinan fisik." Book is NOT deleted. On detail page, pustakawan sees "Tambah Salinan" form (lokasi_rak, kondisi, status). Submitting adds a new row to salinan table.
result: pass

### 7. Mahasiswa does not see admin controls
expected: Logged in as mahasiswa, catalog shows only Jelajah view — search, filter, grid. No tab toggle, no "Tambah Buku", no edit/delete. Detail page has no Edit button or Tambah Salinan form.
result: pass

## Summary

total: 7
passed: 7
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

No gaps found. All tests passed.
