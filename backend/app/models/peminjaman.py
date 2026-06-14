import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.enums import StatusPeminjaman


class Peminjaman(Base):
    __tablename__ = "peminjaman"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    id_pengguna: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pengguna.id"), nullable=False
    )
    id_salinan_buku: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("salinan_buku.id"), nullable=False
    )

    # Relationships for eager-loading
    pengguna: Mapped["Pengguna"] = relationship(
        "Pengguna", back_populates="peminjaman", lazy="joined"
    )
    salinan_buku: Mapped["SalinanBuku"] = relationship(
        "SalinanBuku", back_populates="peminjaman", lazy="joined"
    )
    tanggal_pengajuan: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    tanggal_siap_ambil: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tanggal_pinjam: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tanggal_tenggat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tanggal_kembali: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status_peminjaman: Mapped[StatusPeminjaman] = mapped_column(
        SAEnum(StatusPeminjaman, name="status_peminjaman", create_type=False),
        nullable=False,
        default=StatusPeminjaman.menunggu_persetujuan,
    )
    total_denda: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
