# Biblio — Sistem Manajemen Perpustakaan

A full-stack library management system built with FastAPI (Python), React, and PostgreSQL.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with WSL2 integration enabled (Windows)
- Or Docker Compose on Linux/macOS

## Quick Start

1. **Clone the repository**

```bash
git clone <repo-url>
cd library-management-system
```

2. **Create environment file**

```bash
cp .env.example .env
```

Generate a secure JWT secret:

```bash
openssl rand -hex 32
```

Edit `.env` and replace `JWT_SECRET` with the generated value.

3. **Start the stack**

```bash
docker compose up
```

This starts three services:
- **db** — PostgreSQL 16 (port 5432)
- **backend** — FastAPI with auto-reload (port 8000)
- **frontend** — Vite dev server with HMR (port 5173)

The backend automatically:
- Runs database migrations (`alembic upgrade head`)
- Seeds a default pustakawan account
- Starts uvicorn with hot-reload

4. **Open the app**

Visit [http://localhost:5173](http://localhost:5173)

## Seeded Account

| Role | Email | Password |
|------|-------|----------|
| Pustakawan | `pustakawan@biblio.ac.id` | `admin1234` |

## Usage

1. **Register a new member** — open `/register`, fill in name, email, and password (min. 8 characters)
2. **Login as pustakawan** — use the seeded credentials above
3. **Explore the shell** — navigate via the header menu (features in active development)

## Project Structure

```
.
├── backend/              # FastAPI application
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── dependencies/ # FastAPI dependencies
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/             # React + Vite application
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── layouts/      # Page layouts
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # React hooks
│   │   └── lib/          # Utilities (auth, api)
│   └── Dockerfile
├── docs/                 # Documentation & design assets
├── docker-compose.yml
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/autentikasi/registrasi` | Register a new member |
| POST | `/api/autentikasi/masuk` | Login, returns JWT token |
| GET | `/api/autentikasi/saya` | Get current user info |
| GET | `/api/health` | Health check |

## Development

### Backend-only (without Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### Frontend-only (without Docker)

```bash
cd frontend
npm install
npm run dev
```

> Note: The Vite dev server proxies `/api` requests to `http://backend:8000`. When running without Docker, update the proxy target in `vite.config.js` to `http://localhost:8000`.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, PyJWT, pwdlib(bcrypt)
- **Frontend:** React 18, Vite, react-router v7, Tailwind CSS v3, axios
- **Infrastructure:** Docker Compose, Postgres 16 Alpine
