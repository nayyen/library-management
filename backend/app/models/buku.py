import uuid
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Buku(Base):
    __tablename__ = "buku"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    judul: Mapped[str] = mapped_column(String(255), nullable=False)
    penulis: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    kategori: Mapped[str] = mapped_column(String(100), nullable=False)
    tahun_terbit: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    salinan: Mapped[list["SalinanBuku"]] = relationship(
        "SalinanBuku", back_populates="buku", lazy="select"
    )
