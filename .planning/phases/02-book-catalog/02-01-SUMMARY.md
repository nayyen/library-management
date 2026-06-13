# Plan 02-01 Summary: Backend Catalog Read API

**Status:** ✅ Complete  
**Date:** 2026-06-13  
**Requirements:** CAT-01, CAT-02  

## Deliverables

### Created
- `backend/app/schemas/buku.py` — Pydantic schemas: BukuCreate, BukuUpdate, BukuOut, BukuListItem, BukuListOut, BukuDetailOut, SalinanBukuCreate, SalinanBukuOut
- `backend/app/routers/buku.py` — Read endpoints: GET /api/buku (search+filter), GET /api/buku/kategori, GET /api/buku/{id}
- `backend/tests/test_buku.py` — 7 tests (6 read + 1 unauthorized)

### Modified
- `backend/app/main.py` — Registered `buku.router`
- `backend/app/seed.py` — Added `seed_buku()` with 11 buku + 14 salinan copies (mixed availability)
- `backend/app/dependencies/auth.py` — Fixed UUID comparison for SQLite compatibility

## Test Results
- `test_list_buku` ✅ — Returns all books with derived `tersedia` flag
- `test_search_buku` ✅ — Search by judul/penulis/isbn (case-insensitive)
- `test_filter_kategori` ✅ — Single and multi-category (OR) filter
- `test_kategori_endpoint` ✅ — Distinct sorted categories
- `test_detail_buku` ✅ — Book detail with salinan list
- `test_detail_buku_404` ✅ — Unknown ID returns 404
- `test_list_buku_unauthorized` ✅ — Missing token returns 401
- All 4 auth tests still GREEN

## Seed Data
- 11 books across Fiksi (4), Non-Fiksi (4), Referensi (3)
- Mixed availability: Filosofi Teras (0 copies) and Atomic Habits (all dipinjam) show "Tidak Tersedia"
- Cantik Itu Luka has mixed-state copies (1 tersedia + 1 dipinjam)
- All remaining titles have at least 1 tersedia copy

## Key Changes
- UUID type fix in `get_current_user` (`uuid.UUID(payload["sub"])`) — prevents SQLite UUID comparison error
- Seed refactored into `seed_pustakawan()` + `seed_buku()` for modularity
