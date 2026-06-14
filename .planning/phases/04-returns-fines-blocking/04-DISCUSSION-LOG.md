# Phase 4: Returns, Fines & Blocking - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 4-Returns, Fines & Blocking
**Areas discussed:** Sedang Dipinjam & Return Flow, Denda Lunas UI Placement (RET-04), Mahasiswa-Side Denda Visibility, Brevo Notification Log Format (RET-03)

---

## Sedang Dipinjam & Return Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Show "Terlambat" badge before return is processed | Matches riwayat_peminjaman mockup's Dipinjam vs Terlambat distinction; purely visual | ✓ |
| Only show "Dipinjam" until return processed | Simpler, overdue only visible after return | |

| Option | Description | Selected |
|--------|-------------|----------|
| ConfirmDialog previews denda + block warning | "Buku ini terlambat X hari. Denda Rp X.000 akan tercatat dan akun mahasiswa akan diblokir." | ✓ |
| Simple confirm only | "Tandai buku ini sudah dikembalikan?" — result shown in success toast | |

| Option | Description | Selected |
|--------|-------------|----------|
| All dipinjam, overdue-first, single section | Sorted by tanggal_tenggat ascending — prioritized worklist | ✓ |
| Split into two sections (Terlambat / Sedang Dipinjam) | More structure, adds a 4th stacked section | |

**Notes:** All three recommended options chosen — overdue indicator is purely visual pre-return, return confirm previews the fine, and "Sedang Dipinjam" is one overdue-first section (D-01, D-02, D-03).

---

## Denda Lunas UI Placement (RET-04)

| Option | Description | Selected |
|--------|-------------|----------|
| New "Anggota Diblokir" section on /pinjaman | 3rd actionable section, consistent with Phase 3 D-08's "actionable hub" pattern; Phase 5 can expand into /anggota | ✓ |
| Minimal /anggota page stub | Partially builds AppShell's existing nav link now; risk of Phase 5 rework | |

| Option | Description | Selected |
|--------|-------------|----------|
| Sum of total_denda across all dikembalikan loans | Correct for multiple late returns | ✓ |
| total_denda from most recent late return | Simpler single-row lookup | |

**Notes:** "Anggota Diblokir" lives on /pinjaman (D-04), denda owed = SUM across all dikembalikan loans (D-06), "Denda Lunas" only clears is_diblokir without modifying historical total_denda (D-05).

---

## Mahasiswa-Side Denda Visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Add "Denda" column to Pinjaman Saya for dikembalikan rows | Rp amount or "-", matches riwayat_peminjaman mockup | ✓ |
| Keep table as-is | Denda only via BlockedBanner | |

| Option | Description | Selected |
|--------|-------------|----------|
| Personalize BlockedBanner with actual denda amount | "...denda Rp 5.000 belum dibayar" | ✓ |
| Keep static copy | Generic "ada denda yang belum dibayar" | |

**Notes:** Denda column added (D-07), overdue dipinjam rows also show "Terlambat" badge for mahasiswa (D-08, consistent with pustakawan's D-02), and BlockedBanner is personalized with the real amount (D-09).

---

## Brevo Notification Log Format (RET-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Structured log line via Python logger | Zero schema change, visible via docker-compose logs | ✓ |
| New notifikasi_log DB table | Inspectable via API/UI, requires new migration | |

| Option | Description | Selected |
|--------|-------------|----------|
| Developer via docker logs sufficient | Matches PRD's literal verification step | ✓ |
| Pustakawan needs in-app visibility | Larger scope, pulls in Phase 5 dashboard territory | |

**Notes:** Brevo stub is a structured `logger.info("BREVO_NOTIFICATION", extra={...})` call (D-10), inspected via `docker-compose logs backend` — no pustakawan-facing UI in Phase 4 (D-11).

---

## Claude's Discretion

- Exact endpoint design for `kembalikan` and "Denda Lunas" actions (response shapes, route naming per PRD §7 draft)
- Fine calculation day-boundary rounding formula
- `salinan_buku.status_ketersediaan → tersedia` sync on return
- `StatusBadge.jsx` "terlambat" variant styling (crimson/error-container)
- Overdue-check implementation location (inline vs helper, following `_sweep_expired_pickups` pattern)
- "Denda Lunas" button label/icon (PRD wording + manajemen_anggota's lock_open/sage-green styling)
- Empty-state treatment for new sections (reuse `EmptyState`)

## Deferred Ideas

None — discussion stayed within Phase 4 scope. Full `/anggota` member-management page and dashboard stats remain Phase 5 (DASH-01/DASH-02).
