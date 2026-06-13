# Plan 02-03 Summary: Backend Pustakawan CRUD

**Status:** ✅ Complete  
**Date:** 2026-06-13  
**Requirements:** CAT-03, CAT-04  

## Deliverables

### Modified
- `backend/app/routers/buku.py` — Added 4 mutation endpoints:
  - POST /api/buku (create buku, pustakawan-only, duplicate ISBN → 409)
  - PUT /api/buku/{id} (update buku, pustakawan-only, partial update)
  - DELETE /api/buku/{id} (delete buku, FK-safe — blocks with 409 if copies exist)
  - POST /api/buku/{id}/salinan (add copy, pustakawan-only)
- `backend/tests/test_buku.py` — Added 8 CRUD/role/FK tests

## Test Results
- `test_create_buku_pustakawan` ✅ — 201 with created buku
- `test_create_buku_forbidden_for_mahasiswa` ✅ — 403
- `test_create_buku_duplicate_isbn` ✅ — 409 with Indonesian detail
- `test_edit_buku` ✅ — Update + unknown ID → 404
- `test_delete_buku_no_salinan` ✅ — 204 + book removed
- `test_delete_buku_with_salinan_blocked` ✅ — 409 with FK message
- `test_add_salinan` ✅ — 201 + appears in detail
- `test_add_salinan_forbidden_for_mahasiswa` ✅ — 403
- All 11 read/auth tests still GREEN

## Key Design Decisions
- `_pustakawan_only()` helper extracted to avoid duplication across 4 handlers
- FK-safe: DELETE blocked with `Buku masih memiliki N salinan fisik.` when copies exist
- `tambah_salinan` converts string enum values ("bagus", "tersedia") via `KondisiBuku(body.kondisi)` / `StatusSalinan(body.status_ketersediaan)`
- Pre-check + IntegrityError double guard for duplicate ISBN
