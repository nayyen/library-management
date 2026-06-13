"""Book catalog read tests (CAT-01, CAT-02).

These tests are expected to FAIL (RED) initially because the
buku router and schemas do not exist yet. Plan 02-01 implements
the read endpoints to turn them GREEN.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.buku import Buku
from app.models.salinan_buku import SalinanBuku
from app.models.enums import KondisiBuku, StatusSalinan


def _register_and_login(client: TestClient, email: str = "test@example.com") -> str:
    """Helper: register a mahasiswa and return a Bearer token."""
    client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Test User",
            "email": email,
            "kata_sandi": "password123",
        },
    )
    resp = client.post(
        "/api/autentikasi/masuk",
        json={"email": email, "kata_sandi": "password123"},
    )
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_buku(client: TestClient, db_session: Session) -> None:
    """GET /api/buku returns all books with derived availability flag."""
    token = _register_and_login(client)

    # Seed 2 books with copies directly
    buku1 = Buku(
        judul="Buku Satu",
        penulis="Penulis Satu",
        isbn="9781234567890",
        kategori="Fiksi",
        tahun_terbit=2020,
    )
    buku2 = Buku(
        judul="Buku Dua",
        penulis="Penulis Dua",
        isbn="9780987654321",
        kategori="Non-Fiksi",
        tahun_terbit=2021,
    )
    db_session.add_all([buku1, buku2])
    db_session.flush()

    salinan = SalinanBuku(
        id_buku=buku1.id,
        lokasi_rak="A-1",
        kondisi=KondisiBuku.bagus,
        status_ketersediaan=StatusSalinan.tersedia,
    )
    db_session.add(salinan)
    db_session.commit()

    response = client.get(
        "/api/buku", headers=_auth_header(token)
    )
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "items" in data, f"Response missing 'items': {data}"
    assert len(data["items"]) == 2, (
        f"Expected 2 items, got {len(data['items'])}: {data}"
    )
    # Check tersedia flag
    for item in data["items"]:
        assert "tersedia" in item, f"Item missing 'tersedia': {item}"
        assert isinstance(item["tersedia"], bool), (
            f"tersedia should be bool, got {type(item['tersedia'])}"
        )
    # Buku Satu has a tersedia copy
    satu = [b for b in data["items"] if b["judul"] == "Buku Satu"][0]
    assert satu["tersedia"] is True, f"Buku Satu should be tersedia: {satu}"

    # Buku Dua has no copies
    dua = [b for b in data["items"] if b["judul"] == "Buku Dua"][0]
    assert dua["tersedia"] is False, f"Buku Dua should not be tersedia: {dua}"


def test_search_buku(client: TestClient, db_session: Session) -> None:
    """GET /api/buku?kata_kunci=... matches judul, penulis, or isbn."""
    token = _register_and_login(client)

    buku = Buku(
        judul="Sapiens: Riwayat Singkat",
        penulis="Yuval Noah Harari",
        isbn="9786020641395",
        kategori="Non-Fiksi",
        tahun_terbit=2018,
    )
    db_session.add(buku)
    db_session.commit()

    # Search by judul substring (case-insensitive)
    resp = client.get(
        "/api/buku?kata_kunci=sapiens", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    data = resp.json()
    assert len(data["items"]) == 1, f"Expected 1 result for 'sapiens': {data}"
    assert data["items"][0]["judul"] == buku.judul

    # Search by penulis substring
    resp = client.get(
        "/api/buku?kata_kunci=harari", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    assert len(resp.json()["items"]) == 1

    # Search by isbn
    resp = client.get(
        "/api/buku?kata_kunci=9786020641395", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    assert len(resp.json()["items"]) == 1

    # No match
    resp = client.get(
        "/api/buku?kata_kunci=zzzzzzz", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    assert len(resp.json()["items"]) == 0


def test_filter_kategori(client: TestClient, db_session: Session) -> None:
    """GET /api/buku?kategori=... filters by category (multi-select OR)."""
    token = _register_and_login(client)

    buku1 = Buku(
        judul="Fiksi Book",
        penulis="Author A",
        isbn="9781111111111",
        kategori="Fiksi",
        tahun_terbit=2020,
    )
    buku2 = Buku(
        judul="Non-Fiksi Book",
        penulis="Author B",
        isbn="9782222222222",
        kategori="Non-Fiksi",
        tahun_terbit=2020,
    )
    buku3 = Buku(
        judul="Referensi Book",
        penulis="Author C",
        isbn="9783333333333",
        kategori="Referensi",
        tahun_terbit=2020,
    )
    db_session.add_all([buku1, buku2, buku3])
    db_session.commit()

    # Single category
    resp = client.get(
        "/api/buku?kategori=Fiksi", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["kategori"] == "Fiksi"

    # Multi-category (OR)
    resp = client.get(
        "/api/buku?kategori=Fiksi&kategori=Non-Fiksi",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    items = resp.json()["items"]
    assert len(items) == 2, f"Expected 2 items, got {len(items)}: {items}"
    kategoris = {item["kategori"] for item in items}
    assert kategoris == {"Fiksi", "Non-Fiksi"}, f"Unexpected categories: {kategoris}"


def test_kategori_endpoint(client: TestClient, db_session: Session) -> None:
    """GET /api/buku/kategori returns sorted distinct categories."""
    token = _register_and_login(client)

    buku1 = Buku(
        judul="B Z",
        penulis="A",
        isbn="9784444444444",
        kategori="Referensi",
        tahun_terbit=2020,
    )
    buku2 = Buku(
        judul="A A",
        penulis="B",
        isbn="9785555555555",
        kategori="Fiksi",
        tahun_terbit=2020,
    )
    db_session.add_all([buku1, buku2])
    db_session.commit()

    resp = client.get(
        "/api/buku/kategori", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    data = resp.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert data == ["Fiksi", "Referensi"], f"Unexpected categories: {data}"


def test_detail_buku(client: TestClient, db_session: Session) -> None:
    """GET /api/buku/{id} returns buku with salinan list."""
    token = _register_and_login(client)

    buku = Buku(
        judul="Cantik Itu Luka",
        penulis="Eka Kurniawan",
        isbn="9789793062880",
        kategori="Fiksi",
        tahun_terbit=2002,
    )
    db_session.add(buku)
    db_session.flush()

    salinan1 = SalinanBuku(
        id_buku=buku.id,
        lokasi_rak="B-12",
        kondisi=KondisiBuku.bagus,
        status_ketersediaan=StatusSalinan.tersedia,
    )
    salinan2 = SalinanBuku(
        id_buku=buku.id,
        lokasi_rak="C-3",
        kondisi=KondisiBuku.rusak_ringan,
        status_ketersediaan=StatusSalinan.dipinjam,
    )
    db_session.add_all([salinan1, salinan2])
    db_session.commit()

    resp = client.get(
        f"/api/buku/{buku.id}", headers=_auth_header(token)
    )
    assert resp.status_code == 200, f"Expected 200: {resp.text}"
    data = resp.json()
    assert data["judul"] == "Cantik Itu Luka"
    assert data["tersedia"] is True  # at least one tersedia copy
    assert "salinan" in data, f"Missing 'salinan': {data}"
    assert len(data["salinan"]) == 2, (
        f"Expected 2 salinan, got {len(data['salinan'])}"
    )
    # Check salinan fields
    for salinan in data["salinan"]:
        assert "lokasi_rak" in salinan
        assert "kondisi" in salinan
        assert "status_ketersediaan" in salinan


def test_detail_buku_404(client: TestClient, db_session: Session) -> None:
    """GET /api/buku/{id} with unknown id returns 404."""
    token = _register_and_login(client)
    unknown_id = uuid.uuid4()
    resp = client.get(
        f"/api/buku/{unknown_id}", headers=_auth_header(token)
    )
    assert resp.status_code == 404, (
        f"Expected 404, got {resp.status_code}: {resp.text}"
    )


def test_list_buku_unauthorized(client: TestClient) -> None:
    """GET /api/buku without auth returns 401."""
    resp = client.get("/api/buku")
    assert resp.status_code == 401, (
        f"Expected 401, got {resp.status_code}: {resp.text}"
    )


# ─── CRUD / Role-gate / FK-safe tests (CAT-03, CAT-04) ───


def _create_pustakawan_token(client: TestClient, db_session: Session) -> str:
    """Helper: seed a pustakawan directly and return a Bearer token."""
    from app.core.security import hash_password
    from app.models.pengguna import Pengguna
    from app.models.enums import PeranPengguna

    pustakawan = Pengguna(
        nama="Pustakawan Test",
        email="pustakawan_test@biblio.ac.id",
        kata_sandi=hash_password("admin123"),
        peran=PeranPengguna.pustakawan,
    )
    db_session.add(pustakawan)
    db_session.commit()

    resp = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "pustakawan_test@biblio.ac.id",
            "kata_sandi": "admin123",
        },
    )
    return resp.json()["access_token"]


def test_create_buku_pustakawan(
    client: TestClient, db_session: Session
) -> None:
    """POST /api/buku as pustakawan returns 201 with created book."""
    token = _create_pustakawan_token(client, db_session)

    resp = client.post(
        "/api/buku",
        json={
            "judul": "Buku Baru",
            "penulis": "Penulis Baru",
            "isbn": "9781234567890",
            "kategori": "Fiksi",
            "tahun_terbit": 2023,
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, (
        f"Expected 201, got {resp.status_code}: {resp.text}"
    )
    data = resp.json()
    assert data["judul"] == "Buku Baru"
    assert data["isbn"] == "9781234567890"

    # Verify it's retrievable
    list_resp = client.get("/api/buku", headers=_auth_header(token))
    assert len(list_resp.json()["items"]) >= 1


def test_create_buku_forbidden_for_mahasiswa(client: TestClient) -> None:
    """POST /api/buku as mahasiswa returns 403."""
    token = _register_and_login(client, "mahasiswa@test.com")

    resp = client.post(
        "/api/buku",
        json={
            "judul": "Hacked Book",
            "penulis": "Hacker",
            "isbn": "9789999999999",
            "kategori": "Fiksi",
            "tahun_terbit": 2023,
        },
        headers=_auth_header(token),
    )
    assert resp.status_code == 403, (
        f"Expected 403, got {resp.status_code}: {resp.text}"
    )


def test_create_buku_duplicate_isbn(
    client: TestClient, db_session: Session
) -> None:
    """POST /api/buku with duplicate ISBN returns 409."""
    token = _create_pustakawan_token(client, db_session)

    # Create first book
    resp1 = client.post(
        "/api/buku",
        json={
            "judul": "Buku Pertama",
            "penulis": "Penulis",
            "isbn": "9781111111111",
            "kategori": "Fiksi",
            "tahun_terbit": 2023,
        },
        headers=_auth_header(token),
    )
    assert resp1.status_code == 201

    # Try duplicate ISBN
    resp2 = client.post(
        "/api/buku",
        json={
            "judul": "Buku Duplikat",
            "penulis": "Penulis Lain",
            "isbn": "9781111111111",
            "kategori": "Non-Fiksi",
            "tahun_terbit": 2022,
        },
        headers=_auth_header(token),
    )
    assert resp2.status_code == 409, (
        f"Expected 409 for duplicate ISBN, got {resp2.status_code}: {resp2.text}"
    )
    assert "ISBN" in resp2.json()["detail"]


def test_edit_buku(client: TestClient, db_session: Session) -> None:
    """PUT /api/buku/{id} as pustakawan updates the book."""
    token = _create_pustakawan_token(client, db_session)

    # Create a book first
    create_resp = client.post(
        "/api/buku",
        json={
            "judul": "Judul Lama",
            "penulis": "Penulis",
            "isbn": "9782222222222",
            "kategori": "Fiksi",
            "tahun_terbit": 2020,
        },
        headers=_auth_header(token),
    )
    book_id = create_resp.json()["id"]

    # Edit it
    edit_resp = client.put(
        f"/api/buku/{book_id}",
        json={"judul": "Judul Baru"},
        headers=_auth_header(token),
    )
    assert edit_resp.status_code == 200, (
        f"Expected 200, got {edit_resp.status_code}: {edit_resp.text}"
    )
    assert edit_resp.json()["judul"] == "Judul Baru"

    # Unknown ID → 404
    unknown_id = uuid.uuid4()
    not_found = client.put(
        f"/api/buku/{unknown_id}",
        json={"judul": "Nope"},
        headers=_auth_header(token),
    )
    assert not_found.status_code == 404


def test_delete_buku_no_salinan(
    client: TestClient, db_session: Session
) -> None:
    """DELETE /api/buku/{id} with no copies returns 204."""
    token = _create_pustakawan_token(client, db_session)

    create_resp = client.post(
        "/api/buku",
        json={
            "judul": "To Delete",
            "penulis": "Penulis",
            "isbn": "9783333333333",
            "kategori": "Fiksi",
            "tahun_terbit": 2020,
        },
        headers=_auth_header(token),
    )
    book_id = create_resp.json()["id"]

    del_resp = client.delete(
        f"/api/buku/{book_id}", headers=_auth_header(token)
    )
    assert del_resp.status_code == 204, (
        f"Expected 204, got {del_resp.status_code}: {del_resp.text}"
    )


def test_delete_buku_with_salinan_blocked(
    client: TestClient, db_session: Session
) -> None:
    """DELETE /api/buku/{id} with copies returns 409."""
    token = _create_pustakawan_token(client, db_session)

    # Create a book with a copy
    create_resp = client.post(
        "/api/buku",
        json={
            "judul": "Buku Dengan Salinan",
            "penulis": "Penulis",
            "isbn": "9784444444444",
            "kategori": "Referensi",
            "tahun_terbit": 2020,
        },
        headers=_auth_header(token),
    )
    book_id = create_resp.json()["id"]

    # Add a copy
    client.post(
        f"/api/buku/{book_id}/salinan",
        json={
            "lokasi_rak": "Z-1",
            "kondisi": "bagus",
            "status_ketersediaan": "tersedia",
        },
        headers=_auth_header(token),
    )

    # Try to delete
    del_resp = client.delete(
        f"/api/buku/{book_id}", headers=_auth_header(token)
    )
    assert del_resp.status_code == 409, (
        f"Expected 409, got {del_resp.status_code}: {del_resp.text}"
    )
    assert "salinan" in del_resp.json()["detail"]

    # Verify book still exists
    get_resp = client.get(
        f"/api/buku/{book_id}", headers=_auth_header(token)
    )
    assert get_resp.status_code == 200


def test_add_salinan(client: TestClient, db_session: Session) -> None:
    """POST /api/buku/{id}/salinan as pustakawan adds a copy."""
    token = _create_pustakawan_token(client, db_session)

    # Create a book
    create_resp = client.post(
        "/api/buku",
        json={
            "judul": "Buku Induk",
            "penulis": "Penulis",
            "isbn": "9785555555555",
            "kategori": "Fiksi",
            "tahun_terbit": 2020,
        },
        headers=_auth_header(token),
    )
    book_id = create_resp.json()["id"]

    # Add salinan
    salinan_resp = client.post(
        f"/api/buku/{book_id}/salinan",
        json={
            "lokasi_rak": "A-10",
            "kondisi": "bagus",
            "status_ketersediaan": "tersedia",
        },
        headers=_auth_header(token),
    )
    assert salinan_resp.status_code == 201, (
        f"Expected 201, got {salinan_resp.status_code}: {salinan_resp.text}"
    )
    salinan_data = salinan_resp.json()
    assert salinan_data["lokasi_rak"] == "A-10"

    # Verify it appears in detail view
    detail_resp = client.get(
        f"/api/buku/{book_id}", headers=_auth_header(token)
    )
    assert len(detail_resp.json()["salinan"]) == 1


def test_add_salinan_forbidden_for_mahasiswa(
    client: TestClient, db_session: Session
) -> None:
    """POST /api/buku/{id}/salinan as mahasiswa returns 403."""
    # Create a book directly
    buku = Buku(
        judul="Protected Book",
        penulis="Author",
        isbn="9786666666666",
        kategori="Fiksi",
        tahun_terbit=2020,
    )
    db_session.add(buku)
    db_session.commit()

    # Get mahasiswa token
    mahasiswa_token = _register_and_login(client, "student@test.com")

    # Try to add salinan → 403
    resp = client.post(
        f"/api/buku/{buku.id}/salinan",
        json={
            "lokasi_rak": "Z-9",
            "kondisi": "bagus",
            "status_ketersediaan": "tersedia",
        },
        headers=_auth_header(mahasiswa_token),
    )
    assert resp.status_code == 403, (
        f"Expected 403, got {resp.status_code}: {resp.text}"
    )

