"""Tests for simulation endpoints."""

import pytest
from httpx import AsyncClient

from src.models import SimulationStatus


@pytest.mark.asyncio
async def test_create_simulation(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating a simulation."""
    response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_sim"
    assert data["num_agents"] == 100
    assert data["duration"] == 60.0
    assert data["status"] == SimulationStatus.CREATED


@pytest.mark.asyncio
async def test_create_simulation_requires_authentication(client: AsyncClient) -> None:
    """Creating a simulation without a token must be rejected, not silently
    attributed to a hardcoded user."""
    response = await client.post(
        "/api/v1/simulations",
        json={"name": "test_sim", "num_agents": 100, "duration": 60.0},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_simulation_rejects_invalid_token(client: AsyncClient) -> None:
    """A malformed/invalid bearer token must be rejected."""
    response = await client.post(
        "/api/v1/simulations",
        json={"name": "test_sim", "num_agents": 100, "duration": 60.0},
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_created_simulation_is_owned_by_the_real_authenticated_user(
    client: AsyncClient, auth_headers: dict
) -> None:
    """The simulation's user_id must come from the real auth context, not a
    hardcoded placeholder -- verified by checking two different users get
    two different owners."""
    await client.post("/api/v1/auth/register", json={"email": "other@example.com", "password": "another-long-password"})
    other_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "another-long-password"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp1 = await client.post(
        "/api/v1/simulations",
        json={"name": "sim_a", "num_agents": 1, "duration": 1.0},
        headers=auth_headers,
    )
    resp2 = await client.post(
        "/api/v1/simulations",
        json={"name": "sim_b", "num_agents": 1, "duration": 1.0},
        headers=other_headers,
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201

    # Each user only sees their own simulation.
    list1 = (await client.get("/api/v1/simulations", headers=auth_headers)).json()
    list2 = (await client.get("/api/v1/simulations", headers=other_headers)).json()

    assert [s["name"] for s in list1["simulations"]] == ["sim_a"]
    assert [s["name"] for s in list2["simulations"]] == ["sim_b"]


@pytest.mark.asyncio
async def test_create_simulation_invalid_agents(client: AsyncClient, auth_headers: dict) -> None:
    """Test creating simulation with invalid agent count.

    SimulationCreate's own Field(ge=1, le=1_000_000) constraint rejects this
    at the Pydantic/FastAPI validation layer (422) before the handler's own
    manual range check ever runs.
    """
    response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 2_000_000,  # Too many
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_simulations(client: AsyncClient, auth_headers: dict) -> None:
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
            headers=auth_headers,
        )

    # List them
    response = await client.get("/api/v1/simulations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["simulations"]) == 2


@pytest.mark.asyncio
async def test_list_simulations_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/simulations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_simulation(client: AsyncClient, auth_headers: dict) -> None:
    """Test getting simulation details."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    sim_id = create_response.json()["id"]

    # Get it
    response = await client.get(f"/api/v1/simulations/{sim_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sim_id
    assert data["name"] == "test_sim"


@pytest.mark.asyncio
async def test_get_simulation_owned_by_another_user_is_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    """A user must not be able to read another user's simulation by ID."""
    create_response = await client.post(
        "/api/v1/simulations",
        json={"name": "test_sim", "num_agents": 100, "duration": 60.0},
        headers=auth_headers,
    )
    sim_id = create_response.json()["id"]

    await client.post("/api/v1/auth/register", json={"email": "intruder@example.com", "password": "another-long-password"})
    intruder_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "intruder@example.com", "password": "another-long-password"},
    )
    intruder_headers = {"Authorization": f"Bearer {intruder_login.json()['access_token']}"}

    response = await client.get(f"/api/v1/simulations/{sim_id}", headers=intruder_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_simulation(client: AsyncClient, auth_headers: dict) -> None:
    """Test starting a simulation."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    sim_id = create_response.json()["id"]

    # Start it
    response = await client.post(f"/api/v1/simulations/{sim_id}/start", headers=auth_headers)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == SimulationStatus.RUNNING
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_stop_simulation(client: AsyncClient, auth_headers: dict) -> None:
    """Test stopping a simulation."""
    # Create & start simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    sim_id = create_response.json()["id"]

    await client.post(f"/api/v1/simulations/{sim_id}/start", headers=auth_headers)

    # Stop it
    response = await client.post(f"/api/v1/simulations/{sim_id}/stop", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == SimulationStatus.CANCELLED


@pytest.mark.asyncio
async def test_delete_simulation(client: AsyncClient, auth_headers: dict) -> None:
    """Test deleting a simulation."""
    # Create simulation
    create_response = await client.post(
        "/api/v1/simulations",
        json={
            "name": "test_sim",
            "num_agents": 100,
            "duration": 60.0,
        },
        headers=auth_headers,
    )

    sim_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/v1/simulations/{sim_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/simulations/{sim_id}", headers=auth_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_simulation_owned_by_another_user_is_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    """A user must not be able to delete another user's simulation by ID."""
    create_response = await client.post(
        "/api/v1/simulations",
        json={"name": "test_sim", "num_agents": 100, "duration": 60.0},
        headers=auth_headers,
    )
    sim_id = create_response.json()["id"]

    await client.post("/api/v1/auth/register", json={"email": "intruder2@example.com", "password": "another-long-password"})
    intruder_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "intruder2@example.com", "password": "another-long-password"},
    )
    intruder_headers = {"Authorization": f"Bearer {intruder_login.json()['access_token']}"}

    response = await client.delete(f"/api/v1/simulations/{sim_id}", headers=intruder_headers)
    assert response.status_code == 404

    # The simulation must still exist for its real owner.
    still_there = await client.get(f"/api/v1/simulations/{sim_id}", headers=auth_headers)
    assert still_there.status_code == 200
