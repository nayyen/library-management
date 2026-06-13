"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import autentikasi, buku, peminjaman

app = FastAPI(title="Biblio - Sistem Manajemen Perpustakaan")

app.include_router(autentikasi.router)
app.include_router(buku.router)
app.include_router(peminjaman.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
