"""Book catalog router — read + write endpoints (CAT-01 through CAT-04)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.buku import Buku
from app.models.salinan_buku import SalinanBuku
from app.models.enums import PeranPengguna, KondisiBuku, StatusSalinan
from app.schemas.buku import (
    BukuCreate,
    BukuUpdate,
    BukuOut,
    BukuListItem,
    BukuListOut,
    BukuDetailOut,
    SalinanBukuCreate,
    SalinanBukuOut,
)

router = APIRouter(prefix="/api/buku", tags=["buku"])


@router.get("", response_model=BukuListOut)
def daftar_buku(
    kata_kunci: str | None = None,
    kategori: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> BukuListOut:
    """List all books with optional search and category filter.

    - kata_kunci: case-insensitive search across judul, penulis, isbn
    - kategori: multi-select OR filter (repeat param: ?kategori=A&kategori=B)
    """
    query = db.query(Buku)

    if kata_kunci:
        like = f"%{kata_kunci}%"
        query = query.filter(
            or_(
                Buku.judul.ilike(like),
                Buku.penulis.ilike(like),
                Buku.isbn.ilike(like),
            )
        )

    if kategori:
        query = query.filter(Buku.kategori.in_(kategori))

    buku_list = query.all()

    # Build list items with derived availability
    items = []
    for buku in buku_list:
        tersedia = (
            db.query(SalinanBuku)
            .filter(
                SalinanBuku.id_buku == buku.id,
                SalinanBuku.status_ketersediaan == StatusSalinan.tersedia,
            )
            .count()
            > 0
        )
        items.append(
            BukuListItem(
                id=str(buku.id),
                judul=buku.judul,
                penulis=buku.penulis,
                isbn=buku.isbn,
                kategori=buku.kategori,
                tahun_terbit=buku.tahun_terbit,
                tersedia=tersedia,
            )
        )

    return BukuListOut(items=items, total=len(items))


@router.get("/kategori", response_model=list[str])
def daftar_kategori(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[str]:
    """Return distinct kategori values sorted alphabetically."""
    rows = db.query(Buku.kategori).distinct().order_by(Buku.kategori).all()
    return [r[0] for r in rows]


@router.get("/{id_buku}", response_model=BukuDetailOut)
def detail_buku(
    id_buku: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> BukuDetailOut:
    """Return a single book with its full salinan_buku list."""
    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buku tidak ditemukan.",
        )

    salinan_list = (
        db.query(SalinanBuku)
        .filter(SalinanBuku.id_buku == id_buku)
        .all()
    )

    tersedia = any(
        s.status_ketersediaan == StatusSalinan.tersedia for s in salinan_list
    )

    return BukuDetailOut(
        id=str(buku.id),
        judul=buku.judul,
        penulis=buku.penulis,
        isbn=buku.isbn,
        kategori=buku.kategori,
        tahun_terbit=buku.tahun_terbit,
        tersedia=tersedia,
        salinan=[
            SalinanBukuOut(
                id=str(s.id),
                lokasi_rak=s.lokasi_rak,
                kondisi=s.kondisi.value,
                status_ketersediaan=s.status_ketersediaan.value,
            )
            for s in salinan_list
        ],
    )


def _pustakawan_only(user) -> None:
    """Helper: raise 403 if user is not a pustakawan."""
    if user.peran != PeranPengguna.pustakawan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak.",
        )


@router.post("", response_model=BukuOut, status_code=201)
def tambah_buku(
    body: BukuCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> BukuOut:
    """Create a new master buku record (pustakawan only)."""
    _pustakawan_only(user)

    # Pre-check duplicate ISBN
    existing = db.query(Buku).filter(Buku.isbn == body.isbn).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ISBN ini sudah terdaftar pada buku lain.",
        )

    buku = Buku(
        judul=body.judul,
        penulis=body.penulis,
        isbn=body.isbn,
        kategori=body.kategori,
        tahun_terbit=body.tahun_terbit,
    )
    db.add(buku)
    try:
        db.commit()
        db.refresh(buku)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ISBN ini sudah terdaftar pada buku lain.",
        )

    return BukuOut(
        id=str(buku.id),
        judul=buku.judul,
        penulis=buku.penulis,
        isbn=buku.isbn,
        kategori=buku.kategori,
        tahun_terbit=buku.tahun_terbit,
    )


@router.put("/{id_buku}", response_model=BukuOut)
def ubah_buku(
    id_buku: uuid.UUID,
    body: BukuUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> BukuOut:
    """Update a master buku record (pustakawan only)."""
    _pustakawan_only(user)

    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buku tidak ditemukan.",
        )

    # Update only provided fields
    update_data = body.model_dump(exclude_unset=True)
    if "isbn" in update_data:
        # Check duplicate ISBN if changing ISBN
        existing = (
            db.query(Buku)
            .filter(Buku.isbn == body.isbn, Buku.id != id_buku)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ISBN ini sudah terdaftar pada buku lain.",
            )

    for field, value in update_data.items():
        setattr(buku, field, value)

    try:
        db.commit()
        db.refresh(buku)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ISBN ini sudah terdaftar pada buku lain.",
        )

    return BukuOut(
        id=str(buku.id),
        judul=buku.judul,
        penulis=buku.penulis,
        isbn=buku.isbn,
        kategori=buku.kategori,
        tahun_terbit=buku.tahun_terbit,
    )


@router.delete("/{id_buku}", status_code=204)
def hapus_buku(
    id_buku: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> None:
    """Delete a master buku record (pustakawan only, FK-safe).

    Blocks deletion if the book has physical copies (409).
    """
    _pustakawan_only(user)

    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buku tidak ditemukan.",
        )

    jumlah_salinan = (
        db.query(SalinanBuku)
        .filter(SalinanBuku.id_buku == id_buku)
        .count()
    )
    if jumlah_salinan > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Buku masih memiliki {jumlah_salinan} salinan fisik.",
        )

    db.delete(buku)
    db.commit()


@router.post("/{id_buku}/salinan", response_model=SalinanBukuOut, status_code=201)
def tambah_salinan(
    id_buku: uuid.UUID,
    body: SalinanBukuCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> SalinanBukuOut:
    """Add a physical salinan_buku copy (pustakawan only, add-only per D-04)."""
    _pustakawan_only(user)

    buku = db.query(Buku).filter(Buku.id == id_buku).first()
    if not buku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buku tidak ditemukan.",
        )

    salinan = SalinanBuku(
        id_buku=buku.id,
        lokasi_rak=body.lokasi_rak,
        kondisi=KondisiBuku(body.kondisi),
        status_ketersediaan=StatusSalinan(body.status_ketersediaan),
    )
    db.add(salinan)
    db.commit()
    db.refresh(salinan)

    return SalinanBukuOut(
        id=str(salinan.id),
        lokasi_rak=salinan.lokasi_rak,
        kondisi=salinan.kondisi.value,
        status_ketersediaan=salinan.status_ketersediaan.value,
    )
