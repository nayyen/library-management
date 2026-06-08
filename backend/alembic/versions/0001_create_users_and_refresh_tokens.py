"""create users and refresh_tokens

Revision ID: 0001
Revises:
Create Date: 2026-06-08

Hand-authored (Docker/Postgres unavailable in this sandbox for
`alembic revision --autogenerate` — see 01-RESEARCH.md "Environment
Availability"). Mirrors the SQLAlchemy 2.0 model shapes in
app/models/user.py and app/models/refresh_token.py exactly:
  - `user_role` Postgres ENUM (student|librarian)
  - `users` table (email unique+indexed, hashed_password, role, created_at)
  - `refresh_tokens` table (token_hash unique+indexed, expires_at,
    revoked_at nullable timestamp, replaced_by self-FK, user_agent,
    created_at) + composite index ix_refresh_tokens_user_active
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role_enum = sa.Enum("student", "librarian", name="user_role")


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("student", "librarian", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table("refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["replaced_by"], ["refresh_tokens.id"]),
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_refresh_tokens_user_active", "refresh_tokens", ["user_id", "revoked_at"]
    )


def downgrade() -> None:
    # FK-safe order: refresh_tokens (child) before users (parent); enum last.
    op.drop_index("ix_refresh_tokens_user_active", table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    user_role_enum.drop(op.get_bind(), checkfirst=True)
