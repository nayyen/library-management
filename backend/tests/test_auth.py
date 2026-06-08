"""Wave 0 AUTH stub tests — pre-named anchors for Plans 02-04.

Per 01-VALIDATION.md "Per-Task Verification Map", these nine functions are the
exact test-name contract that AUTH-01..04 implementations must satisfy. Each
is `xfail(strict=False)` so the suite stays green-but-honest until the slice
that implements it lands — `pytest --collect-only -q` must discover all nine
without import errors (Nyquist Wave 0 requirement).

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

import pytest
from httpx import AsyncClient

XFAIL_REASON = "implemented in Plan 02/03/04"


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_signup_student(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-01: implemented in Plan 02")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_signup_librarian_valid_code(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-01: implemented in Plan 02")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_signup_librarian_invalid_code(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-01: implemented in Plan 02")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_login_issues_tokens(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-02: implemented in Plan 02/03")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_refresh_rotates_token(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-02: implemented in Plan 02/03")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_forgot_password_enumeration_safe(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_reset_password_single_use(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_reset_revokes_all_sessions(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-03: implemented in Plan 04")


@pytest.mark.xfail(reason=XFAIL_REASON, strict=False)
async def test_require_role_rejects_wrong_role(async_client: AsyncClient, user_factory) -> None:
    raise NotImplementedError("AUTH-04: implemented in Plan 03/04")
