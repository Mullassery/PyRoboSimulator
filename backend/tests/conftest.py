"""Pytest configuration and shared fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest

# Try to import app dependencies, but allow tests to run without them
try:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from src.main import app
    from src.db.models import Base
    from src.db.session import get_db
    HAS_APP = True
except (ImportError, ModuleNotFoundError):
    HAS_APP = False


if HAS_APP:
    # Use in-memory SQLite for testing
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    @pytest.fixture(scope="session")
    def event_loop():
        """Create event loop for async tests."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

    @pytest.fixture
    async def test_db() -> AsyncGenerator[AsyncSession, None]:
        """Create test database session.

        Yields:
            AsyncSession for test database
        """
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with async_session() as session:
            yield session

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()

    @pytest.fixture
    async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
        """Create async test client for FastAPI app.

        Args:
            test_db: Test database session

        Yields:
            AsyncClient configured to use test database
        """

        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as async_client:
            yield async_client

        app.dependency_overrides.clear()
