"""Create initial schema — 4 ENUM types + 4 tables.

Revision ID: 0001
Revises:
Create Date: 2026-06-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Create ENUM types (checkfirst=True makes them idempotent)
    postgresql.ENUM(
        "mahasiswa",
        "pustakawan",
        name="peran_pengguna",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "bagus",
        "rusak_ringan",
        "rusak_berat",
        name="kondisi_buku",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "tersedia",
        "dipesan",
        "dipinjam",
        name="status_salinan",
    ).create(bind, checkfirst=True)

    postgresql.ENUM(
        "menunggu_persetujuan",
        "siap_diambil",
        "dipinjam",
        "dibatalkan",
        "dikembalikan",
        "ditolak",
        name="status_peminjaman",
    ).create(bind, checkfirst=True)

    # Create pengguna table
    op.create_table(
        "pengguna",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nama", sa.String(150), nullable=False),
        sa.Column(
            "email", sa.String(100), unique=True, index=True, nullable=False
        ),
        sa.Column("kata_sandi", sa.String(255), nullable=False),
        sa.Column(
            "peran",
            postgresql.ENUM(
                "mahasiswa",
                "pustakawan",
                name="peran_pengguna",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "is_diblokir",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Create buku table
    op.create_table(
        "buku",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("judul", sa.String(255), nullable=False),
        sa.Column("penulis", sa.String(255), nullable=False),
        sa.Column(
            "isbn", sa.String(20), unique=True, index=True, nullable=False
        ),
        sa.Column("kategori", sa.String(100), nullable=False),
        sa.Column("tahun_terbit", sa.Integer(), nullable=False),
    )

    # Create salinan_buku table
    op.create_table(
        "salinan_buku",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "id_buku",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("buku.id"),
            nullable=False,
        ),
        sa.Column("lokasi_rak", sa.String(50), nullable=False),
        sa.Column(
            "kondisi",
            postgresql.ENUM(
                "bagus",
                "rusak_ringan",
                "rusak_berat",
                name="kondisi_buku",
                create_type=False,
            ),
            nullable=False,
            server_default="bagus",
        ),
        sa.Column(
            "status_ketersediaan",
            postgresql.ENUM(
                "tersedia",
                "dipesan",
                "dipinjam",
                name="status_salinan",
                create_type=False,
            ),
            nullable=False,
            server_default="tersedia",
        ),
    )

    # Create peminjaman table
    op.create_table(
        "peminjaman",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "id_pengguna",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pengguna.id"),
            nullable=False,
        ),
        sa.Column(
            "id_salinan_buku",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("salinan_buku.id"),
            nullable=False,
        ),
        sa.Column(
            "tanggal_pengajuan",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "tanggal_siap_ambil", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "tanggal_pinjam", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "tanggal_tenggat", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "tanggal_kembali", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "status_peminjaman",
            postgresql.ENUM(
                "menunggu_persetujuan",
                "siap_diambil",
                "dipinjam",
                "dibatalkan",
                "dikembalikan",
                "ditolak",
                name="status_peminjaman",
                create_type=False,
            ),
            nullable=False,
            server_default="menunggu_persetujuan",
        ),
        sa.Column(
            "total_denda",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Drop tables in reverse dependency order
    op.drop_table("peminjaman")
    op.drop_table("salinan_buku")
    op.drop_table("buku")
    op.drop_table("pengguna")

    # Drop ENUM types in reverse creation order
    postgresql.ENUM(name="status_peminjaman").drop(bind, checkfirst=True)
    postgresql.ENUM(name="status_salinan").drop(bind, checkfirst=True)
    postgresql.ENUM(name="kondisi_buku").drop(bind, checkfirst=True)
    postgresql.ENUM(name="peran_pengguna").drop(bind, checkfirst=True)
