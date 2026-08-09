"""Simulation management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models import (
    SimulationCreate,
    SimulationListResponse,
    SimulationResponse,
    SimulationStatus,
    SimulationUpdate,
)
from src.services.auth import get_current_user_id

router = APIRouter(prefix="/simulations", tags=["Simulations"])

# In-memory storage for demo (Task #11 will use database)
simulations_db: dict[int, dict] = {}
next_sim_id = 1


def _get_owned_simulation(sim_id: int, user_id: int) -> dict:
    """Look up a simulation, scoped to its owner.

    A simulation belonging to another user is reported as 404 rather than 403
    so requests can't be used to enumerate other users' simulation IDs.
    """
    sim = simulations_db.get(sim_id)
    if sim is None or sim["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return sim


@router.post("", response_model=SimulationResponse, status_code=201)
async def create_simulation(
    req: SimulationCreate,
    user_id: int = Depends(get_current_user_id),
) -> SimulationResponse:
    """Create a new simulation.

    Request body:
    - name: Simulation name (required)
    - scenario_id: Scenario to clone from (optional)
    - num_agents: Number of agents (1-1,000,000)
    - duration: Simulation duration in seconds (max 3600)

    Returns:
        Newly created simulation with ID and status 'created'

    Raises:
        401: Missing or invalid authentication
        400: Invalid request (bad agent count, duration, etc.)
        409: Duplicate simulation name
    """
    global next_sim_id

    if req.num_agents < 1 or req.num_agents > 1_000_000:
        raise HTTPException(
            status_code=400,
            detail="num_agents must be between 1 and 1,000,000",
        )

    if req.duration <= 0 or req.duration > 3600:
        raise HTTPException(
            status_code=400,
            detail="duration must be between 0 and 3600 seconds",
        )

    sim_id = next_sim_id
    next_sim_id += 1

    sim = {
        "id": sim_id,
        "user_id": user_id,
        "scenario_id": req.scenario_id,
        "name": req.name,
        "status": SimulationStatus.CREATED,
        "num_agents": req.num_agents,
        "duration": req.duration,
        "started_at": None,
        "completed_at": None,
        "created_at": "2024-07-29T00:00:00",
        "updated_at": "2024-07-29T00:00:00",
    }

    simulations_db[sim_id] = sim
    return SimulationResponse(**sim)


@router.get("", response_model=SimulationListResponse)
async def list_simulations(
    limit: int = Query(20, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[SimulationStatus] = Query(None),
    user_id: int = Depends(get_current_user_id),
) -> SimulationListResponse:
    """List the authenticated user's simulations (paginated).

    Query parameters:
    - limit: Items per page (1-1000, default 20)
    - offset: Skip N items (default 0)
    - status: Filter by status (created, running, completed, failed, cancelled)

    Returns:
        Paginated list of simulations belonging to the authenticated user

    Raises:
        401: Missing or invalid authentication
    """
    # Scope to the authenticated user, then filter by status if provided
    filtered = [s for s in simulations_db.values() if s["user_id"] == user_id]
    if status:
        filtered = [s for s in filtered if s["status"] == status]

    # Convert to list and sort by created_at descending
    all_sims = sorted(filtered, key=lambda s: s["created_at"], reverse=True)

    # Paginate
    total = len(all_sims)
    sims = all_sims[offset : offset + limit]

    return SimulationListResponse(
        simulations=[SimulationResponse(**s) for s in sims],
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
    )


@router.get("/{sim_id}", response_model=SimulationResponse)
async def get_simulation(
    sim_id: int, user_id: int = Depends(get_current_user_id)
) -> SimulationResponse:
    """Get simulation details by ID.

    Args:
        sim_id: Simulation ID

    Returns:
        Simulation object with all fields

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
    """
    sim = _get_owned_simulation(sim_id, user_id)
    return SimulationResponse(**sim)


@router.put("/{sim_id}", response_model=SimulationResponse)
async def update_simulation(
    sim_id: int,
    req: SimulationUpdate,
    user_id: int = Depends(get_current_user_id),
) -> SimulationResponse:
    """Update simulation (only name can be changed).

    Args:
        sim_id: Simulation ID
        req: Update request with new name

    Returns:
        Updated simulation

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
        400: Cannot update running simulation
    """
    sim = _get_owned_simulation(sim_id, user_id)

    if sim["status"] == SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot update running simulation",
        )

    if req.name:
        sim["name"] = req.name

    return SimulationResponse(**sim)


@router.delete("/{sim_id}", status_code=204)
async def delete_simulation(
    sim_id: int, user_id: int = Depends(get_current_user_id)
) -> None:
    """Delete simulation by ID.

    Args:
        sim_id: Simulation ID

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
        400: Cannot delete running simulation
    """
    sim = _get_owned_simulation(sim_id, user_id)

    if sim["status"] == SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running simulation",
        )

    del simulations_db[sim_id]


@router.post("/{sim_id}/start", response_model=SimulationResponse, status_code=202)
async def start_simulation(
    sim_id: int, user_id: int = Depends(get_current_user_id)
) -> SimulationResponse:
    """Start simulation execution.

    Args:
        sim_id: Simulation ID

    Returns:
        Simulation with status changed to 'running'

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
        400: Simulation already running or completed
    """
    sim = _get_owned_simulation(sim_id, user_id)

    if sim["status"] in [SimulationStatus.RUNNING, SimulationStatus.COMPLETED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start simulation with status: {sim['status']}",
        )

    sim["status"] = SimulationStatus.RUNNING
    sim["started_at"] = "2024-07-29T00:01:00"

    return SimulationResponse(**sim)


@router.post("/{sim_id}/stop", response_model=SimulationResponse)
async def stop_simulation(
    sim_id: int, user_id: int = Depends(get_current_user_id)
) -> SimulationResponse:
    """Stop simulation execution.

    Args:
        sim_id: Simulation ID

    Returns:
        Simulation with status changed to 'cancelled'

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
        400: Simulation not running
    """
    sim = _get_owned_simulation(sim_id, user_id)

    if sim["status"] != SimulationStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Simulation is not running",
        )

    sim["status"] = SimulationStatus.CANCELLED
    sim["completed_at"] = "2024-07-29T00:02:00"

    return SimulationResponse(**sim)


@router.get("/{sim_id}/status", response_model=dict)
async def get_simulation_status(
    sim_id: int, user_id: int = Depends(get_current_user_id)
) -> dict:
    """Get simulation status.

    Args:
        sim_id: Simulation ID

    Returns:
        Status and progress information

    Raises:
        401: Missing or invalid authentication
        404: Simulation not found (or not owned by the authenticated user)
    """
    sim = _get_owned_simulation(sim_id, user_id)

    return {
        "id": sim["id"],
        "status": sim["status"],
        "progress": 0.0 if sim["status"] == SimulationStatus.CREATED else 0.5,
        "events_recorded": 0,
        "errors": [],
    }
