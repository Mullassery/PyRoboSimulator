"""Tests for simulation endpoints."""

import pytest
from httpx import AsyncClient

from src.models import SimulationStatus


@pytest.mark.asyncio
async def test_create_simulation(client: AsyncClient) -> None:
    """Test creating a simulation."""
    response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_sim"
    assert data["num_agents"] == 100
    assert data["duration"] == 60.0
    assert data["status"] == SimulationStatus.CREATED


@pytest.mark.asyncio
async def test_create_simulation_invalid_agents(client: AsyncClient) -> None:
    """Test creating simulation with invalid agent count."""
    response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 2_000_000,  # Too many
            "duration": 60.0,
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_simulations(client: AsyncClient) -> None:
    """Test listing simulations."""
    # Create two simulations
    for i in range(2):
        await client.post(
            "/api/v1/simulations",
            json={
                "name": f"sim_{i}",
                "num_agents": 100,
                "duration": 60.0,
            },
        )

    # List them
    response = await client.get("/api/v1/simulations")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["simulations"]) == 2


@pytest.mark.asyncio
async def test_get_simulation(client: AsyncClient) -> None:
    """Test getting simulation details."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
    )

    sim_id = create_response.json()["id"]

    # Get it
    response = await client.get(f"/api/v1/simulations/{sim_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sim_id
    assert data["name"] == "test_sim"


@pytest.mark.asyncio
async def test_start_simulation(client: AsyncClient) -> None:
    """Test starting a simulation."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
    )

    sim_id = create_response.json()["id"]

    # Start it
    response = await client.post(f"/api/v1/simulations/{sim_id}/start")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == SimulationStatus.RUNNING
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_stop_simulation(client: AsyncClient) -> None:
    """Test stopping a simulation."""
    # Create & start simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
    )

    sim_id = create_response.json()["id"]

    await client.post(f"/api/v1/simulations/{sim_id}/start")

    # Stop it
    response = await client.post(f"/api/v1/simulations/{sim_id}/stop")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == SimulationStatus.CANCELLED


@pytest.mark.asyncio
async def test_delete_simulation(client: AsyncClient) -> None:
    """Test deleting a simulation."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
    )

    sim_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/v1/simulations/{sim_id}")

    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/simulations/{sim_id}")
    assert get_response.status_code == 404
