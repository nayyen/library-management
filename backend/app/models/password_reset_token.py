"""PasswordResetToken model — single-use, hashed, time-limited reset tokens.

Mirrors the RefreshToken hashed-token / nullable-timestamp pattern:
  - `token_hash` (not `token`) — raw token goes in the email link only; only
    the SHA-256 hex digest is stored (same rationale as refresh tokens).
  - `used_at` nullable timestamp (single-use marker) — preserves WHEN the
    token was consumed (audit trail), avoids a boolean that loses timing info.
  - `expires_at` — 1-hour TTL enforced at validation time in the service layer
    (D-08).
  - `ondelete="CASCADE"` — reset tokens are meaningless without their user;
    clean up automatically if the user row is ever deleted.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="password_reset_tokens")
