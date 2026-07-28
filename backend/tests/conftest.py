"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def app_client():
    """Alternative fixture name for test client."""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        yield async_client
