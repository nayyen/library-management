# Plan 02-04 Summary: Frontend Pustakawan Kelola Buku

**Status:** ✅ Complete (awaiting manual checkpoint verification)
**Date:** 2026-06-13
**Requirements:** CAT-03, CAT-04
**Autonomous:** `false` — requires human login check

## Deliverables

### New Components
- `frontend/src/components/BookFormModal.jsx` — Add/Edit buku modal with:
  - Mode toggle (`add` / `edit`) — populates form from `buku` prop in edit mode
  - Client-side validation (ISBN 13-digit + unique check via 409, tahun_terbit range, required fields)
  - Datalist for categories
  - 409 duplicate ISBN display
  - Escape key / backdrop click to close, `aria-modal="true"`
- `frontend/src/components/KelolaTable.jsx` — Admin table with:
  - Striped rows, skeleton loading, EmptyState fallback
  - Columns: Judul (as Link → detail page), Penulis, ISBN, Kategori, Tahun Terbit, Ketersediaan (AvailabilityBadge), Aksi (edit/delete icons)
- `frontend/src/components/TambahSalinanForm.jsx` — Add physical copy form:
  - Lokasi Rak (text), Kondisi (select: bagus/rusak), Status (select: tersedia/dipinjam)
  - `onAdded` callback to append new salinan to parent state
- `frontend/src/components/ConfirmDialog.jsx` — Reusable confirmation modal:
  - `variant="confirm"` with destructive red button + confirm/cancel
  - `variant="info"` with Tutup-only button

### Modified Pages
- `frontend/src/pages/KatalogPage.jsx` — Added tab toggle (Jelajah/Kelola):
  - Pustakawan: sees both tabs; Kelola tab shows KelolaTable + Tambah Buku button + BookFormModal + delete ConfirmDialog with FK-safe 409 handling
  - Mahasiswa: unchanged (Jelajah only, no toggle)
  - Uses `refreshKey` pattern for re-fetch after mutations
- `frontend/src/pages/BukuDetailPage.jsx` — Extended for pustakawan:
  - Edit button (opens BookFormModal in edit mode)
  - TambahSalinanForm below SalinanTable
  - Uses `refreshKey` pattern to re-fetch detail after edit/add copy

## Lint & Test Results
- **ESLint:** 0 errors, 0 warnings across all 6 modified/new files
- **Backend tests:** 19/19 passed (all CRUD, auth, role, FK tests green)

## Key Design Decisions
- `refreshKey` pattern used instead of `fetchBooks`/`fetchBuku` callbacks to avoid `set-state-in-effect` eslint rule violations
- `paramsSerializer: { indexes: null }` in Axios for FastAPI array param compatibility (`?kategori=A&kategori=B` not `?kategori[]=A`)
- Delete flow: confirm dialog → API call → 409 caught → info dialog with FK message → no data loss
- Tab toggle uses conditional rendering based on `peran !== 'pustakawan'` for the toggle itself, and `tab === 'kelola'` for content
