"""Anggota (member roster) tests — DASH-02.

Tests the GET /api/anggota roster endpoint:
- 403 gate for mahasiswa
- Roster scope (only mahasiswa, not pustakawan)
- pinjaman_aktif counts (siap_diambil + dipinjam only)
- total_denda for blocked vs non-blocked members
- Ordering by nama + total field
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


def _register_and_login(client: TestClient, email: str = "mhs_ang@test.com") -> str:
    """Helper: register a mahasiswa and return a Bearer token."""
    client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Mahasiswa Anggota",
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
        nama="Pustakawan Anggota",
        email="pustakawan_anggota@biblio.ac.id",
        kata_sandi=hash_password("admin123"),
        peran=PeranPengguna.pustakawan,
    )
    db_session.add(pustakawan)
    db_session.commit()

    resp = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "pustakawan_anggota@biblio.ac.id",
            "kata_sandi": "admin123",
        },
    )
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_buku_with_salinan(
    db_session: Session,
    judul: str = "Buku Anggota",
) -> tuple[Buku, SalinanBuku]:
    """Seed a Buku with a single SalinanBuku."""
    buku = Buku(
        judul=judul,
        penulis="Penulis",
        isbn=f"978{uuid.uuid4().hex[:10]}",
        kategori="Fiksi",
        tahun_terbit=2023,
    )
    db_session.add(buku)
    db_session.flush()
    salinan = SalinanBuku(
        id_buku=buku.id,
        lokasi_rak="A-1",
        kondisi=KondisiBuku.bagus,
        status_ketersediaan=StatusSalinan.tersedia,
    )
    db_session.add(salinan)
    db_session.commit()
    return buku, salinan


def _create_mahasiswa(
    db_session: Session,
    nama: str,
    email: str | None = None,
    is_diblokir: bool = False,
) -> Pengguna:
    """Helper: seed a mahasiswa directly."""
    mhs = Pengguna(
        nama=nama,
        email=email or f"mhs_{uuid.uuid4().hex[:8]}@test.com",
        kata_sandi=hash_password("pw"),
        peran=PeranPengguna.mahasiswa,
        is_diblokir=is_diblokir,
    )
    db_session.add(mhs)
    db_session.commit()
    return mhs


def _seed_peminjaman(
    db_session: Session,
    user: Pengguna,
    status: StatusPeminjaman,
    total_denda: int = 0,
) -> Peminjaman:
    """Helper: seed a Peminjaman row."""
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
        peminjaman.tanggal_pinjam = now - timedelta(days=5)
        peminjaman.tanggal_tenggat = now + timedelta(days=9)

    if status == StatusPeminjaman.siap_diambil:
        peminjaman.tanggal_siap_ambil = now - timedelta(hours=1)

    if status == StatusPeminjaman.dikembalikan:
        peminjaman.tanggal_kembali = now

    db_session.add(peminjaman)
    db_session.commit()
    return peminjaman


# ─── Tests ───


def test_daftar_anggota_403_for_mahasiswa(
    client: TestClient, db_session: Session
) -> None:
    """Mahasiswa token calling GET /api/anggota → 403."""
    token = _register_and_login(client)

    resp = client.get("/api/anggota", headers=_auth_header(token))
    assert resp.status_code == 403, (
        f"Expected 403, got {resp.status_code}: {resp.text}"
    )
    assert resp.json()["detail"] == "Akses ditolak."


def test_daftar_anggota_only_mahasiswa(
    client: TestClient, db_session: Session
) -> None:
    """Roster includes only mahasiswa rows, not pustakawan."""
    token = _create_pustakawan_token(client, db_session)

    # Pustakawan already exists from token creation
    # Seed 2 mahasiswa
    _create_mahasiswa(db_session, "Andi")
    _create_mahasiswa(db_session, "Budi")

    resp = client.get("/api/anggota", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2, f"Expected 2, got {data['total']}"
    names = [item["nama"] for item in data["items"]]
    assert "Andi" in names
    assert "Budi" in names
    # Pustakawan should NOT appear
    for item in data["items"]:
        assert item["email"] != "pustakawan_anggota@biblio.ac.id"


def test_daftar_anggota_pinjaman_aktif(
    client: TestClient, db_session: Session
) -> None:
    """pinjaman_aktif counts only siap_diambil + dipinjam."""
    token = _create_pustakawan_token(client, db_session)
    mhs = _create_mahasiswa(db_session, "Citra")

    # 1 siap_diambil, 2 dipinjam, 1 menunggu_persetujuan (not counted)
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.siap_diambil)
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam)
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.dipinjam)
    _seed_peminjaman(db_session, mhs, StatusPeminjaman.menunggu_persetujuan)

    resp = client.get("/api/anggota", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    citra = [i for i in data["items"] if i["nama"] == "Citra"][0]
    assert citra["pinjaman_aktif"] == 3, (
        f"Expected 3, got {citra['pinjaman_aktif']}"
    )


def test_daftar_anggota_total_denda(
    client: TestClient, db_session: Session
) -> None:
    """Blocked member reports total_denda; non-blocked reports 0."""
    token = _create_pustakawan_token(client, db_session)

    # Blocked member with denda
    blocked = _create_mahasiswa(db_session, "Dedi", "dedi@test.com", is_diblokir=True)
    _seed_peminjaman(db_session, blocked, StatusPeminjaman.dikembalikan, total_denda=5000)
    _seed_peminjaman(db_session, blocked, StatusPeminjaman.dikembalikan, total_denda=3000)

    # Non-blocked member (should report 0)
    _create_mahasiswa(db_session, "Eva", "eva@test.com")

    resp = client.get("/api/anggota", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()

    dedi = [i for i in data["items"] if i["nama"] == "Dedi"][0]
    assert dedi["is_diblokir"] is True, "Dedi should be blocked"
    assert dedi["total_denda"] == 8000, f"Expected 8000, got {dedi['total_denda']}"

    eva = [i for i in data["items"] if i["nama"] == "Eva"][0]
    assert eva["is_diblokir"] is False, "Eva should not be blocked"
    assert eva["total_denda"] == 0, f"Expected 0, got {eva['total_denda']}"


def test_daftar_anggota_ordering(
    client: TestClient, db_session: Session
) -> None:
    """Items ordered by nama ascending; total matches count."""
    token = _create_pustakawan_token(client, db_session)

    _create_mahasiswa(db_session, "Zara")
    _create_mahasiswa(db_session, "Agnes")
    _create_mahasiswa(db_session, "Bima")

    resp = client.get("/api/anggota", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    names = [i["nama"] for i in data["items"]]
    assert names == sorted(names), f"Names not sorted: {names}"
    assert data["total"] == len(data["items"])
