"""Simulation models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SimulationStatus(str, Enum):
    """Simulation status enum."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationCreate(BaseModel):
    """Create simulation request."""

    name: str = Field(..., min_length=1, max_length=255, description="Simulation name")
    scenario_id: Optional[int] = Field(
        None,
        description="Scenario ID to clone from",
    )
    num_agents: int = Field(
        ...,
        ge=1,
        le=1_000_000,
        description="Number of agents (1-1M)",
    )
    duration: float = Field(
        ...,
        gt=0,
        le=3600,
        description="Simulation duration in seconds (max 1 hour)",
    )


class SimulationUpdate(BaseModel):
    """Update simulation request (only name can change)."""

    name: Optional[str] = Field(None, description="New simulation name")


class Simulation(BaseModel):
    """Simulation model (internal)."""

    id: int
    user_id: int
    scenario_id: Optional[int]
    name: str
    status: SimulationStatus
    num_agents: int
    duration: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SimulationResponse(BaseModel):
    """Simulation response model (for API)."""

    id: int = Field(..., description="Simulation ID")
    name: str = Field(..., description="Simulation name")
    status: SimulationStatus = Field(..., description="Current status")
    num_agents: int = Field(..., description="Number of agents")
    duration: float = Field(..., description="Simulation duration (seconds)")
    started_at: Optional[datetime] = Field(None, description="When simulation started")
    completed_at: Optional[datetime] = Field(None, description="When simulation completed")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        """Pydantic config."""

        from_attributes = True


class SimulationListResponse(BaseModel):
    """Paginated simulation list."""

    simulations: list[SimulationResponse] = Field(..., description="List of simulations")
    total: int = Field(..., description="Total count")
    offset: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")
    has_more: bool = Field(..., description="More items available")
