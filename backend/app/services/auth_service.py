"""Auth service layer — signup, authenticate, token issuance, refresh
rotation (with row-locked reuse detection), and session revocation.

This is the security spine: routers stay thin and call into this module
exclusively (per 01-PATTERNS "service-layer calls"). The transactional shape
of `rotate_refresh_token` is copied verbatim from 01-RESEARCH.md Pattern 4 —
`with_for_update()` is what makes concurrent-refresh races safe (Pitfall 5).
"""

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidLibrarianCode,
    RefreshTokenInvalid,
    RefreshTokenReused,
    invalid_credentials_exception,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    generate_reset_token,
    get_password_hash,
    verify_password,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole


def _refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


async def _store_refresh_token(
    db: AsyncSession, user_id: int, *, user_agent: str | None = None
) -> str:
    """Generate + persist a new refresh token row; returns the RAW token
    (the only copy that ever leaves the server — only the hash is stored)."""
    raw, hashed = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hashed,
            expires_at=_refresh_expiry(),
            user_agent=user_agent,
        )
    )
    return raw


async def issue_token_pair(
    db: AsyncSession, user: User, *, user_agent: str | None = None
) -> tuple[str, str]:
    """Create an access token + a freshly stored refresh token for `user`.

    Returns `(access_token, raw_refresh_token)`. Caller is responsible for
    committing (signup/login commit the whole operation atomically with the
    user insert / nothing-to-write respectively).
    """
    access_token = create_access_token(user.id, user.role.value)
    raw_refresh = await _store_refresh_token(db, user.id, user_agent=user_agent)
    return access_token, raw_refresh


async def signup(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: UserRole,
    librarian_code: str | None,
    user_agent: str | None = None,
) -> tuple[str, str, User]:
    """Create a new user and issue an initial token pair.

    D-01/D-02/D-03: librarian signup is gated by a single shared secret
    (`LIBRARIAN_SIGNUP_CODE`). A wrong/missing code raises
    `InvalidLibrarianCode` BEFORE any DB write — there is no silent fallback
    to a student account.
    """
    if role == UserRole.LIBRARIAN:
        if not librarian_code or librarian_code != settings.LIBRARIAN_SIGNUP_CODE:
            raise InvalidLibrarianCode

    user = User(email=email, hashed_password=get_password_hash(password), role=role)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise EmailAlreadyRegistered from exc

    access_token, raw_refresh = await issue_token_pair(db, user, user_agent=user_agent)
    await db.commit()
    await db.refresh(user)
    return access_token, raw_refresh, user


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User:
    """Verify credentials; raise the single generic
    `invalid_credentials_exception` for BOTH "no such user" and "wrong
    password" — never reveal which one failed (enumeration-safety, T-01-ENUM)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise invalid_credentials_exception
    return user


async def login(
    db: AsyncSession, *, email: str, password: str, user_agent: str | None = None
) -> tuple[str, str, User]:
    """Authenticate then issue a fresh token pair (new session)."""
    user = await authenticate(db, email=email, password=password)
    access_token, raw_refresh = await issue_token_pair(db, user, user_agent=user_agent)
    await db.commit()
    return access_token, raw_refresh, user


async def rotate_refresh_token(
    db: AsyncSession, raw_token: str, *, user_agent: str | None = None
) -> tuple[str, str, User]:
    """Validate + rotate a refresh token under a row lock (Pattern 4,
    copied verbatim in transactional shape).

    `SELECT ... FOR UPDATE` serializes concurrent refresh attempts on the
    SAME token — the second transaction blocks until the first commits, then
    observes `revoked_at IS NOT NULL` and correctly raises `RefreshTokenReused`
    instead of both succeeding (Pitfall 5: refresh-rotation races).

    Reuse detection: if the looked-up row is ALREADY revoked, this is a
    replay of a previously-rotated token — treat the whole session family as
    compromised and revoke every active session for that user.
    """
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()

    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed).with_for_update()
    result = await db.execute(stmt)
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise RefreshTokenInvalid

    if token_row.revoked_at is not None:
        await revoke_all_user_sessions(db, token_row.user_id)
        await db.commit()
        raise RefreshTokenReused

    if token_row.expires_at < datetime.now(timezone.utc):
        raise RefreshTokenInvalid

    # Rotate: mark old as revoked, mint + persist a new row, link the chain.
    token_row.revoked_at = datetime.now(timezone.utc)
    new_raw, new_hashed = generate_refresh_token()
    new_row = RefreshToken(
        user_id=token_row.user_id,
        token_hash=new_hashed,
        expires_at=_refresh_expiry(),
        user_agent=user_agent,
    )
    db.add(new_row)
    await db.flush()
    token_row.replaced_by = new_row.id
    await db.commit()

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise RefreshTokenInvalid
    new_access = create_access_token(user.id, user.role.value)
    return new_access, new_raw, user


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    """Logout (D-06): revoke ONLY the single session whose refresh token is
    presented. Other devices/sessions remain valid. Idempotent — an
    unknown/already-revoked token is treated as "already logged out", not
    an error (logout should never fail loudly)."""
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed).with_for_update()
    result = await db.execute(stmt)
    token_row = result.scalar_one_or_none()

    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def revoke_all_user_sessions(db: AsyncSession, user_id: int) -> None:
    """Revoke EVERY active (non-revoked) refresh token for a user.

    Used by: reuse-detection (a stolen-and-replayed token implies the whole
    family may be compromised) and — reused again in Plan 04 — password-reset
    completion (D-07: every old session, including a possible attacker's,
    gets logged out the moment account control is regained)."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .with_for_update()
    )
    result = await db.execute(stmt)
    for token_row in result.scalars():
        token_row.revoked_at = now


async def is_reset_token_valid(db: AsyncSession, raw_token: str) -> bool:
    """Read-only preflight: return True iff the token exists, is unused, and has not expired.
    Does NOT consume the token — safe to call on page load."""
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed)
    )
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.used_at is not None:
        return False
    now = datetime.now(timezone.utc)
    if token_row.expires_at.replace(tzinfo=timezone.utc) < now:
        return False
    return True


async def create_reset_token(db: AsyncSession, user: User) -> str:
    """Invalidate any prior unused reset tokens for the user, then create and
    persist a new hashed reset token. Returns the RAW token (to be embedded in
    the email link — never stored).

    Invalidating prior tokens prevents link accumulation: only the most-recently
    requested link is valid at any given time.
    """
    # Invalidate prior unused tokens for this user (mark them used_at = now)
    # so only one active reset token exists at a time.
    now = datetime.now(timezone.utc)
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    )
    result = await db.execute(stmt)
    for prior in result.scalars():
        prior.used_at = now

    raw, hashed = generate_reset_token()
    expires_at = now + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hashed,
            expires_at=expires_at,
        )
    )
    await db.commit()
    return raw


async def reset_password(
    db: AsyncSession,
    raw_token: str,
    new_password: str,
) -> tuple[str, str, User]:
    """Validate a password-reset token, set the new password, revoke ALL
    sessions (D-07), and issue a fresh token pair for auto-login (D-10).

    Rejects the token if: not found, already used (`used_at IS NOT NULL`),
    or past its `expires_at` (D-08). Raises `RefreshTokenInvalid` (reused
    exception type) so the router maps it to a consistent 400/401 response.
    """
    hashed = hashlib.sha256(raw_token.encode()).hexdigest()

    stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed)
    result = await db.execute(stmt)
    token_row = result.scalar_one_or_none()

    if token_row is None or token_row.used_at is not None:
        raise RefreshTokenInvalid

    now = datetime.now(timezone.utc)
    if token_row.expires_at.replace(tzinfo=timezone.utc) < now:
        raise RefreshTokenInvalid

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise RefreshTokenInvalid

    # Set new password hash.
    user.hashed_password = get_password_hash(new_password)
    # Mark token consumed (single-use, D-08).
    token_row.used_at = now

    # Revoke ALL existing sessions — session fixation defence (D-07).
    await revoke_all_user_sessions(db, user.id)

    # Issue a fresh token pair (auto-login, D-10).
    access_token, raw_refresh = await issue_token_pair(db, user)
    await db.commit()
    await db.refresh(user)

    return access_token, raw_refresh, user
