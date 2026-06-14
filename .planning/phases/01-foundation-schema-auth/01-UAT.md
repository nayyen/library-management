---
status: complete
phase: 01-foundation-schema-auth
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
  - 01-03-SUMMARY.md
  - 01-04-SUMMARY.md
started: 2026-06-12T14:00:00+07:00
updated: 2026-06-13T12:00:00+07:00
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start — docker compose up
expected: Running `docker compose up --build` from the project root starts all 3 containers (db, backend, frontend). The entrypoint runs `alembic upgrade head` then `python -m app.seed`. Login page loads at http://localhost:5173 with Biblio brand styling.
result: pass

### 2. Register as Mahasiswa
expected: Navigating to http://localhost:5173/register shows a form with Nama, Email, and Kata Sandi fields (no role picker). Submitting creates a mahasiswa account, returns a JWT, and redirects to the welcome page showing "Selamat datang, {nama}" with a "mahasiswa" role badge.
result: pass

### 3. Login as Seeded Pustakawan
expected: Navigating to http://localhost:5173/login shows Email + Kata Sandi fields (no "Masuk Sebagai" role radio). Logging in with `pustakawan@biblio.ac.id` / `admin1234` returns a JWT and redirects to the welcome page showing "Selamat datang, Admin Perpustakaan" with a "pustakawan" role badge.
result: pass

### 4. Role-Aware Navigation
expected: After logging in as mahasiswa, the nav header shows only Katalog and Pinjaman links. After logging in as pustakawan, the nav header shows Katalog, Pinjaman, Dashboard, and Anggota links. The active route's nav item is visually highlighted.
result: pass

### 5. Protected Routes — Unauthenticated Redirect
expected: Opening http://localhost:5173/katalog (or any protected route) in a private/incognito window (no token) redirects to /login. The page behind the shell is not rendered.
result: pass

### 6. Session Expiry — 401 Handling
expected: If the stored JWT is expired or invalid (simulated by clearing/editing localStorage), the next API call triggers a 401 response. The axios interceptor catches it, clears the token, and redirects to /login?session_expired=1 showing a "Sesi berakhir" banner.
result: pass

### 7. Registration Validation — Min Password Length
expected: Submitting the register form with a password shorter than 8 characters shows an inline validation error (either frontend or API 422 response). The form is not submitted successfully.
result: pass

### 8. Logout Flow
expected: Clicking the "Keluar" button on the welcome page clears the stored JWT and redirects to /login. Navigating back to a protected route after logout shows the login page (not the protected content).
result: pass

### 9. API — GET /api/autentikasi/saya
expected: Calling GET /api/autentikasi/saya with a valid Bearer token returns the current user's profile (id, nama, email, peran). Calling without a token returns 401 Unauthorized.
result: pass

### 10. Duplicate Registration Rejection
expected: Attempting to register again with the same email returns a 400/409 error with an appropriate message (e.g., "Email sudah terdaftar"). No duplicate account is created.
result: pass

### 11. Responsive Layout at 375px
expected: Opening the login page at 375px viewport width shows all form elements without horizontal overflow, truncation, or layout breakage. The card is centered and properly padded.
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

<!-- YAML format for plan-phase --gaps consumption -->
