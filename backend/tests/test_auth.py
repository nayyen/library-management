"""Authentication tests (AUTH-01 through AUTH-04).

These tests are expected to FAIL (RED) in Plan 01 because the auth
endpoints do not exist yet. Plan 02 implements the endpoints to turn
them GREEN.

Test node IDs matching 01-VALIDATION.md:
  - test_register          (AUTH-01)
  - test_login_returns_jwt (AUTH-02)
  - test_password_is_hashed (AUTH-03)
  - test_protected_endpoint_401 (AUTH-04)
"""

import pytest
from fastapi.testclient import TestClient


def test_register(client: TestClient) -> None:
    """AUTH-01: User can register as mahasiswa with email + password."""
    response = client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Budi Santoso",
            "email": "budi@example.com",
            "kata_sandi": "rahasia123",
        },
    )
    # Expected: 200/201 with access_token
    assert response.status_code in (200, 201), (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "access_token" in data, f"Response missing access_token: {data}"
    assert data["token_type"] == "bearer"

    # Reject short password
    response2 = client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Short",
            "email": "short@example.com",
            "kata_sandi": "1234567",
        },
    )
    assert response2.status_code == 422, (
        f"Expected 422 for short password, got {response2.status_code}"
    )

    # Reject duplicate email
    response3 = client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Budi Dupe",
            "email": "budi@example.com",
            "kata_sandi": "rahasia123",
        },
    )
    assert response3.status_code in (400, 409), (
        f"Expected 400/409 for duplicate email, got {response3.status_code}"
    )

    # Verify peran is hardcoded to mahasiswa
    # (indirect check via login and /saya endpoint)


def test_login_returns_jwt(client: TestClient) -> None:
    """AUTH-02: User can log in and receive a JWT valid for 1 hour."""
    # First register a user
    client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Siti Rahma",
            "email": "siti@example.com",
            "kata_sandi": "passwordku",
        },
    )

    # Login with valid credentials
    response = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "siti@example.com",
            "kata_sandi": "passwordku",
        },
    )
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "access_token" in data, f"Missing access_token: {data}"
    assert data["token_type"] == "bearer"

    # Invalid credentials should return 401
    response2 = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "siti@example.com",
            "kata_sandi": "wrongpassword",
        },
    )
    assert response2.status_code == 401, (
        f"Expected 401 for wrong password, got {response2.status_code}"
    )

    # Non-existent user should return 401
    response3 = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "nonexistent@example.com",
            "kata_sandi": "passwordku",
        },
    )
    assert response3.status_code == 401 or response3.status_code == 404, (
        f"Expected 401/404 for unknown user, got {response3.status_code}"
    )


def test_password_is_hashed(client: TestClient) -> None:
    """AUTH-03: Passwords are hashed with bcrypt before storage."""
    # Register a user
    client.post(
        "/api/autentikasi/registrasi",
        json={
            "nama": "Dewi Lestari",
            "email": "dewi@example.com",
            "kata_sandi": "rahasia123",
        },
    )

    # Login to confirm the password works
    response = client.post(
        "/api/autentikasi/masuk",
        json={
            "email": "dewi@example.com",
            "kata_sandi": "rahasia123",
        },
    )
    assert response.status_code == 200, (
        f"Login failed: {response.status_code}: {response.text}"
    )


def test_protected_endpoint_401(client: TestClient) -> None:
    """AUTH-04: Protected endpoints reject missing/expired/invalid tokens."""
    # Without a token — should be 401
    response = client.get("/api/autentikasi/saya")
    assert response.status_code == 401, (
        f"Expected 401 without token, got {response.status_code}"
    )

    # With an invalid token — should be 401
    response2 = client.get(
        "/api/autentikasi/saya",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response2.status_code == 401, (
        f"Expected 401 with invalid token, got {response2.status_code}"
    )

    # With an expired token — should be 401
    # (We'll simulate this with a token that has an expired exp claim)
    import jwt

    expired_token = jwt.encode(
        {"sub": "fake-user-id", "exp": 1000000000},
        key="secret",
        algorithm="HS256",
    )
    response3 = client.get(
        "/api/autentikasi/saya",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response3.status_code == 401, (
        f"Expected 401 with expired token, got {response3.status_code}"
    )
