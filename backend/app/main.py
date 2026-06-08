"""FastAPI application entrypoint.

CORS is configured with an EXPLICIT origin allowlist — never combine
`allow_origins=["*"]` with `allow_credentials=True` (RESEARCH Pitfall 2 /
threat T-01-CORS). `localhost` is used consistently across Vite, CORS, and
cookies to avoid the `localhost` vs `127.0.0.1` mismatch (RESEARCH Pitfall 1).
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.db import get_db

app = FastAPI(title="Library Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Liveness + DB-connectivity check: executes a trivial `SELECT 1`."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
