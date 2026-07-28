"""Integration tests for all API endpoints."""

import pytest
from httpx import AsyncClient

from src.models import SimulationStatus


class TestAuthAPI:
    """Authentication API integration tests."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient) -> None:
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123456",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        """Test registration fails with duplicate email."""
        email = "duplicate@example.com"
        password = "SecurePassword123456"

        # Register first time
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        # Try to register again
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login(self, client: AsyncClient) -> None:
        """Test user login."""
        email = "login@example.com"
        password = "SecurePassword123456"

        # Register
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        """Test login fails with wrong password."""
        email = "wrong@example.com"
        password = "SecurePassword123456"

        # Register
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword"},
        )

        assert response.status_code == 401


class TestSimulationAPI:
    """Simulation API integration tests."""

    @pytest.mark.asyncio
    async def test_full_simulation_workflow(self, client: AsyncClient) -> None:
        """Test complete simulation workflow: create, start, stop, delete."""
        # Create
        create_response = await client.post(
            "/api/v1/simulations",
            json={
                "name": "workflow_test",
                "num_agents": 100,
                "duration": 60.0,
            },
        )

        assert create_response.status_code == 201
        sim_id = create_response.json()["id"]

        # Get
        get_response = await client.get(f"/api/v1/simulations/{sim_id}")
        assert get_response.status_code == 200

        # Update
        update_response = await client.put(
            f"/api/v1/simulations/{sim_id}",
            json={"name": "updated_name"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "updated_name"

        # Start
        start_response = await client.post(f"/api/v1/simulations/{sim_id}/start")
        assert start_response.status_code == 202
        assert start_response.json()["status"] == SimulationStatus.RUNNING

        # Stop
        stop_response = await client.post(f"/api/v1/simulations/{sim_id}/stop")
        assert stop_response.status_code == 200
        assert stop_response.json()["status"] == SimulationStatus.CANCELLED

        # Delete
        delete_response = await client.delete(f"/api/v1/simulations/{sim_id}")
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_invalid_agent_count(self, client: AsyncClient) -> None:
        """Test validation: invalid agent count."""
        response = await client.post(
            "/api/v1/simulations",
            json={
                "name": "invalid",
                "num_agents": 0,  # Invalid
                "duration": 60.0,
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_invalid_duration(self, client: AsyncClient) -> None:
        """Test validation: invalid duration."""
        response = await client.post(
            "/api/v1/simulations",
            json={
                "name": "invalid",
                "num_agents": 100,
                "duration": 5000.0,  # > 3600
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_start_running_simulation(self, client: AsyncClient) -> None:
        """Test cannot start simulation that's already running."""
        # Create and start
        create_response = await client.post(
            "/api/v1/simulations",
            json={"name": "test", "num_agents": 100, "duration": 60.0},
        )
        sim_id = create_response.json()["id"]

        await client.post(f"/api/v1/simulations/{sim_id}/start")

        # Try to start again
        response = await client.post(f"/api/v1/simulations/{sim_id}/start")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_stop_non_running_simulation(self, client: AsyncClient) -> None:
        """Test cannot stop simulation that's not running."""
        create_response = await client.post(
            "/api/v1/simulations",
            json={"name": "test", "num_agents": 100, "duration": 60.0},
        )
        sim_id = create_response.json()["id"]

        # Try to stop without starting
        response = await client.post(f"/api/v1/simulations/{sim_id}/stop")

        assert response.status_code == 400


class TestResultsAPI:
    """Results and events API integration tests."""

    @pytest.mark.asyncio
    async def test_get_results(self, client: AsyncClient) -> None:
        """Test fetching simulation results."""
        # Create simulation
        create_response = await client.post(
            "/api/v1/simulations",
            json={"name": "test", "num_agents": 100, "duration": 60.0},
        )
        sim_id = create_response.json()["id"]

        # Get results (empty initially)
        response = await client.get(f"/api/v1/simulations/{sim_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_summary(self, client: AsyncClient) -> None:
        """Test fetching simulation summary."""
        create_response = await client.post(
            "/api/v1/simulations",
            json={"name": "test", "num_agents": 100, "duration": 60.0},
        )
        sim_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/simulations/{sim_id}/summary")

        assert response.status_code == 200
        data = response.json()
        assert "simulation_id" in data
        assert "total_events" in data
        assert "total_collisions" in data

    @pytest.mark.asyncio
    async def test_get_agents(self, client: AsyncClient) -> None:
        """Test fetching agent positions."""
        create_response = await client.post(
            "/api/v1/simulations",
            json={"name": "test", "num_agents": 100, "duration": 60.0},
        )
        sim_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/simulations/{sim_id}/agents")

        assert response.status_code == 200
        # Should be list
        assert isinstance(response.json(), list)


class TestHealthAPI:
    """Health check API tests."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient) -> None:
        """Test readiness check endpoint."""
        response = await client.get("/api/v1/ready")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "ready" in data
