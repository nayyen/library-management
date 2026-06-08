"""Alembic migration environment — sync engine, async app (hybrid pattern).

Per CLAUDE.md's locked recommendation ("sync Alembic + psycopg, async app +
asyncpg") and RESEARCH Pattern 6: Alembic's runner is fundamentally
synchronous, so we build a SEPARATE sync (psycopg) engine here rather than
wrapping the app's async engine with `run_sync`. This module never touches
`app.database.engine`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings

# Import every model module BEFORE referencing Base.metadata — otherwise
# target_metadata is empty and `alembic revision --autogenerate` produces a
# no-op migration (RESEARCH Pitfall 3: "Empty Alembic autogenerate").
import app.models  # noqa: F401  (registers User + RefreshToken on Base.metadata)
from app.models.base import Base

# this is the Alembic Config object, which provides access to values within
# the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Build a SYNC url (psycopg, not asyncpg) for Alembic only.
# `.replace("%", "%%")` guards against ConfigParser's `%`-interpolation
# choking on URL-encoded special characters in the password (Pitfall 4).
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg")
config.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL to a script, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live sync (NullPool) connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # one-shot migration run — no pooling needed
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
