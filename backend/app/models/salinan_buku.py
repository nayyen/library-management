import uuid
from sqlalchemy import String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.enums import KondisiBuku, StatusSalinan


class SalinanBuku(Base):
    __tablename__ = "salinan_buku"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    id_buku: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buku.id"), nullable=False
    )
    lokasi_rak: Mapped[str] = mapped_column(String(50), nullable=False)
    kondisi: Mapped[KondisiBuku] = mapped_column(
        SAEnum(KondisiBuku, name="kondisi_buku", create_type=False),
        nullable=False,
        default=KondisiBuku.bagus,
    )
    status_ketersediaan: Mapped[StatusSalinan] = mapped_column(
        SAEnum(StatusSalinan, name="status_salinan", create_type=False),
        nullable=False,
        default=StatusSalinan.tersedia,
    )

    # Relationships
    buku: Mapped["Buku"] = relationship("Buku", back_populates="salinan", lazy="joined")
    peminjaman: Mapped[list["Peminjaman"]] = relationship(
        "Peminjaman", back_populates="salinan_buku", lazy="select"
    )
