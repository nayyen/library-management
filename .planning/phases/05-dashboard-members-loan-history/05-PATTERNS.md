# Phase 5: Dashboard, Members & Loan History - Pattern Map

**Mapped:** 2026-06-14
**Files analyzed:** 9
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `backend/app/routers/dashboard.py` | router (controller) | request-response (aggregation/read) | `backend/app/routers/peminjaman.py` | role-match (aggregation helpers in same file) |
| `backend/app/schemas/dashboard.py` | schema | transform | `backend/app/schemas/peminjaman.py` | exact (aggregate-output pattern) |
| `backend/app/routers/anggota.py` (or extend `peminjaman.py`) | router (controller) | CRUD (read roster + 1 mutation) | `backend/app/routers/peminjaman.py` (`lunasi_denda`, `anggota_diblokir` block) | exact |
| `backend/app/schemas/anggota.py` (or extend `peminjaman.py`) | schema | transform | `backend/app/schemas/peminjaman.py` (`AnggotaDiblokirOut`) | exact |
| `backend/app/main.py` | config | event-driven (router registration) | itself (existing) | exact |
| `frontend/src/pages/DashboardPage.jsx` | component (page) | request-response | `frontend/src/pages/PinjamanPage.jsx` | exact (page shell, fetch, EmptyState, tables) |
| `frontend/src/pages/AnggotaPage.jsx` | component (page) | request-response + CRUD (1 mutation) | `frontend/src/pages/PinjamanPage.jsx` (Anggota Diblokir section + KatalogPage toolbar) | exact |
| `frontend/src/components/StatusBadge.jsx` (extend) | component | transform | itself (existing) | exact |
| `frontend/src/pages/PinjamanPage.jsx` (modify) | component (page) | request-response | itself (existing) | exact |
| `frontend/src/router.jsx` (modify) | route | event-driven (route registration) | itself (existing) | exact |

---

## Pattern Assignments

### `backend/app/routers/dashboard.py` (router, request-response/aggregation)

**Analog:** `backend/app/routers/peminjaman.py`

**Imports pattern** (peminjaman.py lines 11-36):
```python
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.buku import Buku
from app.models.pengguna import Pengguna
from app.models.peminjaman import Peminjaman
from app.models.salinan_buku import SalinanBuku
from app.models.enums import (
    PeranPengguna,
    StatusPeminjaman,
    StatusSalinan,
)
from app.schemas.peminjaman import (
    AnggotaDiblokirOut,
    PeminjamanAjukan,
    PeminjamanItemOut,
    PeminjamanResponse,
    PersetujuanBody,
)

router = APIRouter(prefix="/api/peminjaman", tags=["peminjaman"])
```
For the dashboard router, use:
```python
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
```

**Auth/role-gate pattern** (peminjaman.py lines 58-64, identical helper also exists in buku.py lines 139-145):
```python
def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )
```
Either import/reuse `_pustakawan_only` from `peminjaman.py` or duplicate the 6-line helper locally (peminjaman.py and buku.py both define their own copy — duplication is the established convention, no shared `app/dependencies/roles.py` module exists yet).

**Core aggregation pattern — reuse these exact constants/helpers from `peminjaman.py`:**

`ACTIVE_STATUSES` (lines 47-51):
```python
ACTIVE_STATUSES = [
    StatusPeminjaman.menunggu_persetujuan,
    StatusPeminjaman.siap_diambil,
    StatusPeminjaman.dipinjam,
]
```
For "Peminjaman Aktif" stat (D-01: `siap_diambil` + `dipinjam` only, NOT `menunggu_persetujuan`), define a narrower list or filter `ACTIVE_STATUSES` minus `menunggu_persetujuan`:
```python
PEMINJAMAN_AKTIF_STATUSES = [
    StatusPeminjaman.siap_diambil,
    StatusPeminjaman.dipinjam,
]
```

`_is_terlambat` helper (lines 88-98) — reuse verbatim for the "Buku Terlambat" count (count rows where this returns True for all `dipinjam` rows):
```python
def _is_terlambat(row: Peminjaman, now: datetime) -> bool:
    """True if a dipinjam loan is past its tanggal_tenggat (D-02/D-08).

    Handles offset-naive tenggat (SQLite) vs offset-aware now (PostgreSQL).
    """
    tenggat = row.tanggal_tenggat
    if tenggat is None:
        return False
    if tenggat.tzinfo is None and now.tzinfo is not None:
        tenggat = tenggat.replace(tzinfo=now.tzinfo)
    return row.status_peminjaman == StatusPeminjaman.dipinjam and tenggat < now
```
Since this is a Python-side check (not a SQL filter), the dashboard endpoint should fetch all `dipinjam` rows and count via `_is_terlambat(row, now)` in a loop — same approach as `_build_item_out` usage in peminjaman.py line 120.

`_sweep_expired_pickups` (lines 124-144) — call at top of the dashboard stats endpoint too, for consistency with `/api/peminjaman`'s lazy-sweep precedent (D-12 precedent), so "Peminjaman Aktif" counts reflect swept state:
```python
def _sweep_expired_pickups(db: Session) -> None:
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
Either import this from `peminjaman.py` (it's module-level, not class-bound) or duplicate — duplication matches the codebase's existing per-router-self-contained convention.

**Denda aggregation pattern** (peminjaman.py lines 271-295, the `anggota_diblokir` build):
```python
blocked_users = (
    db.query(Pengguna)
    .filter(Pengguna.is_diblokir == True)
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
        .scalar()
        or 0
    )
    anggota_diblokir.append(...)
```
For "Total Denda Belum Lunas" + "dari X mahasiswa" sub-stat: sum `total` across all `blocked_users` for the headline figure, and `len([u for u in blocked_users if total > 0])` for the sub-stat count.

**"Total Buku" count** — simple `func.count`, mirrors `buku.py`'s query style (lines 41-56, though that file uses `.all()` + `len()`; for dashboard prefer `db.query(func.count(Buku.id)).scalar()`).

**Pending-approval preview rows** — reuse `_build_item_out` (peminjaman.py lines 101-121) and the `menunggu_persetujuan` query (lines 246-253), capped with `.limit(N)`:
```python
menunggu = [
    _build_item_out(r)
    for r in base_query.filter(
        Peminjaman.status_peminjaman == StatusPeminjaman.menunggu_persetujuan,
    )
    .order_by(Peminjaman.tanggal_pengajuan.desc())
    .limit(5)
    .all()
]
```
Note: `_build_item_out` returns the full `PeminjamanItemOut` (judul, penulis, nama_mahasiswa, tanggal_pengajuan, etc.) — the dashboard schema can either reuse `PeminjamanItemOut` directly for preview rows (simplest, matches D-02's "Claude's discretion" on shape) or define a slimmer `DashboardPengajuanPreviewOut` with just `id`, `nama_mahasiswa`, `judul`, `penulis`, `tanggal_pengajuan`. Reusing `PeminjamanItemOut` is recommended — avoids duplicating `_build_item_out`.

**Error handling pattern** — no try/except blocks for read-only aggregation in `peminjaman.py`'s GET endpoint (lines 223-327); 404s only appear in mutation endpoints (lines 352-356, 401-404, etc.) via:
```python
if not row:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="... tidak ditemukan.",
    )
```
Dashboard stats endpoint is read-only aggregation with no per-ID lookups — no 404 paths needed, only the `_pustakawan_only` 403 gate.

---

### `backend/app/schemas/dashboard.py` (schema, transform)

**Analog:** `backend/app/schemas/peminjaman.py`

**Pattern** (lines 39-65 — `AnggotaDiblokirOut` + `PeminjamanResponse` composition style):
```python
class AnggotaDiblokirOut(BaseModel):
    """A single blocked member summary, used in the pustakawan aggregate list."""

    id_pengguna: str
    nama: str
    email: str
    total_denda: int

    model_config = {"from_attributes": True}


class PeminjamanResponse(BaseModel):
    items: list[PeminjamanItemOut] | None = None
    total: int | None = None
    ...
```

Suggested `DashboardStatsOut` shape (Claude's discretion per D-02, following this composition convention):
```python
from app.schemas.peminjaman import PeminjamanItemOut


class DashboardStatsOut(BaseModel):
    total_buku: int
    peminjaman_aktif: int
    menunggu_persetujuan_count: int
    buku_terlambat: int
    total_denda_belum_lunas: int
    jumlah_mahasiswa_denda: int
    pengajuan_preview: list[PeminjamanItemOut]
```
All fields plain `int`/`list` — no `model_config = {"from_attributes": True}` needed since this is hand-assembled (not built via `.from_orm`), matching how `PeminjamanResponse` is constructed via keyword args in the router (peminjaman.py lines 297-302, 322-327).

---

### `backend/app/routers/anggota.py` (router, CRUD — read roster + 1 mutation)

**Analog:** `backend/app/routers/peminjaman.py` (the `anggota_diblokir` aggregation block + `lunasi_denda` endpoint)

**Imports** — same block as dashboard.py above, plus `from app.models.salinan_buku import SalinanBuku` if computing active-loan counts via join.

**Roster query pattern** — base on `Pengguna` (peminjaman.py doesn't query `Pengguna` directly except via `is_diblokir` filter at lines 272-276); use `pengguna.py` model fields directly:
```python
# backend/app/models/pengguna.py (lines 10-32)
class Pengguna(Base):
    __tablename__ = "pengguna"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    peran: Mapped[PeranPengguna] = mapped_column(SAEnum(PeranPengguna, ...), nullable=False)
    is_diblokir: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    peminjaman: Mapped[list["Peminjaman"]] = relationship("Peminjaman", back_populates="pengguna", lazy="select")
```
Roster endpoint:
```python
@router.get("", response_model=AnggotaListOut)
def daftar_anggota(
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> AnggotaListOut:
    _pustakawan_only(user)

    mahasiswa_list = (
        db.query(Pengguna)
        .filter(Pengguna.peran == PeranPengguna.mahasiswa)
        .order_by(Pengguna.nama.asc())
        .all()
    )

    items = []
    for m in mahasiswa_list:
        pinjaman_aktif = (
            db.query(Peminjaman)
            .filter(
                Peminjaman.id_pengguna == m.id,
                Peminjaman.status_peminjaman.in_([StatusPeminjaman.siap_diambil, StatusPeminjaman.dipinjam]),
            )
            .count()
        )
        total_denda = 0
        if m.is_diblokir:
            total_denda = (
                db.query(func.sum(Peminjaman.total_denda))
                .filter(
                    Peminjaman.id_pengguna == m.id,
                    Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
                )
                .scalar()
                or 0
            )
        items.append(AnggotaOut(
            id_pengguna=str(m.id),
            nama=m.nama,
            email=m.email,
            is_diblokir=m.is_diblokir,
            pinjaman_aktif=pinjaman_aktif,
            total_denda=total_denda,
        ))

    return AnggotaListOut(items=items, total=len(items))
```
This directly extends the `total_denda` aggregation pattern already proven at peminjaman.py lines 278-295.

**"Denda Lunas" mutation** — D-06/D-05 says this endpoint MOVES from `/pinjaman` to `/anggota`. The existing endpoint `PUT /api/peminjaman/anggota/{id_pengguna}/lunasi_denda` (peminjaman.py lines 484-528) can be either:
1. Left in place and called as-is from the new `AnggotaPage.jsx` (simplest, no backend change — `Claude's discretion` on backend shape allows this), OR
2. Re-registered under `/api/anggota/{id_pengguna}/lunasi_denda` if a fully separate `anggota` router is created.

Exact existing implementation to copy/reuse (peminjaman.py lines 484-528):
```python
@router.put("/anggota/{id_pengguna}/lunasi_denda", response_model=AnggotaDiblokirOut)
def lunasi_denda(
    id_pengguna: uuid.UUID,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> AnggotaDiblokirOut:
    """Pustakawan clears a member's block after fine is paid (RET-04).

    Sets is_diblokir = False on the member's account.  Does NOT touch any
    ``total_denda`` rows (historical record preserved per D-05).
    """
    _pustakawan_only(user)

    member = (
        db.query(Pengguna)
        .filter(Pengguna.id == id_pengguna)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anggota tidak ditemukan.",
        )

    member.is_diblokir = False
    db.commit()
    db.refresh(member)

    total = (
        db.query(func.sum(Peminjaman.total_denda))
        .filter(
            Peminjaman.id_pengguna == member.id,
            Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
        )
        .scalar()
        or 0
    )

    return AnggotaDiblokirOut(
        id_pengguna=str(member.id),
        nama=member.nama,
        email=member.email,
        total_denda=total,
    )
```
**Recommendation:** leave this endpoint where it is (under `peminjaman` router/prefix) — frontend `AnggotaPage.jsx` calls the same URL `PUT /api/peminjaman/anggota/{id_pengguna}/lunasi_denda` that `PinjamanPage.jsx` currently calls (handleLunasiDenda, line 258). No backend move required, only a frontend caller relocation.

---

### `backend/app/main.py` (config, router registration)

**Analog:** itself (lines 1-23)

```python
"""FastAPI application entry point."""

import logging
from fastapi import FastAPI

from app.routers import autentikasi, buku, peminjaman

app = FastAPI(title="Biblio - Sistem Manajemen Perpustakaan")

logging.basicConfig(...)

app.include_router(autentikasi.router)
app.include_router(buku.router)
app.include_router(peminjaman.router)
```
Add:
```python
from app.routers import autentikasi, buku, peminjaman, dashboard  # + anggota if separate

app.include_router(dashboard.router)
app.include_router(anggota.router)  # if created
```

---

### `frontend/src/pages/DashboardPage.jsx` (component, request-response)

**Analog:** `frontend/src/pages/PinjamanPage.jsx`

**Imports pattern** (PinjamanPage.jsx lines 9-17):
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import BookCoverPlaceholder from '../components/BookCoverPlaceholder';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
```
(Omit `BlockedBanner`, `Toast`, `ConfirmDialog` — dashboard has no mutations.)
Add `import { Link } from 'react-router';` for the "Lihat Semua" link and the clickable "Buku Terlambat" card.

**Date helper** (lines 31-37) — reuse `formatDateTime` for "Tanggal Pengajuan" column:
```javascript
function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${d.getDate()} ${MONTHS_ID[d.getMonth()]} ${d.getFullYear()}, ${hh}:${mm}`;
}
```
With `MONTHS_ID` array (lines 20-23). Since both PinjamanPage and DashboardPage are module-local, either duplicate this small helper block or extract to `frontend/src/lib/format.js` (latter is cleaner but not required by D-11's "no restructure" constraint, which applies only to PinjamanPage itself).

**Fetch pattern** (lines 116-132):
```javascript
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState('');

const fetchStats = useCallback(async () => {
  setLoading(true);
  setError('');
  try {
    const res = await api.get('/dashboard/stats');
    setData(res.data);
  } catch {
    setError('Gagal memuat data dashboard. Periksa koneksi Anda dan coba lagi.');
  } finally {
    setLoading(false);
  }
}, []);

useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  fetchStats();
}, [fetchStats]);
```

**Loading skeleton pattern** (lines 295-323) — same `animate-pulse` block structure, adapted to 4-card grid instead of table.

**Error state pattern** (lines 326-338):
```javascript
if (error && !data) {
  return (
    <main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
      <EmptyState
        icon="error_outline"
        title="Gagal Memuat"
        message={error}
        actionLabel="Coba Lagi"
        onAction={fetchStats}
      />
    </main>
  );
}
```

**Page header + section container pattern** (lines 362-371, 383-388):
```javascript
<main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
  <div>
    <h1 className="text-headline-md font-headline-md text-primary mb-1">Dashboard</h1>
    <p className="text-body-md font-body-md text-outline">
      Ringkasan aktivitas perpustakaan hari ini.
    </p>
  </div>
  ...
  <section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
    <div className="p-6 border-b border-paper-shadow bg-surface-container-low flex justify-between items-center">
      <div>
        <h2 className="text-headline-md font-headline-md text-primary">Daftar Pengajuan Peminjaman</h2>
        <p className="text-body-sm font-body-sm text-secondary mt-1">Menunggu persetujuan pustakawan</p>
      </div>
      <Link to="/pinjaman" className="text-ink-blue text-label-md font-label-md hover:underline flex items-center gap-1">
        Lihat Semua
        <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
      </Link>
    </div>
    ... table or EmptyState ...
  </section>
</main>
```

**`BookCell` pattern for the preview table** (lines 274-292):
```javascript
function BookCell({ item }) {
  return (
    <td className="py-3 pr-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-14 shrink-0 rounded overflow-hidden">
          <BookCoverPlaceholder judul={item.judul} kategori={item.kategori ?? ''} />
        </div>
        <div className="min-w-0">
          <p className="text-body-md font-body-md text-primary truncate">{item.judul}</p>
          <p className="text-body-sm font-body-sm text-outline truncate">{item.penulis}</p>
        </div>
      </div>
    </td>
  );
}
```

**Mahasiswa-avatar cell pattern** (lines 499-514, for the "Mahasiswa" column in the preview table):
```javascript
<td className="py-3 px-6">
  <div className="flex items-center gap-3">
    <div className="w-8 h-8 rounded-full bg-surface-tint text-on-primary flex items-center justify-center font-bold text-xs shrink-0">
      {item.nama_mahasiswa?.charAt(0)?.toUpperCase() ?? '?'}
    </div>
    <div>
      <p className="text-body-md font-body-md text-primary">{item.nama_mahasiswa}</p>
      <p className="text-body-sm font-body-sm text-outline">Mahasiswa</p>
    </div>
  </div>
</td>
```

**Empty state for preview table** (lines 468-473):
```javascript
<EmptyState
  icon="inbox"
  title="Tidak Ada Pengajuan"
  message="Belum ada pengajuan peminjaman yang menunggu persetujuan saat ini."
/>
```

**Stat card structure** — no direct existing analog (PinjamanPage has no stat cards); follow UI-SPEC's literal Tailwind classes directly:
```javascript
<div className="bg-surface-container-lowest border border-paper-shadow rounded-xl p-6 relative overflow-hidden shadow-[0_10px_40px_-10px_rgba(0,0,0,0.08)]">
  <div className="absolute top-0 right-0 w-24 h-24 bg-ink-blue/5 rounded-full -translate-y-8 translate-x-8" />
  <span className="material-symbols-outlined text-ink-blue text-3xl mb-3 block">library_books</span>
  <p className="text-headline-md font-headline-md text-primary">{data.total_buku.toLocaleString('id-ID')}</p>
  <p className="text-label-sm font-label-sm text-secondary uppercase tracking-wider mt-1">Total Buku</p>
</div>
```
"Buku Terlambat" card wraps the whole card in `<Link to="/pinjaman">` and adds `border-l-4 border-l-alert-crimson`.

---

### `frontend/src/pages/AnggotaPage.jsx` (component, request-response + CRUD mutation)

**Analog:** `frontend/src/pages/PinjamanPage.jsx` (Anggota Diblokir section, lines 743-799 + `handleLunasiDenda`, lines 249-271) and `frontend/src/pages/KatalogPage.jsx` / `SearchBar.jsx` for the toolbar.

**Imports** — same as DashboardPage plus `Toast`, `ConfirmDialog`, `StatusBadge`:
```javascript
import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';
```

**`handleLunasiDenda` — copy verbatim from PinjamanPage.jsx lines 249-271** (only the route path stays `/peminjaman/anggota/{id}/lunasi_denda` per backend recommendation above):
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
        setToast({
          type: 'success',
          message: `Denda dinyatakan lunas. Akun ${item.nama} tidak lagi diblokir.`,
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
Plus `showConfirm`/`setConfirmLoading` helpers (lines 136-142) and `confirm`/`refreshKey` state (lines 111-114).

**"Denda Lunas" button — copy exact styling from PinjamanPage.jsx lines 786-794**:
```javascript
<button
  type="button"
  onClick={() => handleLunasiDenda(item)}
  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm text-white bg-sage-green hover:opacity-90 transition-opacity min-h-[44px] shrink-0"
  aria-label={`Tandai denda ${item.nama} lunas`}
>
  <span className="material-symbols-outlined text-[18px]">lock_open</span>
  Denda Lunas
</button>
```
UI-SPEC line 191 specifies the button container should use `flex justify-end gap-3 border-t border-paper-shadow pt-4` (action row), distinct from PinjamanPage's `flex items-center justify-between` row layout — adapt the wrapper, keep the button itself unchanged.

**Search input — adapt from `SearchBar.jsx` (lines 40-63)**, but per UI-SPEC this is a simpler non-debounced controlled input (client-side filter, D-07):
```javascript
<div className="relative w-full md:flex-1">
  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-outline text-[20px] pointer-events-none">
    search
  </span>
  <input
    type="text"
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    placeholder="Cari berdasarkan Nama, Email..."
    className="w-full bg-surface-container-low border border-outline-variant rounded-full py-3 pl-12 pr-4 text-body-md font-body-md text-primary placeholder:text-outline-variant focus:outline-none focus:border-antique-gold focus:ring-1 focus:ring-antique-gold transition-all min-h-[44px]"
  />
</div>
```
Note: UI-SPEC mandates `focus:border-antique-gold focus:ring-1 focus:ring-antique-gold` (no `/30` opacity, unlike SearchBar's `ring-antique-gold/30`) — follow UI-SPEC exactly for `/anggota`.

**Status filter `<select>`** — no direct existing `<select>` analog in the codebase; follow same input border/focus convention as search input:
```javascript
<select
  value={statusFilter}
  onChange={(e) => setStatusFilter(e.target.value)}
  className="bg-surface-container-low border border-outline-variant rounded-full py-3 px-4 text-body-md font-body-md text-primary focus:outline-none focus:border-antique-gold focus:ring-1 focus:ring-antique-gold transition-all min-h-[44px]"
>
  <option value="semua">Semua Status</option>
  <option value="aktif">Aktif</option>
  <option value="diblokir">Diblokir</option>
</select>
```

**Member card grid container** (D-04, no direct existing analog — closest is `anggotaDiblokir.map` lines 762-796 but as a 2-col card grid instead of stacked rows):
```javascript
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  {filteredMembers.map((item) => (
    <div
      key={item.id_pengguna}
      className={`bg-surface-container-lowest border rounded-xl p-6 relative overflow-hidden ${
        item.is_diblokir ? 'border-alert-crimson/30' : 'border-paper-shadow'
      }`}
    >
      {/* avatar + name/email + status badge row */}
      {/* info grid */}
      {/* action row (blocked + total_denda > 0 only) */}
    </div>
  ))}
</div>
```

**Avatar circle pattern** — active variant adapts PinjamanPage.jsx lines 502-504 (`bg-surface-tint text-on-primary`); blocked variant adapts lines 768 (`bg-alert-crimson/20 text-alert-crimson`, but UI-SPEC line 187 specifies `bg-alert-crimson/10`):
```javascript
<div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm shrink-0 ${
  item.is_diblokir ? 'bg-alert-crimson/10 text-alert-crimson' : 'bg-primary-fixed text-primary-container'
}`}>
  {item.nama?.charAt(0)?.toUpperCase() ?? '?'}
</div>
```

**Denda Tertunggak text pattern** (PinjamanPage.jsx lines 779-783):
```javascript
<span className="text-alert-crimson font-semibold">
  Rp {item.total_denda.toLocaleString('id-ID')}
</span>
```
(UI-SPEC line 190 says `font-bold` for the info-grid cell version — checker flagged this as non-blocking; either weight is acceptable, `font-bold` matches UI-SPEC literally.)

**Empty states** (per UI-SPEC lines 193, mirrors EmptyState.jsx usage pattern at PinjamanPage.jsx lines 390-397 / 754-759):
```javascript
<EmptyState
  icon="search_off"
  title="Tidak Ditemukan"
  message="Tidak ada anggota yang sesuai dengan pencarian atau filter Anda. Coba ubah kata kunci atau filter status."
/>
```
and
```javascript
<EmptyState
  icon="group_off"
  title="Belum Ada Anggota"
  message="Belum ada mahasiswa yang terdaftar di sistem."
/>
```

---

### `frontend/src/components/StatusBadge.jsx` (extend with member-status variants)

**Analog:** itself (lines 9-40, the `variants` map)

Current structure:
```javascript
const variants = {
  menunggu_persetujuan: {
    label: 'Menunggu Persetujuan',
    class: 'bg-antique-gold/10 text-antique-gold border-antique-gold/20',
    icon: 'hourglass_empty',
  },
  ...
};

export default function StatusBadge({ status, compact = false }) {
  const v = variants[status] ?? { ... };
  return (
    <span className={`inline-flex items-center gap-1 border rounded-full font-label-sm ${v.class} ${
      compact ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-label-sm'
    }`}>
      <span className="material-symbols-outlined" style={{ fontSize: compact ? 14 : 16 }} aria-hidden="true">
        {v.icon}
      </span>
      {v.label}
    </span>
  );
}
```
**Issue:** all existing variants render an icon (`v.icon` always present). UI-SPEC mandates new member-status badges have **no icon** ("plain pill", lines 119-121). Two implementation options:
1. Add `icon: null` to new variant entries and make the render conditionally skip `<span className="material-symbols-outlined">` when `v.icon` is falsy — minimal, localized change to the existing component.
2. Create a sibling `MemberStatusBadge.jsx` component (UI-SPEC explicitly allows this, line 122) — avoids touching the shared component's render logic at all.

**Recommended new variant entries** (if extending `variants` map, option 1):
```javascript
anggota_aktif: {
  label: 'Aktif',
  class: 'bg-sage-green/20 text-sage-green border-sage-green/30',
  icon: null,
},
anggota_diblokir: {
  label: 'Diblokir',
  class: 'bg-alert-crimson text-on-error border-transparent',
  icon: null,
},
```
Note `anggota_diblokir` uses a **solid fill** (`bg-alert-crimson text-on-error`, no `/NN` opacity) per UI-SPEC line 120, distinct from the existing `ditolak`/`terlambat` border-tint style.

---

### `frontend/src/pages/PinjamanPage.jsx` (modify — D-05 removal + D-11 polish)

**Analog:** itself

**D-05 removal** — delete "Section 4: Anggota Diblokir" block (lines 743-799) in full, plus:
- `handleLunasiDenda` function (lines 249-271) — moves to `AnggotaPage.jsx`
- `anggotaDiblokir` derived variable (line 359) — no longer used, remove
- `loanData?.anggota_diblokir` reference — backend schema field `anggota_diblokir` on `PeminjamanResponse` can remain (harmless if unused) or be removed from the pustakawan branch in `peminjaman.py` lines 297-302 if `AnggotaPage` gets its own dedicated endpoint — Claude's discretion.

**D-11 polish** — `TanggalCell` function (lines 49-63):
```javascript
function TanggalCell({ item }) {
  const status = item.status_peminjaman;

  if (status === 'menunggu_persetujuan') {
    return <>{formatDateTime(item.tanggal_pengajuan)}</>;
  }
  if (status === 'siap_diambil') {
    return <>{formatAmbilSebelum(item.tanggal_siap_ambil)}</>;
  }
  if (status === 'dipinjam') {
    return <>Tenggat {formatDate(item.tanggal_tenggat)}</>;
  }
  // ditolak / dibatalkan
  return <>{formatDateTime(item.tanggal_pengajuan)}</>;
}
```
Add a new branch BEFORE the final fallback, for `dikembalikan`:
```javascript
if (status === 'dikembalikan') {
  return <>Dikembalikan {formatDate(item.tanggal_kembali)}</>;
}
```
`formatDate` is already defined (lines 25-29) and `item.tanggal_kembali` is already present in `PeminjamanItemOut` (backend schema line 32) and populated on return (peminjaman.py line 459) — no backend change needed for this polish.

---

### `frontend/src/router.jsx` (modify — route registration)

**Analog:** itself (lines 1-39)

Replace:
```javascript
{ path: 'dashboard', element: <ComingSoonPage title="Dashboard Pustakawan" /> },
{ path: 'anggota', element: <ComingSoonPage title="Manajemen Anggota" /> },
```
with:
```javascript
{ path: 'dashboard', element: <DashboardPage /> },
{ path: 'anggota', element: <AnggotaPage /> },
```
and add imports at top (alongside line 11's `PinjamanPage` import):
```javascript
import DashboardPage from './pages/DashboardPage';
import AnggotaPage from './pages/AnggotaPage';
```
`ComingSoonPage` import (line 8) can remain if used elsewhere, or be removed if these were its only two usages — verify before removing.

---

## Shared Patterns

### Role-gate (`_pustakawan_only`)
**Source:** `backend/app/routers/peminjaman.py` lines 58-64 (identical copy also in `backend/app/routers/buku.py` lines 139-145)
**Apply to:** `dashboard.py` stats endpoint, `anggota.py`/roster endpoint (or extended `peminjaman.py` endpoints) — both pustakawan-only per D-02/CONTEXT discretion section.
```python
def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )
```

### Lazy overdue/sweep checks (`_is_terlambat`, `_sweep_expired_pickups`)
**Source:** `backend/app/routers/peminjaman.py` lines 88-98, 124-144
**Apply to:** `dashboard.py` — must reuse the SAME logic for "Buku Terlambat" count to keep it consistent with `/pinjaman`'s `is_terlambat` badges (single source of truth, per CONTEXT's explicit note).

### Page container + section wrapper
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 297, 362, 383
**Apply to:** `DashboardPage.jsx`, `AnggotaPage.jsx` — both use:
```javascript
<main className="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-8 md:py-12 space-y-8">
```
and section containers:
```javascript
<section className="bg-surface-container-lowest border border-paper-shadow rounded-xl overflow-hidden">
```

### Fetch / loading / error state trio
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 105-127 (state), 295-338 (loading/error render)
**Apply to:** `DashboardPage.jsx`, `AnggotaPage.jsx` — `useState(null)`/`useState(true)`/`useState('')` for data/loading/error, `useCallback` fetch function, `EmptyState` with `icon="error_outline"` + "Coba Lagi" action for error state.

### Refresh-after-mutation (`refreshKey`)
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 114, 129-132, 156, 177, 204, 240, 264
**Apply to:** `AnggotaPage.jsx` — bump `refreshKey` after `handleLunasiDenda` succeeds to re-fetch the roster.

### Toast + ConfirmDialog
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 834-854 (render), 136-142 (`showConfirm`/`setConfirmLoading` helpers)
**Apply to:** `AnggotaPage.jsx` for the "Denda Lunas" confirmation flow — copy the render block and helper functions verbatim.

### `formatDate` / `formatDateTime` date helpers
**Source:** `frontend/src/pages/PinjamanPage.jsx` lines 20-37
**Apply to:** `DashboardPage.jsx` (Tanggal Pengajuan column in preview table). Either duplicate the small module-local block or extract to a shared `frontend/src/lib/format.js` — extraction is optional but reduces duplication across 2 files.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Stat card component (4x, in `DashboardPage.jsx`) | component | transform/display | No existing "stat card" / bento-grid component in the codebase — follow UI-SPEC literal Tailwind classes (lines 164-168 of UI-SPEC) directly; this is greenfield UI within an existing page-shell pattern. |
| Member card grid (`AnggotaPage.jsx`) | component | display | No existing 2-column card-grid component; closest precedent (`anggotaDiblokir` stacked list, PinjamanPage.jsx lines 761-798) uses a different (1-col stacked) layout — adapt per UI-SPEC's explicit grid spec (lines 183-192) rather than copying the stacked layout structurally. |
| Status filter `<select>` dropdown | component | transform | No `<select>` element exists anywhere in the current frontend codebase — style per UI-SPEC's input-border convention (matches `SearchBar.jsx`'s focus-ring classes). |

---

## Metadata

**Analog search scope:** `backend/app/routers/`, `backend/app/schemas/`, `backend/app/models/`, `frontend/src/pages/`, `frontend/src/components/`
**Files scanned:** `peminjaman.py` (router + schema + model), `buku.py` (router + schema + model), `pengguna.py` (model), `main.py`, `PinjamanPage.jsx`, `KatalogPage.jsx`, `StatusBadge.jsx`, `EmptyState.jsx`, `SearchBar.jsx`, `router.jsx`
**Pattern extraction date:** 2026-06-14
