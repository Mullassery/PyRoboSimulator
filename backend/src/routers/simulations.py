"""Simulation endpoints (to be implemented in Task #7)."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/simulations")
async def create_simulation():
    """Create a new simulation (placeholder)."""
    return {"status": "not_implemented"}


@router.get("/simulations")
async def list_simulations():
    """List simulations (placeholder)."""
    return {"simulations": []}


@router.get("/simulations/{sim_id}")
async def get_simulation(sim_id: int):
    """Get simulation details (placeholder)."""
    return {"sim_id": sim_id, "status": "not_implemented"}
