# Plan 01-01: Backend Skeleton — Summary

**Status:** ✅ Complete
**Date:** 2026-06-12

## What Was Built

### Backend Package Structure
- `backend/app/core/config.py` — pydantic-settings `Settings` (DB, JWT config)
- `backend/app/core/database.py` — SQLAlchemy engine, session, `get_db` dependency, `Base`
- `backend/app/models/enums.py` — 4 Python ENUM classes (PeranPengguna, KondisiBuku, StatusSalinan, StatusPeminjaman)
- `backend/app/models/pengguna.py` — Pengguna ORM model (UUID PK, bcrypt hash column, email index)
- `backend/app/models/buku.py` — Buku ORM model (ISBN unique index)
- `backend/app/models/salinan_buku.py` — SalinanBuku ORM model (FK to buku)
- `backend/app/models/peminjaman.py` — Peminjaman ORM model (FKs to pengguna + salinan_buku, all timestamp columns)
- `backend/app/seed.py` — Idempotent pustakawan seed (pustakawan@biblio.ac.id)
- `backend/app/main.py` — Minimal FastAPI app skeleton (health endpoint)
- `backend/requirements.txt` + `backend/requirements-dev.txt` — All dependencies installed and verified

### Database Migration
- `backend/alembic/versions/0001_initial_schema.py` — Hand-written migration creating all 4 ENUM types + 4 tables with FKs

### Test Scaffold (RED)
- `backend/pytest.ini` — pytest config
- `backend/tests/conftest.py` — TestClient + SQLite test DB fixtures
- `backend/tests/test_auth.py` — 4 failing tests for AUTH-01..04 (RED — intended)

## Verification

| Criterion | Status |
|-----------|--------|
| Models import cleanly | ✅ `mahasiswa` printed |
| `create_type=False` in all model files | ✅ 4 occurrences |
| Migration has all 4 table names | ✅ |
| Migration has all 4 ENUM names | ✅ |
| `.env.example` has `changeme` placeholder | ✅ |
| No raw SQL f-strings in `app/` | ✅ |
| 4 tests collected without collection error | ✅ |
| 4 tests fail (RED) with 404 | ✅ |

## Next

→ Plan 01-02 (Wave 2): Auth API — bcrypt, JWT, registrasi/masuk/saya endpoints
