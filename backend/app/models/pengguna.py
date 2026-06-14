import uuid
from sqlalchemy import Boolean, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.enums import PeranPengguna


class Pengguna(Base):
    __tablename__ = "pengguna"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nama: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    kata_sandi: Mapped[str] = mapped_column(String(255), nullable=False)
    peran: Mapped[PeranPengguna] = mapped_column(
        SAEnum(PeranPengguna, name="peran_pengguna", create_type=False),
        nullable=False,
    )
    is_diblokir: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # Relationships
    peminjaman: Mapped[list["Peminjaman"]] = relationship(
        "Peminjaman", back_populates="pengguna", lazy="select"
    )
