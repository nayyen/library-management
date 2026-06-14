# Plan 01-02: Auth API — Summary

**Status:** ✅ Complete
**Date:** 2026-06-12

## What Was Built

- `backend/app/core/security.py` — bcrypt hashing (pwdlib BcryptHasher) + PyJWT encode/decode with timezone-aware exp
- `backend/app/schemas/auth.py` — Pydantic schemas (RegistrasiRequest with min_length=8, MasukRequest, TokenResponse, UserOut)
- `backend/app/dependencies/auth.py` — `get_current_user` JWT dependency (raises 401 on missing/invalid/expired token)
- `backend/app/routers/autentikasi.py` — 3 endpoints (registrasi, masuk, saya)
- `backend/app/main.py` — wired with `include_router(autentikasi.router)`
- `backend/app/seed.py` — updated to use `security.hash_password` directly

### API Endpoints

| Method | Path | Auth | Behavior |
|--------|------|------|----------|
| POST | `/api/autentikasi/registrasi` | None | Register mahasiswa (auto-login JWT) |
| POST | `/api/autentikasi/masuk` | None | Login returns 1-hour JWT |
| GET | `/api/autentikasi/saya` | Bearer | Returns current user profile |

## Verification

| Criterion | Status |
|-----------|--------|
| Security smoke test | ✅ `ok` |
| `BcryptHasher` used | ✅ |
| `timezone.utc` used (no naive datetime) | ✅ |
| `min_length=8` in RegistrasiRequest | ✅ |
| RegistrasiRequest has NO `peran` field | ✅ |
| No CORS middleware in main.py | ✅ |
| **All 4 AUTH tests GREEN** | ✅ 4 passed |

## Next

→ Plan 01-03 (Wave 3): Frontend skeleton — Vite/React/Tailwind + auth UI + shell
