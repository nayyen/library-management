# Phase 4: Returns, Fines & Blocking - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

A pustakawan processes a return for a `dipinjam` loan via a new "Sedang Dipinjam" section on `/pinjaman` (→ `status_peminjaman = dikembalikan`, records `tanggal_kembali`). If `tanggal_kembali` is after `tanggal_tenggat`, the system calculates `total_denda` (Rp 1.000/day), sets `pengguna.is_diblokir = TRUE`, and logs a stubbed Brevo notification. A pustakawan can clear the block via a "Denda Lunas" action in a new "Anggota Diblokir" section. Mahasiswa see denda amounts, overdue indicators, and a personalized block banner on their own `/pinjaman` view.

Full member-management (`/anggota`, DASH-02) and the dashboard (DASH-01) remain Phase 5 — out of scope here.

</domain>

<decisions>
## Implementation Decisions

### Return Flow & Overdue Indicators (Pustakawan)
- **D-01:** New "Sedang Dipinjam" stacked section (3rd section, after "Menunggu Persetujuan" + "Siap Diambil" from Phase 3) on pustakawan's `/pinjaman` — lists ALL `dipinjam` loans across all mahasiswa, sorted overdue-first (`tanggal_tenggat` ascending). Fulfills Phase 3 D-08's deferred scope.
- **D-02:** Rows past `tanggal_tenggat` show a "Terlambat" (crimson) badge instead of "Dipinjam" — purely visual, computed by comparing `tanggal_tenggat` to now. No denda/block until return is processed. Matches the `riwayat_peminjaman` mockup's Terlambat vs Dipinjam badge styling.
- **D-03:** "Kembalikan" action opens `ConfirmDialog`. For overdue loans, preview the calculated denda + block warning before confirming, e.g. "Buku ini terlambat X hari. Denda Rp X.000 akan tercatat dan akun mahasiswa akan diblokir." For on-time loans, a simple confirm: "Tandai buku ini sudah dikembalikan?" The preview is a client-side estimate (now vs `tanggal_tenggat`) — actual calculation happens server-side on confirm.

### Denda Lunas / Unblock (RET-04)
- **D-04:** New "Anggota Diblokir" stacked section (4th section) on pustakawan's `/pinjaman` — lists mahasiswa where `is_diblokir = true`, with nama + total denda owed + "Denda Lunas" button. Consistent with Phase 3 D-08's "actionable hub" pattern for `/pinjaman`. Phase 5's `/anggota` page (DASH-02) can later expand/restructure this into the full member-management view.
- **D-05:** "Denda Lunas" clears `pengguna.is_diblokir → FALSE` only. `total_denda` values on individual `peminjaman` rows remain unchanged as historical record — no schema change needed.
- **D-06:** "Denda owed" displayed per blocked mahasiswa = `SUM(total_denda)` across ALL their `dikembalikan` loans (handles the edge case of multiple late returns).

### Mahasiswa-Side Visibility
- **D-07:** "Pinjaman Saya" table gets a new "Denda" column — shows "Rp X.000" for `dikembalikan` rows with `total_denda > 0`, "-" otherwise. Matches the `riwayat_peminjaman` mockup's Denda column.
- **D-08:** Active `dipinjam` rows past `tanggal_tenggat` also show the "Terlambat" badge for mahasiswa (same `StatusBadge` variant as D-02) — consistent visual language across both roles.
- **D-09:** `BlockedBanner`'s 'blocked' variant is personalized with the actual denda amount, e.g. "Akun Anda diblokir karena denda Rp 5.000 belum dibayar..." — derived from the same `SUM(total_denda)` as D-06, returned in the mahasiswa's `GET /api/peminjaman` response.

### Brevo Notification Stub (RET-03)
- **D-10:** Stub implemented as a structured log line via Python's `logging` module (e.g. `logger.info("BREVO_NOTIFICATION", extra={id_peminjaman, email, total_denda, status: "Sent"})`) when a return is processed late. No new DB table/migration.
- **D-11:** Inspection is developer-facing via `docker-compose logs backend` — satisfies the PRD's literal verification step ("log email Brevo memunculkan status Sent"). No pustakawan-facing UI for notification history in Phase 4.

### Claude's Discretion
- Exact backend endpoint design for `PUT /api/peminjaman/{id}/kembalikan` and the "Denda Lunas" endpoint (e.g. `PUT /api/peminjaman/anggota/{id_pengguna}/lunasi_denda` or similar) — response schema shapes, per PRD §7 draft naming conventions.
- Fine calculation formula: `total_denda = max(0, days_late) * 1000`, where `days_late = (tanggal_kembali.date() - tanggal_tenggat.date()).days`. Pick the simplest defensible day-boundary rounding.
- `salinan_buku.status_ketersediaan → tersedia` on return (mirrors LOAN-04's sync pattern).
- `StatusBadge.jsx` new "terlambat" variant styling — derive crimson/error-container classes from the `riwayat_peminjaman` mockup (`bg-error-container text-on-error-container border-alert-crimson`).
- Whether the "Terlambat" overdue check is computed inline in `_build_item_out`/response builder vs a small helper — follow the existing `_sweep_expired_pickups`-adjacent helper pattern in `peminjaman.py`.
- Button label/icon for "Denda Lunas" — combine the PRD's literal "Denda Lunas" wording with the `manajemen_anggota` mockup's `lock_open` icon / sage-green styling for "Buka Blokir".
- Empty-state treatment for "Sedang Dipinjam" and "Anggota Diblokir" when empty — reuse `EmptyState` per established pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements & Roadmap
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria (4 numbered TRUE statements), depends on Phase 3
- `.planning/REQUIREMENTS.md` — RET-01, RET-02, RET-03, RET-04

### PRD — Data Model & Workflow
- `docs/PRD.md` §4 — `peminjaman` table columns (`tanggal_kembali`, `total_denda`, `status_peminjaman`) and `pengguna.is_diblokir`
- `docs/PRD.md` §5.C "Alur Pengembalian & Denda" — return→fine→block→Denda Lunas flow
- `docs/PRD.md` §6 — Acceptance criteria for "Keterlambatan" (16 days late → Rp 2.000 denda, `is_diblokir=true`, Brevo log status "Sent")
- `docs/PRD.md` §7 — Peminjaman API draft: `PUT /peminjaman/{id}/kembalikan`, `PUT /peminjaman/{id}/lunasi_denda`

### Design System & Mockups
- `docs/design/stitch_botanical_scholar_library/biblio_design_system/DESIGN.md` — colors, typography, spacing, status-indicator specs (Overdue: Alert Crimson)
- `docs/design/stitch_botanical_scholar_library/riwayat_peminjaman_biblio/code.html` — table reference for D-01/D-02/D-07: Mahasiswa/Buku/Tanggal Pinjam/Tanggal Tenggat/Status (Terlambat/Kembali/Dipinjam badges)/Denda/Aksi columns
- `docs/design/stitch_botanical_scholar_library/manajemen_anggota_biblio/code.html` — blocked-member card reference for D-04/D-06: "Denda Tertunggak" + "Buka Blokir" (sage-green, `lock_open` icon)

### Prior Phase Context
- `.planning/phases/03-loan-request-approval-workflow/03-CONTEXT.md` — D-05 (shared `/pinjaman` route), D-06/D-08 (stacked sections, deferred "Sedang Dipinjam"), D-09/D-10/D-11 (mahasiswa list shape), D-12 (lazy-sweep precedent for the overdue check)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/routers/peminjaman.py` — existing router with `_pustakawan_only`/`_mahasiswa_only` guards, `_build_item_out`, `ACTIVE_STATUSES`, `_sweep_expired_pickups` (lazy-check pattern) — extend with `kembalikan`/`lunasi_denda` endpoints and an overdue-detection helper.
- `backend/app/schemas/peminjaman.py` — `PeminjamanItemOut`, `PeminjamanResponse` — extend with `total_denda`/`tanggal_kembali` fields and a new blocked-member item shape.
- `backend/app/models/peminjaman.py` — `total_denda` (Integer, default 0) and `tanggal_kembali` already exist on the model — **no migration needed**.
- `backend/app/models/pengguna.py` — `is_diblokir` already exists — **no migration needed**.
- `frontend/src/pages/PinjamanPage.jsx` — existing shared page with `refreshKey`/`ConfirmDialog`/`Toast` pattern, `BookCell`, date-format helpers — extend with 2 new pustakawan sections and 1 new mahasiswa column.
- `frontend/src/components/StatusBadge.jsx` — add a "terlambat"/overdue variant (crimson) following the existing variant-map shape.
- `frontend/src/components/BlockedBanner.jsx` — 'blocked' variant copy gets interpolated with the denda amount.

### Established Patterns
- Backend: one router + one schema module per resource — `peminjaman.py`/`peminjaman.py` already exist; extend rather than create new files.
- Frontend: `refreshKey` re-fetch + `ConfirmDialog` + `Toast` for all mutating actions (Phase 3 03-03).
- Lazy check-on-read pattern (D-12 from Phase 3) is the precedent for the new "Terlambat" overdue detection — no scheduled job.

### Integration Points
- `backend/app/routers/peminjaman.py` — add `PUT /api/peminjaman/{id}/kembalikan` and a "Denda Lunas" endpoint; extend the `GET /api/peminjaman` pustakawan branch with `sedang_dipinjam` and `anggota_diblokir` lists.
- `frontend/src/pages/PinjamanPage.jsx` — add "Sedang Dipinjam" and "Anggota Diblokir" sections (pustakawan), "Denda" column (mahasiswa).

</code_context>

<specifics>
## Specific Ideas

- `riwayat_peminjaman` mockup badge classes: "Terlambat" = `bg-error-container text-on-error-container border-alert-crimson`; "Kembali" = `bg-sage-green/20 text-sage-green border-sage-green`; "Dipinjam" = `bg-primary-container text-on-primary-container border-primary-fixed`.
- `manajemen_anggota` mockup blocked-card: "Denda Tertunggak" label + Rp amount in `alert-crimson`, "Buka Blokir" button = `bg-sage-green text-on-primary` with `lock_open` icon.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 4 scope. Full `/anggota` member-management page (search/filter, full member list, active-loan counts) remains Phase 5 (DASH-02). Dashboard stats (DASH-01) remain Phase 5.

</deferred>

---

*Phase: 4-Returns, Fines & Blocking*
*Context gathered: 2026-06-14*
