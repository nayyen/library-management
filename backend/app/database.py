"""Async SQLAlchemy engine, sessionmaker, and the `get_db` dependency.

Async app + sync Alembic hybrid (CLAUDE.md recommendation): this module owns
the async engine used by the running app; `alembic/env.py` builds its own
separate sync (psycopg) engine for migrations only.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an `AsyncSession` for the lifetime of a single request."""
    async with AsyncSessionLocal() as session:
        yield session
