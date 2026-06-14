# Plan 01-03: Frontend Skeleton — Summary

**Status:** ✅ Complete
**Date:** 2026-06-12

## What Was Built

### Frontend Scaffold
- `frontend/package.json` — Vite + React + react-router v7 + axios + Tailwind v3
- `frontend/vite.config.js` — host: true, proxy `/api` → `http://backend:8000`
- `frontend/tailwind.config.js` — Biblio theme tokens (antique-gold, ink-blue, paper-shadow, sage-green, etc.)
- `frontend/postcss.config.js` — Tailwind + autoprefixer
- `frontend/index.html` — Google Fonts (Inter 400/600, Playfair Display 600/700), Material Symbols
- `frontend/src/index.css` — Tailwind directives
- `frontend/src/main.jsx` — React root with RouterProvider

### Auth Infrastructure
- `frontend/src/lib/auth.js` — localStorage token management (getToken, setToken, clearToken, decodeToken)
- `frontend/src/lib/api.js` — Axios instance (`/api` baseURL) with Bearer request interceptor + 401 response interceptor (redirects to `/login?session_expired=1`)
- `frontend/src/hooks/useAuth.js` — `useAuth` hook exposing { user, isAuthenticated, logout }
- `frontend/src/components/ProtectedRoute.jsx` — Redirects to `/login` if no token
- `frontend/src/router.jsx` — createBrowserRouter with public routes (/login, /register) and protected shell routes (/, /katalog, /pinjaman, /dashboard, /anggota)

### Auth UI Pages
- `frontend/src/components/InputField.jsx` — Bottom-border input with Material Symbols icon, error state, focus:border-antique-gold
- `frontend/src/components/RoleBadge.jsx` — Role-aware badge (mahasiswa: secondary-container, pustakawan: primary-container)
- `frontend/src/layouts/AuthLayout.jsx` — Centered max-w-md card, brand logo, spine accent, footer
- `frontend/src/layouts/AppShell.jsx` — Header with role-aware nav (mahasiswa: Katalog+Pinjaman; pustakawan: +Dashboard+Anggota), active indicator
- `frontend/src/pages/LoginPage.jsx` — Email + Kata Sandi (no role radio), session-expired banner, error handling, cross-link to register
- `frontend/src/pages/RegisterPage.jsx` — Nama + Email + Kata Sandi (min 8), auto-login on success, cross-link to login
- `frontend/src/pages/WelcomePage.jsx` — "Selamat datang, {nama}" with RoleBadge, Keluar logout button
- `frontend/src/pages/ComingSoonPage.jsx` — "Segera Hadir" placeholder with back link

## Verification

| Criterion | Status |
|-----------|--------|
| Tailwind v3 installed (not v4) | ✅ `^3.4.19` |
| Biblio theme tokens (antique-gold, ink-blue, paper-shadow, margin-mobile) | ✅ |
| Vite proxy target `http://backend:8000` (not localhost) | ✅ |
| `server.host: true` configured | ✅ |
| Font links in index.html (Inter, Playfair Display, Material Symbols) | ✅ |
| LoginPage has NO "Masuk Sebagai" role radio (D-01) | ✅ |
| WelcomePage has "Selamat datang" + RoleBadge | ✅ |
| ComingSoonPage has "Segera Hadir" | ✅ |
| AppShell has role-aware nav items | ✅ |
| ProtectedRoute redirects without token | ✅ |
| api.js has both request + 401 response interceptors | ✅ |
| axios baseURL is `/api` (relative) | ✅ |
| `react-router` imports (not `react-router-dom`) | ✅ |
| `npm run build` succeeds | ✅ |

## Next

→ Plan 01-04 (Wave 4): docker-compose orchestration + manual smoke
