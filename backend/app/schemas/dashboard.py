"""Pydantic schemas for dashboard stats endpoint.

A single DashboardStatsOut response powers the 4-stat-card + pending-approval
preview on the pustakawan /dashboard page (DASH-01).
"""

from pydantic import BaseModel

from app.schemas.peminjaman import PeminjamanItemOut


class DashboardStatsOut(BaseModel):
    """Aggregated dashboard stats for the pustakawan landing page.

    All fields are ints/lists — no nested model_config needed since
    the response is hand-assembled via keyword args, not from_attributes.
    """

    total_buku: int
    peminjaman_aktif: int
    menunggu_persetujuan_count: int
    buku_terlambat: int
    total_denda_belum_lunas: int
    jumlah_mahasiswa_denda: int
    pengajuan_preview: list[PeminjamanItemOut]
