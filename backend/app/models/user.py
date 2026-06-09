"""User model + role enum.

Single `users` table with a `role` enum column (student|librarian) — per
CLAUDE.md "Stack Patterns by Variant" (no separate admin role / per-role tables).
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken


class UserRole(str, enum.Enum):
    STUDENT = "student"
    LIBRARIAN = "librarian"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # "RefreshToken" is a string forward-reference: SQLAlchemy resolves it via
    # the shared declarative registry at mapper-configuration time (not at
    # import time), so `user.py` and `refresh_token.py` never need to import
    # each other directly — avoids a circular import. Both classes are
    # registered together by `app/models/__init__.py` before any query runs.
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
