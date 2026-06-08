"""RefreshToken model — opaque, hashed, revocable session tokens.

Per 01-RESEARCH.md "User & RefreshToken SQLAlchemy 2.0 models" + schema-design
rationale:
  - `token_hash` (not `token`) — never store the raw bearer credential.
  - `revoked_at` nullable timestamp (NOT a boolean `is_revoked`) — preserves
    *when* revocation happened (audit trail + reuse-detection check).
  - `replaced_by` self-referencing FK — builds the rotation chain.
  - Composite index `(user_id, revoked_at)` — supports "find active sessions
    for user X" (D-06 logout, D-07 reset-completion mass-revocation).
  - `user_agent` — optional session metadata (Claude's discretion per CONTEXT).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[int | None] = mapped_column(
        ForeignKey("refresh_tokens.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (Index("ix_refresh_tokens_user_active", "user_id", "revoked_at"),)
