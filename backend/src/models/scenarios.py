"""Scenario models."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WorldConfig(BaseModel):
    """World configuration for scenario."""

    bounds: Dict[str, float] = Field(
        ...,
        description="World bounds: {x_min, x_max, y_min, y_max}",
    )
    grid_size: float = Field(default=50.0, description="Grid cell size in meters")
    spawn_zones: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="Zones where agents can spawn",
    )
    obstacles: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="Static obstacles",
    )
    weather: str = Field(default="sunny", description="Weather condition")
    time_of_day: str = Field(default="noon", description="Time of day")


class ScenarioCreate(BaseModel):
    """Create scenario request."""

    name: str = Field(..., min_length=1, max_length=255, description="Scenario name")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Scenario description",
    )
    world_config: WorldConfig = Field(..., description="World configuration")
    published: bool = Field(default=False, description="Publish scenario to community")


class ScenarioUpdate(BaseModel):
    """Update scenario request."""

    name: Optional[str] = Field(None, description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    world_config: Optional[WorldConfig] = Field(None, description="World configuration")
    published: Optional[bool] = Field(None, description="Publish to community")


class Scenario(BaseModel):
    """Scenario model (internal)."""

    id: int
    name: str
    description: Optional[str]
    world_config: Dict[str, Any]
    published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ScenarioResponse(BaseModel):
    """Scenario response model (for API)."""

    id: int = Field(..., description="Scenario ID")
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    world_config: WorldConfig = Field(..., description="World configuration")
    published: bool = Field(..., description="Published status")
    created_at: datetime = Field(..., description="Creation time")

    class Config:
        """Pydantic config."""

        from_attributes = True
