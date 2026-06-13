# Phase 2: Book Catalog - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Mahasiswa can search/filter the book catalog by `judul`, `penulis`, `isbn`, and `kategori`. Pustakawan can fully manage the catalog: CRUD master `buku` records and add physical `salinan_buku` copies (`lokasi_rak`, `kondisi`, `status_ketersediaan`). Both roles share a `/katalog` list view and a `/katalog/{id}` detail view.

Loan requests (the "Pinjam Buku" action), approvals, returns, fines, and dashboards are out of scope — those are Phases 3-5. The catalog UI is built now so Phase 3 can wire the real loan-request flow into it.

</domain>

<decisions>
## Implementation Decisions

### Pustakawan Catalog Management
- **D-01:** `/katalog` is a single shared route. Pustakawan sees a tab/toggle between "Jelajah" (browse grid, same as mahasiswa) and "Kelola" (admin table view with edit/delete actions, styled per DESIGN.md's striped-table pattern). No new nav items — fits the existing AppShell "Katalog" link from Phase 1 (D-05).
- **D-02:** `/katalog/{id}` is a shared book detail view for both roles, showing buku info (judul, penulis, isbn, kategori, tahun_terbit) plus a table of all `salinan_buku` copies (lokasi_rak, kondisi, status_ketersediaan per copy).
- **D-03:** Add/edit `buku` happens via a modal dialog (overlay form: judul, penulis, isbn, kategori, tahun_terbit) triggered from the "Kelola" tab — no separate `/katalog/tambah` or `/katalog/{id}/edit` routes.
- **D-04:** `salinan_buku` is add-only in Phase 2 (per CAT-04's literal scope). Pustakawan adds new physical copies (lokasi_rak, kondisi, status_ketersediaan) from the detail view's "Tambah Salinan" form. Editing/deleting existing copies is deferred — not built in Phase 2.

### Availability Display & "Pinjam Buku"
- **D-05:** Catalog card availability badge is binary: "Tersedia" (sage-green) if at least one `salinan_buku` for that `buku` has `status_ketersediaan = tersedia`; otherwise "Tidak Tersedia" (grey/neutral) — including the zero-copy case. Matches the mockup's two-state badge.
- **D-06:** The "Pinjam Buku" button is clickable and styled per the mockup, but in Phase 2 it shows a "coming soon" message (e.g. toast/snackbar: "Fitur peminjaman akan tersedia di fase berikutnya.") — no `peminjaman` record is created. Phase 3 wires the real action into this button.
- **D-07:** On `/katalog/{id}`, both mahasiswa and pustakawan see the full per-copy table (lokasi_rak, kondisi, status_ketersediaan for every salinan_buku) — helps mahasiswa locate the physical book and lets pustakawan verify their additions.
- **D-08:** Catalog search is live and debounced (~300ms after typing stops), calling `GET /api/buku?kata_kunci=...&kategori=...` server-side. Matches the PRD's draft API.

### Category Filter & Seed Data
- **D-09:** `kategori` remains free-text VARCHAR(100) as defined in the schema — no fixed/hardcoded category list. The filter sidebar's category checkboxes are populated from the distinct `kategori` values present in the `buku` table (e.g. via a `GET /api/buku/kategori` endpoint or derived from the catalog response).
- **D-10:** The kategori filter supports multi-select checkboxes — selecting multiple categories combines with OR (`?kategori=Fiksi&kategori=Non-Fiksi` or equivalent comma-separated param).
- **D-11:** Seed ~10-12 `buku` records reusing titles/authors from the `katalog_buku_biblio` mockup (Gadis Kretek — Ratih Kumala; Sapiens: Riwayat Singkat Umat Manusia — Yuval Noah Harari; Cantik Itu Luka — Eka Kurniawan; Kamus Besar Bahasa Indonesia — Badan Pengembangan Bahasa) plus additional titles spanning the same categories (Fiksi, Non-Fiksi, Referensi) for variety.
- **D-12:** Seed `salinan_buku` with a mixed status distribution: most books have ≥1 `tersedia` copy; at least one book has all copies `dipinjam`/`dipesan` (showing "Tidak Tersedia"); at least one book has multiple copies in different states — exercises the D-05 availability rollup visually.

### Book Covers
- **D-13:** No schema change — `buku` table keeps its current columns (per Phase 1's D-10 schema lock). Book "covers" are generic placeholders: a colored block with a centered `menu_book` material icon, color-coded by `kategori` (e.g. ink-blue tones for Fiksi, antique-gold tones for Non-Fiksi, etc., echoing the mockup's category accent colors).
- **D-14:** Catalog cards keep the mockup's 4px category-colored left-edge accent (`border-l-4`) — the "book spine" motif from DESIGN.md, colored by kategori (muted/grey when the book is "Tidak Tersedia").
- **D-15:** On `/katalog/{id}`, the same placeholder treatment appears larger/more prominent alongside the buku info table — visual consistency with the catalog grid, no real cover images.

### Claude's Discretion
- Exact category→color mapping for placeholders and left-edge accents (informed by D-13/D-14, using the Biblio palette: sage-green, antique-gold, ink-blue, etc.)
- FK-safe delete behavior for `buku` (e.g., block deletion if `salinan_buku` copies exist, or cascade) — not discussed; pick the safer option and document it
- Exact debounce timing, loading/empty-state treatments, and pagination (if any) for the catalog grid
- Backend response shape for category list (dedicated endpoint vs derived field on `/api/buku`)
- "Kelola" admin table column set and exact CRUD form validation (isbn format, tahun_terbit range, etc.)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria (CAT-01–04), dependencies
- `.planning/REQUIREMENTS.md` — CAT-01, CAT-02, CAT-03, CAT-04
- `docs/PRD.md` §4 — data model (`buku`, `salinan_buku` tables, `KONDISI_BUKU`/`STATUS_SALINAN` ENUMs); §7 — catalog API draft (`GET /buku`, `POST /buku`, `POST /buku/{id_buku}/salinan`)

### Design System & Mockups
- `docs/design/stitch_botanical_scholar_library/biblio_design_system/DESIGN.md` — colors, typography, spacing, table/card/status component specs
- `docs/design/stitch_botanical_scholar_library/katalog_buku_biblio/code.html` — mahasiswa catalog mockup (search bar, category/availability filter sidebar, book card grid with status badges and "Pinjam Buku"); reference for D-05–D-10, D-13, D-14

### Prior Phase Context
- `.planning/phases/01-foundation-schema-auth/01-CONTEXT.md` — D-05 (AppShell nav structure with "Katalog" link), D-10 (complete schema already migrated, no new tables expected), D-16 (relative `/api/*` paths via Vite proxy)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/buku.py`, `backend/app/models/salinan_buku.py`, `backend/app/models/enums.py` — SQLAlchemy models for `Buku`, `SalinanBuku`, `KondisiBuku`, `StatusSalinan` already exist from Phase 1's migration; Phase 2 adds routers/schemas against these, no new migration needed (per D-13).
- `backend/app/routers/autentikasi.py` + `backend/app/schemas/auth.py` — established router/schema pattern (APIRouter with `/api/...` prefix, Pydantic request/response models, `Depends(get_db)`, `Depends(get_current_user)`) to mirror for a new `buku` router.
- `frontend/src/lib/api.js` — axios instance with auth header + 401 interceptor, ready to use for catalog API calls.
- `frontend/src/layouts/AppShell.jsx` — nav already has a "Katalog" link (`/katalog`) for both `MAHASISWA_NAV` and `PUSTAKAWAN_NAV`; currently routes to `ComingSoonPage`.
- `frontend/src/router.jsx` — `{ path: 'katalog', element: <ComingSoonPage title="Katalog Buku" /> }` is the route to replace; add a new `{ path: 'katalog/:id', ... }` route for the detail view.
- `frontend/src/components/InputField.jsx` — existing styled input component, reusable for search bar and CRUD modal forms.
- `frontend/src/dependencies/auth.py` — `get_current_user` dependency provides `Pengguna` with `.peran` for role-gating pustakawan-only actions (Kelola tab, CRUD modals, Tambah Salinan).

### Established Patterns
- Backend: routers under `app/routers/`, schemas under `app/schemas/`, models under `app/models/` — one file per resource, mirroring `autentikasi.py`/`auth.py`.
- Frontend: pages under `src/pages/`, shared layout via `AppShell` + `Outlet`, role read from decoded JWT (`decodeToken(token).peran`) as seen in `AppShell.jsx`.
- Design tokens (colors, typography, radius) are already wired into `tailwind.config.js` from Phase 1 — reuse existing Tailwind classes (`bg-sage-green`, `text-antique-gold`, `border-l-ink-blue`, `rounded-DEFAULT`, `text-headline-sm font-headline-sm`, etc.) matching the mockup.

### Integration Points
- New backend router (e.g. `app/routers/buku.py`) registered in `backend/app/main.py` alongside `autentikasi.router`.
- `frontend/src/router.jsx` — add `katalog` (list) and `katalog/:id` (detail) routes inside the existing `AppShell`-wrapped, `ProtectedRoute`-guarded route group.
- Seed data (D-11/D-12) extends `backend/app/seed.py` (currently seeds only the pustakawan account per Phase 1's D-11).

</code_context>

<specifics>
## Specific Ideas

- Reuse the `katalog_buku_biblio` mockup's exact book titles/authors/categories for seed data (D-11) so the running app visually matches the design reference.
- Card left-edge accent colors and category-coded placeholders should draw from the Biblio palette already present in `tailwind.config.js` (sage-green, antique-gold, ink-blue, paper-shadow).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope. Editing/deleting `salinan_buku` copies (D-04) was explicitly deferred past Phase 2; note for backlog/future phase if needed.

</deferred>

---

*Phase: 2-Book Catalog*
*Context gathered: 2026-06-13*
