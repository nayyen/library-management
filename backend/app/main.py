"""FastAPI application entry point."""

import logging
from fastapi import FastAPI

from app.routers import autentikasi, buku, peminjaman, dashboard, anggota

app = FastAPI(title="Biblio - Sistem Manajemen Perpustakaan")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

app.include_router(autentikasi.router)
app.include_router(buku.router)
app.include_router(peminjaman.router)
app.include_router(dashboard.router)
app.include_router(anggota.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
