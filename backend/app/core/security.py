"""Security primitives: Argon2 password hashing, JWT access tokens, opaque
refresh tokens.

Per 01-RESEARCH.md Patterns 2 & 3:
  - Passwords: `pwdlib.PasswordHash.recommended()` (Argon2id, NOT passlib —
    see CLAUDE.md "What NOT to Use").
  - Access tokens: short-lived `pyjwt` HS256 JWTs (`sub`, `role`, `exp`,
    `type="access"`). `decode_access_token` ALWAYS passes an explicit
    `algorithms=["HS256"]` list — never read the algorithm from the token's
    own header (T-01-ALGCONF: alg:none / HS↔RS confusion mitigation).
  - Refresh tokens: NOT JWTs. Random opaque strings (`secrets.token_urlsafe`)
    stored only as SHA-256 hex digests — high-entropy random tokens don't
    need slow/salted password-grade hashing (Pattern 3 rationale).

`leeway=10` on decode absorbs small clock-skew between containers
(RESEARCH Pitfall 7 — WSL2/Docker clock drift).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import settings

# Argon2id with pwdlib's secure recommended defaults
# ($argon2id$v=19$m=65536,t=3,p=4$...).
password_hasher = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(user_id: int, role: str) -> str:
    """Issue a short-lived stateless JWT access token.

    Claims: `sub` (user id, as a string per JWT spec convention), `role`,
    `exp`, and `type="access"` (distinguishes from any future token kinds).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode + verify a JWT access token.

    ALWAYS pass an explicit `algorithms=` allowlist — accepting whatever
    algorithm the token header claims (`alg: none`, or RS-signed tokens
    verified with the HS secret) is the canonical JWT confusion attack
    (T-01-ALGCONF). Raises `jwt.PyJWTError` on any failure (expired,
    malformed, bad signature, wrong algorithm).
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"], leeway=10)


def generate_refresh_token() -> tuple[str, str]:
    """Returns `(raw_token_for_cookie, sha256_hex_for_db_storage)`.

    The refresh token is a random opaque string — NOT a JWT — so it can be
    revoked server-side (you can delete/mark-revoked a DB row; you cannot
    "delete" a stateless JWT). Stored only as a SHA-256 hash: it's a
    high-entropy random token, not a low-entropy password, so a fast hash
    is appropriate (Argon2 would be wasteful here).
    """
    raw = secrets.token_urlsafe(48)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed
