"""Anggota (member roster) router — DASH-02 roster endpoint.

Provides GET /api/anggota returning all mahasiswa with active-loan counts
and, for blocked members, outstanding denda totals.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.pengguna import Pengguna
from app.models.peminjaman import Peminjaman
from app.models.enums import (
    PeranPengguna,
    StatusPeminjaman,
)
from app.schemas.anggota import AnggotaListOut, AnggotaOut

router = APIRouter(prefix="/api/anggota", tags=["anggota"])

# ──────────────────────────────────────────────────────────────────────
# Helper (duplicated per-router per codebase convention)
# ──────────────────────────────────────────────────────────────────────


def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.get("", response_model=AnggotaListOut)
def daftar_anggota(
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> AnggotaListOut:
    """Full mahasiswa roster with active-loan counts and denda (DASH-02).

    Returns all mahasiswa ordered by nama. Blocked members include their
    outstanding denda total; non-blocked members report total_denda=0.
    Gated to pustakawan — mahasiswa receive 403.
    """
    _pustakawan_only(user)

    members = (
        db.query(Pengguna)
        .filter(Pengguna.peran == PeranPengguna.mahasiswa)
        .order_by(Pengguna.nama.asc())
        .all()
    )

    items: list[AnggotaOut] = []
    for m in members:
        pinjaman_aktif = (
            db.query(func.count(Peminjaman.id))
            .filter(
                Peminjaman.id_pengguna == m.id,
                Peminjaman.status_peminjaman.in_(
                    [StatusPeminjaman.siap_diambil, StatusPeminjaman.dipinjam]
                ),
            )
            .scalar()
            or 0
        )

        total_denda = 0
        if m.is_diblokir:
            total_denda = (
                db.query(func.sum(Peminjaman.total_denda))
                .filter(
                    Peminjaman.id_pengguna == m.id,
                    Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
                )
                .scalar()
                or 0
            )

        items.append(
            AnggotaOut(
                id_pengguna=str(m.id),
                nama=m.nama,
                email=m.email,
                is_diblokir=m.is_diblokir,
                pinjaman_aktif=pinjaman_aktif,
                total_denda=total_denda,
            )
        )

    return AnggotaListOut(items=items, total=len(items))
