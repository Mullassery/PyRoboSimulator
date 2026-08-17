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

    @pytest.fixture(autouse=True)
    def reset_demo_state():
        """Reset the in-memory demo stores between tests.

        routers.auth.users_db / routers.simulations.simulations_db are plain
        module-level globals (the real database wiring is tracked separately),
        so without a reset they leak state and make tests order-dependent.

        Imported without the `src.` prefix deliberately: main.py itself does
        `from routers import auth, simulations, ...` (no prefix), and since
        both `backend/` and `backend/src/` end up on sys.path, `routers.auth`
        and `src.routers.auth` are two distinct module objects with two
        distinct `users_db` dicts. Resetting the `src.`-prefixed copy would
        silently leave the app's real, running copy never reset.
        """
        from routers import auth as auth_router
        from routers import simulations as simulations_router

        auth_router.users_db.clear()
        auth_router.next_user_id = 1
        simulations_router.simulations_db.clear()
        simulations_router.next_sim_id = 1

        yield

        auth_router.users_db.clear()
        auth_router.next_user_id = 1
        simulations_router.simulations_db.clear()
        simulations_router.next_sim_id = 1

    @pytest.fixture
    async def client(
        test_db: AsyncSession, reset_demo_state
    ) -> AsyncGenerator[AsyncClient, None]:
        """Create async test client for FastAPI app.

        Args:
            test_db: Test database session
            reset_demo_state: Ensures the in-memory demo stores are reset
                before this fixture builds the client (explicit dependency,
                not just autouse, so ordering relative to `client` is guaranteed)

        Yields:
            AsyncClient configured to use test database
        """

        async def override_get_db():
            yield test_db

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(app=app, base_url="http://test") as async_client:
            yield async_client

        app.dependency_overrides.clear()

    @pytest.fixture
    async def auth_headers(client: AsyncClient) -> dict:
        """Register and log in a real test user; return real Bearer auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": "tester@example.com", "password": "correct-horse-battery-staple"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "tester@example.com", "password": "correct-horse-battery-staple"},
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
