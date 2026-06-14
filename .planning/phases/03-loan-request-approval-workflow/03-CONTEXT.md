# Phase 3: Loan Request & Approval Workflow - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

A mahasiswa requests to borrow an available physical copy (`salinan_buku`) of a book from `/katalog/{id}`, the system enforces the 5-active-loan limit (LOAN-02) and the blocked-account check (LOAN-03) before creating a `peminjaman` record (`menunggu_persetujuan`). A pustakawan reviews pending requests on a new `/pinjaman` page, approving (→ `siap_diambil`, starts 2x24h pickup timer) or rejecting (→ `ditolak`), syncing `salinan_buku.status_ketersediaan`. An expired pickup window auto-becomes `dibatalkan` via lazy check. The pustakawan marks a `siap_diambil` loan as handed over (→ `dipinjam`, sets `tanggal_tenggat` = handover + 14 days).

Returns, fines, blocking-on-late-return, and the full dashboard/member-management/loan-history views are Phases 4-5 — out of scope here.

</domain>

<decisions>
## Implementation Decisions

### Loan Request Flow (Mahasiswa)
- **D-01:** The "Pinjam" action lives on `/katalog/{id}` (detail page) only — not on catalog cards. Phase 2's D-06 spec'd a "Pinjam Buku" button with a "coming soon" toast, but it was **never actually built** (verified: no "Pinjam" references in `BookCard.jsx`/`BukuDetailPage.jsx`). Phase 3 builds this from scratch.
- **D-02:** Mahasiswa picks a specific copy — the existing `SalinanTable` (Phase 2 D-07) gets a "Pinjam" action on each row where `status_ketersediaan = tersedia`. No auto-assignment.
- **D-03:** Clicking "Pinjam" on a copy opens a confirmation modal based on the `form_pengajuan_pinjam` mockup: "Buku Terpilih" (book + selected copy/lokasi_rak), "Informasi Peminjam" (mahasiswa nama + peran), "Estimasi Tenggat Waktu" (informational preview: today + 14 days — the real `tanggal_tenggat` is set later at handover, per D-12 of this phase / LOAN-06), and a "Kirim" submit button. On success/failure, show a Toast (reuse Phase 2's unused `Toast.jsx` component).
- **D-04:** Pre-check + disable pattern for LOAN-02/03: on page load (or `/pinjaman` fetch), get the mahasiswa's active-loan count and `is_diblokir`. If blocked or at 5 active loans, disable all "Pinjam" buttons site-wide and show a persistent banner explaining why. The API still enforces both rules server-side (400 + reason) as the actual gate — the UI pre-check is just better UX.

### Pustakawan Approval & Handover UI
- **D-05:** Replace the `/pinjaman` `ComingSoonPage` with a real shared route, following Phase 2's `/katalog` role-based pattern (D-01): pustakawan and mahasiswa see different content on the same route based on `peran`.
- **D-06:** Pustakawan's view uses **stacked sections** (not tabs), both visible at once: "Menunggu Persetujuan" (table with ✓/✕ approve/reject actions, from the `dashboard_pustakawan` mockup's "Daftar Pengajuan Peminjaman") above "Siap Diambil" (table with a "Serahkan" handover action).
- **D-07:** Every action (✓ approve / ✕ reject / Serahkan) opens a `ConfirmDialog` (reuse Phase 2's component) before calling the API — e.g. "Setujui pengajuan ini?", "Tolak pengajuan ini?", "Tandai buku sudah diserahkan?". On confirm: API call → toast feedback → row removed from its section (or moved to the next section on success).
- **D-08:** Pustakawan's `/pinjaman` page in Phase 3 is **actionable-only** — just "Menunggu Persetujuan" and "Siap Diambil". No read-only "Sedang Dipinjam" listing; that's Phase 4/5 dashboard territory.

### Mahasiswa's "Pinjaman" View
- **D-09:** On the same shared `/pinjaman` route, mahasiswa sees a basic "Pinjaman Saya" list — a single list/table sorted most-recent-first, with a status badge column and a relevant date per row.
- **D-10:** The list includes **all statuses** — `menunggu_persetujuan`, `siap_diambil`, `dipinjam`, `ditolak`, `dibatalkan` — each with its own status badge, so the mahasiswa knows why a request left the "active" set.
- **D-11:** For `siap_diambil` rows, show the computed pickup deadline as an absolute date/time (`tanggal_siap_ambil` + 2x24h), e.g. "Ambil sebelum 15 Jun 2026, 10:00" — not a live countdown.

### Pickup-Window Auto-Cancellation (LOAN-05)
- **D-12:** Lazy check-on-read, no scheduled job/worker. Whenever the `/pinjaman` list endpoint is queried (by either role), the backend checks each `siap_diambil` row: if `tanggal_siap_ambil + 2 days < now()`, update `status_peminjaman → dibatalkan` and reset the linked `salinan_buku.status_ketersediaan → tersedia` before returning results.

### Claude's Discretion
- Exact Bahasa Indonesia wording for modal text, toast messages, button labels, banner copy — within the Biblio design system.
- Active-loan definition for LOAN-02 (which `status_peminjaman` values count as "active" — expected: `menunggu_persetujuan`, `siap_diambil`, `dipinjam`).
- Backend endpoint/route design for `/api/peminjaman/*` (PRD §7 draft names: `ajukan`, `persetujuan`, `serahkan`) and response schema shapes.
- Empty-state treatment for "Pinjaman Saya" / queue sections when empty (reuse Phase 2's `EmptyState`).
- Where the D-12 lazy-check sweep is implemented (e.g. a shared service function called by both role branches of the `/pinjaman` list endpoint) so it isn't duplicated.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria (5 numbered TRUE statements), depends on Phase 2
- `.planning/REQUIREMENTS.md` — LOAN-01 through LOAN-06

### PRD — Data Model & Workflow
- `docs/PRD.md` §4 — `peminjaman` table columns (`tanggal_pengajuan`, `tanggal_siap_ambil`, `tanggal_pinjam`, `tanggal_tenggat`, `tanggal_kembali`, `status_peminjaman`, `total_denda`) and `STATUS_PEMINJAMAN` ENUM
- `docs/PRD.md` §5.B "Alur Peminjaman" — the request→approve→pickup→handover state machine and timers (2x24h, 14 days)
- `docs/PRD.md` §7 — Peminjaman API draft: `POST /peminjaman/ajukan`, `PUT /peminjaman/{id}/persetujuan`, `PUT /peminjaman/{id}/serahkan`

### Design System & Mockups
- `docs/design/stitch_botanical_scholar_library/biblio_design_system/DESIGN.md` — colors, typography, spacing, component/table/badge specs
- `docs/design/stitch_botanical_scholar_library/form_pengajuan_pinjam_biblio/code.html` — loan request confirmation modal reference (D-03): "Buku Terpilih", "Informasi Peminjam", "Estimasi Tenggat Waktu", "Kirim"
- `docs/design/stitch_botanical_scholar_library/dashboard_pustakawan_biblio/code.html` — "Daftar Pengajuan Peminjaman" table reference (D-06: Mahasiswa, Buku, Tanggal Pengajuan, ✓/✕ Aksi columns). **Note:** ignore the stat cards (Total Buku, Peminjaman Aktif, etc.) on this mockup — those are Phase 5's DASH-01.
- `docs/design/stitch_botanical_scholar_library/riwayat_peminjaman_biblio/code.html` — loan list table shape reference for D-09 (Mahasiswa, Buku, Tanggal Pinjam, Tanggal Tenggat, Status, Denda columns) — Phase 3 builds a simpler subset; full table is Phase 5

### Prior Phase Context
- `.planning/phases/01-foundation-schema-auth/01-CONTEXT.md` — D-05 (AppShell nav already has "Pinjaman" link for both roles → currently `ComingSoonPage`, replaced per D-05 above), D-16 (relative `/api/*` paths via Vite proxy)
- `.planning/phases/02-book-catalog/02-CONTEXT.md` — D-07 (per-copy `SalinanTable` on `/katalog/{id}`, reused for copy selection per D-02), D-06 (the un-built "Pinjam Buku" button — see Integration Points note below)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/Toast.jsx` — built in Phase 2, **currently unused anywhere in the app** — reuse for loan request success/error feedback (D-03).
- `frontend/src/components/ConfirmDialog.jsx` — built in Phase 2 (`variant="confirm"` / `variant="info"`) — reuse for approve/reject/Serahkan confirmations (D-07).
- `frontend/src/components/SalinanTable.jsx`, `AvailabilityBadge.jsx`, `EmptyState.jsx` — reusable for copy display and status badges in both the loan request modal and the `/pinjaman` lists.
- `backend/app/dependencies/auth.py::get_current_user` — returns `Pengguna` with `.peran`; mirrors the role-gating pattern already used in `app/routers/buku.py` for pustakawan-only mutation endpoints.
- `backend/app/models/peminjaman.py` + `app/models/enums.py::StatusPeminjaman` — full `peminjaman` table and ENUM already migrated (Phase 1 D-10) — **no new Alembic migration needed**, only new router/schema/service code.

### Established Patterns
- Backend: one router + one schema module per resource (`app/routers/buku.py` + `app/schemas/buku.py`) — mirror this with `app/routers/peminjaman.py` + `app/schemas/peminjaman.py`.
- Frontend: shared route with role-conditional content (Phase 2's `/katalog` Jelajah/Kelola toggle, D-01) — apply the same shape to `/pinjaman` (D-05).
- `refreshKey` state-bump pattern (from Phase 2's 02-04) to re-fetch lists after a mutation, avoiding `set-state-in-effect` ESLint violations.

### Integration Points
- **Important:** Phase 2's D-06 "Pinjam Buku" button/toast was specified but never implemented — Phase 3 is not "wiring an existing button", it's building the entry point from scratch on `/katalog/{id}` (D-01/D-02/D-03).
- `frontend/src/router.jsx` — replace `{ path: 'pinjaman', element: <ComingSoonPage title="Riwayat Peminjaman" /> }` with the new shared Pinjaman page (D-05).
- `backend/app/main.py` — register a new `peminjaman.router` alongside `autentikasi.router` and `buku.router`.
- `frontend/src/pages/BukuDetailPage.jsx`'s `SalinanTable` usage needs a "Pinjam" action column for `tersedia` rows when `peran === 'mahasiswa'` (D-02).

</code_context>

<specifics>
## Specific Ideas

- The `form_pengajuan_pinjam` mockup's "Estimasi Tenggat Waktu" block is purely an informational preview (today + 14 days) shown at request time — the actual `tanggal_tenggat` column is only set later, at handover (LOAN-06), not at request time (D-03).
- Note the layout difference: pustakawan's queue uses **stacked sections by status** (D-06), while the mahasiswa's own loans use a **single sorted list with status badges** (D-09) — these are intentionally different shapes for the same `/pinjaman` route.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 3 scope. Read-only "Sedang Dipinjam" visibility for pustakawan (D-08) and the full "Riwayat Peminjaman" table (search, pagination, denda column) are explicitly deferred to Phase 4/5, per ROADMAP grouping.

</deferred>

---

*Phase: 3-Loan Request & Approval Workflow*
*Context gathered: 2026-06-13*
