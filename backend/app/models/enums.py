import enum


class PeranPengguna(str, enum.Enum):
    mahasiswa = "mahasiswa"
    pustakawan = "pustakawan"


class KondisiBuku(str, enum.Enum):
    bagus = "bagus"
    rusak_ringan = "rusak_ringan"
    rusak_berat = "rusak_berat"


class StatusSalinan(str, enum.Enum):
    tersedia = "tersedia"
    dipesan = "dipesan"
    dipinjam = "dipinjam"


class StatusPeminjaman(str, enum.Enum):
    menunggu_persetujuan = "menunggu_persetujuan"
    siap_diambil = "siap_diambil"
    dipinjam = "dipinjam"
    dibatalkan = "dibatalkan"
    dikembalikan = "dikembalikan"
    ditolak = "ditolak"
