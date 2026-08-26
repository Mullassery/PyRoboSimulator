"""Gazebo Backend Implementation.

**Not available in this environment.** Real Gazebo simulation requires a
full ROS 2 installation (`rclpy`, `ros_gz`/`gazebo_ros` bridge packages)
plus the Gazebo simulator itself (Ignition/Gazebo Sim), which are system
packages distributed via ROS 2's apt repositories, not pip. That stack
is not present in a typical sandboxed development environment or CI
runner without a dedicated ROS 2 image, so this backend cannot be made
to do real physics here the way `MuJoCoBackend` does.

Rather than silently pretending to simulate (the previous behavior: every
method below returned a plausible-looking but hardcoded/no-op result),
`initialize()` now fails fast with a clear `EnvironmentError` explaining
exactly what real infrastructure is missing, instead of setting
`self._initialized = True` and letting callers believe physics is running
when it isn't.

If you need real, working physics simulation today, use
`backend.src.simulators.mujoco_backend.MuJoCoBackend` instead: MuJoCo is
pip-installable, requires no ROS 2/GPU, and this backend integration is
real (see `backend/tests/test_mujoco_backend.py`).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.simulators.backend_interface import (
    ContactInfo, ObjectState, RobotConfig, RobotState, SensorConfig, SensorData,
    SimulationStep, SimulatorBackend, SimulatorConfig, SimulatorType, WorldConfig,
)

logger = logging.getLogger(__name__)


class GazeboBackend(SimulatorBackend):
    """Gazebo (ROS 2) backend - High-fidelity simulation with ROS 2 integration."""

    def __init__(self):
        self._config: Optional[SimulatorConfig] = None
        self._initialized = False
        self._paused = False
        self._step_count = 0
        self._robots: Dict[str, Any] = {}
        self._objects: Dict[str, Any] = {}
        self._sensors: Dict[str, Any] = {}
        self._last_error: Optional[str] = None
        logger.info("Initialized GazeboBackend")

    def initialize(self, config: SimulatorConfig) -> None:
        """Attempt to initialize Gazebo. Always fails in this environment.

        Real Gazebo requires a full ROS 2 installation (`rclpy` +
        `ros_gz`/`gazebo_ros`) and the Gazebo simulator itself, both
        installed as system packages via ROS 2's apt repositories rather
        than pip. This raises `EnvironmentError` rather than pretending to
        succeed, so callers get an honest failure instead of a backend that
        silently does no physics.

        Raises:
            EnvironmentError: Always, in any environment lacking a ROS 2 +
                Gazebo installation (i.e. this one). Message explains the
                real requirement.
        """
        try:
            import rclpy  # noqa: F401  (real ROS 2 Python client library)

            has_ros2 = True
        except ImportError:
            has_ros2 = False

        self._last_error = (
            "GazeboBackend is not functional in this environment: Gazebo "
            "simulation requires a full ROS 2 installation (`rclpy` + the "
            "`ros_gz`/`gazebo_ros` bridge) and the Gazebo simulator itself, "
            "installed as system packages via ROS 2's apt repositories "
            "(not `pip install`). "
            + ("ROS 2's `rclpy` was importable, but no Gazebo bridge "
               "integration is implemented here." if has_ros2 else
               "`rclpy` (ROS 2) was not importable in this environment. ")
            + "Use MuJoCoBackend for real, working physics simulation "
              "(pip-installable, no ROS 2 required)."
        )
        logger.error(self._last_error)
        raise EnvironmentError(self._last_error)

    def shutdown(self) -> None:
        self._initialized = False
        logger.info("Gazebo backend shutdown")

    def is_running(self) -> bool:
        return self._initialized

    def create_world(self, config: WorldConfig) -> str:
        logger.info(f"Creating Gazebo world: {config.name}")
        return config.name

    def load_world(self, world_path: str) -> str:
        logger.info(f"Loading Gazebo world from: {world_path}")
        return world_path

    def save_world(self, world_id: str, output_path: str) -> None:
        logger.info(f"Saving Gazebo world to: {output_path}")

    def get_world_info(self, world_id: str) -> Dict[str, Any]:
        return {"world_id": world_id, "simulator": "gazebo"}

    def spawn_robot(self, robot_config: RobotConfig) -> str:
        logger.info(f"Spawning robot in Gazebo: {robot_config.name}")
        self._robots[robot_config.name] = {"config": robot_config}
        return robot_config.name

    def remove_robot(self, robot_name: str) -> None:
        if robot_name in self._robots:
            del self._robots[robot_name]

    def reset_robot(self, robot_name: str) -> None:
        pass

    def get_robot_state(self, robot_name: str) -> RobotState:
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")
        return RobotState(
            robot_name=robot_name, position=(0.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0, 1.0), linear_velocity=(0.0, 0.0, 0.0),
            angular_velocity=(0.0, 0.0, 0.0), joint_positions={},
            joint_velocities={}, joint_forces={}, timestamp=0.0,
        )

    def set_robot_pose(self, robot_name: str, position: Tuple[float, float, float],
                       rotation: Tuple[float, float, float, float]) -> None:
        pass

    def set_joint_target(self, robot_name: str, joint_name: str, target_value: float,
                        velocity: float = 0.0, force: float = 1000.0) -> None:
        pass

    def apply_joint_force(self, robot_name: str, joint_name: str, force: float) -> None:
        pass

    def get_joint_state(self, robot_name: str, joint_name: str) -> Dict[str, float]:
        return {"position": 0.0, "velocity": 0.0, "force": 0.0}

    def spawn_object(self, name: str, model_path: str, position: Tuple[float, float, float],
                     rotation: Tuple[float, float, float, float], scale: float = 1.0,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        self._objects[name] = {"path": model_path}
        return name

    def remove_object(self, object_name: str) -> None:
        if object_name in self._objects:
            del self._objects[object_name]

    def get_object_state(self, object_name: str) -> ObjectState:
        if object_name not in self._objects:
            raise KeyError(f"Object not found: {object_name}")
        return ObjectState(object_name=object_name, position=(0.0, 0.0, 0.0),
                          rotation=(0.0, 0.0, 0.0, 1.0), linear_velocity=(0.0, 0.0, 0.0),
                          angular_velocity=(0.0, 0.0, 0.0), timestamp=0.0)

    def set_object_pose(self, object_name: str, position: Tuple[float, float, float],
                       rotation: Tuple[float, float, float, float]) -> None:
        pass

    def attach_sensor(self, robot_name: str, sensor_config: SensorConfig) -> str:
        sensor_id = f"{robot_name}_{sensor_config.name}"
        self._sensors[sensor_id] = {"config": sensor_config}
        return sensor_id

    def remove_sensor(self, robot_name: str, sensor_name: str) -> None:
        sensor_id = f"{robot_name}_{sensor_name}"
        if sensor_id in self._sensors:
            del self._sensors[sensor_id]

    def get_sensor_data(self, robot_name: str, sensor_name: str) -> SensorData:
        sensor_id = f"{robot_name}_{sensor_name}"
        if sensor_id not in self._sensors:
            raise KeyError(f"Sensor not found: {sensor_id}")
        return SensorData(sensor_name=sensor_id, sensor_type=self._sensors[sensor_id]["config"].sensor_type,
                         timestamp=0.0, raw_data=b"")

    def get_camera_image(self, robot_name: str, camera_name: str, include_depth: bool = False,
                        include_segmentation: bool = False) -> Dict[str, Any]:
        return {"rgb": None}

    def get_lidar_scan(self, robot_name: str, lidar_name: str) -> Dict[str, Any]:
        return {"points": None, "num_points": 0}

    def get_imu_data(self, robot_name: str, imu_name: str) -> Dict[str, Any]:
        return {"accel": (0.0, 0.0, -9.81), "gyro": (0.0, 0.0, 0.0), "quat": (0.0, 0.0, 0.0, 1.0)}

    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        pass

    def get_gravity(self) -> Tuple[float, float, float]:
        return (0.0, 0.0, -9.81)

    def set_timestep(self, timestep_ms: float) -> None:
        pass

    def get_contacts(self) -> List[ContactInfo]:
        return []

    def raycast(self, origin: Tuple[float, float, float], direction: Tuple[float, float, float],
               max_distance: float = 1000.0) -> Optional[Dict[str, Any]]:
        return None

    def step(self, num_steps: int = 1) -> SimulationStep:
        self._step_count += num_steps
        return SimulationStep(
            step_count=self._step_count, elapsed_time_sec=0.0, timestep_ms=1.0,
            robot_states={}, object_states={}, contacts=[], sensor_data={},
        )

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def reset(self) -> None:
        self._step_count = 0

    def is_paused(self) -> bool:
        return self._paused

    def enable_rendering(self) -> None:
        pass

    def disable_rendering(self) -> None:
        pass

    def set_camera_view(self, position: Tuple[float, float, float],
                       target: Tuple[float, float, float],
                       up: Tuple[float, float, float] = (0.0, 0.0, 1.0)) -> None:
        pass

    def render_frame(self) -> Optional[bytes]:
        return None

    def randomize_lighting(self, intensity_range: Tuple[float, float],
                          color_range: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None) -> None:
        pass

    def randomize_friction(self, object_name: str, friction_range: Tuple[float, float]) -> None:
        pass

    def randomize_mass(self, object_name: str, mass_range: Tuple[float, float]) -> None:
        pass

    def get_simulator_type(self) -> SimulatorType:
        return SimulatorType.GAZEBO

    def get_simulation_info(self) -> Dict[str, Any]:
        return {"simulator": "gazebo", "step_count": self._step_count}

    def list_robots(self) -> List[str]:
        return list(self._robots.keys())

    def list_objects(self) -> List[str]:
        return list(self._objects.keys())

    def get_robot_info(self, robot_name: str) -> Dict[str, Any]:
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")
        return {"name": robot_name, "type": self._robots[robot_name]["config"].robot_type.value}

    def validate_configuration(self, config: SimulatorConfig) -> bool:
        if config.timestep_ms <= 0:
            self._last_error = "timestep_ms must be positive"
            return False
        return True

    def get_last_error(self) -> Optional[str]:
        return self._last_error
