"""Mock Backend - Test implementation of SimulatorBackend interface.

Provides a fully functional mock simulator for testing and validation.
All operations simulate without external dependencies.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.simulators.backend_interface import (
    CameraConfig,
    ContactInfo,
    IMUConfig,
    LidarConfig,
    ObjectState,
    PhysicsEngineType,
    RenderingBackend,
    RobotConfig,
    RobotState,
    RobotType,
    SensorConfig,
    SensorData,
    SensorType,
    SimulationStep,
    SimulatorBackend,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)

logger = logging.getLogger(__name__)


class MockBackend(SimulatorBackend):
    """Mock simulator backend for testing and validation.

    Simulates physics, sensors, and world without external dependencies.
    """

    def __init__(self):
        """Initialize mock backend."""
        self._config: Optional[SimulatorConfig] = None
        self._initialized = False
        self._paused = False
        self._step_count = 0
        self._start_time = time.time()

        # State containers
        self._robots: Dict[str, Dict[str, Any]] = {}
        self._objects: Dict[str, ObjectState] = {}
        self._sensors: Dict[str, Dict[str, Any]] = {}
        self._contacts: List[ContactInfo] = []
        self._gravity = (0.0, 0.0, -9.81)
        self._timestep_ms = 1.0
        self._world_id: Optional[str] = None
        self._last_error: Optional[str] = None

    # ==================== INITIALIZATION & LIFECYCLE ====================

    def initialize(self, config: SimulatorConfig) -> None:
        """Initialize mock backend."""
        logger.info("Initializing MockBackend")
        self._config = config
        self._gravity = config.gravity
        self._timestep_ms = config.timestep_ms
        self._initialized = True

    def shutdown(self) -> None:
        """Shutdown mock backend."""
        logger.info("Shutting down MockBackend")
        self._robots.clear()
        self._objects.clear()
        self._sensors.clear()
        self._initialized = False

    def is_running(self) -> bool:
        """Check if running."""
        return self._initialized

    # ==================== WORLD MANAGEMENT ====================

    def create_world(self, config: WorldConfig) -> str:
        """Create a new world."""
        self._world_id = config.name
        logger.info(f"Created world: {self._world_id}")
        return self._world_id

    def load_world(self, world_path: str) -> str:
        """Load world from file."""
        self._world_id = f"world_{int(time.time())}"
        logger.info(f"Loaded world from: {world_path}")
        return self._world_id

    def save_world(self, world_id: str, output_path: str) -> None:
        """Save world to file."""
        logger.info(f"Saved world {world_id} to {output_path}")

    def get_world_info(self, world_id: str) -> Dict[str, Any]:
        """Get world info."""
        return {
            "world_id": world_id,
            "robot_count": len(self._robots),
            "object_count": len(self._objects),
            "sensor_count": len(self._sensors),
            "gravity": self._gravity,
            "timestep_ms": self._timestep_ms,
        }

    # ==================== ROBOT MANAGEMENT ====================

    def spawn_robot(self, robot_config: RobotConfig) -> str:
        """Spawn a robot."""
        self._robots[robot_config.name] = {
            "config": robot_config,
            "position": robot_config.position,
            "rotation": robot_config.rotation,
            "velocity": (0.0, 0.0, 0.0),
            "angular_velocity": (0.0, 0.0, 0.0),
            "joints": {},
            "sensors": {},
        }

        logger.info(f"Spawned robot: {robot_config.name}")
        return robot_config.name

    def remove_robot(self, robot_name: str) -> None:
        """Remove robot."""
        if robot_name in self._robots:
            del self._robots[robot_name]
            logger.info(f"Removed robot: {robot_name}")

    def reset_robot(self, robot_name: str) -> None:
        """Reset robot."""
        if robot_name in self._robots:
            robot = self._robots[robot_name]
            config = robot["config"]
            robot["position"] = config.position
            robot["rotation"] = config.rotation
            robot["velocity"] = (0.0, 0.0, 0.0)
            robot["angular_velocity"] = (0.0, 0.0, 0.0)
            logger.info(f"Reset robot: {robot_name}")

    def get_robot_state(self, robot_name: str) -> RobotState:
        """Get robot state."""
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")

        robot = self._robots[robot_name]

        return RobotState(
            robot_name=robot_name,
            position=robot["position"],
            rotation=robot["rotation"],
            linear_velocity=robot["velocity"],
            angular_velocity=robot["angular_velocity"],
            joint_positions=robot["joints"],
            joint_velocities={k: 0.0 for k in robot["joints"]},
            joint_forces={k: 0.0 for k in robot["joints"]},
            timestamp=time.time(),
        )

    def set_robot_pose(
        self,
        robot_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        """Set robot pose."""
        if robot_name in self._robots:
            self._robots[robot_name]["position"] = position
            self._robots[robot_name]["rotation"] = rotation

    def set_joint_target(
        self,
        robot_name: str,
        joint_name: str,
        target_value: float,
        velocity: float = 0.0,
        force: float = 1000.0,
    ) -> None:
        """Set joint target."""
        if robot_name in self._robots:
            self._robots[robot_name]["joints"][joint_name] = target_value

    def apply_joint_force(self, robot_name: str, joint_name: str, force: float) -> None:
        """Apply joint force."""
        if robot_name in self._robots:
            # Just track the last applied force
            self._robots[robot_name]["joints"][f"{joint_name}_force"] = force

    def get_joint_state(self, robot_name: str, joint_name: str) -> Dict[str, float]:
        """Get joint state."""
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")

        robot = self._robots[robot_name]
        position = robot["joints"].get(joint_name, 0.0)

        return {
            "position": position,
            "velocity": 0.0,
            "force": 0.0,
        }

    # ==================== OBJECT/ASSET MANAGEMENT ====================

    def spawn_object(
        self,
        name: str,
        model_path: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
        scale: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Spawn object."""
        self._objects[name] = ObjectState(
            object_name=name,
            position=position,
            rotation=rotation,
            linear_velocity=(0.0, 0.0, 0.0),
            angular_velocity=(0.0, 0.0, 0.0),
            timestamp=time.time(),
        )

        logger.info(f"Spawned object: {name}")
        return name

    def remove_object(self, object_name: str) -> None:
        """Remove object."""
        if object_name in self._objects:
            del self._objects[object_name]
            logger.info(f"Removed object: {object_name}")

    def get_object_state(self, object_name: str) -> ObjectState:
        """Get object state."""
        if object_name not in self._objects:
            raise KeyError(f"Object not found: {object_name}")

        return self._objects[object_name]

    def set_object_pose(
        self,
        object_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        """Set object pose."""
        if object_name in self._objects:
            state = self._objects[object_name]
            self._objects[object_name] = ObjectState(
                object_name=state.object_name,
                position=position,
                rotation=rotation,
                linear_velocity=state.linear_velocity,
                angular_velocity=state.angular_velocity,
                timestamp=time.time(),
            )

    # ==================== SENSOR MANAGEMENT ====================

    def attach_sensor(self, robot_name: str, sensor_config: SensorConfig) -> str:
        """Attach sensor."""
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")

        sensor_id = f"{robot_name}_{sensor_config.name}"
        self._robots[robot_name]["sensors"][sensor_id] = {
            "config": sensor_config,
            "type": sensor_config.sensor_type,
        }

        logger.info(f"Attached sensor: {sensor_id}")
        return sensor_id

    def remove_sensor(self, robot_name: str, sensor_name: str) -> None:
        """Remove sensor."""
        if robot_name in self._robots:
            sensor_id = f"{robot_name}_{sensor_name}"
            if sensor_id in self._robots[robot_name]["sensors"]:
                del self._robots[robot_name]["sensors"][sensor_id]
                logger.info(f"Removed sensor: {sensor_id}")

    def get_sensor_data(self, robot_name: str, sensor_name: str) -> SensorData:
        """Get sensor data."""
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")

        robot = self._robots[robot_name]
        sensor_id = f"{robot_name}_{sensor_name}"

        if sensor_id not in robot["sensors"]:
            raise KeyError(f"Sensor not found: {sensor_id}")

        sensor = robot["sensors"][sensor_id]

        return SensorData(
            sensor_name=sensor_id,
            sensor_type=sensor["type"],
            timestamp=time.time(),
            raw_data=b"",  # Empty mock data
        )

    def get_camera_image(
        self,
        robot_name: str,
        camera_name: str,
        include_depth: bool = False,
        include_segmentation: bool = False,
    ) -> Dict[str, Any]:
        """Get camera image."""
        # Create dummy image data
        result = {
            "rgb": np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8),
            "timestamp": time.time(),
        }

        if include_depth:
            result["depth"] = np.random.rand(480, 640).astype(np.float32) * 100

        if include_segmentation:
            result["segmentation"] = np.random.randint(0, 10, (480, 640), dtype=np.int32)

        return result

    def get_lidar_scan(self, robot_name: str, lidar_name: str) -> Dict[str, Any]:
        """Get Lidar scan."""
        # Create dummy point cloud
        num_points = 1024
        points = np.random.randn(num_points, 3).astype(np.float32) * 10

        return {
            "points": points,
            "intensities": np.random.rand(num_points).astype(np.float32),
            "timestamps": np.zeros(num_points),
            "num_points": num_points,
        }

    def get_imu_data(self, robot_name: str, imu_name: str) -> Dict[str, Any]:
        """Get IMU data."""
        return {
            "accel": (0.0, 0.0, -9.81),
            "gyro": (0.0, 0.0, 0.0),
            "quat": (0.0, 0.0, 0.0, 1.0),
            "timestamp": time.time(),
        }

    # ==================== PHYSICS & DYNAMICS ====================

    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        """Set gravity."""
        self._gravity = gravity

    def get_gravity(self) -> Tuple[float, float, float]:
        """Get gravity."""
        return self._gravity

    def set_timestep(self, timestep_ms: float) -> None:
        """Set timestep."""
        self._timestep_ms = timestep_ms

    def get_contacts(self) -> List[ContactInfo]:
        """Get contacts."""
        return self._contacts

    def raycast(
        self,
        origin: Tuple[float, float, float],
        direction: Tuple[float, float, float],
        max_distance: float = 1000.0,
    ) -> Optional[Dict[str, Any]]:
        """Raycast."""
        # Mock: 50% chance of hit
        if np.random.random() > 0.5:
            distance = np.random.random() * max_distance

            return {
                "body_name": "mock_object",
                "position": (
                    origin[0] + direction[0] * distance,
                    origin[1] + direction[1] * distance,
                    origin[2] + direction[2] * distance,
                ),
                "normal": direction,
                "distance": distance,
            }

        return None

    # ==================== SIMULATION CONTROL ====================

    def step(self, num_steps: int = 1) -> SimulationStep:
        """Step simulation."""
        if self._paused:
            raise RuntimeError("Cannot step while paused")

        for _ in range(num_steps):
            self._step_count += 1

        elapsed = time.time() - self._start_time

        robot_states = {
            name: self.get_robot_state(name) for name in self._robots.keys()
        }

        return SimulationStep(
            step_count=self._step_count,
            elapsed_time_sec=elapsed,
            timestep_ms=self._timestep_ms,
            robot_states=robot_states,
            object_states=dict(self._objects),
            contacts=self._contacts,
            sensor_data={},
        )

    def pause(self) -> None:
        """Pause simulation."""
        self._paused = True

    def resume(self) -> None:
        """Resume simulation."""
        self._paused = False

    def reset(self) -> None:
        """Reset simulation."""
        self._step_count = 0
        self._start_time = time.time()
        self._robots.clear()
        self._objects.clear()

    def is_paused(self) -> bool:
        """Check if paused."""
        return self._paused

    # ==================== RENDERING & VISUALIZATION ====================

    def enable_rendering(self) -> None:
        """Enable rendering."""
        pass

    def disable_rendering(self) -> None:
        """Disable rendering."""
        pass

    def set_camera_view(
        self,
        position: Tuple[float, float, float],
        target: Tuple[float, float, float],
        up: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> None:
        """Set camera view."""
        pass

    def render_frame(self) -> Optional[bytes]:
        """Render frame."""
        return None

    # ==================== DOMAIN RANDOMIZATION ====================

    def randomize_lighting(
        self,
        intensity_range: Tuple[float, float],
        color_range: Optional[
            Tuple[Tuple[float, float, float], Tuple[float, float, float]]
        ] = None,
    ) -> None:
        """Randomize lighting."""
        pass

    def randomize_friction(
        self, object_name: str, friction_range: Tuple[float, float]
    ) -> None:
        """Randomize friction."""
        pass

    def randomize_mass(self, object_name: str, mass_range: Tuple[float, float]) -> None:
        """Randomize mass."""
        pass

    # ==================== UTILITIES & INFO ====================

    def get_simulator_type(self) -> SimulatorType:
        """Get simulator type."""
        return SimulatorType.CUSTOM

    def get_simulation_info(self) -> Dict[str, Any]:
        """Get simulation info."""
        return {
            "simulator_type": "mock",
            "step_count": self._step_count,
            "elapsed_time_sec": time.time() - self._start_time,
            "robot_count": len(self._robots),
            "object_count": len(self._objects),
            "sensor_count": sum(
                len(r["sensors"]) for r in self._robots.values()
            ),
        }

    def list_robots(self) -> List[str]:
        """List robots."""
        return list(self._robots.keys())

    def list_objects(self) -> List[str]:
        """List objects."""
        return list(self._objects.keys())

    def get_robot_info(self, robot_name: str) -> Dict[str, Any]:
        """Get robot info."""
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")

        robot = self._robots[robot_name]

        return {
            "name": robot_name,
            "type": robot["config"].robot_type.value,
            "position": robot["position"],
            "rotation": robot["rotation"],
            "joints": list(robot["joints"].keys()),
            "sensors": list(robot["sensors"].keys()),
        }

    # ==================== ERROR HANDLING & VALIDATION ====================

    def validate_configuration(self, config: SimulatorConfig) -> bool:
        """Validate configuration."""
        if config.timestep_ms <= 0:
            self._last_error = "timestep_ms must be positive"
            return False

        if not isinstance(config.gravity, tuple) or len(config.gravity) != 3:
            self._last_error = "gravity must be a 3-tuple"
            return False

        return True

    def get_last_error(self) -> Optional[str]:
        """Get last error."""
        return self._last_error
