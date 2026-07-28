"""Agent models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent type enum."""

    VEHICLE = "vehicle"
    PEDESTRIAN = "pedestrian"
    ROBOT = "robot"
    OBSTACLE = "obstacle"


class Vector3(BaseModel):
    """3D vector (position or velocity)."""

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate")


class AgentState(BaseModel):
    """Current state of an agent."""

    position: Vector3 = Field(..., description="Agent position")
    velocity: Vector3 = Field(..., description="Agent velocity vector")


class AgentCreate(BaseModel):
    """Create agent request."""

    simulation_id: int = Field(..., description="Simulation ID")
    agent_type: AgentType = Field(default=AgentType.VEHICLE, description="Agent type")
    position: Vector3 = Field(..., description="Initial position")
    velocity: Vector3 = Field(
        default_factory=lambda: Vector3(x=0.0, y=0.0, z=0.0),
        description="Initial velocity",
    )


class Agent(BaseModel):
    """Agent model (internal)."""

    id: int
    simulation_id: int
    agent_type: AgentType
    position_x: float
    position_y: float
    position_z: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    created_at: datetime

    def to_state(self) -> AgentState:
        """Convert to AgentState."""
        return AgentState(
            position=Vector3(x=self.position_x, y=self.position_y, z=self.position_z),
            velocity=Vector3(x=self.velocity_x, y=self.velocity_y, z=self.velocity_z),
        )

    class Config:
        """Pydantic config."""

        from_attributes = True


class AgentResponse(BaseModel):
    """Agent response model (for API)."""

    id: int = Field(..., description="Agent ID")
    agent_type: AgentType = Field(..., description="Agent type")
    position: Vector3 = Field(..., description="Current position")
    velocity: Vector3 = Field(..., description="Current velocity")
    created_at: datetime = Field(..., description="Creation time")

    class Config:
        """Pydantic config."""

        from_attributes = True
