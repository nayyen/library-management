"""AUTH backend tests — Plan 02 implements AUTH-01/02/04 (signup, login,
refresh rotation, role enforcement). AUTH-03 (forgot/reset password) remains
xfail until Plan 04.

Naming -> requirement map (see 01-VALIDATION.md):
  AUTH-01 (signup + role + librarian code):
    test_signup_student
    test_signup_librarian_valid_code
    test_signup_librarian_invalid_code
  AUTH-02 (login issues tokens, refresh rotation, silent refresh):
    test_login_issues_tokens
    test_refresh_rotates_token
  AUTH-03 (forgot/reset password — enumeration-safe, single-use, revokes sessions):
    test_forgot_password_enumeration_safe   [xfail — Plan 04]
    test_reset_password_single_use          [xfail — Plan 04]
    test_reset_revokes_all_sessions         [xfail — Plan 04]
  AUTH-04 (server-side role enforcement):
    test_require_role_rejects_wrong_role
"""

import pytest
from httpx import AsyncClient

from app.config import settings

XFAIL_REASON = "implemented in Plan 02/03/04"


# ---------------------------------------------------------------------------
# AUTH-01: signup
# ---------------------------------------------------------------------------


async def test_signup_student(async_client: AsyncClient, user_factory) -> None:
    response = await async_client.post(
        "/auth/signup",
        json={
            "email": "new.student@library.local",
            "password": "correct horse battery staple",
            "role": "student",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body and body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "new.student@library.local"
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
            "email": "new.librarian@library.local",
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
            "email": "wannabe.librarian@library.local",
            "password": "correct horse battery staple",
            "role": "librarian",
            "librarian_code": "definitely-the-wrong-code",
        },
    )

    # D-03: exact reject copy, 400, and NO silent fallback to a student account.
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid librarian code — check with your library administrator, "
        "or sign up as a student."
    )

    # No user row was created — re-attempting signup with the SAME email and
    # the correct code must succeed (proves nothing was inserted above).
    retry = await async_client.post(
        "/auth/signup",
        json={
            "email": "wannabe.librarian@library.local",
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
    await user_factory(email="login.test@library.local", password="correct horse battery staple")

    response = await async_client.post(
        "/auth/login",
        json={"email": "login.test@library.local", "password": "correct horse battery staple"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body and body["access_token"]
    assert body["user"]["email"] == "login.test@library.local"
    assert "refresh_token" not in body
    assert "refresh_token" in response.cookies

    # Invalid credentials — generic 401, identical message for bad email AND
    # bad password (enumeration-safe).
    bad_email = await async_client.post(
        "/auth/login",
        json={"email": "no.such.user@library.local", "password": "whatever-password"},
    )
    bad_password = await async_client.post(
        "/auth/login",
        json={"email": "login.test@library.local", "password": "wrong-password-entirely"},
    )
    assert bad_email.status_code == 401
    assert bad_password.status_code == 401
    assert bad_email.json()["detail"] == bad_password.json()["detail"]
    assert bad_email.json()["detail"] == "Invalid email or password. Check your details and try again."


async def test_refresh_rotates_token(async_client: AsyncClient, user_factory) -> None:
    await user_factory(email="refresh.test@library.local", password="correct horse battery staple")

    login_response = await async_client.post(
        "/auth/login",
        json={"email": "refresh.test@library.local", "password": "correct horse battery staple"},
    )
    assert login_response.status_code == 200
    old_refresh_cookie = login_response.cookies["refresh_token"]

    # First refresh: rotates — issues a new access token AND a new refresh cookie.
    refresh_response = await async_client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    assert new_access_token and new_access_token != login_response.json()["access_token"]

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
# AUTH-03: forgot/reset password — implemented in Plan 04
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_forgot_password_enumeration_safe(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_reset_password_single_use(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_reset_revokes_all_sessions(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


# ---------------------------------------------------------------------------
# AUTH-04: server-side role enforcement
# ---------------------------------------------------------------------------


async def test_require_role_rejects_wrong_role(
    async_client: AsyncClient, user_factory, access_token_for
) -> None:
    student = await user_factory(email="student.demo@library.local", role="student")
    librarian = await user_factory(email="librarian.demo@library.local", role="librarian")

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
