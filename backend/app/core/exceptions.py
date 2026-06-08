"""Shared HTTP exception helpers for the auth slice.

Centralizing these keeps error copy/status-codes consistent across
`get_current_user`, the auth service, and the routers — and makes the
"single generic 401" / "exact D-03 string" acceptance checks easy to satisfy
from one place rather than scattered literals.
"""

from fastapi import HTTPException, status

# Raised by `get_current_user` for ANY token-validation failure (missing,
# malformed, expired, wrong algorithm, user no longer exists). A single
# generic message + WWW-Authenticate header — never leaks *why* validation
# failed (mirrors the login-enumeration-safety principle, T-01-ENUM).
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# Single generic login failure for both "no such email" and "wrong password" —
# enumeration-safe per Security Domain guidance and the UI-SPEC Copywriting
# Contract (identical message regardless of which check failed).
invalid_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password. Check your details and try again.",
)

# Raised by `require_role` when the DB-loaded user's role doesn't match —
# server-side re-check; UI role-gating is cosmetic only (AUTH-04 / T-01-04).
forbidden_role_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to perform this action",
)


class InvalidLibrarianCode(Exception):
    """Raised by `auth_service.signup` when role=librarian and the supplied
    `librarian_code` does not match `settings.LIBRARIAN_SIGNUP_CODE` (or is
    missing). D-03: NO silent fallback to a student account — the router
    translates this into a 400 with the exact D-03 copy."""


class EmailAlreadyRegistered(Exception):
    """Raised by `auth_service.signup` on a duplicate email (unique
    constraint). The router translates this into a 409 with the UI-SPEC
    "already exists" copy."""


class RefreshTokenInvalid(Exception):
    """Raised by `auth_service.rotate_refresh_token` / `revoke_refresh_token`
    when the presented refresh token is missing, unknown, expired, or has
    already been rotated (and is not a reuse-detection case). The router
    translates this into a 401."""


class RefreshTokenReused(Exception):
    """Raised by `auth_service.rotate_refresh_token` when an
    already-revoked/rotated token is replayed — signals that the entire
    session family has just been revoked (reuse detection, Pattern 4). The
    router translates this into a 401."""
