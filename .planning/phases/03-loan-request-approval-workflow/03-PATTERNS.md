# Phase 3: Loan Request & Approval Workflow - Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 9
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|----------------|
| `backend/app/routers/peminjaman.py` | router/controller | CRUD + request-response | `backend/app/routers/buku.py` | exact |
| `backend/app/schemas/peminjaman.py` | schema | request-response | `backend/app/schemas/buku.py` | exact |
| `backend/app/main.py` (modify) | config | request-response | `backend/app/main.py` itself | exact (existing registration pattern) |
| `backend/tests/test_peminjaman.py` | test | request-response | `backend/tests/test_buku.py` | exact |
| `frontend/src/pages/PinjamanPage.jsx` | component (page) | request-response, CRUD | `frontend/src/pages/KatalogPage.jsx` | exact (role-conditional shared route) |
| `frontend/src/components/LoanRequestModal.jsx` | component (modal) | request-response | `frontend/src/components/BookFormModal.jsx` | exact |
| `frontend/src/components/StatusBadge.jsx` | component | transform (display) | `frontend/src/components/AvailabilityBadge.jsx` | exact |
| `frontend/src/components/AntrianTable.jsx` | component (table) | CRUD (action rows) | `frontend/src/components/SalinanTable.jsx` | role-match |
| `frontend/src/components/BlockedBanner.jsx` | component | transform (display) | `frontend/src/components/EmptyState.jsx` (banner-ish) + `AvailabilityBadge.jsx` (chip styling) | role-match |
| `frontend/src/components/SalinanTable.jsx` (modify) | component | CRUD (action column) | itself (Phase 2) | exact |
| `frontend/src/pages/BukuDetailPage.jsx` (modify) | component (page) | request-response | itself (Phase 2) | exact |
| `frontend/src/router.jsx` (modify) | route config | request-response | itself (Phase 1/2) | exact |

## Pattern Assignments

### `backend/app/routers/peminjaman.py` (router, CRUD + request-response)

**Analog:** `backend/app/routers/buku.py`

**Imports pattern** (lines 1-24):
```python
"""Book catalog router — read + write endpoints (CAT-01 through CAT-04)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.buku import Buku
from app.models.salinan_buku import SalinanBuku
from app.models.enums import PeranPengguna, KondisiBuku, StatusSalinan
from app.schemas.buku import (
    BukuCreate,
    BukuUpdate,
    BukuOut,
    ...
)

router = APIRouter(prefix="/api/buku", tags=["buku"])
```
For peminjaman, mirror this exactly:
```python
from app.models.peminjaman import Peminjaman
from app.models.salinan_buku import SalinanBuku
from app.models.enums import PeranPengguna, StatusSalinan, StatusPeminjaman
from app.schemas.peminjaman import (
    PeminjamanAjukan, PeminjamanOut, PeminjamanListOut, PersetujuanAction,
)

router = APIRouter(prefix="/api/peminjaman", tags=["peminjaman"])
```

**Role-gate helper pattern** (lines 139-145):
```python
def _pustakawan_only(user) -> None:
    """Helper: raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )
```
Reuse verbatim for `PUT /peminjaman/{id}/persetujuan` and `PUT /peminjaman/{id}/serahkan` (pustakawan-only mutations).

**Core CRUD/create pattern with pre-check + commit** (lines 148-190, `tambah_buku`):
```python
@router.post("", response_model=BukuOut, status_code=201)
def tambah_buku(
    body: BukuCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> BukuOut:
    """Create ... """
    _pustakawan_only(user)  # <- swap for mahasiswa-only check on /ajukan, or omit

    # Pre-check (uniqueness / business rule)
    existing = db.query(Buku).filter(Buku.isbn == body.isbn).first()
    if existing:
        raise HTTPException(status_code=409, detail="...")

    entity = Buku(...)
    db.add(entity)
    try:
        db.commit()
        db.refresh(entity)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="...")

    return BukuOut(...)
```
For `POST /api/peminjaman/ajukan` (D-01..D-04, LOAN-01/02/03):
- Pre-checks before commit: (1) `user.is_diblokir` → 400 LOAN-03, (2) active-loan count (`status_peminjaman in [menunggu_persetujuan, siap_diambil, dipinjam]`) >= 5 → 400 LOAN-02, (3) `salinan_buku.status_ketersediaan == tersedia` → 400/409 if not (race condition copy).
- On success: create `Peminjaman` row with `status_peminjaman=menunggu_persetujuan`, set `salinan_buku.status_ketersediaan = dipesan`, commit both in one transaction.

**404-then-mutate pattern** (lines 193-245, `ubah_buku`):
```python
@router.put("/{id_buku}", response_model=BukuOut)
def ubah_buku(id_buku: uuid.UUID, body: BukuUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)) -> BukuOut:
    _pustakawan_only(user)
    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan.")
    # mutate fields, commit, refresh
```
Use this shape for `PUT /peminjaman/{id}/persetujuan` (approve/reject) and `PUT /peminjaman/{id}/serahkan` (handover): fetch by id → 404 if missing → validate current `status_peminjaman` is in the expected pre-state (else 409/400) → mutate `status_peminjaman` + related `salinan_buku.status_ketersediaan` + timestamps → commit.

**List endpoint with derived/joined data** (lines 29-82, `daftar_buku`):
```python
@router.get("", response_model=BukuListOut)
def daftar_buku(..., db: Session = Depends(get_db), _=Depends(get_current_user)) -> BukuListOut:
    query = db.query(Buku)
    ...
    items = []
    for buku in buku_list:
        tersedia = db.query(SalinanBuku).filter(...).count() > 0
        items.append(BukuListItem(...))
    return BukuListOut(items=items, total=len(items))
```
For `GET /api/peminjaman` (the shared list endpoint, D-05/D-09/D-12):
- Branch on `user.peran`: pustakawan gets two filtered querysets (`menunggu_persetujuan`, `siap_diambil`); mahasiswa gets all rows for `id_pengguna == user.id` ordered by `tanggal_pengajuan desc`.
- **D-12 lazy-sweep**: before building the response, run a shared helper (e.g. `_sweep_expired_pickups(db)`) that queries all `siap_diambil` rows where `tanggal_siap_ambil + timedelta(days=2) < now()`, sets `status_peminjaman = dibatalkan` and resets the linked `salinan_buku.status_ketersediaan = tersedia`, then commits — called once at the top of this endpoint regardless of role, matching the "no duplication across role branches" discretion note.
- Join `Peminjaman` -> `SalinanBuku` -> `Buku` and `Peminjaman` -> `Pengguna` to populate `judul`/`penulis`/`nama_mahasiswa`/`lokasi_rak` fields in the response items (similar join-then-build-item-list shape as `daftar_buku`).

**Error handling pattern**: `HTTPException(status_code=..., detail="...")` for all error cases (400 for business-rule violations LOAN-02/03, 404 for missing records, 403 via `_pustakawan_only`/mahasiswa-only checks, 409 for race-condition conflicts like "salinan sudah tidak tersedia"). No centralized exception handler exists — each endpoint raises inline, matching `buku.py`.

---

### `backend/app/schemas/peminjaman.py` (schema, request-response)

**Analog:** `backend/app/schemas/buku.py`

**Output model with `from_attributes`** (lines 71-89):
```python
class SalinanBukuOut(BaseModel):
    id: str
    lokasi_rak: str
    kondisi: str
    status_ketersediaan: str

    model_config = {"from_attributes": True}
```
Use this shape for `PeminjamanOut` (id, status_peminjaman, tanggal_* fields as ISO strings or datetime, total_denda).

**Create/input model with Field validators** (lines 9-32):
```python
class BukuCreate(BaseModel):
    judul: str = Field(..., min_length=1, max_length=255)
    ...
    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        ...
```
For `PeminjamanAjukan`, the only required input is `id_salinan_buku: str` (or `uuid.UUID`) — minimal validation, mirror the `Field(...)` style.

**List wrapper** (lines 95-97):
```python
class BukuListOut(BaseModel):
    items: list[BukuListItem]
    total: int
```
For the `/pinjaman` GET response, consider two shapes depending on role — either a single `PeminjamanListOut` with `items: list[PeminjamanItemOut]` (mahasiswa) or a pustakawan-specific shape with `menunggu_persetujuan: list[...]` and `siap_diambil: list[...]` sections (matches D-06 stacked-sections UI). Discretion: planner should decide on one unified schema with optional/nullable sections vs. two distinct response models — `BukuDetailOut(BukuOut)` (line 100-103) shows the "extend base with extra fields" pattern if a shared base is preferred.

**Detail/extended model pattern** (lines 100-103):
```python
class BukuDetailOut(BukuOut):
    tersedia: bool
    salinan: list[SalinanBukuOut]
```
Use this inheritance style if `PeminjamanItemOut` needs to nest book/copy info (e.g. `judul`, `penulis`, `lokasi_rak`, `nama_mahasiswa`).

---

### `backend/app/main.py` (modify, config)

**Analog:** itself, current registration block

```python
from app.routers import autentikasi, buku
...
app.include_router(autentikasi.router)
app.include_router(buku.router)
```
Add:
```python
from app.routers import autentikasi, buku, peminjaman
...
app.include_router(peminjaman.router)
```

---

### `backend/tests/test_peminjaman.py` (test, request-response)

**Analog:** `backend/tests/test_buku.py`

Mirror structure: helper logins via `client.post("/api/auth/login", ...)` to get tokens for mahasiswa/pustakawan fixtures, then `client.post`/`client.put` with `headers={"Authorization": f"Bearer {token}"}`. Test groups to replicate:
- `test_create_buku_pustakawan` / `test_create_buku_forbidden_for_mahasiswa` (lines 315-362) → analog for `test_ajukan_peminjaman_mahasiswa` / `test_ajukan_forbidden_for_pustakawan`.
- `test_create_buku_duplicate_isbn` (lines 364-399, pre-check + 409) → analog for LOAN-02 (5-loan limit, 400) and LOAN-03 (blocked account, 400) tests.
- `test_edit_buku` + `test_detail_buku_404` (lines 220-278, 402-439) → analog for `persetujuan`/`serahkan` 404 and invalid-state-transition tests.
- `test_list_buku_unauthorized` (line 279) → analog for unauthenticated `/api/peminjaman` 401 test.

---

### `frontend/src/pages/PinjamanPage.jsx` (page, request-response + CRUD)

**Analog:** `frontend/src/pages/KatalogPage.jsx`

**Role detection + refreshKey pattern** (lines 1-10, 48-55, 65-95):
```jsx
import { useState, useEffect } from 'react';
import api from '../lib/api';
import { getToken, decodeToken } from '../lib/auth';
import EmptyState from '../components/EmptyState';

export default function PinjamanPage() {
  const token = getToken();
  const decoded = token ? decodeToken(token) : null;
  const peran = decoded?.peran ?? 'mahasiswa';

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const abortController = new AbortController();
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError('');

    api.get('/peminjaman', { signal: abortController.signal })
      .then((res) => { if (!cancelled) setData(res.data); })
      .catch(() => { if (!cancelled) setError('Gagal memuat data pinjaman. Periksa koneksi Anda dan coba lagi.'); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; abortController.abort(); };
  }, [refreshKey]);
  // ...
}
```

**Conditional role-based rendering** (lines 154-197, 202-277 — the `tab === 'kelola'` vs jelajah branches):
```jsx
{peran === 'pustakawan' ? (
  /* stacked sections: AntrianTable x2 */
) : (
  /* single sorted list table */
)}
```

**Action handler → ConfirmDialog → refreshKey bump pattern** (lines 125-152, `handleDeleteClick`/`handleDeleteConfirm`):
```jsx
function handleActionClick(row, action) {
  setSelectedRow(row);
  setPendingAction(action);
}

async function handleActionConfirm() {
  setActionLoading(true);
  try {
    await api.put(`/peminjaman/${selectedRow.id}/persetujuan`, { aksi: pendingAction });
    setSelectedRow(null);
    setToast({ message: '...', type: 'success' });
    setRefreshKey((k) => k + 1);
  } catch (err) {
    setToast({ message: err.response?.data?.detail || 'Gagal memproses tindakan. Silakan coba lagi.', type: 'error' });
  } finally {
    setActionLoading(false);
  }
}
```

**Empty/loading/error state pattern** (lines 234-263):
```jsx
{loading ? <SkeletonRows /> : error ? (
  <EmptyState icon="error" title="Terjadi Kesalahan" message={error} actionLabel="Coba Lagi" onAction={() => setRefreshKey((k) => k + 1)} />
) : items.length === 0 ? (
  <EmptyState icon="inbox" title="Tidak Ada Pengajuan" message="..." />
) : (
  /* table */
)}
```

---

### `frontend/src/components/LoanRequestModal.jsx` (modal, request-response)

**Analog:** `frontend/src/components/BookFormModal.jsx`

**Modal shell, backdrop/escape close, header/footer structure** (lines 123-146, 215-238):
```jsx
function handleBackdrop(e) {
  if (e.target === e.currentTarget) onClose();
}
function handleKeyDown(e) {
  if (e.key === 'Escape') onClose();
}

return (
  <div
    className="fixed inset-0 z-50 flex items-center justify-center bg-primary/40 backdrop-blur-sm p-4"
    role="dialog" aria-modal="true" aria-labelledby="form-modal-title"
    onClick={handleBackdrop} onKeyDown={handleKeyDown}
  >
    <div className="bg-surface-container-lowest rounded-xl border border-paper-shadow ... max-w-lg w-full ... max-h-[90vh] overflow-y-auto">
      {/* header with title + close button */}
      {/* body sections */}
      {/* footer: Batal + submit button with spinner */}
    </div>
  </div>
);
```
Per UI-SPEC, widen to `max-w-lg`, body uses `space-y-8` with 3 sections (Buku Terpilih / Informasi Peminjam / Ringkasan Peminjaman) instead of `BookFormModal`'s flat form fields.

**Submit handler with try/catch + error mapping** (lines 73-113):
```jsx
async function handleSubmit(e) {
  e.preventDefault();
  setLoading(true);
  setSubmitError('');
  try {
    const res = await api.post('/peminjaman/ajukan', { id_salinan_buku: salinan.id });
    onSubmitted(res.data);  // triggers Toast + refreshKey in parent
    onClose();
  } catch (err) {
    const detail = err.response?.data?.detail;
    // map LOAN-02 / LOAN-03 / generic per Copywriting Contract
    onError(detail);  // parent shows error Toast, modal stays open per D-03
  } finally {
    setLoading(false);
  }
}
```
Note: unlike `BookFormModal` (closes always), per UI-SPEC the modal **stays open on error** so the user can retry/cancel — only close on success.

**Submit button with spinner** (lines 224-233):
```jsx
<button type="submit" disabled={loading} className="px-5 py-2.5 rounded-full text-label-sm font-label-sm text-white bg-antique-gold hover:opacity-90 transition-opacity disabled:opacity-50 inline-flex items-center gap-2">
  {loading && <span className="material-symbols-outlined text-[16px] animate-spin">sync</span>}
  Ajukan Peminjaman
</button>
```

---

### `frontend/src/components/StatusBadge.jsx` (display/transform)

**Analog:** `frontend/src/components/AvailabilityBadge.jsx`

**Variant-map + compact-prop pattern** (full file, lines 1-37):
```jsx
const variants = {
  tersedia: { label: 'Tersedia', class: 'bg-sage-green/10 text-sage-green border-sage-green/20', icon: 'check_circle' },
  tidak_tersedia: { label: 'Tidak Tersedia', class: 'bg-alert-crimson/10 text-alert-crimson border-alert-crimson/20', icon: 'block' },
};

export default function AvailabilityBadge({ tersedia, compact = false }) {
  const v = tersedia ? variants.tersedia : variants.tidak_tersedia;
  return (
    <span className={`inline-flex items-center gap-1 border rounded-full font-label-sm ${v.class} ${compact ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-label-sm'}`}>
      <span className="material-symbols-outlined" style={{ fontSize: compact ? 14 : 16 }}>{v.icon}</span>
      {v.label}
    </span>
  );
}
```
Directly portable: replace the 2-key `variants` map with the 5-entry Status Badge Color Map from `03-UI-SPEC.md` (`menunggu_persetujuan`, `siap_diambil`, `dipinjam`, `ditolak`, `dibatalkan`), keep the `compact` prop and `inline-flex items-center gap-1 border rounded-full` shell unchanged. Props: `{ status, compact }`.

---

### `frontend/src/components/AntrianTable.jsx` (table, CRUD action rows)

**Analog:** `frontend/src/components/SalinanTable.jsx`

**Empty-state-inline + table shell pattern** (full file, lines 26-83):
```jsx
export default function SalinanTable({ salinan = [] }) {
  if (salinan.length === 0) {
    return <p className="text-body-md font-body-md text-outline-variant italic">Belum ada salinan buku ini.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-outline-variant/40">
            <th className="pb-3 text-label-sm font-label-sm text-outline uppercase tracking-wider">Rak</th>
            ...
          </tr>
        </thead>
        <tbody>
          {salinan.map((s) => (
            <tr key={s.id} className="border-b border-outline-variant/20 last:border-none">
              <td className="py-3 text-body-md font-body-md text-primary">{s.lokasi_rak}</td>
              ...
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```
For `AntrianTable`, per UI-SPEC use the more elaborate styling described in `03-UI-SPEC.md` (header `bg-surface`, striped rows `bg-surface-container-low` on even rows, `hover:bg-primary/5`), but keep `SalinanTable`'s overall shape: props `{ items, columns config, onAction, loading }`. Replace the inline "no items" string with `EmptyState` per D-06 spec (compact `py-12` variant inside a `<tbody><tr><td colSpan=...>`).
- For Section 1 ("Menunggu Persetujuan"): columns Mahasiswa / Buku / Tanggal Pengajuan / Aksi (Setujui+Tolak buttons → `ConfirmDialog`).
- For Section 2 ("Siap Diambil"): columns Mahasiswa / Buku / Batas Pengambilan / Aksi (Serahkan button → `ConfirmDialog`).
- Loading state: 3 skeleton rows, follow `KatalogPage.jsx`'s `SkeletonGrid` (lines 12-26) animate-pulse bar pattern adapted to `<tr><td>` cells.

---

### `frontend/src/components/BlockedBanner.jsx` (display)

**Analog:** `frontend/src/components/AvailabilityBadge.jsx` (chip/variant styling) + `frontend/src/components/EmptyState.jsx` (icon+heading+body block layout)

**Variant-driven chip styling** (from `AvailabilityBadge.jsx` lines 9-20, adapted to two banner variants):
```jsx
const variants = {
  limit: {
    heading: 'Batas Pinjaman Tercapai',
    body: 'Anda memiliki 5 pinjaman aktif, batas maksimum yang diizinkan. Selesaikan atau kembalikan salah satu pinjaman sebelum mengajukan yang baru.',
    class: 'bg-antique-gold/10 border-antique-gold/30 text-on-surface',
    icon: 'inventory_2',
  },
  blocked: {
    heading: 'Akun Diblokir',
    body: 'Akun Anda diblokir karena ada denda yang belum dibayar. Selesaikan pembayaran denda di perpustakaan untuk mengajukan pinjaman baru.',
    class: 'bg-alert-crimson/10 border-alert-crimson/30 text-alert-crimson',
    icon: 'block',
  },
};
```

**Heading+body block layout** (from `EmptyState.jsx` lines 19-24, adapted from centered-column to horizontal `flex items-start gap-3`):
```jsx
export default function BlockedBanner({ variant }) {
  const v = variants[variant];
  if (!v) return null;
  return (
    <div role="status" aria-live="polite" className={`rounded-lg border p-4 flex items-start gap-3 mb-6 ${v.class}`}>
      <span className="material-symbols-outlined" aria-hidden="true">{v.icon}</span>
      <div>
        <h3 className="text-label-md font-label-md">{v.heading}</h3>
        <p className="text-body-lg font-body-lg mt-1">{v.body}</p>
      </div>
    </div>
  );
}
```
Props: `{ variant: 'limit' | 'blocked' | null }` — render nothing if neither condition is true. Used on `/katalog/{id}` and `/pinjaman` (mahasiswa view) per D-04.

---

### `frontend/src/components/SalinanTable.jsx` (modify — add "Pinjam" action column)

**Analog:** itself (current implementation, lines 1-84)

Current table has 3 columns (Rak, Kondisi, Status) with no action column. Add:
- New props: `onPinjam(salinan)`, `peran`, `pinjamDisabled` (bool, from D-04 pre-check).
- Conditionally render a 4th `<th>Aksi</th>` and `<td>` only when `peran === 'mahasiswa'`.
- Per-row: if `s.status_ketersediaan === 'tersedia'`, render the "Pinjam" button (Sage Green, `bookmark_add` icon, `min-h-[44px]`, `aria-label="Pinjam salinan di {s.lokasi_rak}"`, `disabled={pinjamDisabled}` with `aria-disabled`); otherwise render `—` or empty cell.
- Follow the existing `statusColor`/`statusLabel` map pattern (lines 8-24) for any new label/icon lookups — same lookup-object idiom.
- Button styling reference — copy the "Pinjam Buku" button shell from `frontend/src/components/BookCard.jsx` if it has a button style already (check during implementation), otherwise use the same `inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-label-sm font-label-sm` pattern seen on `BukuDetailPage.jsx`'s "Edit" button (lines 132-141), swapped to `bg-sage-green text-on-primary hover:bg-sage-green/90`.

---

### `frontend/src/pages/BukuDetailPage.jsx` (modify — wire LoanRequestModal)

**Analog:** itself (current implementation, lines 1-217)

- Add state: `const [showLoanModal, setShowLoanModal] = useState(false);` and `const [selectedSalinan, setSelectedSalinan] = useState(null);`
- Pass new props to `<SalinanTable salinan={buku.salinan} peran={peran} pinjamDisabled={blocked || atLimit} onPinjam={(s) => { setSelectedSalinan(s); setShowLoanModal(true); }} />` (line 183).
- Add `<BlockedBanner variant={...} />` near the top of the page (after the back link, before the book header) when mahasiswa is blocked/at-limit — fetch the pre-check data (active-loan count + `is_diblokir`) the same way `categories` is fetched in the existing `useEffect` (lines 28-35), via a new `GET /api/peminjaman` call or a small dedicated pre-check endpoint (planner's discretion per D-04).
- On modal success: bump `refreshKey` (existing pattern, line 25/62) so `SalinanTable` re-fetches and the requested copy's status flips from `tersedia` to `dipesan`.
- Render `{showLoanModal && <LoanRequestModal buku={buku} salinan={selectedSalinan} onClose={...} onSubmitted={...} onError={...} />}` following the existing conditional-render pattern for `BookFormModal` (lines 202-213).
- Toast rendering: add `const [toast, setToast] = useState(null);` and `{toast && <Toast {...toast} onClose={() => setToast(null)} />}` at the page root — first usage of `Toast.jsx` in the app (currently unused, per CONTEXT.md).

---

### `frontend/src/router.jsx` (modify)

**Analog:** itself (current, lines 1-39)

```jsx
import PinjamanPage from './pages/PinjamanPage';
...
{ path: 'pinjaman', element: <ComingSoonPage title="Riwayat Peminjaman" /> },  // REMOVE
{ path: 'pinjaman', element: <PinjamanPage /> },  // ADD
```
Keep position within the `AppShell`-wrapped `ProtectedRoute` children array unchanged (line 29).

---

## Shared Patterns

### Role gating (backend)
**Source:** `backend/app/routers/buku.py` lines 139-145 (`_pustakawan_only`)
**Apply to:** `peminjaman.py` — `persetujuan` and `serahkan` endpoints (pustakawan-only); add an analogous `_mahasiswa_only` helper (raise 403 if `user.peran != PeranPengguna.mahasiswa`) for `ajukan`.

### Role detection (frontend)
**Source:** `frontend/src/pages/KatalogPage.jsx` lines 48-50
```jsx
const token = getToken();
const decoded = token ? decodeToken(token) : null;
const peran = decoded?.peran ?? 'mahasiswa';
```
**Apply to:** `PinjamanPage.jsx`, `BukuDetailPage.jsx` (already present), `SalinanTable.jsx` (passed as prop).

### refreshKey re-fetch pattern
**Source:** `frontend/src/pages/KatalogPage.jsx` lines 53-95, 121-123, 131-152
**Apply to:** `PinjamanPage.jsx` (after approve/reject/serahkan actions), `BukuDetailPage.jsx` (after loan request submission).

### Toast feedback (first real usage)
**Source:** `frontend/src/components/Toast.jsx` (full file, currently unused)
**Apply to:** `BukuDetailPage.jsx` (loan request result), `PinjamanPage.jsx` (approve/reject/serahkan results). Message copy comes from `03-UI-SPEC.md` Copywriting Contract.

### ConfirmDialog reuse
**Source:** `frontend/src/components/ConfirmDialog.jsx` (full file) — usage example at `frontend/src/pages/KatalogPage.jsx` lines 291-315
**Apply to:** `PinjamanPage.jsx` for Setujui/Tolak/Serahkan actions — `destructive=false` for Setujui/Serahkan, `destructive=true` for Tolak, per `03-UI-SPEC.md`.

### Error response shape (backend)
**Source:** `backend/app/routers/buku.py` — every `HTTPException(status_code=..., detail="...")` call (e.g. lines 104-107, 159-163, 273-276)
**Apply to:** All new `peminjaman.py` endpoints — 400 for LOAN-02/03 business rules, 404 for missing `peminjaman`/`salinan_buku`, 403 via role-gate helpers, 409 for race-condition "salinan sudah tidak tersedia".

### Frontend error mapping from API detail
**Source:** `frontend/src/components/BookFormModal.jsx` lines 91-113 (`catch (err) { const detail = err.response?.data?.detail; ... }`)
**Apply to:** `LoanRequestModal.jsx` (map 400 LOAN-02/LOAN-03/race-condition details to the specific Toast copy in `03-UI-SPEC.md`), `PinjamanPage.jsx` action handlers (generic "Gagal memproses tindakan" fallback).

## No Analog Found

None — all 9 new/modified files have a strong analog in Phase 1/2 code.

## Metadata

**Analog search scope:** `backend/app/routers/`, `backend/app/schemas/`, `backend/app/models/`, `backend/app/dependencies/`, `backend/tests/`, `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/router.jsx`
**Files scanned:** 17 (buku.py router/schema/model, peminjaman.py model, enums.py, auth.py dependency, pengguna.py model, main.py, test_buku.py, KatalogPage.jsx, BukuDetailPage.jsx, SalinanTable.jsx, ConfirmDialog.jsx, Toast.jsx, BookFormModal.jsx, AvailabilityBadge.jsx, EmptyState.jsx, router.jsx)
**Pattern extraction date:** 2026-06-13
