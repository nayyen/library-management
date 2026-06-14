"""Dashboard router — DASH-01 aggregation endpoint.

Provides a single GET /api/dashboard/stats endpoint that returns all
four stat-card values plus a read-only pending-approval preview.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.buku import Buku
from app.models.pengguna import Pengguna
from app.models.peminjaman import Peminjaman
from app.models.salinan_buku import SalinanBuku
from app.models.enums import (
    PeranPengguna,
    StatusPeminjaman,
    StatusSalinan,
)
from app.schemas.dashboard import DashboardStatsOut
from app.schemas.peminjaman import PeminjamanItemOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

PEMINJAMAN_AKTIF_STATUSES = [
    StatusPeminjaman.siap_diambil,
    StatusPeminjaman.dipinjam,
]

# ──────────────────────────────────────────────────────────────────────
# Helpers (duplicated per-router per codebase convention)
# ──────────────────────────────────────────────────────────────────────


def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )


def _is_terlambat(row: Peminjaman, now: datetime) -> bool:
    """True if a dipinjam loan is past its tanggal_tenggat.

    Handles offset-naive tenggat (SQLite) vs offset-aware now (PostgreSQL).
    """
    tenggat = row.tanggal_tenggat
    if tenggat is None:
        return False
    if tenggat.tzinfo is None and now.tzinfo is not None:
        tenggat = tenggat.replace(tzinfo=now.tzinfo)
    return row.status_peminjaman == StatusPeminjaman.dipinjam and tenggat < now


def _sweep_expired_pickups(db: Session) -> None:
    """Lazy check-on-read: auto-cancel siap_diambil rows past the 2x24h window.

    Called at the start of the dashboard stats endpoint.  No scheduled worker.
    Mirrors the same function in peminjaman.py (per-router duplication convention).
    Uses cutoff comparison (tanggal_siap_ambil < cutoff) rather than
    (tanggal_siap_ambil + 2days < now) for SQLite compatibility.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=2)
    expired = (
        db.query(Peminjaman)
        .options(joinedload(Peminjaman.salinan_buku))
        .filter(
            Peminjaman.status_peminjaman == StatusPeminjaman.siap_diambil,
            Peminjaman.tanggal_siap_ambil < cutoff,
        )
        .all()
    )
    for row in expired:
        row.status_peminjaman = StatusPeminjaman.dibatalkan
        row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia
    if expired:
        db.commit()


def _build_item_out(row: Peminjaman) -> PeminjamanItemOut:
    """Build a PeminjamanItemOut from a joined peminjaman row."""
    now = datetime.now(timezone.utc)
    return PeminjamanItemOut(
        id=str(row.id),
        status_peminjaman=row.status_peminjaman.value,
        judul=row.salinan_buku.buku.judul,
        penulis=row.salinan_buku.buku.penulis,
        lokasi_rak=row.salinan_buku.lokasi_rak,
        nama_mahasiswa=row.pengguna.nama,
        tanggal_pengajuan=row.tanggal_pengajuan,
        tanggal_siap_ambil=row.tanggal_siap_ambil,
        tanggal_tenggat=row.tanggal_tenggat,
        tanggal_kembali=row.tanggal_kembali,
        total_denda=row.total_denda,
        is_terlambat=_is_terlambat(row, now),
    )


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.get("/stats", response_model=DashboardStatsOut)
def dashboard_stats(
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> DashboardStatsOut:
    """Aggregated dashboard stats for the pustakawan landing page (DASH-01).

    Returns four stat-card values plus a read-only preview of pending
    loan-approval requests. Gated to pustakawan — mahasiswa receive 403.
    """
    # Role gate
    _pustakawan_only(user)

    # Sweep expired pickups before counting (lazy-sweep precedent from /peminjaman)
    _sweep_expired_pickups(db)

    now = datetime.now(timezone.utc)

    # ── Total Buku ──
    total_buku = db.query(func.count(Buku.id)).scalar() or 0

    # ── Peminjaman Aktif + Menunggu Persetujuan Count ──
    peminjaman_aktif = (
        db.query(func.count(Peminjaman.id))
        .filter(Peminjaman.status_peminjaman.in_(PEMINJAMAN_AKTIF_STATUSES))
        .scalar()
        or 0
    )
    menunggu_persetujuan_count = (
        db.query(func.count(Peminjaman.id))
        .filter(Peminjaman.status_peminjaman == StatusPeminjaman.menunggu_persetujuan)
        .scalar()
        or 0
    )

    # ── Buku Terlambat (Python-side _is_terlambat check) ──
    dipinjam_rows = (
        db.query(Peminjaman)
        .options(joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku))
        .filter(Peminjaman.status_peminjaman == StatusPeminjaman.dipinjam)
        .all()
    )
    buku_terlambat = sum(1 for r in dipinjam_rows if _is_terlambat(r, now))

    # ── Total Denda Belum Lunas + Jumlah Mahasiswa ──
    blocked_users = (
        db.query(Pengguna)
        .filter(Pengguna.is_diblokir == True)
        .all()
    )
    total_denda_belum_lunas = 0
    jumlah_mahasiswa_denda = 0
    for u in blocked_users:
        total = (
            db.query(func.sum(Peminjaman.total_denda))
            .filter(
                Peminjaman.id_pengguna == u.id,
                Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
            )
            .scalar()
            or 0
        )
        if total > 0:
            total_denda_belum_lunas += total
            jumlah_mahasiswa_denda += 1

    # ── Pending-approval preview (max 5, newest first) ──
    base_query = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
    )
    menunggu_rows = (
        base_query
        .filter(Peminjaman.status_peminjaman == StatusPeminjaman.menunggu_persetujuan)
        .order_by(Peminjaman.tanggal_pengajuan.desc())
        .limit(5)
        .all()
    )
    pengajuan_preview = [_build_item_out(r) for r in menunggu_rows]

    return DashboardStatsOut(
        total_buku=total_buku,
        peminjaman_aktif=peminjaman_aktif,
        menunggu_persetujuan_count=menunggu_persetujuan_count,
        buku_terlambat=buku_terlambat,
        total_denda_belum_lunas=total_denda_belum_lunas,
        jumlah_mahasiswa_denda=jumlah_mahasiswa_denda,
        pengajuan_preview=pengajuan_preview,
    )
