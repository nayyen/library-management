# Phase 4: Returns, Fines & Blocking - Pattern Map

**Mapped:** 2026-06-14
**Files analyzed:** 4 (all modifications, zero new files)
**Analogs found:** 4 / 4 (all patterns found within the same files — Phase 4 extends existing modules)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `backend/app/routers/peminjaman.py` | router/controller | CRUD + request-response | itself (Phase 3 endpoints in same file) | exact |
| `backend/app/schemas/peminjaman.py` | schema | request-response (DTO) | itself (Phase 3 schemas in same file) | exact |
| `frontend/src/pages/PinjamanPage.jsx` | page/component | CRUD + request-response | itself (Phase 3 sections in same file) | exact |
| `frontend/src/components/StatusBadge.jsx` | component | transform (presentational) | itself (existing variant map) | exact |
| `frontend/src/components/BlockedBanner.jsx` | component | transform (presentational) | itself (existing variantConfig) | exact |

No external analogs were needed — Phase 3 already established every pattern Phase 4 extends, in the exact same files.

---

## Pattern Assignments

### `backend/app/routers/peminjaman.py` (router, CRUD/request-response)

**Analog:** itself — `serahkan_peminjaman` (lines 307-349), `_sweep_expired_pickups` (lines 100-119), `_build_item_out` (lines 81-97), `daftar_peminjaman` (lines 199-256), `_pustakawan_only`/`_mahasiswa_only` (lines 51-66)

**Imports pattern** (lines 1-32) — already imports everything Phase 4 needs (`datetime`, `timedelta`, `timezone`, `joinedload`, `HTTPException`, `status`, models, enums). Only new schema names need adding to the `from app.schemas.peminjaman import (...)` block:
```python
from app.schemas.peminjaman import (
    PeminjamanAjukan,
    PeminjamanItemOut,
    PeminjamanResponse,
    PersetujuanBody,
    # add: AnggotaDiblokirOut (or similar) for the new blocked-member shape
)
```

**Guard pattern** (lines 51-66) — reuse verbatim for both new endpoints:
```python
def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )
```
`kembalikan` and `lunasi_denda` endpoints are both pustakawan-only → call `_pustakawan_only(user)` first line, same as `serahkan_peminjaman`.

**Core endpoint pattern to copy — `serahkan_peminjaman`** (lines 307-349):
```python
@router.put("/{id_peminjaman}/serahkan", response_model=PeminjamanItemOut)
def serahkan_peminjaman(
    id_peminjaman: uuid.UUID,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanItemOut:
    _pustakawan_only(user)

    row = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
        .filter(Peminjaman.id == id_peminjaman)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengajuan peminjaman tidak ditemukan.",
        )

    if row.status_peminjaman != StatusPeminjaman.siap_diambil:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pinjaman tidak dalam status siap diambil.",
        )

    now = datetime.now(timezone.utc)
    row.status_peminjaman = StatusPeminjaman.dipinjam
    row.tanggal_pinjam = now
    row.tanggal_tenggat = now + timedelta(days=14)
    row.salinan_buku.status_ketersediaan = StatusSalinan.dipinjam

    db.commit()
    db.refresh(row)
    return _build_item_out(row)
```

**New `PUT /{id_peminjaman}/kembalikan` should follow this exact shape:**
- Same `_pustakawan_only(user)` guard
- Same row-lookup-with-joinedload + 404 pattern
- Status-precondition check: `if row.status_peminjaman != StatusPeminjaman.dipinjam: raise 409 (...)`
- Mutation block:
  ```python
  now = datetime.now(timezone.utc)
  row.tanggal_kembali = now
  row.status_peminjaman = StatusPeminjaman.dikembalikan
  row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia  # mirrors LOAN-04 reject-path sync (line 300)

  days_late = max(0, (row.tanggal_kembali.date() - row.tanggal_tenggat.date()).days)
  if days_late > 0:
      row.total_denda = days_late * 1000
      row.pengguna.is_diblokir = True
      logger.info("BREVO_NOTIFICATION", extra={
          "id_peminjaman": str(row.id),
          "email": row.pengguna.email,
          "total_denda": row.total_denda,
          "status": "Sent",
      })

  db.commit()
  db.refresh(row)
  return _build_item_out(row)
  ```
- Needs `import logging` + `logger = logging.getLogger(__name__)` near top of file (no logger currently exists — add alongside other module-level constants, lines ~36-44).

**Lazy-check / overdue-detection helper pattern — `_sweep_expired_pickups`** (lines 100-119):
```python
def _sweep_expired_pickups(db: Session) -> None:
    """Lazy check-on-read: auto-cancel siap_diambil rows past the 2x24h window.

    Called at the start of every GET /api/peminjaman.  No scheduled worker.
    """
    now = datetime.now(timezone.utc)
    expired = (
        db.query(Peminjaman)
        .options(joinedload(Peminjaman.salinan_buku))
        .filter(
            Peminjaman.status_peminjaman == StatusPeminjaman.siap_diambil,
            Peminjaman.tanggal_siap_ambil + timedelta(days=2) < now,
        )
        .all()
    )
    for row in expired:
        row.status_peminjaman = StatusPeminjaman.dibatalkan
        row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia
    if expired:
        db.commit()
```
**Use this as the template for a new `_is_terlambat(row, now)` helper** — but per discretion, the overdue flag is a *pure read-only computed field* (no DB write), so it does NOT need the commit-loop shape. Simplest form, called from `_build_item_out`:
```python
def _is_terlambat(row: Peminjaman, now: datetime) -> bool:
    """True if a dipinjam loan is past its tanggal_tenggat (D-02/D-08)."""
    return (
        row.status_peminjaman == StatusPeminjaman.dipinjam
        and row.tanggal_tenggat is not None
        and row.tanggal_tenggat < now
    )
```
Call site: inside `_build_item_out`, compute `is_terlambat = _is_terlambat(row, datetime.now(timezone.utc))` and add to `PeminjamanItemOut(... is_terlambat=is_terlambat)`.

**Response builder pattern — `_build_item_out`** (lines 81-97):
```python
def _build_item_out(row: Peminjaman) -> PeminjamanItemOut:
    """Build a PeminjamanItemOut from a joined peminjaman row.

    Expects the row to have eager-loaded relations:
    ``salinan_buku`` → ``buku`` and ``pengguna``.
    """
    return PeminjamanItemOut(
        id=str(row.id),
        status_peminjaman=row.status_peminjaman.value,
        judul=row.salinan_buku.buku.judul,
        penulis=row.salinan_buku.buku.penulis,
        lokasi_rak=row.salinan_buku.lokasi_rak,
        nama_mahasiswa=row.pengguna.nama,
        tanggal_pengajuan=row.tanggal_pengajuan,
        tanggal_siap_ambil=row.tanggal_siap_ambil,
        tanggal_tenggat=row.tanggal_tenggat,
    )
```
Extend to add `tanggal_kembali=row.tanggal_kembali`, `total_denda=row.total_denda`, `is_terlambat=...` (see helper above).

**List-builder pattern for new sections — `daftar_peminjaman` pustakawan branch** (lines 221-241):
```python
menunggu = [
    _build_item_out(r)
    for r in base_query.filter(
        Peminjaman.status_peminjaman == StatusPeminjaman.menunggu_persetujuan,
    )
    .order_by(Peminjaman.tanggal_pengajuan.desc())
    .all()
]
siap_diambil = [
    _build_item_out(r)
    for r in base_query.filter(
        Peminjaman.status_peminjaman == StatusPeminjaman.siap_diambil,
    )
    .order_by(Peminjaman.tanggal_siap_ambil.desc())
    .all()
]
return PeminjamanResponse(
    menunggu_persetujuan=menunggu,
    siap_diambil=siap_diambil,
)
```
**New `sedang_dipinjam` list** — identical shape, filter `StatusPeminjaman.dipinjam`, order `Peminjaman.tanggal_tenggat.asc()` (D-01, most-overdue-first):
```python
sedang_dipinjam = [
    _build_item_out(r)
    for r in base_query.filter(
        Peminjaman.status_peminjaman == StatusPeminjaman.dipinjam,
    )
    .order_by(Peminjaman.tanggal_tenggat.asc())
    .all()
]
```

**New `anggota_diblokir` list** — different shape (groups by `Pengguna`, not `Peminjaman`). No direct analog in this file; closest structural precedent is still the list-comprehension-over-query style above, but the query itself needs a `Pengguna`-rooted query + a `SUM(total_denda)` aggregate over `dikembalikan` loans (D-06):
```python
from sqlalchemy import func

blocked_users = (
    db.query(Pengguna)
    .filter(Pengguna.is_diblokir == True)  # noqa: E712
    .all()
)
anggota_diblokir = []
for u in blocked_users:
    total = (
        db.query(func.sum(Peminjaman.total_denda))
        .filter(
            Peminjaman.id_pengguna == u.id,
            Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
        )
        .scalar() or 0
    )
    anggota_diblokir.append(
        AnggotaDiblokirOut(
            id_pengguna=str(u.id),
            nama=u.nama,
            email=u.email,
            total_denda=total,
        )
    )
```

**Mahasiswa branch — `denda_tertunggak` field (D-09)** (lines 244-256):
```python
items = [
    _build_item_out(r)
    for r in base_query.filter(
        Peminjaman.id_pengguna == user.id,
    )
    .order_by(Peminjaman.tanggal_pengajuan.desc())
    .all()
]
return PeminjamanResponse(
    items=items,
    total=len(items),
    is_diblokir=user.is_diblokir,  # LOAN-03 banner data source (D-04)
)
```
Extend with the same `SUM(total_denda)` aggregate as above, scoped to `user.id`, added as `denda_tertunggak=<sum>`.

**`_sweep_expired_pickups` call site** (line 214, inside `daftar_peminjaman`) — the overdue computation in `_build_item_out` requires no equivalent "sweep" call since it's stateless per-row; just ensure `_build_item_out` is called after `_sweep_expired_pickups()` as it already is.

---

### `backend/app/schemas/peminjaman.py` (schema, request-response DTO)

**Analog:** itself — `PeminjamanItemOut` (lines 20-33), `PeminjamanResponse` (lines 36-47)

**Extend `PeminjamanItemOut`** (lines 20-33):
```python
class PeminjamanItemOut(BaseModel):
    """A single peminjaman row, used by both role branches."""

    id: str
    status_peminjaman: str
    judul: str
    penulis: str
    lokasi_rak: str
    nama_mahasiswa: str
    tanggal_pengajuan: datetime | None = None
    tanggal_siap_ambil: datetime | None = None
    tanggal_tenggat: datetime | None = None
    # Phase 4 additions:
    tanggal_kembali: datetime | None = None
    total_denda: int = 0
    is_terlambat: bool = False

    model_config = {"from_attributes": True}
```

**New blocked-member shape** — follow the same flat-`BaseModel` + `from_attributes` convention as `PeminjamanItemOut`:
```python
class AnggotaDiblokirOut(BaseModel):
    """A blocked member entry for the pustakawan 'Anggota Diblokir' section (D-04/D-06)."""

    id_pengguna: str
    nama: str
    email: str
    total_denda: int  # SUM(total_denda) across dikembalikan loans

    model_config = {"from_attributes": True}
```

**Extend `PeminjamanResponse`** (lines 36-47) — same optional-field pattern already used for role-conditional sections:
```python
class PeminjamanResponse(BaseModel):
    items: list[PeminjamanItemOut] | None = None
    total: int | None = None
    is_diblokir: bool | None = None
    denda_tertunggak: int | None = None  # Phase 4 (D-09), mahasiswa branch
    menunggu_persetujuan: list[PeminjamanItemOut] | None = None
    siap_diambil: list[PeminjamanItemOut] | None = None
    sedang_dipinjam: list[PeminjamanItemOut] | None = None  # Phase 4 (D-01)
    anggota_diblokir: list[AnggotaDiblokirOut] | None = None  # Phase 4 (D-04)
```

**New endpoint response schemas** — `kembalikan` and `lunasi_denda` should both return `PeminjamanItemOut`-shaped (or `AnggotaDiblokirOut`-adjacent) data consistent with existing endpoints (`serahkan_peminjaman` returns `PeminjamanItemOut`, line 307). Recommend:
- `PUT /{id}/kembalikan` → `response_model=PeminjamanItemOut` (mirrors `serahkan_peminjaman`)
- `PUT /lunasi_denda` (or `/anggota/{id_pengguna}/lunasi_denda`) → a small dedicated response, e.g. reuse `AnggotaDiblokirOut` with `total_denda` unchanged but `is_diblokir` implicitly false — OR a minimal ack shape. Either is consistent with project convention of typed `response_model`s.

No `PersetujuanBody`-style request body needed for either new endpoint (both are path-param-only mutations, like `serahkan_peminjaman`).

---

### `frontend/src/components/StatusBadge.jsx` (component, transform)

**Analog:** itself — `variants` map (lines 9-35)

**Current variant shape** (lines 20-24, `dipinjam` entry — closest sibling):
```javascript
dipinjam: {
  label: 'Dipinjam',
  class: 'bg-primary-container/10 text-primary-container border-primary-fixed',
  icon: 'inventory_2',
},
```

**Add new `terlambat` variant** (per UI-SPEC lines 144-149), inserted into the same `variants` object (suggested position: immediately after `dipinjam`, before `ditolak`):
```javascript
terlambat: {
  label: 'Terlambat',
  class: 'bg-error-container text-on-error-container border-alert-crimson',
  icon: 'warning',
},
```
No changes to the component function itself (lines 37-60) — the existing `variants[status] ?? {...}` fallback and render logic handle the new key automatically. Callers (PinjamanPage) decide `terlambat` vs `dipinjam` based on `item.is_terlambat`.

---

### `frontend/src/components/BlockedBanner.jsx` (component, transform)

**Analog:** itself — `variantConfig.blocked` (lines 16-22) and render logic (lines 25-49)

**Current shape** (lines 16-22):
```javascript
blocked: {
  heading: 'Akun Diblokir',
  body: 'Akun Anda diblokir karena ada denda yang belum dibayar. Selesaikan pembayaran denda di perpustakaan untuk mengajukan pinjaman baru.',
  icon: 'block',
  class: 'bg-alert-crimson/10 border-alert-crimson/30 text-alert-crimson',
  iconClass: 'text-alert-crimson',
},
```

**Change `body` to a function** (per UI-SPEC lines 161-169):
```javascript
blocked: {
  heading: 'Akun Diblokir',
  body: (dendaAmount) =>
    `Akun Anda diblokir karena denda Rp ${dendaAmount.toLocaleString('id-ID')} belum dibayar. Selesaikan pembayaran denda di perpustakaan untuk mengajukan pinjaman baru.`,
  icon: 'block',
  class: 'bg-alert-crimson/10 border-alert-crimson/30 text-alert-crimson',
  iconClass: 'text-alert-crimson',
},
```

**Render logic change** — current (lines 25-48):
```jsx
export default function BlockedBanner({ variant }) {
  if (!variant) return null;

  const config = variantConfig[variant];
  if (!config) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`rounded-lg border p-4 flex items-start gap-3 mb-6 ${config.class}`}
    >
      <span
        className={`material-symbols-outlined text-2xl shrink-0 ${config.iconClass}`}
        aria-hidden="true"
      >
        {config.icon}
      </span>
      <div>
        <p className="text-label-md font-label-md">{config.heading}</p>
        <p className="text-body-lg font-body-lg mt-1">{config.body}</p>
      </div>
    </div>
  );
}
```
**Change signature to `BlockedBanner({ variant, dendaAmount })`** and the body line to:
```jsx
<p className="text-body-lg font-body-lg mt-1">
  {typeof config.body === 'function' ? config.body(dendaAmount ?? 0) : config.body}
</p>
```
The `limit` variant's `body` stays a plain string (line 11) — the `typeof` guard preserves it untouched.

---

### `frontend/src/pages/PinjamanPage.jsx` (page, CRUD/request-response)

**Analog:** itself — `handleHandover` (lines 183-208) for the mutating-action pattern; `siapDiambil` table section (lines 472-568) for the new "Sedang Dipinjam" table section; mahasiswa table section (lines 316-374) for the "Denda" column addition; `EmptyState` usage (lines 391-395, 483-487) for empty states.

**Mutating-action pattern to copy — `handleHandover`** (lines 183-208):
```javascript
async function handleHandover(item) {
  const tenggat = new Date();
  tenggat.setDate(tenggat.getDate() + 14);
  const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
  const formatted = `${tenggat.getDate()} ${months[tenggat.getMonth()]} ${tenggat.getFullYear()}`;

  showConfirm({
    title: 'Tandai Sudah Diserahkan?',
    message: `Buku "${item.judul}" akan ditandai sebagai diserahkan kepada ${item.nama_mahasiswa}. Tenggat pengembalian akan diatur ke 14 hari dari sekarang (${formatted}).`,
    confirmLabel: 'Serahkan',
    destructive: false,
    onConfirm: async () => {
      setConfirmLoading(true);
      try {
        await api.put(`/peminjaman/${item.id}/serahkan`);
        setConfirm(null);
        setToast({ type: 'success', message: `Buku berhasil diserahkan. Tenggat pengembalian: ${formatted}.` });
        setRefreshKey((k) => k + 1);
      } catch {
        setConfirm(null);
        setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
      }
    },
  });
}
```

**New `handleKembalikan(item)`** — same shape, with on-time/overdue branching per D-03/UI-SPEC lines 213-223:
```javascript
async function handleKembalikan(item) {
  const now = new Date();
  const tenggat = new Date(item.tanggal_tenggat);
  const isOverdue = tenggat < now;
  const daysLate = isOverdue
    ? Math.floor((now - tenggat) / 86400000)
    : 0;

  showConfirm({
    title: 'Tandai Sudah Dikembalikan?',
    message: isOverdue
      ? `Buku "${item.judul}" terlambat ${daysLate} hari. Denda Rp ${(daysLate * 1000).toLocaleString('id-ID')} akan tercatat dan akun ${item.nama_mahasiswa} akan diblokir.`
      : 'Tandai buku ini sudah dikembalikan?',
    confirmLabel: 'Kembalikan',
    destructive: isOverdue,
    onConfirm: async () => {
      setConfirmLoading(true);
      try {
        const res = await api.put(`/peminjaman/${item.id}/kembalikan`);
        setConfirm(null);
        const denda = res.data.total_denda ?? 0;
        setToast({
          type: 'success',
          message: denda > 0
            ? `Buku berhasil dikembalikan. Denda Rp ${denda.toLocaleString('id-ID')} tercatat dan akun mahasiswa diblokir.`
            : 'Buku berhasil dikembalikan.',
        });
        setRefreshKey((k) => k + 1);
      } catch {
        setConfirm(null);
        setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
      }
    },
  });
}
```

**New `handleLunasiDenda(item)`** — same shape, per UI-SPEC lines 274-279:
```javascript
async function handleLunasiDenda(item) {
  showConfirm({
    title: 'Tandai Denda Lunas?',
    message: `Denda sebesar Rp ${item.total_denda.toLocaleString('id-ID')} milik ${item.nama} akan dinyatakan lunas dan akun akan dibuka kembali.`,
    confirmLabel: 'Denda Lunas',
    destructive: false,
    onConfirm: async () => {
      setConfirmLoading(true);
      try {
        await api.put(`/peminjaman/anggota/${item.id_pengguna}/lunasi_denda`);
        setConfirm(null);
        setToast({ type: 'success', message: `Denda dinyatakan lunas. Akun ${item.nama} tidak lagi diblokir.` });
        setRefreshKey((k) => k + 1);
      } catch {
        setConfirm(null);
        setToast({ type: 'error', message: 'Gagal memproses tindakan. Silakan coba lagi.' });
      }
    },
  });
}
```

**New "Sedang Dipinjam" table section** — copy the full `<section>` shell + table structure from "Siap Diambil" (lines 472-568), substituting:
- Title "Sedang Dipinjam" / subtitle from UI-SPEC line 185
- Columns: Mahasiswa (same avatar-cell markup, lines 517-531) / Buku (`<BookCell item={item} />`) / Tenggat (`formatDate(item.tanggal_tenggat)`, crimson if `item.is_terlambat`) / Status (`<StatusBadge status={item.is_terlambat ? 'terlambat' : 'dipinjam'} />`) / Aksi ("Kembalikan" button per UI-SPEC lines 199-210, calling `handleKembalikan(item)`)
- Empty state: `<EmptyState icon="inventory_2" title="Tidak Ada Pinjaman Aktif" message="Tidak ada buku yang sedang dipinjam saat ini." />` (matches the `EmptyState` call shape at lines 391-395/483-487, no action button)
- Data source: `const sedangDipinjam = loanData?.sedang_dipinjam ?? [];` (mirrors `siapDiambil` at line 294)

**New "Anggota Diblokir" card-list section** — no direct table analog (card layout per UI-SPEC lines 237-268); follow the `<section>` shell convention (lines 380, 472) for the outer wrapper, but body is `<div className="p-6 space-y-4">` containing one card per `anggota_diblokir` item (markup given verbatim in UI-SPEC). Empty state: `<EmptyState icon="task_alt" title="Tidak Ada Anggota Diblokir" message="Semua anggota dalam status baik — tidak ada denda tertunggak." />`. Data source: `const anggotaDiblokir = loanData?.anggota_diblokir ?? [];`

**"Denda" column on mahasiswa table** — extend the existing `<thead>` (lines 336-346) and row-rendering (lines 352-367):
```jsx
{/* new <th>, after Tanggal */}
<th className="px-6 pt-4 pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider text-right">
  Denda
</th>
```
```jsx
{/* new <td>, after TanggalCell <td> */}
<td className="py-3 px-6 text-right text-body-sm font-body-sm">
  {item.status_peminjaman === 'dikembalikan' && item.total_denda > 0 ? (
    <span className="text-alert-crimson font-medium">
      Rp {item.total_denda.toLocaleString('id-ID')}
    </span>
  ) : (
    <span className="text-outline">-</span>
  )}
</td>
```
Also extend `SkeletonRows` (lines 66-86) with a 4th `<td>` skeleton block, matching the existing `<td className="py-3"><div className="h-4 ... w-28" /></td>` shape (line 81-83).

**Status column for mahasiswa table** — `<StatusBadge status={item.status_peminjaman} />` (line 361) becomes `<StatusBadge status={item.is_terlambat ? 'terlambat' : item.status_peminjaman} />` (D-08).

**BlockedBanner call site** (lines 309-313) — extend with `dendaAmount` prop:
```jsx
{isMahasiswa && (
  <BlockedBanner
    variant={isDiblokir ? 'blocked' : activeCount >= 5 ? 'limit' : null}
    dendaAmount={loanData?.denda_tertunggak ?? 0}
  />
)}
```

**Loading skeleton for pustakawan** (lines 572-601) — the `[1, 2].map(...)` loop should become `[1, 2, 3, 4].map(...)` to account for the 2 new sections, or leave as-is if the new sections render only post-load (existing pattern already gates pustakawan sections on `!loading`, line 377).

---

## Shared Patterns

### Auth Guards (backend)
**Source:** `backend/app/routers/peminjaman.py` lines 51-66 (`_pustakawan_only`, `_mahasiswa_only`)
**Apply to:** Both new endpoints (`kembalikan`, `lunasi_denda`) — both pustakawan-only, call `_pustakawan_only(user)` as the first statement.

### Row Lookup + 404/409 Error Handling (backend)
**Source:** `backend/app/routers/peminjaman.py` lines 320-339 (`serahkan_peminjaman`)
**Apply to:** Both new endpoints — `joinedload`-eager query, `if not row: raise 404`, status-precondition `raise 409`.

### Response Builder (backend)
**Source:** `backend/app/routers/peminjaman.py` lines 81-97 (`_build_item_out`)
**Apply to:** `kembalikan` endpoint response and all `*_dipinjam`-status list items — extend with `tanggal_kembali`, `total_denda`, `is_terlambat`.

### Confirm + Toast + RefreshKey Mutation Cycle (frontend)
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 183-208 (`handleHandover`)
**Apply to:** `handleKembalikan` and `handleLunasiDenda` — identical `showConfirm({...}) → onConfirm async → api.put → setConfirm(null) → setToast(...) → setRefreshKey((k) => k+1)` / catch → error toast cycle.

### EmptyState Usage (frontend)
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 391-395 (Menunggu Persetujuan) and 483-487 (Siap Diambil)
**Apply to:** "Sedang Dipinjam" and "Anggota Diblokir" empty states — same `<EmptyState icon="..." title="..." message="..." />`, no action button.

### Section Shell (frontend)
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 380, 472 (`<section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">` + header `<div className="p-6 border-b border-paper-shadow bg-surface-container-low">`)
**Apply to:** Both new sections — reuse the shell wrapper; "Anggota Diblokir" cards live inside a `<div className="p-6 space-y-4">` body instead of a table.

---

## No Analog Found

None — every file in scope is a Phase 3 file being extended, and Phase 3 already established the exact patterns needed (CRUD endpoint shape, lazy-check helper shape, response-builder shape, mutating-action UI shape, variant-map shape).

---

## Metadata

**Analog search scope:** `backend/app/routers/peminjaman.py`, `backend/app/schemas/peminjaman.py`, `backend/app/models/peminjaman.py`, `backend/app/models/pengguna.py`, `backend/app/models/enums.py`, `frontend/src/pages/PinjamanPage.jsx`, `frontend/src/components/StatusBadge.jsx`, `frontend/src/components/BlockedBanner.jsx`
**Files scanned:** 8
**Pattern extraction date:** 2026-06-14
