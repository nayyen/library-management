"""RBAC dependency chain — `get_current_user` + `require_role`.

Copied verbatim (in shape) from 01-RESEARCH.md Pattern 1: this is the
canonical analog every later phase's protected routes will reuse
(catalog management, borrow approval, loan/fine admin, etc — see
01-PATTERNS.md "Authentication / Authorization (backend)").

`get_current_user` decodes the access token via `core.security.decode_access_token`
(which ALWAYS passes an explicit `algorithms=["HS256"]` — algorithm-confusion
mitigation lives there, not here) and loads the DB-backed `User`.
`require_role(*roles)` re-checks that DB-loaded user's role server-side —
the UI's role-based gating is purely cosmetic; this is the actual enforcement
boundary (AUTH-04 / T-01-04).
"""

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import credentials_exception, forbidden_role_exception
from app.core.security import decode_access_token
from app.dependencies.db import get_db
from app.models.user import User, UserRole

# tokenUrl is documentation-only (drives the OpenAPI "Authorize" UI) — the
# actual login endpoint is mounted at `/auth/login` via the router prefix.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the bearer access token, load the user. Any failure — missing,
    malformed, expired, wrong algorithm, or a `sub` that no longer maps to a
    user — collapses to the SAME generic 401 (`credentials_exception`,
    `WWW-Authenticate: Bearer`). Never reveal *which* check failed."""
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        # Expired / malformed / bad-signature / wrong-algorithm — all
        # collapse to the same generic 401 (never reveal which check failed).
        raise credentials_exception from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory: returns an inner dependency that yields the
    current user if their (DB-loaded, server-verified) role is one of
    `allowed_roles`, else raises 403.

    Usage: `Depends(require_role(UserRole.LIBRARIAN))` or
    `dependencies=[Depends(require_role(UserRole.LIBRARIAN))]`.
    """

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise forbidden_role_exception
        return user

    return _checker
