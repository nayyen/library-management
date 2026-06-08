"""Wave 0 test infrastructure — shared fixtures for the backend test suite.

Provides:
  - `db_session`: a transactional, rollback-per-test AsyncSession (test
    isolation without recreating the schema between tests)
  - `async_client`: an `httpx.AsyncClient` wired to the FastAPI app via
    `ASGITransport`, with `get_db` overridden to the test session
  - `user_factory`: inserts a student or librarian user row for use in
    AUTH integration tests

`user_factory` depends on the `User` model + password-hashing helpers that
land in Plan 02 (see app/models/__init__.py placeholder comment). Until then
it raises a clear `pytest.skip` so importing this module never fails collection
— the AUTH stub tests in test_auth.py are independently marked `xfail` and do
not depend on this fixture executing successfully yet.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine
from app.dependencies.db import get_db
from app.main import app


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession bound to a connection-level transaction that is
    rolled back after the test — keeps the database clean without dropping
    and recreating tables between tests (transaction-per-test pattern).
    """
    async with engine.connect() as connection:
        await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        # Nested (SAVEPOINT) transaction so the test code's own commits don't
        # end the outer rollback-able transaction.
        nested = await connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            if nested.is_active:
                await nested.rollback()
            await connection.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient wired directly to the ASGI app, with `get_db`
    overridden to yield the per-test transactional session."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def user_factory(db_session: AsyncSession):
    """Factory fixture: `await user_factory(role="student", email=..., password=...)`
    inserts a real user row (via the now-existing `User` model + `pwdlib`
    Argon2 hashing) and returns it.

    Guarded import: the `User` model + `app.core.security` password hashing
    land in Plan 02. Until then, calling this fixture skips the test with a
    clear message rather than raising an ImportError at collection time —
    keeps `test_health_ok` collectible even if this module is imported before
    Plan 02 lands.
    """

    async def _create(
        *,
        email: str = "test.user@library.local",
        password: str = "correct horse battery staple",
        role: str = "student",
        **extra: Any,
    ):
        try:
            from app.core.security import password_hasher  # noqa: PLC0415
            from app.models.user import User  # noqa: PLC0415
        except ImportError:
            pytest.skip("user_factory requires Plan 02's User model + security module")

        user = User(
            email=email,
            hashed_password=password_hasher.hash(password),
            role=role,
            **extra,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user

    return _create


@pytest.fixture
def access_token_for():
    """Helper: `access_token_for(user)` mints a real access token (via the
    finalized `core.security.create_access_token`) so tests can authenticate
    the `async_client` as a given user without going through `/auth/login`.

    Used by `test_require_role_rejects_wrong_role` (and any future protected-
    route test) to assert AUTH-04 enforcement directly against a known user
    + role, independent of the login flow under test elsewhere.
    """

    def _mint(user: Any) -> str:
        from app.core.security import create_access_token  # noqa: PLC0415

        role = user.role.value if hasattr(user.role, "value") else user.role
        return create_access_token(user.id, role)

    return _mint
