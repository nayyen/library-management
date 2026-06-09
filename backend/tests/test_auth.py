"""AUTH backend tests — Plan 02 implements AUTH-01/02/04 (signup, login,
refresh rotation, role enforcement). AUTH-03 (forgot/reset password) is
implemented in Plan 04.

Naming -> requirement map (see 01-VALIDATION.md):
  AUTH-01 (signup + role + librarian code):
    test_signup_student
    test_signup_librarian_valid_code
    test_signup_librarian_invalid_code
  AUTH-02 (login issues tokens, refresh rotation, silent refresh):
    test_login_issues_tokens
    test_refresh_rotates_token
  AUTH-03 (forgot/reset password — enumeration-safe, single-use, revokes sessions):
    test_forgot_password_enumeration_safe
    test_reset_password_single_use
    test_reset_revokes_all_sessions
  AUTH-04 (server-side role enforcement):
    test_require_role_rejects_wrong_role
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


# ---------------------------------------------------------------------------
# AUTH-01: signup
# ---------------------------------------------------------------------------


async def test_signup_student(async_client: AsyncClient, user_factory) -> None:
    response = await async_client.post(
        "/auth/signup",
        json={
            "email": "new.student@example.com",
            "password": "correct horse battery staple",
            "role": "student",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body and body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "new.student@example.com"
    assert body["user"]["role"] == "student"
    # Refresh token: httpOnly cookie only — never in the response body (D-05).
    assert "refresh_token" not in body
    assert "refresh_token" in response.cookies
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header
    assert "samesite=lax" in set_cookie_header.lower()


async def test_signup_librarian_valid_code(async_client: AsyncClient, user_factory) -> None:
    response = await async_client.post(
        "/auth/signup",
        json={
            "email": "new.librarian@example.com",
            "password": "correct horse battery staple",
            "role": "librarian",
            "librarian_code": settings.LIBRARIAN_SIGNUP_CODE,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "librarian"
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in response.cookies


async def test_signup_librarian_invalid_code(async_client: AsyncClient, user_factory) -> None:
    response = await async_client.post(
        "/auth/signup",
        json={
            "email": "wannabe.librarian@example.com",
            "password": "correct horse battery staple",
            "role": "librarian",
            "librarian_code": "definitely-the-wrong-code",
        },
    )

    # D-03: exact reject copy, 422, and NO silent fallback to a student account.
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Invalid librarian code — check with your library administrator, "
        "or sign up as a student."
    )

    # No user row was created — re-attempting signup with the SAME email and
    # the correct code must succeed (proves nothing was inserted above).
    retry = await async_client.post(
        "/auth/signup",
        json={
            "email": "wannabe.librarian@example.com",
            "password": "correct horse battery staple",
            "role": "librarian",
            "librarian_code": settings.LIBRARIAN_SIGNUP_CODE,
        },
    )
    assert retry.status_code == 201
    assert retry.json()["user"]["role"] == "librarian"


# ---------------------------------------------------------------------------
# AUTH-02: login + refresh rotation
# ---------------------------------------------------------------------------


async def test_login_issues_tokens(async_client: AsyncClient, user_factory) -> None:
    await user_factory(email="login.test@example.com", password="correct horse battery staple")

    response = await async_client.post(
        "/auth/login",
        json={"email": "login.test@example.com", "password": "correct horse battery staple"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body and body["access_token"]
    assert body["user"]["email"] == "login.test@example.com"
    assert "refresh_token" not in body
    assert "refresh_token" in response.cookies

    # Invalid credentials — generic 401, identical message for bad email AND
    # bad password (enumeration-safe).
    bad_email = await async_client.post(
        "/auth/login",
        json={"email": "no.such.user@example.com", "password": "whatever-password"},
    )
    bad_password = await async_client.post(
        "/auth/login",
        json={"email": "login.test@example.com", "password": "wrong-password-entirely"},
    )
    assert bad_email.status_code == 401
    assert bad_password.status_code == 401
    assert bad_email.json()["detail"] == bad_password.json()["detail"]
    assert bad_email.json()["detail"] == "Invalid email or password. Check your details and try again."


async def test_refresh_rotates_token(async_client: AsyncClient, user_factory) -> None:
    await user_factory(email="refresh.test@example.com", password="correct horse battery staple")

    login_response = await async_client.post(
        "/auth/login",
        json={"email": "refresh.test@example.com", "password": "correct horse battery staple"},
    )
    assert login_response.status_code == 200
    old_refresh_cookie = login_response.cookies["refresh_token"]

    # First refresh: rotates — issues a new access token AND a new refresh cookie.
    refresh_response = await async_client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    assert new_access_token  # rotation issued a valid access token

    new_refresh_cookie = async_client.cookies.get("refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != old_refresh_cookie

    # Reuse detection: replay the OLD (now-revoked) refresh cookie — must be
    # rejected with 401 AND revoke the entire session family. We simulate the
    # replay by setting the client's cookie jar back to the old value.
    async_client.cookies.set("refresh_token", old_refresh_cookie, path="/auth")
    replay_response = await async_client.post("/auth/refresh")
    assert replay_response.status_code == 401

    # The whole family is now revoked — even the most-recently-issued
    # (valid-looking) refresh token must now be rejected.
    async_client.cookies.set("refresh_token", new_refresh_cookie, path="/auth")
    post_reuse_response = await async_client.post("/auth/refresh")
    assert post_reuse_response.status_code == 401


# ---------------------------------------------------------------------------
# AUTH-03: forgot/reset password
# ---------------------------------------------------------------------------


async def test_forgot_password_enumeration_safe(
    async_client: AsyncClient, user_factory, db_session: AsyncSession
) -> None:
    """D-09: identical response for a registered vs. unregistered email."""
    await user_factory(email="reset.enum@example.com")

    with patch("app.services.email_service.send_reset_email", new_callable=AsyncMock):
        resp_registered = await async_client.post(
            "/auth/forgot-password", json={"email": "reset.enum@example.com"}
        )
        resp_unknown = await async_client.post(
            "/auth/forgot-password", json={"email": "nobody.here@example.com"}
        )

    assert resp_registered.status_code == 200
    assert resp_unknown.status_code == 200
    # D-09: body must be byte-identical regardless of registration status.
    assert resp_registered.json() == resp_unknown.json()
    assert "reset link" in resp_registered.json()["message"].lower()


async def test_reset_password_single_use(
    async_client: AsyncClient, user_factory, db_session: AsyncSession
) -> None:
    """D-08: a reset token is rejected on second use (used_at set on first use)."""
    user = await user_factory(email="reset.single@example.com", password="original-password-1")

    # Create a reset token directly via the service (bypasses email delivery).
    from app.services.auth_service import create_reset_token  # noqa: PLC0415

    raw_token = await create_reset_token(db_session, user)

    # First use: succeeds — sets new password, auto-logs-in.
    first = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "new-secure-password-1"},
    )
    assert first.status_code == 200
    body = first.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in first.cookies

    # Second use: same token must be rejected (D-08 single-use).
    second = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "another-new-password"},
    )
    assert second.status_code == 400
    assert "no longer valid" in second.json()["detail"].lower()


async def test_reset_revokes_all_sessions(
    async_client: AsyncClient, user_factory, db_session: AsyncSession
) -> None:
    """D-07: resetting password revokes ALL existing refresh tokens; the new
    access token from the reset response is valid."""
    user = await user_factory(email="reset.revoke@example.com", password="original-password-2")

    # Login to establish a pre-existing session (simulates "other device").
    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "reset.revoke@example.com", "password": "original-password-2"},
    )
    assert login_resp.status_code == 200
    old_refresh_cookie = login_resp.cookies["refresh_token"]

    # Create a reset token directly via the service.
    from app.services.auth_service import create_reset_token  # noqa: PLC0415

    raw_token = await create_reset_token(db_session, user)

    # Perform the reset.
    reset_resp = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "post-reset-password-2"},
    )
    assert reset_resp.status_code == 200
    new_access_token = reset_resp.json()["access_token"]
    assert new_access_token  # auto-login issued a valid access token (D-10)

    # D-07: the pre-existing refresh token must now be revoked — attempting to
    # use it should return 401.
    async_client.cookies.set("refresh_token", old_refresh_cookie, path="/auth")
    stale_refresh = await async_client.post("/auth/refresh")
    assert stale_refresh.status_code == 401

    # The new access token from the reset response must be functional.
    me_resp = await async_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "reset.revoke@example.com"


# ---------------------------------------------------------------------------
# AUTH-03 (cont.): validate-reset-token preflight endpoint
# ---------------------------------------------------------------------------


async def test_validate_reset_token_valid(
    async_client: AsyncClient, user_factory, db_session: AsyncSession
) -> None:
    """GET /auth/validate-reset-token returns 200 for a fresh, unused token."""
    user = await user_factory(email="validate.valid@example.com")
    from app.services.auth_service import create_reset_token  # noqa: PLC0415

    raw_token = await create_reset_token(db_session, user)

    response = await async_client.get(f"/auth/validate-reset-token?token={raw_token}")
    assert response.status_code == 200
    assert response.json()["valid"] is True


async def test_validate_reset_token_used(
    async_client: AsyncClient, user_factory, db_session: AsyncSession
) -> None:
    """GET /auth/validate-reset-token returns 400 for a token that has been used."""
    user = await user_factory(email="validate.used@example.com", password="original-pw-3")
    from app.services.auth_service import create_reset_token  # noqa: PLC0415

    raw_token = await create_reset_token(db_session, user)

    # Consume the token via the reset endpoint.
    used = await async_client.post(
        "/auth/reset-password",
        json={"token": raw_token, "new_password": "post-reset-pw-3"},
    )
    assert used.status_code == 200

    # Preflight for the same token must now return 400.
    response = await async_client.get(f"/auth/validate-reset-token?token={raw_token}")
    assert response.status_code == 400
    assert "no longer valid" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AUTH-04: server-side role enforcement
# ---------------------------------------------------------------------------


async def test_require_role_rejects_wrong_role(
    async_client: AsyncClient, user_factory, access_token_for
) -> None:
    student = await user_factory(email="student.demo@example.com", role="student")
    librarian = await user_factory(email="librarian.demo@example.com", role="librarian")

    student_token = access_token_for(student)
    librarian_token = access_token_for(librarian)

    student_response = await async_client.get(
        "/demo/librarian-only", headers={"Authorization": f"Bearer {student_token}"}
    )
    librarian_response = await async_client.get(
        "/demo/librarian-only", headers={"Authorization": f"Bearer {librarian_token}"}
    )

    # require_role re-checks the DB-loaded user's role server-side — a
    # student token is rejected with 403 regardless of any client-side claims;
    # a librarian token is accepted (AUTH-04 / T-01-04).
    assert student_response.status_code == 403
    assert librarian_response.status_code == 200
    assert librarian_response.json()["message"]
