# Import every model module here so Base.metadata is populated before Alembic
# autogenerate runs (RESEARCH Pitfall 3 — "Empty Alembic autogenerate").

from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401

__all__ = ["User", "UserRole", "RefreshToken", "PasswordResetToken"]
