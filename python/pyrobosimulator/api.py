"""FastAPI backend for PyRoboSimulator Phase 0 PoC."""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from .schemas import WorldSpec
from .world_gen import WorldGenerator

logger = logging.getLogger(__name__)

# Global state for loaded worlds (in memory for PoC)
_loaded_worlds: Dict[str, WorldSpec] = {}
_sensor_outputs: Dict[str, Dict[str, Any]] = {}


class GenerateWorldRequest(BaseModel):
    """Request to generate a world from NLP prompt."""
    prompt: str = Field(..., description="Natural language description of world")
    reference_world_id: Optional[str] = Field(
        None, description="Optional existing world to extend"
    )


class LoadWorldRequest(BaseModel):
    """Request to load a world spec."""
    spec: WorldSpec
    world_id: Optional[str] = Field(None, description="Unique identifier for this world")


class GenerateWorldResponse(BaseModel):
    """Response from world generation."""
    world_id: str
    spec: WorldSpec
    generated_at: str


class LoadWorldResponse(BaseModel):
    """Response from world load."""
    world_id: str
    status: str
    message: str


class SensorDataResponse(BaseModel):
    """Response with sensor data."""
    sensor_type: str
    world_id: str
    timestamp: str
    data_path: Optional[str] = None
    preview: Optional[Dict[str, Any]] = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="PyRoboSimulator Phase 0 PoC API",
        description="World generation and sensor simulation API",
        version="0.1.0",
    )

    world_gen = WorldGenerator()
    output_dir = Path(os.getenv("PYROBO_OUTPUT_DIR", "/tmp/pyrobo_sensor_output"))
    output_dir.mkdir(parents=True, exist_ok=True)

    @app.post("/api/v1/generate-world", response_model=GenerateWorldResponse)
    def generate_world(request: GenerateWorldRequest) -> GenerateWorldResponse:
        """Generate world specification from NLP prompt.

        This endpoint uses Claude Sonnet 5 with extended thinking to create
        a complete world specification (lighting, materials, objects, weather, etc.)
        from a natural language description.
        """
        try:
            logger.info(f"Generating world from prompt: {request.prompt[:100]}...")

            reference_spec = None
            if request.reference_world_id:
                if request.reference_world_id not in _loaded_worlds:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Reference world not found: {request.reference_world_id}",
                    )
                reference_spec = _loaded_worlds[request.reference_world_id]

            spec = world_gen.generate(request.prompt, reference_spec)

            world_id = spec.metadata.get("world_id") or datetime.now().isoformat()
            spec.metadata["world_id"] = world_id
            _loaded_worlds[world_id] = spec

            return GenerateWorldResponse(
                world_id=world_id,
                spec=spec,
                generated_at=datetime.now().isoformat(),
            )

        except ValueError as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/api/v1/load-world", response_model=LoadWorldResponse)
    def load_world(request: LoadWorldRequest) -> LoadWorldResponse:
        """Load a world specification for rendering.

        This endpoint accepts a complete world spec and prepares it for UE5 rendering.
        The spec can come from /generate-world or be provided directly.
        """
        try:
            world_id = request.world_id or datetime.now().isoformat()
            _loaded_worlds[world_id] = request.spec

            world_dir = output_dir / world_id
            world_dir.mkdir(parents=True, exist_ok=True)

            spec_path = world_dir / "world_spec.json"
            with open(spec_path, "w") as f:
                json.dump(request.spec.model_dump(), f, indent=2)

            logger.info(f"World loaded: {world_id}")

            return LoadWorldResponse(
                world_id=world_id,
                status="loaded",
                message=f"World ready for rendering at {spec_path}",
            )

        except Exception as e:
            logger.error(f"Load failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/sensors/{world_id}/{sensor_type}")
    def get_sensor_data(
        world_id: str,
        sensor_type: str,
        frame: int = 0,
    ) -> SensorDataResponse:
        """Get sensor output for a world.

        Sensor types: rgb, depth, lidar, thermal

        In Phase 0 PoC, this endpoint returns placeholder data with file paths.
        Week 3 will implement actual sensor capture from UE5.
        """
        if world_id not in _loaded_worlds:
            raise HTTPException(status_code=404, detail=f"World not found: {world_id}")

        if sensor_type not in ["rgb", "depth", "lidar", "thermal"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sensor type: {sensor_type}. Use: rgb, depth, lidar, thermal",
            )

        world_spec = _loaded_worlds[world_id]

        world_dir = output_dir / world_id
        world_dir.mkdir(parents=True, exist_ok=True)

        if sensor_type == "rgb":
            filename = f"frame_{frame:04d}.png"
            data_path = str(world_dir / "rgb" / filename)
            preview = {
                "resolution": [
                    world_spec.rendering.resolution_width,
                    world_spec.rendering.resolution_height,
                ],
                "format": "png",
                "fps": world_spec.rendering.fps,
            }

        elif sensor_type == "depth":
            filename = f"frame_{frame:04d}.npy"
            data_path = str(world_dir / "depth" / filename)
            preview = {
                "format": "npy",
                "dtype": "float32",
                "shape": [
                    world_spec.rendering.resolution_height,
                    world_spec.rendering.resolution_width,
                ],
            }

        elif sensor_type == "lidar":
            filename = f"frame_{frame:04d}.pcd"
            data_path = str(world_dir / "lidar" / filename)
            preview = {
                "format": "pcd",
                "channels": world_spec.sensors.lidar_channels,
                "range_max": world_spec.sensors.lidar_range_max,
            }

        else:  # thermal
            filename = f"frame_{frame:04d}.npy"
            data_path = str(world_dir / "thermal" / filename)
            preview = {
                "format": "npy",
                "dtype": "float32",
                "temperature_range_celsius": [-20, 60],
            }

        return SensorDataResponse(
            sensor_type=sensor_type,
            world_id=world_id,
            timestamp=datetime.now().isoformat(),
            data_path=data_path,
            preview=preview,
        )

    @app.get("/api/v1/worlds/{world_id}")
    def get_world(world_id: str) -> Dict[str, Any]:
        """Get loaded world specification."""
        if world_id not in _loaded_worlds:
            raise HTTPException(status_code=404, detail=f"World not found: {world_id}")
        return _loaded_worlds[world_id].model_dump()

    @app.get("/api/v1/health")
    def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "pyrobosimulator-phase0"}

    @app.get("/")
    def root() -> Dict[str, str]:
        """Root endpoint."""
        return {
            "service": "PyRoboSimulator Phase 0 PoC",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
