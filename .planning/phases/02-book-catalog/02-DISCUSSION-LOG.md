# Phase 2: Book Catalog - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 2-Book Catalog
**Areas discussed:** Pustakawan catalog management, Availability display & "Pinjam Buku" button, Category filter & seed data, Book cover images

---

## Pustakawan Catalog Management

| Option | Description | Selected |
|--------|-------------|----------|
| Tab/toggle on /katalog | Same route, pustakawan toggles between "Jelajah" (browse grid) and "Kelola" (admin table). No new nav items. | ✓ |
| Same grid, inline admin controls | Pustakawan sees mahasiswa's grid plus edit/delete icons and a floating "Tambah Buku" button. | |
| Let Claude decide | | |

**User's choice:** Tab/toggle on /katalog

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — shared detail page for both roles | /katalog/{id} shows buku info + salinan_buku list (lokasi_rak, kondisi, status); pustakawan sees "Tambah Salinan". | ✓ |
| No — manage copies via modal | No new route; "Salinan" button in admin table opens a modal. | |
| Let Claude decide | | |

**User's choice:** Yes — shared detail page for both roles

| Option | Description | Selected |
|--------|-------------|----------|
| Modal dialog | "Tambah Buku" / edit icon opens an overlay form (judul, penulis, isbn, kategori, tahun_terbit). | ✓ |
| Dedicated form page | Separate routes /katalog/tambah and /katalog/{id}/edit. | |
| Let Claude decide | | |

**User's choice:** Modal dialog

| Option | Description | Selected |
|--------|-------------|----------|
| Add only (per CAT-04) | Pustakawan adds new physical copies; existing copies read-only in Phase 2. | ✓ |
| Add + edit (lokasi_rak, kondisi) | Pustakawan can also update shelf location/condition after creation. | |
| Let Claude decide | | |

**User's choice:** Add only (per CAT-04)

**Notes:** No further questions requested for this area.

---

## Availability display & "Pinjam Buku" button

| Option | Description | Selected |
|--------|-------------|----------|
| Binary: Tersedia / Tidak Tersedia | "Tersedia" if ≥1 copy is tersedia; otherwise "Tidak Tersedia" (covers 0-copy case too). Matches mockup. | ✓ |
| Count-based: "3/5 tersedia" | Badge shows available/total copy counts. | |
| Let Claude decide | | |

**User's choice:** Binary: Tersedia / Tidak Tersedia

| Option | Description | Selected |
|--------|-------------|----------|
| Clickable — shows 'coming soon' message | Button enabled per mockup; click shows a toast about loan requests arriving in a future phase. No peminjaman record created. | ✓ |
| Disabled with tooltip | Button renders disabled/greyed regardless of availability. | |
| Let Claude decide | | |

**User's choice:** Clickable — shows 'coming soon' message

| Option | Description | Selected |
|--------|-------------|----------|
| Full per-copy table (lokasi_rak, kondisi, status) | Both roles see every salinan_buku with shelf location, condition, status. | ✓ |
| Aggregate only for mahasiswa | Mahasiswa sees "X dari Y salinan tersedia"; full table pustakawan-only. | |
| Let Claude decide | | |

**User's choice:** Full per-copy table (lokasi_rak, kondisi, status)

| Option | Description | Selected |
|--------|-------------|----------|
| Live debounced search + server-side filters | GET /buku?kata_kunci=...&kategori=... ~300ms after typing/selecting stops. | ✓ |
| Submit-based search (Enter/button) | Search fires only on Enter or a "Cari" button click. | |
| Let Claude decide | | |

**User's choice:** Live debounced search + server-side filters

**Notes:** No further questions requested for this area.

---

## Category filter & seed data

| Option | Description | Selected |
|--------|-------------|----------|
| Dynamic (free-text, derived from data) | kategori stays free-text; filter sidebar lists distinct values present in the catalog. | ✓ |
| Fixed list (Fiksi / Non-Fiksi / Referensi) | Backend validates kategori against a hardcoded set of 3. | |
| Let Claude decide | | |

**User's choice:** Dynamic (free-text, derived from data)

| Option | Description | Selected |
|--------|-------------|----------|
| ~10-12 books, reuse mockup titles | Seed real titles/authors from the katalog mockup plus a few more across categories. | ✓ |
| Generic placeholder data | Simple titles like "Buku Contoh 1". | |
| Let Claude decide | | |

**User's choice:** ~10-12 books, reuse mockup titles

| Option | Description | Selected |
|--------|-------------|----------|
| Single-select | One active category filter at a time plus "Semua Kategori". | |
| Multi-select checkboxes | User can check multiple categories; backend combines with OR. | ✓ |
| Let Claude decide | | |

**User's choice:** Multi-select checkboxes

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — mixed statuses | Most books fully available; at least one book all-dipinjam; one book with mixed-state copies. | ✓ |
| All copies start 'tersedia' | Simplest seed; every book shows "Tersedia" initially. | |
| Let Claude decide | | |

**User's choice:** Yes — mixed statuses

**Notes:** No further questions requested for this area.

---

## Book cover images

| Option | Description | Selected |
|--------|-------------|----------|
| Generic placeholder per category | Colored block + genre icon, colored by kategori. No schema change. | ✓ |
| Add a `cover_url` column | Small Alembic migration; seed points to external placeholder-image URLs. | |
| Let Claude decide | | |

**User's choice:** Generic placeholder per category

| Option | Description | Selected |
|--------|-------------|----------|
| Colored block + icon, category-coded | Background tint varies by kategori with a centered menu_book icon. | ✓ |
| Plain neutral block + icon | Same treatment for every book regardless of category. | |
| Let Claude decide | | |

**User's choice:** Colored block + icon, category-coded

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, keep it | Cards keep the 4px left-border accent, colored by kategori (muted for unavailable). | ✓ |
| No, drop it | Simpler cards without the left-border accent. | |
| Let Claude decide | | |

**User's choice:** Yes, keep it

| Option | Description | Selected |
|--------|-------------|----------|
| Larger version of the same placeholder | Detail page shows an enlarged cover placeholder alongside buku info. | ✓ |
| No cover on detail page | Detail page is text/table-focused, no cover element. | |
| Let Claude decide | | |

**User's choice:** Larger version of the same placeholder

**Notes:** No further questions requested for this area.

---

## Claude's Discretion

- Exact category→color mapping for placeholders and left-edge accents (using the existing Biblio palette)
- FK-safe delete behavior for `buku` when `salinan_buku` copies exist (block vs cascade)
- Debounce timing, loading/empty-state treatments, pagination (if any)
- Backend response shape for category list (dedicated endpoint vs derived field)
- "Kelola" admin table columns and CRUD form validation rules (isbn format, tahun_terbit range)

## Deferred Ideas

- Editing/deleting existing `salinan_buku` copies — explicitly deferred past Phase 2 (D-04); revisit in backlog/future phase if needed.
