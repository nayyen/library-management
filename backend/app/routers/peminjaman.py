"""Peminjaman (loan) router — LOAN-01 through LOAN-06, RET-01 through RET-04.

Endpoints:
- POST /api/peminjaman/ajukan    — Mahasiswa requests a loan
- GET  /api/peminjaman            — Shared list (role-conditional content)
- PUT  /api/peminjaman/{id}/persetujuan — Pustakawan approve/reject
- PUT  /api/peminjaman/{id}/serahkan    — Pustakawan handover
- PUT  /api/peminjaman/{id}/kembalikan  — Pustakawan process return
"""

import logging
import uuid
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
from app.schemas.peminjaman import (
    AnggotaDiblokirOut,
    PeminjamanAjukan,
    PeminjamanItemOut,
    PeminjamanResponse,
    PersetujuanBody,
)

router = APIRouter(prefix="/api/peminjaman", tags=["peminjaman"])

# Module-level logger for Brevo notification stub (RET-03)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

ACTIVE_STATUSES = [
    StatusPeminjaman.menunggu_persetujuan,
    StatusPeminjaman.siap_diambil,
    StatusPeminjaman.dipinjam,
]

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────


def _pustakawan_only(user: Pengguna) -> None:
    """Raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )


def _mahasiswa_only(user: Pengguna) -> None:
    """Raise 403 if user is not a mahasiswa."""
    if user.peran != PeranPengguna.mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )


def _active_loan_count(db: Session, id_pengguna: uuid.UUID) -> int:
    """Count the user's current active loans."""
    return (
        db.query(Peminjaman)
        .filter(
            Peminjaman.id_pengguna == id_pengguna,
            Peminjaman.status_peminjaman.in_(ACTIVE_STATUSES),
        )
        .count()
    )


def _is_terlambat(row: Peminjaman, now: datetime) -> bool:
    """True if a dipinjam loan is past its tanggal_tenggat (D-02/D-08).

    Handles offset-naive tenggat (SQLite) vs offset-aware now (PostgreSQL).
    """
    tenggat = row.tanggal_tenggat
    if tenggat is None:
        return False
    if tenggat.tzinfo is None and now.tzinfo is not None:
        tenggat = tenggat.replace(tzinfo=now.tzinfo)
    return row.status_peminjaman == StatusPeminjaman.dipinjam and tenggat < now


def _build_item_out(row: Peminjaman) -> PeminjamanItemOut:
    """Build a PeminjamanItemOut from a joined peminjaman row.

    Expects the row to have eager-loaded relations:
    ``salinan_buku`` → ``buku`` and ``pengguna``.
    """
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


def _sweep_expired_pickups(db: Session) -> None:
    """Lazy check-on-read: auto-cancel siap_diambil rows past the 2x24h window.

    Called at the start of every GET /api/peminjaman.  No scheduled worker.
    """
    now = datetime.now(timezone.utc)
    expired = (
        db.query(Peminjaman)
        .options(joinedload(Peminjaman.salinan_buku))
        .filter(
            Peminjaman.status_peminjaman == StatusPeminjaman.siap_diambil,
            Peminjaman.tanggal_siap_ambil + timedelta(days=2) < now,
        )
        .all()
    )
    for row in expired:
        row.status_peminjaman = StatusPeminjaman.dibatalkan
        row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia
    if expired:
        db.commit()


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.post("/ajukan", response_model=PeminjamanItemOut, status_code=201)
def ajukan_peminjaman(
    body: PeminjamanAjukan,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanItemOut:
    """Mahasiswa requests to borrow an available copy (LOAN-01).

    Enforces the 5-active-loan limit (LOAN-02) and the blocked-account
    check (LOAN-03) server-side.
    """
    _mahasiswa_only(user)

    # LOAN-03: blocked check
    if user.is_diblokir:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Akun Anda diblokir karena denda belum lunas.",
        )

    # LOAN-02: active loan limit
    if _active_loan_count(db, user.id) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anda sudah memiliki 5 pinjaman aktif.",
        )

    # Resolve salinan
    salinan_id = uuid.UUID(body.id_salinan_buku)
    salinan = (
        db.query(SalinanBuku)
        .filter(SalinanBuku.id == salinan_id)
        .first()
    )
    if not salinan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salinan buku tidak ditemukan.",
        )

    if salinan.status_ketersediaan != StatusSalinan.tersedia:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Salinan ini sudah tidak tersedia.",
        )

    now = datetime.now(timezone.utc)
    peminjaman = Peminjaman(
        id_pengguna=user.id,
        id_salinan_buku=salinan.id,
        tanggal_pengajuan=now,
        status_peminjaman=StatusPeminjaman.menunggu_persetujuan,
    )
    salinan.status_ketersediaan = StatusSalinan.dipesan

    db.add(peminjaman)
    db.commit()
    db.refresh(peminjaman)

    # Reload with relationships for the response
    row = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
        .filter(Peminjaman.id == peminjaman.id)
        .first()
    )
    return _build_item_out(row)


@router.get("", response_model=PeminjamanResponse)
def daftar_peminjaman(
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanResponse:
    """Shared GET /api/peminjaman list.

    - Mahasiswa branch: returns ``items`` (all caller's rows, most-recent-first)
      + ``is_diblokir`` (the caller's own block flag for the LOAN-03 banner).
    - Pustakawan branch: returns ``menunggu_persetujuan`` and ``siap_diambil``
      stacked sections (D-06).

    The lazy pickup-window sweep (LOAN-05 / D-12) runs before either branch.
    """
    # Sweep expired pickups first (D-12)
    _sweep_expired_pickups(db)

    base_query = db.query(Peminjaman).options(
        joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
        joinedload(Peminjaman.pengguna),
    )

    if user.peran == PeranPengguna.pustakawan:
        menunggu = [
            _build_item_out(r)
            for r in base_query.filter(
                Peminjaman.status_peminjaman == StatusPeminjaman.menunggu_persetujuan,
            )
            .order_by(Peminjaman.tanggal_pengajuan.desc())
            .all()
        ]
        siap_diambil = [
            _build_item_out(r)
            for r in base_query.filter(
                Peminjaman.status_peminjaman == StatusPeminjaman.siap_diambil,
            )
            .order_by(Peminjaman.tanggal_siap_ambil.desc())
            .all()
        ]
        sedang_dipinjam = [
            _build_item_out(r)
            for r in base_query.filter(
                Peminjaman.status_peminjaman == StatusPeminjaman.dipinjam,
            )
            .order_by(Peminjaman.tanggal_tenggat.asc())
            .all()
        ]

        # RET-04 / D-06: anggota_diblokir aggregate list
        blocked_users = (
            db.query(Pengguna)
            .filter(Pengguna.is_diblokir == True)
            .all()
        )
        anggota_diblokir = []
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
            anggota_diblokir.append(
                AnggotaDiblokirOut(
                    id_pengguna=str(u.id),
                    nama=u.nama,
                    email=u.email,
                    total_denda=total,
                )
            )

        return PeminjamanResponse(
            menunggu_persetujuan=menunggu,
            siap_diambil=siap_diambil,
            sedang_dipinjam=sedang_dipinjam,
            anggota_diblokir=anggota_diblokir,
        )

    # Mahasiswa branch: own loans only + is_diblokir flag + denda_tertunggak
    items = [
        _build_item_out(r)
        for r in base_query.filter(
            Peminjaman.id_pengguna == user.id,
        )
        .order_by(Peminjaman.tanggal_pengajuan.desc())
        .all()
    ]
    denda_tertunggak = (
        db.query(func.sum(Peminjaman.total_denda))
        .filter(
            Peminjaman.id_pengguna == user.id,
            Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
        )
        .scalar()
        or 0
    )
    return PeminjamanResponse(
        items=items,
        total=len(items),
        is_diblokir=user.is_diblokir,  # LOAN-03 banner data source (D-04)
        denda_tertunggak=denda_tertunggak,
    )


@router.put("/{id_peminjaman}/persetujuan", response_model=PeminjamanItemOut)
def proses_persetujuan(
    id_peminjaman: uuid.UUID,
    body: PersetujuanBody,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanItemOut:
    """Pustakawan approves (→ siap_diambil) or rejects (→ ditolak) a pending request.

    LOAN-04: on reject the linked salinan is reset to tersedia.
    """
    _pustakawan_only(user)

    row = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
        .filter(Peminjaman.id == id_peminjaman)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengajuan peminjaman tidak ditemukan.",
        )

    if row.status_peminjaman != StatusPeminjaman.menunggu_persetujuan:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pengajuan tidak dalam status menunggu persetujuan.",
        )

    now = datetime.now(timezone.utc)
    if body.aksi == "setujui":
        row.status_peminjaman = StatusPeminjaman.siap_diambil
        row.tanggal_siap_ambil = now
        # salinan stays dipesan until handover
    else:  # tolak
        row.status_peminjaman = StatusPeminjaman.ditolak
        row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia

    db.commit()
    db.refresh(row)
    return _build_item_out(row)


@router.put("/{id_peminjaman}/serahkan", response_model=PeminjamanItemOut)
def serahkan_peminjaman(
    id_peminjaman: uuid.UUID,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanItemOut:
    """Pustakawan marks a siap_diambil loan as handed over (LOAN-06).

    Transitions to dipinjam, sets tanggal_tenggat = now + 14 days,
    and flips the salinan to dipinjam.
    """
    _pustakawan_only(user)

    row = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
        .filter(Peminjaman.id == id_peminjaman)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengajuan peminjaman tidak ditemukan.",
        )

    if row.status_peminjaman != StatusPeminjaman.siap_diambil:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pinjaman tidak dalam status siap diambil.",
        )

    now = datetime.now(timezone.utc)
    row.status_peminjaman = StatusPeminjaman.dipinjam
    row.tanggal_pinjam = now
    row.tanggal_tenggat = now + timedelta(days=14)
    row.salinan_buku.status_ketersediaan = StatusSalinan.dipinjam

    db.commit()
    db.refresh(row)
    return _build_item_out(row)


@router.put("/{id_peminjaman}/kembalikan", response_model=PeminjamanItemOut)
def kembalikan_peminjaman(
    id_peminjaman: uuid.UUID,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> PeminjamanItemOut:
    """Pustakawan processes a return for a dipinjam loan (RET-01).

    On late returns: calculates total_denda (Rp 1.000/day), sets
    pengguna.is_diblokir = True, and logs a stubbed Brevo notification (RET-02/03).
    The salinan is reset to tersedia regardless of timeliness.
    """
    _pustakawan_only(user)

    row = (
        db.query(Peminjaman)
        .options(
            joinedload(Peminjaman.salinan_buku).joinedload(SalinanBuku.buku),
            joinedload(Peminjaman.pengguna),
        )
        .filter(Peminjaman.id == id_peminjaman)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengajuan peminjaman tidak ditemukan.",
        )

    if row.status_peminjaman != StatusPeminjaman.dipinjam:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pinjaman tidak dalam status dipinjam.",
        )

    now = datetime.now(timezone.utc)
    row.tanggal_kembali = now
    row.status_peminjaman = StatusPeminjaman.dikembalikan
    row.salinan_buku.status_ketersediaan = StatusSalinan.tersedia

    # RET-02: Fine calculation
    days_late = max(
        0,
        (row.tanggal_kembali.date() - row.tanggal_tenggat.date()).days,
    )
    if days_late > 0:
        row.total_denda = days_late * 1000
        row.pengguna.is_diblokir = True
        # RET-03: Brevo notification stub
        logger.info(
            "BREVO_NOTIFICATION id_peminjaman=%s email=%s total_denda=%s status=Sent",
            str(row.id),
            row.pengguna.email,
            row.total_denda,
        )

    db.commit()
    db.refresh(row)
    return _build_item_out(row)


@router.put("/anggota/{id_pengguna}/lunasi_denda", response_model=AnggotaDiblokirOut)
def lunasi_denda(
    id_pengguna: uuid.UUID,
    db: Session = Depends(get_db),
    user: Pengguna = Depends(get_current_user),
) -> AnggotaDiblokirOut:
    """Pustakawan clears a member's block after fine is paid (RET-04).

    Sets is_diblokir = False on the member's account.  Does NOT touch any
    ``total_denda`` rows (historical record preserved per D-05).
    """
    _pustakawan_only(user)

    member = (
        db.query(Pengguna)
        .filter(Pengguna.id == id_pengguna)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anggota tidak ditemukan.",
        )

    member.is_diblokir = False
    db.commit()
    db.refresh(member)

    # Recompute the summed denda for the response
    total = (
        db.query(func.sum(Peminjaman.total_denda))
        .filter(
            Peminjaman.id_pengguna == member.id,
            Peminjaman.status_peminjaman == StatusPeminjaman.dikembalikan,
        )
        .scalar()
        or 0
    )

    return AnggotaDiblokirOut(
        id_pengguna=str(member.id),
        nama=member.nama,
        email=member.email,
        total_denda=total,
    )
