"""Pydantic schemas for peminjaman (loan) endpoints.

Mahasiswa "Pinjaman Saya" response carries a top-level `is_diblokir` field
reflecting the caller's own block flag (LOAN-03 / D-04), so the frontend
banner renders from real data rather than a client-side guess.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PeminjamanAjukan(BaseModel):
    """Request body for POST /api/peminjaman/ajukan."""

    id_salinan_buku: str = Field(..., description="UUID of the physical copy to borrow")


class PeminjamanItemOut(BaseModel):
    """A single peminjaman row, used by both role branches."""

    id: str
    status_peminjaman: str
    judul: str
    penulis: str
    lokasi_rak: str
    nama_mahasiswa: str
    tanggal_pengajuan: datetime | None = None
    tanggal_siap_ambil: datetime | None = None
    tanggal_tenggat: datetime | None = None
    tanggal_kembali: datetime | None = None
    total_denda: int = 0
    is_terlambat: bool = False

    model_config = {"from_attributes": True}


class AnggotaDiblokirOut(BaseModel):
    """A single blocked member summary, used in the pustakawan aggregate list."""

    id_pengguna: str
    nama: str
    email: str
    total_denda: int

    model_config = {"from_attributes": True}


class PeminjamanResponse(BaseModel):
    """Unified GET /api/peminjaman response.

    Mahasiswa branch populates ``items`` / ``total`` / ``is_diblokir``.
    Pustakawan branch populates ``menunggu_persetujuan`` / ``siap_diambil`` /
    ``sedang_dipinjam`` / ``anggota_diblokir``.
    """

    items: list[PeminjamanItemOut] | None = None
    total: int | None = None
    is_diblokir: bool | None = None
    denda_tertunggak: int | None = None
    menunggu_persetujuan: list[PeminjamanItemOut] | None = None
    siap_diambil: list[PeminjamanItemOut] | None = None
    sedang_dipinjam: list[PeminjamanItemOut] | None = None
    anggota_diblokir: list[AnggotaDiblokirOut] | None = None


class PersetujuanBody(BaseModel):
    """Request body for PUT /api/peminjaman/{id}/persetujuan."""

    aksi: Literal["setujui", "tolak"] = Field(
        ...,
        description='Either "setujui" (approve) or "tolak" (reject)',
    )
