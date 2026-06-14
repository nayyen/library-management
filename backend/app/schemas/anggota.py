"""Pydantic schemas for anggota (member roster) endpoint.

A single AnggotaListOut response powers the pustakawan /anggota page
member-card grid (DASH-02).
"""

from pydantic import BaseModel


class AnggotaOut(BaseModel):
    """A single mahasiswa member with active-loan count and optional denda."""

    id_pengguna: str
    nama: str
    email: str
    is_diblokir: bool
    pinjaman_aktif: int
    total_denda: int

    model_config = {"from_attributes": True}


class AnggotaListOut(BaseModel):
    """List of mahasiswa members with total count."""

    items: list[AnggotaOut]
    total: int
