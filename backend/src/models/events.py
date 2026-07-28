"""Event models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event type enum."""

    STEP_COMPLETE = "step_complete"
    COLLISION = "collision"
    GOAL_REACHED = "goal_reached"
    SENSOR_READING = "sensor_reading"
    STATE_CHANGE = "state_change"
    ERROR = "error"


class EventCreate(BaseModel):
    """Create event request."""

    simulation_id: int = Field(..., description="Simulation ID")
    agent_id: Optional[int] = Field(None, description="Agent ID (if applicable)")
    timestamp: float = Field(..., ge=0, description="Event timestamp (simulation time)")
    event_type: EventType = Field(..., description="Event type")
    data: Optional[Dict[str, Any]] = Field(None, description="Event-specific data")


class Event(BaseModel):
    """Event model (internal)."""

    id: int
    simulation_id: int
    agent_id: Optional[int]
    timestamp: float
    event_type: EventType
    data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class EventResponse(BaseModel):
    """Event response model (for API)."""

    id: int = Field(..., description="Event ID")
    agent_id: Optional[int] = Field(None, description="Agent ID")
    timestamp: float = Field(..., description="Simulation timestamp")
    event_type: EventType = Field(..., description="Event type")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")

    class Config:
        """Pydantic config."""

        from_attributes = True


class EventBatch(BaseModel):
    """Batch of events."""

    events: list[EventResponse] = Field(..., description="List of events")
    total: int = Field(..., description="Total event count")
    offset: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")
    has_more: bool = Field(..., description="More events available")


class SimulationSummary(BaseModel):
    """Summary statistics for simulation."""

    simulation_id: int = Field(..., description="Simulation ID")
    total_events: int = Field(..., description="Total events recorded")
    total_collisions: int = Field(..., description="Total collision events")
    goals_reached: int = Field(..., description="Agents that reached goal")
    simulation_duration: float = Field(..., description="Actual simulation duration")
    average_agent_velocity: float = Field(..., description="Average velocity across agents")
