"""Password hashing (bcrypt) and JWT helpers."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib.hashers.bcrypt import BcryptHasher
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash((BcryptHasher(),))

ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return password_hash.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """Create a signed JWT with an expiration claim.

    The input dict should contain at minimum: sub (user id), peran, nama.
    The exp claim is added automatically.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT.

    Returns the payload dict on success.
    Raises jwt.PyJWTError on invalid/expired token.
    """
    return jwt.decode(
        token, settings.jwt_secret, algorithms=[ALGORITHM]
    )
