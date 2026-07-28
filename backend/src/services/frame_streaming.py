"""Real-time frame streaming for browser visualization."""

import base64
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import msgpack
import numpy as np


@dataclass
class Vector3:
    """3D vector."""

    x: float
    y: float
    z: float

    def to_list(self) -> List[float]:
        """Convert to list [x, y, z]."""
        return [self.x, self.y, self.z]


@dataclass
class AgentFrame:
    """Agent state for a single frame."""

    id: int
    position: Vector3
    rotation: Vector3
    velocity: Vector3
    state: str  # "idle", "moving", "goal_reached", "collision"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "pos": self.position.to_list(),
            "rot": self.rotation.to_list(),
            "vel": self.velocity.to_list(),
            "state": self.state,
        }


@dataclass
class EventFrame:
    """Event that occurred this frame."""

    id: int
    type: str  # "collision", "goal_reached", etc
    agent_id: int
    position: Vector3
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "id": self.id,
            "type": self.type,
            "agent_id": self.agent_id,
            "pos": self.position.to_list(),
        }
        if self.data:
            result["data"] = self.data
        return result


@dataclass
class SensorData:
    """Sensor data for an agent."""

    rgb: Optional[str] = None  # Base64 encoded JPEG
    depth: Optional[bytes] = None  # Base64 encoded float32 array
    lidar: Optional[List[List[float]]] = None  # List of [x, y, z] points
    thermal: Optional[bytes] = None  # Base64 encoded float32 array

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {}
        if self.rgb:
            result["rgb"] = self.rgb  # Already base64 encoded
        if self.depth is not None:
            result["depth"] = self.depth
        if self.lidar:
            result["lidar"] = self.lidar
        if self.thermal:
            result["thermal"] = self.thermal
        return result


@dataclass
class WorldFrame:
    """Real-time world state for visualization."""

    frame_id: int
    timestamp_ms: float
    agents: List[AgentFrame]
    events: List[EventFrame]
    sensors: Optional[Dict[int, SensorData]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "frame",
            "frame_id": self.frame_id,
            "timestamp_ms": self.timestamp_ms,
            "agents": [agent.to_dict() for agent in self.agents],
            "events": [event.to_dict() for event in self.events],
            "sensors": {
                agent_id: sensor.to_dict()
                for agent_id, sensor in (self.sensors or {}).items()
            }
            if self.sensors
            else {},
        }

    def to_msgpack(self) -> bytes:
        """Serialize to MessagePack binary format."""
        return msgpack.packb(self.to_dict(), use_bin_type=True)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ControlCommand:
    """Control command from browser."""

    type: str  # "play", "pause", "resume", "speed", "camera"
    payload: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ControlCommand":
        """Deserialize from dictionary."""
        return cls(
            type=data.get("type", ""),
            payload=data.get("payload", {}),
        )


class FrameBuffer:
    """Buffer for managing frame queues per client."""

    def __init__(self, max_size: int = 30):
        """Initialize frame buffer.

        Args:
            max_size: Maximum frames to buffer (60 FPS * 0.5s = 30 frames)
        """
        self.max_size = max_size
        self.frames: List[WorldFrame] = []
        self.last_frame_id = -1

    def add_frame(self, frame: WorldFrame) -> None:
        """Add frame to buffer."""
        self.frames.append(frame)
        self.last_frame_id = frame.frame_id

        # Keep buffer size limited
        if len(self.frames) > self.max_size:
            self.frames = self.frames[-self.max_size :]

    def get_frames_since(self, frame_id: int) -> List[WorldFrame]:
        """Get all frames since given frame ID."""
        return [f for f in self.frames if f.frame_id > frame_id]

    def get_latest_frame(self) -> Optional[WorldFrame]:
        """Get most recent frame."""
        return self.frames[-1] if self.frames else None

    def clear(self) -> None:
        """Clear all buffered frames."""
        self.frames.clear()
        self.last_frame_id = -1


def encode_depth_map(depth_map: np.ndarray) -> str:
    """Encode depth map as base64 string.

    Args:
        depth_map: numpy float32 array (H x W)

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(depth_map.astype(np.float32).tobytes()).decode("utf-8")


def encode_thermal_image(thermal_image: np.ndarray) -> str:
    """Encode thermal image as base64 string.

    Args:
        thermal_image: numpy float32 array (H x W)

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(thermal_image.astype(np.float32).tobytes()).decode("utf-8")


def encode_rgb_image(rgb_image: bytes) -> str:
    """Encode RGB image as base64 string.

    Args:
        rgb_image: JPEG bytes

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(rgb_image).decode("utf-8")
