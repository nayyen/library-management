"""Dashboard tests — DASH-01 stats endpoint.

Tests the GET /api/dashboard/stats aggregation endpoint:
- 403 gate for mahasiswa
- Total Buku count
- Peminjaman Aktif (siap_diambil + dipinjam only)
- Menunggu Persetujuan count
- Buku Terlambat (via _is_terlambat)
- Total Denda Belum Lunas + Jumlah Mahasiswa
- Pengajuan Preview (max 5, newest first)
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.buku import Buku
from app.models.salinan_buku import SalinanBuku
from app.models.pengguna import Pengguna
from app.models.peminjaman import Peminjaman
from app.models.enums import (
    KondisiBuku,
    StatusSalinan,
    PeranPengguna,
    StatusPeminjaman,
)
from app.core.security import hash_password


def _register_and_login(client: TestClient, email: str = "mhs_dash@test.com") -> str:
    """Helper: register a mahasiswa and return a Bearer token."""
    client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Mahasiswa Dashboard",
            "email": email,
            "kata_sandi": "password123",
        },
    )
    resp = client.post(
        "/api/autentikasi/masuk",
        json={"email": email, "kata_sandi": "password123"},
    )
    return resp.json()["access_token"]


def _create_pustakawan_token(client: TestClient, db_session: Session) -> str:
    """Helper: seed a pustakawan directly and return a Bearer token."""
    pustakawan = Pengguna(
        nama="Pustakawan Dashboard",
        email="pustakawan_dashboard@biblio.ac.id",
        kata_sandi=hash_password("admin123"),
        peran=PeranPengguna.pustakawan,
    )
    db_session.add(pustakawan)
    db_session.commit()

    resp = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "pustakawan_dashboard@biblio.ac.id",
            "kata_sandi": "admin123",
        },
    )
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_buku_with_salinan(
    db_session: Session,
    judul: str = "Buku Dashboard",
    lokasi_rak: str = "A-1",
) -> tuple[Buku, SalinanBuku]:
    """Seed a Buku with a single SalinanBuku. Returns (buku, salinan)."""
    buku = Buku(
        judul=judul,
        penulis="Penulis Dashboard",
        isbn=f"978{uuid.uuid4().hex[:10]}",
        kategori="Fiksi",
        tahun_terbit=2023,
    )
    db_session.add(buku)
    db_session.flush()

    salinan = SalinanBuku(
        id_buku=buku.id,
        lokasi_rak=lokasi_rak,
        kondisi=KondisiBuku.bagus,
        status_ketersediaan=StatusSalinan.tersedia,
    )
    db_session.add(salinan)
    db_session.commit()
    return buku, salinan


def _create_mahasiswa(
    db_session: Session,
    nama: str = "Mahasiswa",
    email: str | None = None,
) -> Pengguna:
    """Helper: seed a mahasiswa directly."""
    mhs = Pengguna(
        nama=nama,
        email=email or f"mhs_{uuid.uuid4().hex[:8]}@test.com",
        kata_sandi=hash_password("password123"),
        peran=PeranPengguna.mahasiswa,
    )
    db_session.add(mhs)
    db_session.commit()
    return mhs


def _seed_peminjaman(
    db_session: Session,
    user: Pengguna,
    status: StatusPeminjaman,
    salinan: SalinanBuku | None = None,
    tenggat_offset_days: int | None = None,
    total_denda: int = 0,
) -> Peminjaman:
    """Helper: seed a Peminjaman row with optional tenggat and denda."""
    if salinan is None:
        _, salinan = _seed_buku_with_salinan(db_session)
        salinan.status_ketersediaan = StatusSalinan.dipesan
        db_session.flush()

    now = datetime.now(timezone.utc)
    peminjaman = Peminjaman(
        id_pengguna=user.id,
        id_salinan_buku=salinan.id,
        tanggal_pengajuan=now - timedelta(hours=2),
        status_peminjaman=status,
        total_denda=total_denda,
        tanggal_kembali=None,
    )

    if status == StatusPeminjaman.dipinjam:
        peminjaman.tanggal_pinjam=now - timedelta(days=10)
        if tenggat_offset_days is not None:
            peminjaman.tanggal_tenggat=now - timedelta(days=tenggat_offset_days)  # past = terlambat
        else:
            peminjaman.tanggal_tenggat=now + timedelta(days=4)  # future = on time

    if status == StatusPeminjaman.siap_diambil:
        peminjaman.tanggal_siap_ambil=now - timedelta(hours=1)

    if status == StatusPeminjaman.dikembalikan:
        peminjaman.tanggal_kembali=now
        peminjaman.total_denda=total_denda

    db_session.add(peminjaman)
    db_session.commit()
    return peminjaman


# ─── Tests ───


def test_dashboard_stats_403_for_mahasiswa(
    client: TestClient, db_session: Session
) -> None:
    """Mahasiswa token calling GET /api/dashboard/stats → 403."""
    token = _register_and_login(client)

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 403, (
        f"Expected 403, got {resp.status_code}: {resp.text}"
    )
    assert resp.json()["detail"] == "Akses ditolak."


def test_dashboard_stats_total_buku(
    client: TestClient, db_session: Session
) -> None:
    """With N seeded buku, total_buku == N."""
    token = _create_pustakawan_token(client, db_session)

    # Seed 3 buku
    for i in range(3):
        _seed_buku_with_salinan(db_session, judul=f"Buku {i}")

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["total_buku"] == 3, f"Expected 3, got {data['total_buku']}"


def test_dashboard_stats_peminjaman_aktif(
    client: TestClient, db_session: Session
) -> None:
    """peminjaman_aktif counts ONLY siap_diambil + dipinjam (not menunggu_persetujuan)."""
    token = _create_pustakawan_token(client, db_session)
    mhs = _create_mahasiswa(db_session, "Mahasiswa Aktif")

    # 1 siap_diambil, 2 dipinjam, 3 menunggu_persetujuan (should NOT count)
    for i in range(2):
        _, s = _seed_buku_with_salinan(db_session, judul=f"Buku Dipinjam {i}")
        _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam, salinan=s)

    _, s2 = _seed_buku_with_salinan(db_session, judul="Buku Siap Diambil")
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.siap_diambil, salinan=s2)

    for i in range(3):
        _, s3 = _seed_buku_with_salinan(db_session, judul=f"Buku Menunggu {i}")
        _seed_peminjaman(db_session, mhs, StatusPeminjaman.menunggu_persetujuan, salinan=s3)

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["peminjaman_aktif"] == 3, (
        f"Expected 3 (2 dipinjam + 1 siap_diambil), got {data['peminjaman_aktif']}"
    )
    assert data["menunggu_persetujuan_count"] == 3, (
        f"Expected 3 menunggu, got {data['menunggu_persetujuan_count']}"
    )


def test_dashboard_stats_buku_terlambat(
    client: TestClient, db_session: Session
) -> None:
    """dipinjam with past tenggat counts as terlambat; future tenggat does not."""
    token = _create_pustakawan_token(client, db_session)
    mhs = _create_mahasiswa(db_session, "Mahasiswa Terlambat")

    # 1 dipinjam — tenggat offset -2 days = terlambat
    _, s1 = _seed_buku_with_salinan(db_session, judul="Buku Terlambat")
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam, salinan=s1, tenggat_offset_days=2)

    # 1 dipinjam — tenggat offset -5 days = also terlambat
    _, s2 = _seed_buku_with_salinan(db_session, judul="Buku Juga Terlambat")
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam, salinan=s2, tenggat_offset_days=5)

    # 1 dipinjam — future tenggat = on time
    _, s3 = _seed_buku_with_salinan(db_session, judul="Buku Tepat Waktu")
    p3 = _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam, salinan=s3)
    # Set tenggat to future
    now = datetime.now(timezone.utc)
    p3.tanggal_tenggat = now + timedelta(days=4)
    db_session.commit()

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["buku_terlambat"] == 2, (
        f"Expected 2, got {data['buku_terlambat']}"
    )


def test_dashboard_stats_total_denda(
    client: TestClient, db_session: Session
) -> None:
    """total_denda_belum_lunas sums denda across blocked members with denda."""
    token = _create_pustakawan_token(client, db_session)

    # Blocked member 1 — denda 5000
    mhs1 = _create_mahasiswa(db_session, "Mahasiswa Blokir 1", "blokir1@test.com")
    mhs1.is_diblokir = True
    db_session.flush()
    _, s1 = _seed_buku_with_salinan(db_session, judul="Buku Denda 1")
    _seed_peminjaman(db_session, mhs1, StatusPeminjaman.dikembalikan, salinan=s1, total_denda=5000)

    # Blocked member 2 — denda 12000 (combined = 17000)
    mhs2 = _create_mahasiswa(db_session, "Mahasiswa Blokir 2", "blokir2@test.com")
    mhs2.is_diblokir = True
    db_session.flush()
    _, s2 = _seed_buku_with_salinan(db_session, judul="Buku Denda 2")
    _seed_peminjaman(db_session, mhs2, StatusPeminjaman.dikembalikan, salinan=s2, total_denda=8000)
    _, s3 = _seed_buku_with_salinan(db_session, judul="Buku Denda 3")
    _seed_peminjaman(db_session, mhs2, StatusPeminjaman.dikembalikan, salinan=s3, total_denda=4000)

    # Non-blocked member — should NOT count (denda 3000 but not blocked)
    mhs3 = _create_mahasiswa(db_session, "Mahasiswa Aktif", "aktif@test.com")
    _, s4 = _seed_buku_with_salinan(db_session, judul="Buku Tidak Dihitung")
    _seed_peminjaman(db_session, mhs3, StatusPeminjaman.dikembalikan, salinan=s4, total_denda=3000)

    # Blocked member with 0 denda — should NOT count in jumlah_mahasiswa_denda
    mhs4 = _create_mahasiswa(db_session, "Mahasiswa Blokir 3", "blokir3@test.com")
    mhs4.is_diblokir = True
    db_session.commit()

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_denda_belum_lunas"] == 17000, (
        f"Expected 17000, got {data['total_denda_belum_lunas']}"
    )
    assert data["jumlah_mahasiswa_denda"] == 2, (
        f"Expected 2, got {data['jumlah_mahasiswa_denda']}"
    )


def test_dashboard_stats_pengajuan_preview(
    client: TestClient, db_session: Session
) -> None:
    """pengajuan_preview returns at most 5 rows, newest first."""
    token = _create_pustakawan_token(client, db_session)
    mhs = _create_mahasiswa(db_session, "Mahasiswa Preview")

    # Seed 7 menunggu_persetujuan rows
    for i in range(7):
        _, s = _seed_buku_with_salinan(db_session, judul=f"Buku Preview {i}")
        peminjaman = Peminjaman(
            id_pengguna=mhs.id,
            id_salinan_buku=s.id,
            tanggal_pengajuan=datetime.now(timezone.utc) - timedelta(hours=7 - i),
            status_peminjaman=StatusPeminjaman.menunggu_persetujuan,
        )
        db_session.add(peminjaman)
    db_session.commit()

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["pengajuan_preview"]) == 5, (
        f"Expected 5 preview items, got {len(data['pengajuan_preview'])}"
    )
    # Verify newest first (descending tanggal_pengajuan)
    dates = [item["tanggal_pengajuan"] for item in data["pengajuan_preview"]]
    assert dates == sorted(dates, reverse=True), (
        f"Preview rows not in descending order: {dates}"
    )


def test_dashboard_stats_empty(
    client: TestClient, db_session: Session
) -> None:
    """With no data seeded, all counts return 0 and preview is empty."""
    token = _create_pustakawan_token(client, db_session)

    resp = client.get("/api/dashboard/stats", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_buku"] == 0
    assert data["peminjaman_aktif"] == 0
    assert data["menunggu_persetujuan_count"] == 0
    assert data["buku_terlambat"] == 0
    assert data["total_denda_belum_lunas"] == 0
    assert data["jumlah_mahasiswa_denda"] == 0
    assert data["pengajuan_preview"] == []
