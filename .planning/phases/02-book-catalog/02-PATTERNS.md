# Phase 2: Book Catalog - Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 19
**Analogs found:** 15 / 19

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|----------------|
| `backend/app/schemas/buku.py` | model (schema) | CRUD | `backend/app/schemas/auth.py` | exact |
| `backend/app/routers/buku.py` | controller (router) | CRUD + request-response | `backend/app/routers/autentikasi.py` | exact |
| `backend/app/main.py` | config | request-response | `backend/app/main.py` (modify) | exact (self) |
| `backend/app/seed.py` | utility (seed/batch) | batch | `backend/app/seed.py` (modify) | exact (self) |
| `backend/tests/test_buku.py` | test | request-response | `backend/tests/test_auth.py` | exact |
| `frontend/src/router.jsx` | route | request-response | `frontend/src/router.jsx` (modify) | exact (self) |
| `frontend/src/pages/KatalogPage.jsx` | component (page) | request-response | `frontend/src/pages/LoginPage.jsx` | role-match |
| `frontend/src/pages/BukuDetailPage.jsx` | component (page) | request-response | `frontend/src/pages/LoginPage.jsx` | role-match |
| `frontend/src/components/BookCard.jsx` | component | transform | `frontend/src/components/RoleBadge.jsx` | role-match |
| `frontend/src/components/AvailabilityBadge.jsx` | component | transform | `frontend/src/components/RoleBadge.jsx` | exact |
| `frontend/src/components/BookCoverPlaceholder.jsx` | component | transform | `frontend/src/components/RoleBadge.jsx` | role-match |
| `frontend/src/components/SearchBar.jsx` | component | request-response | `frontend/src/components/InputField.jsx` | role-match |
| `frontend/src/components/BookFormModal.jsx` | component (modal/form) | CRUD | `frontend/src/pages/LoginPage.jsx` (form) + `frontend/src/components/InputField.jsx` | role-match |
| `frontend/src/components/CategoryFilterSidebar.jsx` | component | transform | none | no analog |
| `frontend/src/components/KelolaTable.jsx` | component (table) | CRUD | none | no analog |
| `frontend/src/components/SalinanTable.jsx` | component (table) | CRUD | none | no analog |
| `frontend/src/components/TambahSalinanForm.jsx` | component (form) | CRUD | `frontend/src/pages/LoginPage.jsx` (form pattern) | role-match |
| `frontend/src/components/EmptyState.jsx` | component | transform | `frontend/src/pages/ComingSoonPage.jsx` | exact |
| `frontend/src/components/Toast.jsx` | component | event-driven | none | no analog |

## Pattern Assignments

### `backend/app/schemas/buku.py` (model/schema, CRUD)

**Analog:** `backend/app/schemas/auth.py` (full file, 29 lines)

**Imports pattern** (lines 1-3):
```python
"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field
```
For `buku.py`, use `from pydantic import BaseModel, Field, field_validator` and `import uuid` for UUID typing, plus `from typing import Optional` if needed for partial updates.

**Request/Response model pattern** (lines 6-28):
```python
class RegistrasiRequest(BaseModel):
    nama: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    kata_sandi: str = Field(..., min_length=8)
...
class UserOut(BaseModel):
    id: str
    nama: str
    email: str
    peran: str

    model_config = {"from_attributes": True}
```
Mirror this for `BukuCreate`/`BukuUpdate`/`BukuOut`, `SalinanBukuCreate`/`SalinanBukuOut`, and a `BukuListOut` (paginated/result wrapper) with `model_config = {"from_attributes": True}` for ORM-backed response models. Apply field-level validation (`Field(..., min_length=..., max_length=...)`) for `judul`/`penulis`/`isbn`/`kategori`, and a `field_validator` for ISBN 10/13-digit format and `tahun_terbit` range (1900-current year) per the UI-SPEC validation copy.

---

### `backend/app/routers/buku.py` (controller, CRUD + request-response)

**Analog:** `backend/app/routers/autentikasi.py` (full file, 104 lines)

**Imports pattern** (lines 1-17):
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.pengguna import Pengguna
from app.schemas.auth import (...)
```
For `buku.py`, swap in `from app.models.buku import Buku`, `from app.models.salinan_buku import SalinanBuku`, `from app.models.enums import KondisiBuku, StatusSalinan`, and the new `app.schemas.buku` imports. Add `from sqlalchemy import func, or_` for search/filter and distinct-category queries.

**Router declaration pattern** (line 19):
```python
router = APIRouter(prefix="/api/autentikasi", tags=["autentikasi"])
```
New router: `router = APIRouter(prefix="/api/buku", tags=["buku"])`.

**Auth/role-gating pattern** (line 95-96, `saya` endpoint):
```python
@router.get("/saya", response_model=UserOut)
def saya(user: Pengguna = Depends(get_current_user)) -> UserOut:
```
For pustakawan-only mutation endpoints (`POST /api/buku`, `PUT /api/buku/{id}`, `DELETE /api/buku/{id}`, `POST /api/buku/{id}/salinan`), depend on `get_current_user` and then check `if user.peran != PeranPengguna.pustakawan: raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Akses ditolak.")` — no existing 403 example in the codebase, so this check must be written fresh inline at the top of each pustakawan-only handler body, following the same `HTTPException(status_code=..., detail="...")` shape as the 401/409 examples below.

**CRUD + IntegrityError pattern** (lines 22-65, registrasi):
```python
@router.post("/registrasi", response_model=TokenResponse, status_code=201)
def registrasi(body: RegistrasiRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = (
        db.query(Pengguna)
        .filter(Pengguna.email == body.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )

    pengguna = Pengguna(...)
    db.add(pengguna)
    try:
        db.commit()
        db.refresh(pengguna)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )
```
Mirror this exactly for `POST /api/buku` (duplicate ISBN -> 409 "ISBN ini sudah terdaftar pada buku lain.") and for `PUT /api/buku/{id}` (lookup-or-404, then update fields, commit/refresh with IntegrityError->409 for ISBN conflicts).

**404-lookup pattern (new, to be written, modeled on the 409 shape above):**
```python
buku = db.query(Buku).filter(Buku.id == id_buku).first()
if not buku:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buku tidak ditemukan.")
```

**FK-safe delete pattern (new — per CONTEXT.md's documented contract):**
```python
@router.delete("/{id_buku}", status_code=204)
def hapus_buku(id_buku: uuid.UUID, db: Session = Depends(get_db), user: Pengguna = Depends(get_current_user)):
    # role check ...
    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Buku tidak ditemukan.")
    jumlah_salinan = db.query(SalinanBuku).filter(SalinanBuku.id_buku == id_buku).count()
    if jumlah_salinan > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Buku masih memiliki {jumlah_salinan} salinan fisik.",
        )
    db.delete(buku)
    db.commit()
```

**List/search/filter endpoint (new — GET /api/buku with kata_kunci + kategori):**
```python
@router.get("", response_model=BukuListOut)
def daftar_buku(
    kata_kunci: str | None = None,
    kategori: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
) -> BukuListOut:
    query = db.query(Buku)
    if kata_kunci:
        like = f"%{kata_kunci}%"
        query = query.filter(
            or_(Buku.judul.ilike(like), Buku.penulis.ilike(like), Buku.isbn.ilike(like))
        )
    if kategori:
        query = query.filter(Buku.kategori.in_(kategori))
    buku_list = query.all()
    # for each buku, compute availability rollup via SalinanBuku query
    ...
```

**Distinct categories endpoint (new — GET /api/buku/kategori):**
```python
@router.get("/kategori", response_model=list[str])
def daftar_kategori(db: Session = Depends(get_db)) -> list[str]:
    rows = db.query(Buku.kategori).distinct().order_by(Buku.kategori).all()
    return [r[0] for r in rows]
```
Note: register this route BEFORE `/{id_buku}` in the router so "kategori" isn't matched as a UUID path param.

---

### `backend/app/main.py` (config, modify)

**Analog:** self (full file, 15 lines)

**Current pattern:**
```python
from app.routers import autentikasi

app = FastAPI(title="Biblio - Sistem Manajemen Perpustakaan")

app.include_router(autentikasi.router)
```
**Change:** add `from app.routers import buku` and `app.include_router(buku.router)` alongside the existing line.

---

### `backend/app/seed.py` (utility/batch, modify)

**Analog:** self (full file, 53 lines)

**Idempotent seed pattern** (lines 19-48):
```python
def run() -> None:
    db = SessionLocal()
    try:
        existing = (
            db.query(Pengguna)
            .filter(Pengguna.email == PUSTAKAWAN_EMAIL)
            .first()
        )
        if existing:
            print(f"Seed: pustakawan {PUSTAKAWAN_EMAIL} already exists, skipping.")
            return
        pustakawan = Pengguna(...)
        db.add(pustakawan)
        db.commit()
        print(f"Seed: created pustakawan {PUSTAKAWAN_EMAIL}.")
    except Exception as exc:
        db.rollback()
        print(f"Seed error: {exc}")
        raise
    finally:
        db.close()
```
**Change:** add a second idempotent block (or a separate `seed_buku()` function called from `run()`) that checks `db.query(Buku).count()` — if zero, inserts ~10-12 `Buku` rows (titles/authors from D-11: Gadis Kretek, Sapiens, Cantik Itu Luka, KBBI, etc., across Fiksi/Non-Fiksi/Referensi) plus `SalinanBuku` rows per D-12's mixed-status distribution (some `tersedia`, one book fully `dipinjam`/`dipesan`, one book with mixed statuses across copies). Follow the same try/except/rollback/finally structure and idempotency check (skip if already seeded) as the pustakawan block.

---

### `backend/tests/test_buku.py` (test, request-response)

**Analog:** `backend/tests/test_auth.py` (lines 1-60 read; pattern is representative of full file)

**Test structure pattern:**
```python
def test_register(client: TestClient) -> None:
    """AUTH-01: User can register as mahasiswa with email + password."""
    response = client.post(
        "/api/autentikasi/registrasi",
        json={...},
    )
    assert response.status_code in (200, 201), (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "access_token" in data, f"Response missing access_token: {data}"
```
Mirror for catalog tests: `test_list_buku`, `test_search_buku`, `test_filter_kategori`, `test_create_buku_pustakawan`, `test_create_buku_forbidden_for_mahasiswa` (expect 403), `test_delete_buku_with_salinan_blocked` (expect 409), `test_add_salinan`. Use the `client` fixture from `backend/tests/conftest.py` (SQLite in-memory, `setup_database` autouse fixture creates all tables including `buku`/`salinan_buku` automatically via `Base.metadata`). For pustakawan-gated endpoints, first register/login a mahasiswa AND seed/create a pustakawan user directly via `db_session` fixture + `Pengguna(..., peran=PeranPengguna.pustakawan)`, then call `/api/autentikasi/masuk` to get a token, and pass `headers={"Authorization": f"Bearer {token}"}`.

---

### `frontend/src/router.jsx` (route, modify)

**Analog:** self (full file, 36 lines)

**Current pattern** (lines 18-32):
```javascript
{
  element: <ProtectedRoute />,
  children: [
    {
      element: <AppShell />,
      children: [
        { index: true, element: <WelcomePage /> },
        { path: 'katalog', element: <ComingSoonPage title="Katalog Buku" /> },
        ...
      ],
    },
  ],
},
```
**Change:** import `KatalogPage` and `BukuDetailPage`; replace the `katalog` line with `{ path: 'katalog', element: <KatalogPage /> }` and add `{ path: 'katalog/:id', element: <BukuDetailPage /> }` immediately after it, inside the same `AppShell` children array.

---

### `frontend/src/pages/KatalogPage.jsx` and `BukuDetailPage.jsx` (page components, request-response)

**Analog:** `frontend/src/pages/LoginPage.jsx` (full file, 98 lines) for state/effect/API-call conventions; `frontend/src/pages/ComingSoonPage.jsx` for empty/placeholder layout shell.

**State + API call pattern** (LoginPage.jsx lines 1-34):
```javascript
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import api from '../lib/api';
import { setToken } from '../lib/auth';
import InputField from '../components/InputField';

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', kata_sandi: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/autentikasi/masuk', form);
      ...
    } catch (err) {
      const msg = err.response?.data?.detail || 'Email atau kata sandi salah.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }
  ...
}
```
For `KatalogPage.jsx`, replace the submit-driven flow with a `useEffect`-driven fetch: `useState` for `buku list`, `loading`, `error`, `searchTerm`, `selectedKategori`, `tab` (Jelajah/Kelola for pustakawan). Debounce `searchTerm` (300ms) before calling `api.get('/buku', { params: { kata_kunci, kategori } })`. Use `decodeToken(getToken()).peran` (see AppShell.jsx pattern, lines 18-21) to gate the Kelola tab and CRUD UI.

For `BukuDetailPage.jsx`, use `useParams()` from `react-router` to get `:id`, fetch `GET /api/buku/{id}` in a `useEffect`, and render the header block + `SalinanTable` + (pustakawan-only) `TambahSalinanForm`.

**Error message extraction pattern** (LoginPage.jsx line 28-29):
```javascript
const msg = err.response?.data?.detail || 'Email atau kata sandi salah.';
```
Reuse this `err.response?.data?.detail || '<fallback Indonesian message>'` idiom for all catalog API error handling (matches FastAPI's `HTTPException(detail=...)` shape from the router).

---

### `frontend/src/components/AvailabilityBadge.jsx`, `BookCard.jsx`, `BookCoverPlaceholder.jsx` (presentational components, transform)

**Analog:** `frontend/src/components/RoleBadge.jsx` (full file, 16 lines)

**Conditional-class chip pattern** (full file):
```javascript
export default function RoleBadge({ peran }) {
  const isPustakawan = peran === 'pustakawan';

  return (
    <span
      className={`inline-block px-3 py-1 rounded text-label-sm font-label-sm ${
        isPustakawan
          ? 'bg-primary-container text-on-primary-container'
          : 'bg-secondary-container text-on-secondary-container'
      }`}
    >
      {peran}
    </span>
  );
}
```
This is the exact shape to mirror for `AvailabilityBadge.jsx`:
```javascript
export default function AvailabilityBadge({ tersedia }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-label-sm font-label-sm border ${
        tersedia
          ? 'bg-sage-green/10 text-sage-green border-paper-shadow'
          : 'bg-surface-container text-on-surface-variant border-outline-variant'
      }`}
    >
      {tersedia ? 'Tersedia' : 'Tidak Tersedia'}
    </span>
  );
}
```
For `BookCoverPlaceholder.jsx`, take a `kategori` and `tersedia` prop, derive the category-color mapping from the 02-UI-SPEC.md table (Fiksi -> ink-blue, Non-Fiksi -> antique-gold, Referensi -> secondary-fixed, fallback -> sage-green; override to secondary-fixed when `!tersedia`), and render a `div` with `aspect-[2/3]` + `bg-{color}/10` + centered `material-symbols-outlined` `menu_book` icon (`text-5xl` for cards, `text-7xl` for detail per D-15), following the same single-purpose presentational-component shape as `RoleBadge`.

For `BookCard.jsx`, compose `BookCoverPlaceholder` + `AvailabilityBadge` inside the `<article>` structure specified in 02-UI-SPEC.md's "Book grid" section (lines 192-195) — wrap the title in `<Link to={`/katalog/${id}`}>` per the `Link` import convention used in `LoginPage.jsx` (`import { Link } from 'react-router'`, line 2) and `ComingSoonPage.jsx` (line 1).

---

### `frontend/src/components/SearchBar.jsx` (component, request-response)

**Analog:** `frontend/src/components/InputField.jsx` (full file, 43 lines)

**Icon + input pattern** (lines 16-36):
```javascript
<div className="relative">
  {icon && (
    <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-[20px]">
      {icon}
    </span>
  )}
  <input
    type={type}
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    className={`w-full bg-transparent border-b-2 py-3 text-body-md font-body-md text-primary placeholder:text-outline-variant focus:outline-none transition-colors ${
      icon ? 'pl-10' : 'pl-0'
    } ${...}`}
    {...props}
  />
</div>
```
`SearchBar.jsx` follows the same icon-prefixed input shape but with the UI-SPEC's pill styling (`rounded-full bg-surface-container-low border border-paper-shadow focus:border-antique-gold focus:ring-1 focus:ring-antique-gold`) instead of `InputField`'s underline style — a deliberate visual divergence per 02-UI-SPEC.md lines 187, but the icon-positioning technique (`absolute left-3 top-1/2 -translate-y-1/2`) and controlled-input (`value`/`onChange`) convention should be copied directly. Internally, debounce the `onChange` value with `useEffect` + `setTimeout(300ms)` before calling the parent's `onSearch` callback (no existing debounce pattern in the codebase — implement using standard `useState` + `useEffect` cleanup).

---

### `frontend/src/components/BookFormModal.jsx` (modal/form, CRUD)

**Analog:** `frontend/src/pages/LoginPage.jsx` (form/state/submit pattern, lines 11-34, 51-83) + `frontend/src/components/InputField.jsx` (field component, reused as-is)

**Form state + validation + submit pattern** (LoginPage.jsx lines 11-34):
```javascript
const [form, setForm] = useState({ email: '', kata_sandi: '' });
const [error, setError] = useState('');
const [loading, setLoading] = useState(false);

function handleChange(e) {
  setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
}

async function handleSubmit(e) {
  e.preventDefault();
  setError('');
  setLoading(true);
  try {
    const res = await api.post('/autentikasi/masuk', form);
    ...
  } catch (err) {
    const msg = err.response?.data?.detail || 'Email atau kata sandi salah.';
    setError(msg);
  } finally {
    setLoading(false);
  }
}
```
**Field rendering pattern** (LoginPage.jsx lines 52-71):
```javascript
<InputField
  label="Email"
  type="email"
  name="email"
  placeholder="contoh@email.com"
  icon="mail"
  value={form.email}
  onChange={handleChange}
  required
/>
```
For `BookFormModal.jsx`: reuse `form`/`setForm`/`handleChange`/`loading`/`error` state exactly as above, but track per-field validation errors as an object (`fieldErrors: { judul: '...', isbn: '...' }`) since `InputField` accepts a per-field `error` prop (InputField.jsx lines 6, 37-39). On submit, call `api.post('/buku', form)` (add mode) or `api.put(`/buku/${id}`, form)` (edit mode) — branch on a `mode` prop. Wrap fields in `<InputField label="Judul" name="judul" icon="title" value={form.judul} onChange={handleChange} error={fieldErrors.judul} required />` etc., per the UI-SPEC field list (lines 218-222). The submit button reuses the `disabled={loading}` + ternary-label pattern from LoginPage.jsx line 78-83 (`{loading ? 'Memproses…' : 'Masuk'}` -> `{loading ? <spinner/> : 'Simpan Buku'}`).

The modal shell itself (overlay, `role="dialog"`, focus management, `Escape` to close) has no existing analog — implement fresh per 02-UI-SPEC.md lines 213-226 using standard React patterns (`useEffect` for `Escape` keydown listener and focus-on-open).

---

### `frontend/src/components/TambahSalinanForm.jsx` (form, CRUD)

**Analog:** `frontend/src/pages/LoginPage.jsx` (same form/state/submit pattern as above, lines 11-34)

Same `form`/`handleChange`/`handleSubmit`/`loading`/`error` shape, posting to `api.post(`/buku/${id_buku}/salinan`, form)`. Fields are `lokasi_rak` (text `InputField`), `kondisi` and `status_ketersediaan` (native `<select>` elements styled to match `InputField`'s `border-b-2` underline treatment — no existing `<select>` component in the codebase, so style manually using `InputField`'s className conventions, lines 27-33). On success, reset `form` to defaults (`{ lokasi_rak: '', kondisi: 'bagus', status_ketersediaan: 'tersedia' }`) and call a parent-provided `onAdded(newSalinan)` callback to append the row to `SalinanTable`.

---

### `frontend/src/components/EmptyState.jsx` (component, transform)

**Analog:** `frontend/src/pages/ComingSoonPage.jsx` (full file, 29 lines)

**Centered icon + heading + body pattern** (lines 5-17):
```javascript
<div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
  <span className="material-symbols-outlined text-7xl text-outline-variant mb-6">
    construction
  </span>

  <h1 className="text-headline-lg font-headline-lg text-primary mb-3">
    {title}
  </h1>

  <p className="text-body-md font-body-md text-outline mt-2 max-w-md">
    Fitur ini sedang dalam tahap pengembangan dan akan segera tersedia.
    Pantau terus informasi terbaru dari kami.
  </p>
</div>
```
`EmptyState.jsx` mirrors this exact icon+heading+body composition as a reusable component taking `icon`, `heading`, `body`, and optional `action` (button/link slot) props — per 02-UI-SPEC.md's empty/error state specs (lines 197-198, 209-210), using `min-h-[40vh]` (not `60vh`) and `text-headline-md font-headline-md` (not `headline-lg`, per the Phase 2 4-size scale) for the heading. The optional action slot covers the "Coba Lagi" retry button and the repeated "Tambah Buku" button in the Kelola empty state.

---

## Shared Patterns

### Error message extraction (frontend)
**Source:** `frontend/src/pages/LoginPage.jsx` line 28-29
```javascript
const msg = err.response?.data?.detail || 'Email atau kata sandi salah.';
```
**Apply to:** All catalog API calls (`KatalogPage`, `BukuDetailPage`, `BookFormModal`, `TambahSalinanForm`) — replace the fallback string with the relevant Indonesian copy from 02-UI-SPEC.md's Copywriting Contract.

### Axios instance with auth header
**Source:** `frontend/src/lib/api.js` (full file)
```javascript
const api = axios.create({ baseURL: '/api' });
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```
**Apply to:** All frontend API calls — `api.get('/buku', ...)`, `api.post('/buku', ...)`, `api.put('/buku/{id}', ...)`, `api.delete('/buku/{id}')`, `api.post('/buku/{id}/salinan', ...)`, `api.get('/buku/kategori')`. The 401 interceptor (lines 21-29) already handles session expiry globally — no extra handling needed in catalog components.

### Role detection from JWT
**Source:** `frontend/src/layouts/AppShell.jsx` lines 18-21, using `frontend/src/lib/auth.js` `decodeToken`
```javascript
const token = getToken();
const decoded = token ? decodeToken(token) : null;
const peran = decoded?.peran ?? 'mahasiswa';
```
**Apply to:** `KatalogPage.jsx` (gate Kelola tab + "Tambah Buku"), `BukuDetailPage.jsx` (gate Edit button + Tambah Salinan form), `BookCard.jsx`/`KelolaTable.jsx` (gate edit/delete actions).

### FastAPI router + Depends(get_db) + Depends(get_current_user)
**Source:** `backend/app/routers/autentikasi.py` lines 1-22, 95-96
```python
from app.core.database import get_db
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/buku", tags=["buku"])

@router.get("/saya", response_model=UserOut)
def saya(user: Pengguna = Depends(get_current_user)) -> UserOut:
    ...
```
**Apply to:** All endpoints in `backend/app/routers/buku.py`. Public endpoints (`GET /api/buku`, `GET /api/buku/{id}`, `GET /api/buku/kategori`) still require `Depends(get_current_user)` since the whole API is behind auth (no anonymous catalog browsing per Phase 1's auth wall) — confirm against `ProtectedRoute.jsx`/Phase 1 conventions if an endpoint needs to be public.

### IntegrityError -> 409 Conflict
**Source:** `backend/app/routers/autentikasi.py` lines 47-56
```python
db.add(pengguna)
try:
    db.commit()
    db.refresh(pengguna)
except IntegrityError:
    db.rollback()
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email sudah terdaftar.")
```
**Apply to:** `POST /api/buku` and `PUT /api/buku/{id}` for duplicate-ISBN conflicts (`detail="ISBN ini sudah terdaftar pada buku lain."`).

### Pydantic schema with `from_attributes` for ORM responses
**Source:** `backend/app/schemas/auth.py` lines 22-28
```python
class UserOut(BaseModel):
    id: str
    nama: str
    email: str
    peran: str

    model_config = {"from_attributes": True}
```
**Apply to:** `BukuOut`, `SalinanBukuOut`, and any other response models returning SQLAlchemy ORM instances directly.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/src/components/CategoryFilterSidebar.jsx` | component | transform | No filter/checkbox-list component exists yet; build per 02-UI-SPEC.md lines 188 (checkbox list, mutually-exclusive "Semua Kategori" logic) using plain `<input type="checkbox">`/`<label>` and controlled state — no existing analog beyond generic form-state patterns already covered above. |
| `frontend/src/components/KelolaTable.jsx` | component (table) | CRUD | No table component exists in the codebase yet (Phase 1 has no admin tables). Build fresh per 02-UI-SPEC.md lines 204-210 (striped rows, `bg-primary/[0.03]` even rows, `th`/`td` per DESIGN.md table spec) and 02-CONTEXT.md D-01. Reuse `AvailabilityBadge` and role-detection shared pattern for the Aksi column. |
| `frontend/src/components/SalinanTable.jsx` | component (table) | CRUD | Same as `KelolaTable.jsx` — no existing table analog; build per 02-UI-SPEC.md lines 236-239 with the same striped-table styling, reusing `KelolaTable`'s styling once built (consider extracting a shared `<Table>`/`<TableRow>` primitive if duplication becomes significant, though not required for Phase 2 scope). |
| `frontend/src/components/Toast.jsx` | component | event-driven | No toast/snackbar/notification component exists. Build fresh per 02-UI-SPEC.md's "coming soon" toast spec (lines 123, 257) — `role="status" aria-live="polite"`, `bg-primary text-on-primary rounded-DEFAULT`, auto-dismiss via `setTimeout` (~3s), positioned bottom-center/bottom-right. A simple local-state (`useState` for visibility + message) + `setTimeout` implementation in `KatalogPage.jsx` is sufficient — no global toast context needed for Phase 2's single use case. |

## Metadata

**Analog search scope:** `backend/app/routers/`, `backend/app/schemas/`, `backend/app/models/`, `backend/app/dependencies/`, `backend/tests/`, `backend/app/main.py`, `backend/app/seed.py`, `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/layouts/`, `frontend/src/lib/`, `frontend/src/router.jsx`
**Files scanned:** 16 (read in full or targeted ranges)
**Pattern extraction date:** 2026-06-13
