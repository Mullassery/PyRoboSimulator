"""World streaming service for UE5 synchronization.

Handles serialization and streaming of world geometry, obstacles,
and dynamic objects to UE5 with chunking and optimization.
"""

import asyncio
import json
import logging
import struct
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Vector3:
    """3D vector for serialization."""

    x: float
    y: float
    z: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y, "z": self.z}

    def to_bytes(self) -> bytes:
        """Serialize to binary format (12 bytes)."""
        return struct.pack("<fff", self.x, self.y, self.z)

    @staticmethod
    def from_bytes(data: bytes) -> "Vector3":
        """Deserialize from binary format."""
        x, y, z = struct.unpack("<fff", data[:12])
        return Vector3(x, y, z)


@dataclass
class Mesh:
    """Triangle mesh definition."""

    vertices: List[Vector3]  # 3D positions
    indices: List[int]  # Triangle indices
    material: str = "default"  # Material name
    collision_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "vertices": [v.to_dict() for v in self.vertices],
            "indices": self.indices,
            "material": self.material,
            "collision_enabled": self.collision_enabled,
        }

    def vertex_count(self) -> int:
        """Get vertex count."""
        return len(self.vertices)

    def triangle_count(self) -> int:
        """Get triangle count."""
        return len(self.indices) // 3

    def memory_size(self) -> int:
        """Estimate memory size in bytes."""
        vertex_bytes = len(self.vertices) * 12  # 3 floats per vertex
        index_bytes = len(self.indices) * 4  # 4 bytes per index
        return vertex_bytes + index_bytes


@dataclass
class Obstacle:
    """Static obstacle definition."""

    id: int
    position: Vector3
    size: Vector3  # Width, height, depth for box obstacles
    rotation: float = 0.0  # Rotation around Z axis (radians)
    mesh: Optional[Mesh] = None
    collision_type: str = "box"  # box, mesh, capsule
    material: str = "concrete"
    dynamic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "id": self.id,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "rotation": self.rotation,
            "collision_type": self.collision_type,
            "material": self.material,
            "dynamic": self.dynamic,
        }
        if self.mesh:
            result["mesh"] = self.mesh.to_dict()
        return result

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get AABB bounds (x_min, x_max, y_min, y_max)."""
        half_width = self.size.x / 2
        half_depth = self.size.y / 2
        return (
            self.position.x - half_width,
            self.position.x + half_width,
            self.position.y - half_depth,
            self.position.y + half_depth,
        )


@dataclass
class WorldChunk:
    """A chunk of the world (500m × 500m)."""

    chunk_x: int  # Chunk grid coordinate
    chunk_y: int  # Chunk grid coordinate
    chunk_size: float = 500.0  # Size in meters
    obstacles: List[Obstacle] = None
    dynamic_objects: List[Dict[str, Any]] = None
    terrain_data: Optional[np.ndarray] = None  # Height map if available
    lod_level: int = 0  # Level of detail (0=full, 1=simplified, 2=very simple)

    def __post_init__(self):
        """Initialize default values."""
        if self.obstacles is None:
            self.obstacles = []
        if self.dynamic_objects is None:
            self.dynamic_objects = []

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get chunk world bounds."""
        x_min = self.chunk_x * self.chunk_size
        x_max = x_min + self.chunk_size
        y_min = self.chunk_y * self.chunk_size
        y_max = y_min + self.chunk_size
        return (x_min, x_max, y_min, y_max)

    def to_dict(self, include_terrain: bool = False) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "chunk_x": self.chunk_x,
            "chunk_y": self.chunk_y,
            "chunk_size": self.chunk_size,
            "lod_level": self.lod_level,
            "obstacles": [obs.to_dict() for obs in self.obstacles],
            "dynamic_objects": self.dynamic_objects,
            "obstacle_count": len(self.obstacles),
            "dynamic_object_count": len(self.dynamic_objects),
        }
        if include_terrain and self.terrain_data is not None:
            result["terrain_data"] = self.terrain_data.tolist()
        return result

    def memory_size(self) -> int:
        """Estimate memory size in bytes."""
        size = 0
        for obs in self.obstacles:
            if obs.mesh:
                size += obs.mesh.memory_size()
            else:
                size += 100  # Estimate for obstacle metadata
        size += len(self.dynamic_objects) * 200  # Dynamic objects
        if self.terrain_data is not None:
            size += self.terrain_data.nbytes
        return size


class WorldStreamingService:
    """Service for streaming world geometry to UE5."""

    def __init__(self, world_size: float = 2000.0, chunk_size: float = 500.0):
        """Initialize world streaming service.

        Args:
            world_size: Total world size in meters
            chunk_size: Individual chunk size in meters
        """
        self.world_size = world_size
        self.chunk_size = chunk_size
        self.num_chunks_per_side = int(world_size / chunk_size)
        self.chunks: Dict[Tuple[int, int], WorldChunk] = {}
        self.obstacle_id_counter = 0
        self.cache_enabled = True
        self.chunk_cache: Dict[Tuple[int, int], bytes] = {}

    def create_box_obstacle(
        self,
        position: Vector3,
        size: Vector3,
        material: str = "concrete",
        rotation: float = 0.0,
        dynamic: bool = False,
    ) -> Obstacle:
        """Create a box obstacle.

        Args:
            position: Center position
            size: Box dimensions (width, height, depth)
            material: Material type
            rotation: Rotation around Z axis in radians
            dynamic: Whether obstacle moves

        Returns:
            Obstacle instance
        """
        self.obstacle_id_counter += 1
        return Obstacle(
            id=self.obstacle_id_counter,
            position=position,
            size=size,
            rotation=rotation,
            collision_type="box",
            material=material,
            dynamic=dynamic,
        )

    def create_mesh_obstacle(
        self,
        position: Vector3,
        mesh: Mesh,
        material: str = "concrete",
        rotation: float = 0.0,
        dynamic: bool = False,
    ) -> Obstacle:
        """Create a mesh-based obstacle.

        Args:
            position: Center position
            mesh: Triangle mesh
            material: Material type
            rotation: Rotation around Z axis
            dynamic: Whether obstacle moves

        Returns:
            Obstacle instance
        """
        self.obstacle_id_counter += 1
        return Obstacle(
            id=self.obstacle_id_counter,
            position=position,
            size=Vector3(0, 0, 0),  # Size derived from mesh bounds
            rotation=rotation,
            mesh=mesh,
            collision_type="mesh",
            material=material,
            dynamic=dynamic,
        )

    def add_obstacle(self, obstacle: Obstacle) -> None:
        """Add obstacle to world and appropriate chunks.

        Args:
            obstacle: Obstacle to add
        """
        bounds = obstacle.get_bounds()
        affected_chunks = self._get_chunks_for_bounds(bounds)

        for chunk_x, chunk_y in affected_chunks:
            chunk_key = (chunk_x, chunk_y)
            if chunk_key not in self.chunks:
                self.chunks[chunk_key] = WorldChunk(
                    chunk_x=chunk_x, chunk_y=chunk_y, chunk_size=self.chunk_size
                )
            self.chunks[chunk_key].obstacles.append(obstacle)
            self._invalidate_chunk_cache(chunk_key)

        logger.info(f"Added obstacle {obstacle.id} to {len(affected_chunks)} chunks")

    def add_dynamic_object(
        self,
        chunk_x: int,
        chunk_y: int,
        obj_id: str,
        position: Vector3,
        velocity: Vector3,
        obj_type: str = "vehicle",
    ) -> None:
        """Add dynamic object (agent/vehicle) to chunk.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            obj_id: Object identifier
            position: Current position
            velocity: Current velocity
            obj_type: Type of object
        """
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            self.chunks[chunk_key] = WorldChunk(
                chunk_x=chunk_x, chunk_y=chunk_y, chunk_size=self.chunk_size
            )

        # Check if object already exists and update it
        found = False
        for obj in self.chunks[chunk_key].dynamic_objects:
            if obj["id"] == obj_id:
                obj["position"] = position.to_dict()
                obj["velocity"] = velocity.to_dict()
                found = True
                break

        if not found:
            self.chunks[chunk_key].dynamic_objects.append(
                {
                    "id": obj_id,
                    "type": obj_type,
                    "position": position.to_dict(),
                    "velocity": velocity.to_dict(),
                }
            )
        self._invalidate_chunk_cache(chunk_key)

    def get_chunk(self, chunk_x: int, chunk_y: int, lod: int = 0) -> Optional[WorldChunk]:
        """Get a specific chunk.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            lod: Level of detail (0=full, 1=simplified)

        Returns:
            WorldChunk or None if out of bounds
        """
        if chunk_x < 0 or chunk_x >= self.num_chunks_per_side:
            return None
        if chunk_y < 0 or chunk_y >= self.num_chunks_per_side:
            return None

        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            self.chunks[chunk_key] = WorldChunk(
                chunk_x=chunk_x, chunk_y=chunk_y, chunk_size=self.chunk_size
            )

        chunk = self.chunks[chunk_key]
        chunk.lod_level = lod
        return chunk

    def get_chunks_for_position(
        self, position: Vector3, radius: float = 1000.0, lod: int = 0
    ) -> List[WorldChunk]:
        """Get chunks around a position.

        Args:
            position: Center position
            radius: Radius around position to query
            lod: Level of detail

        Returns:
            List of WorldChunk objects
        """
        x_min = position.x - radius
        x_max = position.x + radius
        y_min = position.y - radius
        y_max = position.y + radius

        chunks = []
        chunk_x_min = int(x_min / self.chunk_size)
        chunk_x_max = int(x_max / self.chunk_size) + 1
        chunk_y_min = int(y_min / self.chunk_size)
        chunk_y_max = int(y_max / self.chunk_size) + 1

        for chunk_x in range(chunk_x_min, chunk_x_max + 1):
            for chunk_y in range(chunk_y_min, chunk_y_max + 1):
                chunk = self.get_chunk(chunk_x, chunk_y, lod)
                if chunk:
                    chunks.append(chunk)

        return chunks

    def get_chunk_json(self, chunk_x: int, chunk_y: int, include_terrain: bool = False) -> Optional[str]:
        """Get chunk as JSON string.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            include_terrain: Whether to include terrain data

        Returns:
            JSON string or None if chunk doesn't exist
        """
        chunk_key = (chunk_x, chunk_y)

        # Check cache
        if self.cache_enabled and chunk_key in self.chunk_cache:
            return self.chunk_cache[chunk_key].decode("utf-8")

        chunk = self.get_chunk(chunk_x, chunk_y)
        if not chunk:
            return None

        chunk_dict = chunk.to_dict(include_terrain=include_terrain)
        json_str = json.dumps(chunk_dict)

        # Cache result
        if self.cache_enabled:
            self.chunk_cache[chunk_key] = json_str.encode("utf-8")

        return json_str

    def get_all_chunks_json(self) -> str:
        """Get all chunks as JSON array.

        Returns:
            JSON string with all chunks
        """
        chunks_data = []
        for chunk in self.chunks.values():
            chunks_data.append(chunk.to_dict())
        return json.dumps(chunks_data)

    def stream_chunk_binary(self, chunk_x: int, chunk_y: int) -> Optional[bytes]:
        """Stream chunk as optimized binary format.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            Binary data or None
        """
        chunk = self.get_chunk(chunk_x, chunk_y)
        if not chunk:
            return None

        # Build binary stream: header + obstacles
        buffer = bytearray()

        # Header: chunk_x (4), chunk_y (4), num_obstacles (4)
        buffer.extend(struct.pack("<iii", chunk_x, chunk_y, len(chunk.obstacles)))

        # Obstacles
        for obs in chunk.obstacles:
            buffer.extend(self._serialize_obstacle_binary(obs))

        return bytes(buffer)

    def _serialize_obstacle_binary(self, obs: Obstacle) -> bytes:
        """Serialize obstacle to binary format.

        Args:
            obs: Obstacle to serialize

        Returns:
            Binary data
        """
        buffer = bytearray()

        # ID (4), position (12), size (12), rotation (4), type enum (1), dynamic (1)
        buffer.extend(struct.pack("<i", obs.id))
        buffer.extend(obs.position.to_bytes())
        buffer.extend(obs.size.to_bytes())
        buffer.extend(struct.pack("<f", obs.rotation))
        buffer.extend(struct.pack("<B", {"box": 0, "mesh": 1, "capsule": 2}[obs.collision_type]))
        buffer.extend(struct.pack("<B", 1 if obs.dynamic else 0))

        # Material name (variable length)
        material_bytes = obs.material.encode("utf-8")
        buffer.extend(struct.pack("<H", len(material_bytes)))
        buffer.extend(material_bytes)

        return bytes(buffer)

    def get_world_bounds(self) -> Dict[str, float]:
        """Get world bounds.

        Returns:
            Dictionary with x_min, x_max, y_min, y_max
        """
        return {
            "x_min": 0,
            "x_max": self.world_size,
            "y_min": 0,
            "y_max": self.world_size,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics.

        Returns:
            Dictionary with stats
        """
        total_obstacles = sum(len(c.obstacles) for c in self.chunks.values())
        total_dynamic = sum(len(c.dynamic_objects) for c in self.chunks.values())
        total_memory = sum(c.memory_size() for c in self.chunks.values())

        return {
            "total_chunks": len(self.chunks),
            "total_obstacles": total_obstacles,
            "total_dynamic_objects": total_dynamic,
            "estimated_memory_mb": total_memory / (1024 * 1024),
            "chunk_size": self.chunk_size,
            "world_size": self.world_size,
            "cache_size": len(self.chunk_cache),
        }

    def _get_chunks_for_bounds(self, bounds: Tuple[float, float, float, float]) -> List[Tuple[int, int]]:
        """Get all chunks intersecting with bounds.

        Args:
            bounds: (x_min, x_max, y_min, y_max)

        Returns:
            List of (chunk_x, chunk_y) tuples
        """
        x_min, x_max, y_min, y_max = bounds

        chunk_x_min = int(x_min / self.chunk_size)
        chunk_x_max = int(x_max / self.chunk_size)
        chunk_y_min = int(y_min / self.chunk_size)
        chunk_y_max = int(y_max / self.chunk_size)

        chunks = []
        for chunk_x in range(chunk_x_min, chunk_x_max + 1):
            for chunk_y in range(chunk_y_min, chunk_y_max + 1):
                chunks.append((chunk_x, chunk_y))

        return chunks

    def _invalidate_chunk_cache(self, chunk_key: Tuple[int, int]) -> None:
        """Invalidate cache for a chunk.

        Args:
            chunk_key: (chunk_x, chunk_y) tuple
        """
        if chunk_key in self.chunk_cache:
            del self.chunk_cache[chunk_key]
