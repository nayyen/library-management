"""Idempotent seed script for development.

Creates the default pustakawan account if it does not exist.
Seeds catalog data (buku + salinan_buku) on first run.
Safe to run multiple times.

Usage: python -m app.seed
"""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.buku import Buku
from app.models.salinan_buku import SalinanBuku
from app.models.enums import PeranPengguna, KondisiBuku, StatusSalinan
from app.models.pengguna import Pengguna

PUSTAKAWAN_EMAIL = "pustakawan@biblio.ac.id"
PUSTAKAWAN_PASSWORD = "admin1234"
PUSTAKAWAN_NAMA = "Admin Perpustakaan"

BUKU_SEED = [
    {"judul": "Gadis Kretek", "penulis": "Ratih Kumala", "isbn": "9786020337922", "kategori": "Fiksi", "tahun_terbit": 2012},
    {"judul": "Cantik Itu Luka", "penulis": "Eka Kurniawan", "isbn": "9789793062880", "kategori": "Fiksi", "tahun_terbit": 2002},
    {"judul": "Laskar Pelangi", "penulis": "Andrea Hirata", "isbn": "9789793062798", "kategori": "Fiksi", "tahun_terbit": 2005},
    {"judul": "Ronggeng Dukuh Paruk", "penulis": "Ahmad Tohari", "isbn": "9789792206771", "kategori": "Fiksi", "tahun_terbit": 2003},
    {"judul": "Sapiens: Riwayat Singkat Umat Manusia", "penulis": "Yuval Noah Harari", "isbn": "9786020641395", "kategori": "Non-Fiksi", "tahun_terbit": 2018},
    {"judul": "Filosofi Teras", "penulis": "Henry Manampiring", "isbn": "9786020642996", "kategori": "Non-Fiksi", "tahun_terbit": 2019},
    {"judul": "Sebuah Seni untuk Bersikap Bodo Amat", "penulis": "Mark Manson", "isbn": "9786020640923", "kategori": "Non-Fiksi", "tahun_terbit": 2018},
    {"judul": "Atomic Habits", "penulis": "James Clear", "isbn": "9786024816148", "kategori": "Non-Fiksi", "tahun_terbit": 2019},
    {"judul": "Kamus Besar Bahasa Indonesia", "penulis": "Badan Pengembangan Bahasa", "isbn": "9789794071826", "kategori": "Referensi", "tahun_terbit": 2016},
    {"judul": "Ensiklopedia Sejarah Dunia", "penulis": "Philip Parker", "isbn": "9786230401819", "kategori": "Referensi", "tahun_terbit": 2020},
    {"judul": "Peta Nusantara", "penulis": "Tim Nasional", "isbn": "9789791847092", "kategori": "Referensi", "tahun_terbit": 2015},
]


def seed_pustakawan(db) -> None:
    """Idempotent pustakawan seed."""
    existing = (
        db.query(Pengguna)
        .filter(Pengguna.email == PUSTAKAWAN_EMAIL)
        .first()
    )
    if existing:
        print(f"Seed: pustakawan {PUSTAKAWAN_EMAIL} already exists, skipping.")
        return

    pustakawan = Pengguna(
        nama=PUSTAKAWAN_NAMA,
        email=PUSTAKAWAN_EMAIL,
        kata_sandi=hash_password(PUSTAKAWAN_PASSWORD),
        peran=PeranPengguna.pustakawan,
    )
    db.add(pustakawan)
    db.commit()
    print(f"Seed: created pustakawan {PUSTAKAWAN_EMAIL}.")


def seed_buku(db) -> None:
    """Idempotent buku + salinan_buku seed (D-11/D-12)."""
    if db.query(Buku).count() > 0:
        print("Seed: buku already seeded, skipping.")
        return

    created_books = []
    for data in BUKU_SEED:
        buku = Buku(**data)
        db.add(buku)
        created_books.append(buku)
    db.flush()

    # D-12: mixed status distribution
    salinan_data = [
        # Gadis Kretek — 2 tersedia copies
        {"buku_idx": 0, "lokasi_rak": "A-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        {"buku_idx": 0, "lokasi_rak": "A-2", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Cantik Itu Luka — 1 tersedia, 1 dipinjam (mixed)
        {"buku_idx": 1, "lokasi_rak": "B-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        {"buku_idx": 1, "lokasi_rak": "B-2", "kondisi": KondisiBuku.rusak_ringan, "status": StatusSalinan.dipinjam},
        # Laskar Pelangi — 2 tersedia
        {"buku_idx": 2, "lokasi_rak": "C-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        {"buku_idx": 2, "lokasi_rak": "C-2", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Ronggeng Dukuh Paruk — 1 dipesan (shows Tersedia, since still available via dipesan)
        {"buku_idx": 3, "lokasi_rak": "D-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.dipesan},
        # Sapiens — 1 tersedia
        {"buku_idx": 4, "lokasi_rak": "E-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Filosofi Teras — 0 copies → Tidak Tersedia
        # (no salinan added)
        # Sebuah Seni — 1 tersedia
        {"buku_idx": 6, "lokasi_rak": "F-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Atomic Habits — all 2 copies dipinjam → Tidak Tersedia
        {"buku_idx": 7, "lokasi_rak": "G-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.dipinjam},
        {"buku_idx": 7, "lokasi_rak": "G-2", "kondisi": KondisiBuku.rusak_ringan, "status": StatusSalinan.dipinjam},
        # KBBI — 1 tersedia
        {"buku_idx": 8, "lokasi_rak": "H-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Ensiklopedia Sejarah — 1 tersedia
        {"buku_idx": 9, "lokasi_rak": "I-1", "kondisi": KondisiBuku.bagus, "status": StatusSalinan.tersedia},
        # Peta Nusantara — 0 copies → Tidak Tersedia
    ]

    for s in salinan_data:
        salinan = SalinanBuku(
            id_buku=created_books[s["buku_idx"]].id,
            lokasi_rak=s["lokasi_rak"],
            kondisi=s["kondisi"],
            status_ketersediaan=s["status"],
        )
        db.add(salinan)

    db.commit()
    print(f"Seed: created {len(BUKU_SEED)} buku with {len(salinan_data)} salinan copies.")


def run() -> None:
    db = SessionLocal()
    try:
        seed_pustakawan(db)
        seed_buku(db)
    except Exception as exc:
        db.rollback()
        print(f"Seed error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
