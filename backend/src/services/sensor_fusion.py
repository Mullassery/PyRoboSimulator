"""Real-time multi-sensor fusion pipeline with temporal sync and coordinate transforms."""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

import numpy as np


@dataclass
class SensorReading:
    """Base class for sensor readings with metadata."""

    sensor_id: str
    agent_id: int
    timestamp_ms: float
    sensor_type: str  # "rgb", "depth", "lidar", "thermal"
    confidence: float = 1.0
    data: Optional[np.ndarray] = None


@dataclass
class RGBReading(SensorReading):
    """RGB camera reading."""

    width: int = 640
    height: int = 480
    sensor_type: str = field(default="rgb", init=False)
    confidence: float = 0.95


@dataclass
class DepthReading(SensorReading):
    """Depth camera reading."""

    width: int = 512
    height: int = 512
    sensor_type: str = field(default="depth", init=False)
    min_range: float = 0.1
    max_range: float = 300.0
    confidence: float = 0.9


@dataclass
class LidarReading(SensorReading):
    """Lidar point cloud reading."""

    num_points: int = 8192
    sensor_type: str = field(default="lidar", init=False)
    confidence: float = 0.85


@dataclass
class ThermalReading(SensorReading):
    """Thermal camera reading."""

    width: int = 256
    height: int = 256
    sensor_type: str = field(default="thermal", init=False)
    min_temp: float = -20.0
    max_temp: float = 60.0
    confidence: float = 0.80


@dataclass
class FusedSensorFrame:
    """Fused multi-sensor frame with synchronized data."""

    frame_id: int
    timestamp_ms: float
    agent_id: int

    rgb: Optional[RGBReading] = None
    depth: Optional[DepthReading] = None
    lidar: Optional[LidarReading] = None
    thermal: Optional[ThermalReading] = None

    # Fusion metadata
    fusion_latency_ms: float = 0.0
    timestamp_deviation_ms: float = 0.0
    num_sensors_fused: int = 0

    # Coordinate transforms
    rgb_to_world: Optional[np.ndarray] = None
    depth_to_world: Optional[np.ndarray] = None
    lidar_to_world: Optional[np.ndarray] = None
    thermal_to_world: Optional[np.ndarray] = None


class SensorFusionPipeline:
    """Real-time sensor fusion system for multi-modal sensor integration."""

    def __init__(self, agent_id: int, max_sync_deviation_ms: float = 10.0):
        """Initialize sensor fusion pipeline.

        Args:
            agent_id: Agent ID for fusion
            max_sync_deviation_ms: Maximum allowed timestamp deviation (ms)
        """
        self.agent_id = agent_id
        self.max_sync_deviation_ms = max_sync_deviation_ms

        # Sensor buffers (circular, one frame per sensor type)
        self.sensor_buffers: Dict[str, Optional[SensorReading]] = {
            "rgb": None,
            "depth": None,
            "lidar": None,
            "thermal": None,
        }

        # Timing and statistics
        self.frame_count = 0
        self.fusion_times: List[float] = []
        self.last_fusion_time_ms = 0.0

    def push_rgb_reading(self, rgb_data: np.ndarray, timestamp_ms: float) -> None:
        """Push RGB reading to fusion pipeline.

        Args:
            rgb_data: RGB image data (H×W×3 uint8)
            timestamp_ms: Sensor timestamp (milliseconds)
        """
        reading = RGBReading(
            sensor_id=f"rgb_{self.agent_id}",
            agent_id=self.agent_id,
            timestamp_ms=timestamp_ms,
            width=rgb_data.shape[1],
            height=rgb_data.shape[0],
            data=rgb_data.copy(),
        )
        self.sensor_buffers["rgb"] = reading

    def push_depth_reading(
        self,
        depth_data: np.ndarray,
        timestamp_ms: float,
        min_range: float = 0.1,
        max_range: float = 300.0,
    ) -> None:
        """Push depth reading to fusion pipeline.

        Args:
            depth_data: Depth map (H×W float32, meters)
            timestamp_ms: Sensor timestamp (milliseconds)
            min_range: Minimum range (meters)
            max_range: Maximum range (meters)
        """
        reading = DepthReading(
            sensor_id=f"depth_{self.agent_id}",
            agent_id=self.agent_id,
            timestamp_ms=timestamp_ms,
            width=depth_data.shape[1],
            height=depth_data.shape[0],
            min_range=min_range,
            max_range=max_range,
            data=depth_data.copy(),
        )
        self.sensor_buffers["depth"] = reading

    def push_lidar_reading(
        self,
        lidar_points: List[List[float]],
        timestamp_ms: float,
    ) -> None:
        """Push Lidar reading to fusion pipeline.

        Args:
            lidar_points: List of [x, y, z] points
            timestamp_ms: Sensor timestamp (milliseconds)
        """
        reading = LidarReading(
            sensor_id=f"lidar_{self.agent_id}",
            agent_id=self.agent_id,
            timestamp_ms=timestamp_ms,
            num_points=len(lidar_points),
            data=np.array(lidar_points, dtype=np.float32),
        )
        self.sensor_buffers["lidar"] = reading

    def push_thermal_reading(
        self,
        thermal_data: np.ndarray,
        timestamp_ms: float,
        min_temp: float = -20.0,
        max_temp: float = 60.0,
    ) -> None:
        """Push thermal reading to fusion pipeline.

        Args:
            thermal_data: Thermal map (H×W float32, degrees C)
            timestamp_ms: Sensor timestamp (milliseconds)
            min_temp: Minimum temperature (°C)
            max_temp: Maximum temperature (°C)
        """
        reading = ThermalReading(
            sensor_id=f"thermal_{self.agent_id}",
            agent_id=self.agent_id,
            timestamp_ms=timestamp_ms,
            width=thermal_data.shape[1],
            height=thermal_data.shape[0],
            min_temp=min_temp,
            max_temp=max_temp,
            data=thermal_data.copy(),
        )
        self.sensor_buffers["thermal"] = reading

    def fuse(self, agent_position: Tuple[float, float, float]) -> Optional[FusedSensorFrame]:
        """Fuse buffered sensor readings into synchronized frame.

        Args:
            agent_position: Agent position (x, y, z) for coordinate transforms

        Returns:
            FusedSensorFrame with synchronized and transformed sensor data, or None if fusion fails
        """
        start_time = time.perf_counter()

        # 1. Timestamp synchronization check
        timestamps = [
            reading.timestamp_ms
            for reading in self.sensor_buffers.values()
            if reading is not None
        ]

        if not timestamps:
            return None  # No sensor data available

        # Check timestamp deviation
        timestamp_min = min(timestamps)
        timestamp_max = max(timestamps)
        timestamp_deviation = timestamp_max - timestamp_min

        if timestamp_deviation > self.max_sync_deviation_ms:
            # Timestamps too out of sync, skip fusion
            return None

        # 2. Create fused frame
        fused_frame = FusedSensorFrame(
            frame_id=self.frame_count,
            timestamp_ms=np.mean(timestamps),
            agent_id=self.agent_id,
            rgb=self.sensor_buffers["rgb"],
            depth=self.sensor_buffers["depth"],
            lidar=self.sensor_buffers["lidar"],
            thermal=self.sensor_buffers["thermal"],
            timestamp_deviation_ms=timestamp_deviation,
        )

        # 3. Apply coordinate transforms (agent frame → world frame)
        fused_frame = self._apply_coordinate_transforms(fused_frame, agent_position)

        # 4. Calculate fusion metrics
        num_sensors = sum(1 for reading in self.sensor_buffers.values() if reading is not None)
        fused_frame.num_sensors_fused = num_sensors

        # 5. Measure fusion latency
        end_time = time.perf_counter()
        fusion_latency_ms = (end_time - start_time) * 1000
        fused_frame.fusion_latency_ms = fusion_latency_ms
        self.fusion_times.append(fusion_latency_ms)

        self.last_fusion_time_ms = fusion_latency_ms
        self.frame_count += 1

        return fused_frame

    def _apply_coordinate_transforms(
        self, fused_frame: FusedSensorFrame, agent_position: Tuple[float, float, float]
    ) -> FusedSensorFrame:
        """Apply coordinate transforms from agent frame to world frame.

        Args:
            fused_frame: Fused frame to transform
            agent_position: Agent position (x, y, z)

        Returns:
            FusedSensorFrame with transformation matrices set
        """
        # Create simple translation matrix (agent position → world frame)
        # In full implementation, would include rotation (orientation)
        translation = np.array(agent_position, dtype=np.float32)

        # Transformation matrix (4×4 homogeneous)
        transform = np.eye(4, dtype=np.float32)
        transform[0:3, 3] = translation

        # Apply same transform to all sensors (simplified: same mounting)
        fused_frame.rgb_to_world = transform.copy()
        fused_frame.depth_to_world = transform.copy()
        fused_frame.lidar_to_world = transform.copy()
        fused_frame.thermal_to_world = transform.copy()

        return fused_frame

    def get_fusion_stats(self) -> Dict[str, float]:
        """Get sensor fusion pipeline statistics.

        Returns:
            Dictionary with fusion metrics
        """
        if not self.fusion_times:
            return {
                "avg_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "frames_fused": 0,
            }

        return {
            "avg_latency_ms": np.mean(self.fusion_times),
            "max_latency_ms": np.max(self.fusion_times),
            "min_latency_ms": np.min(self.fusion_times),
            "frames_fused": self.frame_count,
        }

    def reset(self) -> None:
        """Reset fusion pipeline state."""
        self.sensor_buffers = {sensor_type: None for sensor_type in self.sensor_buffers}
        self.fusion_times.clear()
        self.frame_count = 0
        self.last_fusion_time_ms = 0.0
