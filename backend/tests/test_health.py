"""Real, passing test proving the fixture chain + app boot work now.

Everything else in Wave 0 (AUTH stubs) is xfail until Plans 02-04 land —
this is the one test that must be green from day one.
"""

from httpx import AsyncClient


async def test_health_ok(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
