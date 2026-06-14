# Phase 3: Loan Request & Approval Workflow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 3-Loan Request & Approval Workflow
**Areas discussed:** Loan request flow (mahasiswa), Pustakawan approval & handover UI, Mahasiswa's 'Pinjaman' view, Pickup-window auto-cancellation (LOAN-05)

---

## Loan request flow (mahasiswa)

### Where should the 'Pinjam Buku' button live?

| Option | Description | Selected |
|--------|-------------|----------|
| Detail page only | On /katalog/{id}, near book info and per-copy table (D-07). Simpler — one integration point. | ✓ |
| Catalog card + detail page | Quick action on grid cards AND detail page — more mockup-faithful but two integration points. | |
| You decide | Claude picks based on existing layout. | |

**User's choice:** Detail page only

### Which physical copy (salinan_buku) gets reserved when a mahasiswa requests a loan?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-pick first available | System picks any tersedia salinan automatically — simplest UX. | |
| Mahasiswa picks a copy | SalinanTable gets a 'Pinjam' action per tersedia row; matches form_pengajuan_pinjam mockup's 'Buku Terpilih' with barcode. | ✓ |
| You decide | Claude picks based on simplicity vs fidelity. | |

**User's choice:** Mahasiswa picks a copy

### Should clicking 'Pinjam' on a copy show the form_pengajuan_pinjam confirmation modal before submitting?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, confirmation modal | Shows Buku Terpilih, Informasi Peminjam, Estimasi Tenggat Waktu, then Kirim. Toast on success. | ✓ |
| Submit immediately + toast | Direct create on click; Toast shows result/rejection reason. Fewer clicks. | |
| You decide | Claude picks simplest + consistent. | |

**User's choice:** Yes, confirmation modal

### How should the 5-loan-limit (LOAN-02) and blocked-account (LOAN-03) rejections surface to the mahasiswa?

| Option | Description | Selected |
|--------|-------------|----------|
| Reject at submit, show reason | Confirm modal always available; API 400 + reason shown on Kirim if blocked/at limit. | |
| Pre-check + disable buttons | Fetch loan status on load; disable all Pinjam buttons + persistent banner if blocked/at-limit, API still enforces. | ✓ |
| You decide | Claude picks simplest with clear feedback. | |

**User's choice:** Pre-check + disable buttons

---

## Pustakawan approval & handover UI

### Where does the pustakawan's approval queue ('Daftar Pengajuan Peminjaman') live?

| Option | Description | Selected |
|--------|-------------|----------|
| Shared 'Pinjaman' page | Replace /pinjaman ComingSoonPage; pustakawan sees status sections, mahasiswa sees own requests. Mirrors Phase 2's /katalog role-tab pattern. | ✓ |
| Build it into '/dashboard' now | Replace /dashboard ComingSoonPage with just the queue table; /pinjaman stays placeholder. | |
| You decide | Claude picks based on nav fit. | |

**User's choice:** Shared 'Pinjaman' page

### How should the pustakawan's view of pending/siap_diambil requests be organized on the 'Pinjaman' page?

| Option | Description | Selected |
|--------|-------------|----------|
| Status tabs | Tabs: Menunggu Persetujuan / Siap Diambil, each with own table+actions. | |
| Stacked sections | Both sections visible at once, stacked vertically — no tab-switching needed. | ✓ |
| You decide | Claude picks based on volume/components. | |

**User's choice:** Stacked sections

### How do the approve/reject (✓/✕) and 'Serahkan' actions behave when clicked?

| Option | Description | Selected |
|--------|-------------|----------|
| Direct action + toast | Immediate API call + toast, no confirmation step. | |
| Confirm dialog first | Reuse Phase 2's ConfirmDialog before each action — e.g. 'Tolak pengajuan ini?'. | ✓ |
| You decide | Claude picks per-action. | |

**User's choice:** Confirm dialog first

### Should the pustakawan 'Pinjaman' page also show a read-only list of currently active loans (dipinjam) in Phase 3?

| Option | Description | Selected |
|--------|-------------|----------|
| No — actionable only | Just Menunggu Persetujuan + Siap Diambil. Active-loan visibility is Phase 4/5. | ✓ |
| Yes — add a 3rd section | Add 'Sedang Dipinjam' read-only table now. | |
| You decide | Claude picks based on focus. | |

**User's choice:** No — actionable only

---

## Mahasiswa's 'Pinjaman' view

### What should the mahasiswa see on the 'Pinjaman' page in Phase 3?

| Option | Description | Selected |
|--------|-------------|----------|
| Basic 'Pinjaman Saya' list | Simple list of own peminjaman: buku, status badge, relevant date. Phase 5 (DASH-03) enriches later. | ✓ |
| Keep as 'Coming soon' | Only feedback is the confirm modal + toast from Area 1; full history is Phase 5. | |
| You decide | Claude picks based on demonstrating the state machine end-to-end. | |

**User's choice:** Basic 'Pinjaman Saya' list

### How should 'Pinjaman Saya' be organized for the mahasiswa?

| Option | Description | Selected |
|--------|-------------|----------|
| Stacked sections by status | Mirrors pustakawan page: Menunggu Persetujuan / Siap Diambil / Sedang Dipinjam as separate sections. | |
| Single list, sorted | One list/table, most recent first, status badge column + relevant date. | ✓ |
| You decide | Claude picks for consistency. | |

**User's choice:** Single list, sorted

### Should the mahasiswa's 'Pinjaman Saya' list include closed requests (ditolak/dibatalkan), or only active ones?

| Option | Description | Selected |
|--------|-------------|----------|
| All statuses | Show every peminjaman record including ditolak/dibatalkan with status badges. | ✓ |
| Active only | Only menunggu_persetujuan/siap_diambil/dipinjam; closed ones vanish. | |
| You decide | Claude picks for clearest feedback. | |

**User's choice:** All statuses

### For 'Siap Diambil' rows in the mahasiswa's list, what pickup-deadline info should be shown?

| Option | Description | Selected |
|--------|-------------|----------|
| Deadline date/time | Show computed deadline (tanggal_siap_ambil + 2x24h) as absolute date/time. | ✓ |
| Relative countdown | Show remaining time as a live countdown. | |
| You decide | Claude picks simplest consistent approach. | |

**User's choice:** Deadline date/time

---

## Pickup-window auto-cancellation (LOAN-05)

### How should the 2x24h siap_diambil → dibatalkan expiry be enforced, given there's no background worker yet?

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy check-on-read | On every /pinjaman list query, check each siap_diambil row's deadline; if expired, update to dibatalkan and reset salinan_buku to tersedia before returning. No new infra. | ✓ |
| Scheduled background job | Add APScheduler (or similar) to sweep expired rows periodically — new moving part for docker-compose. | |
| You decide | Claude picks best fit for stack/timeline. | |

**User's choice:** Lazy check-on-read

---

## Claude's Discretion

- Exact Bahasa Indonesia wording for modal text, toast messages, button labels, banner copy.
- Active-loan definition for LOAN-02 (which status_peminjaman values count as "active").
- Backend endpoint/route design for `/api/peminjaman/*` and response schema shapes.
- Empty-state treatment for "Pinjaman Saya" / queue sections when empty.
- Where the lazy-check sweep (D-12) is implemented to avoid duplication across role branches.

## Deferred Ideas

None — discussion stayed within Phase 3 scope. Read-only "Sedang Dipinjam" visibility for pustakawan and the full "Riwayat Peminjaman" table (search, pagination, denda) are explicitly deferred to Phase 4/5.
