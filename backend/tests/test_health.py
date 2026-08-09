"""Tests for health check endpoints.

/ready used to unconditionally return {"ready": True} with "checking..."
placeholders for database/cache regardless of whether either was actually
reachable. These tests verify it now performs a real check and reports a
real degraded state (503) when a dependency is down.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test /api/v1/health endpoint."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_readiness_reports_real_unavailable_cache(client: AsyncClient) -> None:
    """With no real Redis server reachable in the test environment, /ready
    must honestly report the cache as unavailable and return 503 -- not the
    old hardcoded {"ready": True}."""
    response = await client.get("/api/v1/ready")

    data = response.json()
    assert data["ready"] is False
    assert data["cache"] == "unavailable"
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_readiness_ok_when_database_and_cache_are_healthy(client: AsyncClient) -> None:
    """When both real checks succeed, /ready reports ready with 200.

    Patched without the `src.` prefix deliberately: main.py imports routers
    via `from routers import ...` (no prefix), so `routers.health` and
    `src.routers.health` are two distinct module objects. Patching the
    `src.`-prefixed one would silently miss the module the app actually runs.
    """
    with patch("routers.health.check_database", new=AsyncMock(return_value=True)), patch(
        "routers.health.check_cache", new=AsyncMock(return_value=True)
    ):
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()
    assert data == {"ready": True, "database": "ok", "cache": "ok"}


@pytest.mark.asyncio
async def test_readiness_503_when_database_down(client: AsyncClient) -> None:
    """When the database check fails, /ready must report not-ready with 503,
    regardless of cache status."""
    with patch("routers.health.check_database", new=AsyncMock(return_value=False)), patch(
        "routers.health.check_cache", new=AsyncMock(return_value=True)
    ):
        response = await client.get("/api/v1/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["ready"] is False
    assert data["database"] == "unavailable"
    assert data["cache"] == "ok"


@pytest.mark.asyncio
async def test_top_level_readiness_matches_api_v1_readiness(client: AsyncClient) -> None:
    """main.py's top-level /ready must use the same real checks, not a
    separate hardcoded stub.

    Patched as `src.main` (unlike routers.health above): conftest.py builds
    the app via `from src.main import app`, so the module object that
    actually defines this route's closure is `sys.modules["src.main"]`, not
    a separately-imported `main`.
    """
    with patch("src.main.check_database", new=AsyncMock(return_value=True)), patch(
        "src.main.check_cache", new=AsyncMock(return_value=False)
    ):
        response = await client.get("/ready")

    assert response.status_code == 503
    data = response.json()
    assert data == {"ready": False, "database": "ok", "cache": "unavailable"}


@pytest.mark.asyncio
async def test_top_level_health_check(client: AsyncClient) -> None:
    """Test top-level /health endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
