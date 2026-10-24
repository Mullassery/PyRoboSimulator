"""Gazebo Backend Implementation.

Real Gazebo integration requires ROS 2 (rclpy) and Gazebo/ros_gz bridge
installed as system packages. This backend uses a runtime adapter with
lazy imports and fallbacks; when unavailable it fails fast with
EnvironmentError.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from src.integrations.gazebo_runtime import GazeboRuntime, GazeboRuntimeUnavailable
from src.simulators.backend_interface import (
    ContactInfo,
    ObjectState,
    PhysicsEngineType,
    RobotConfig,
    RobotState,
    SensorConfig,
    SensorData,
    SimulationStep,
    SimulatorBackend,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)

logger = logging.getLogger(__name__)


class GazeboBackend(SimulatorBackend):
    """Gazebo (ROS 2) backend - High-fidelity simulation with ROS 2 integration."""

    def __init__(self, runtime: Optional[GazeboRuntime] = None):
        self._config: Optional[SimulatorConfig] = None
        self._initialized = False
        self._paused = False
        self._step_count = 0
        self._robots: Dict[str, Any] = {}
        self._objects: Dict[str, Any] = {}
        self._sensors: Dict[str, Any] = {}
        self._last_error: Optional[str] = None
        self._runtime = runtime or GazeboRuntime()
        self._runtime_status = None
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
            + (
                "ROS 2's `rclpy` was importable, but no Gazebo bridge "
                "integration is implemented here."
                if has_ros2
                else "`rclpy` (ROS 2) was not importable in this environment. "
            )
            + "Use MuJoCoBackend for real, working physics simulation "
            "(pip-installable, no ROS 2 required)."
        )
        logger.error(self._last_error)
        raise EnvironmentError(self._last_error)

    def shutdown(self) -> None:
        try:
            self._runtime.shutdown()
        except Exception:
            logger.exception("Error shutting down Gazebo runtime")
        self._initialized = False
        self._paused = False
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
        self._robots[robot_config.name] = {
            "config": robot_config,
            "position": (0.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0, 1.0),
            "linear_velocity": (0.0, 0.0, 0.0),
            "angular_velocity": (0.0, 0.0, 0.0),
            "joint_positions": {},
            "joint_velocities": {},
            "joint_forces": {},
        }
        return robot_config.name

    def remove_robot(self, robot_name: str) -> None:
        if robot_name in self._robots:
            del self._robots[robot_name]

    def reset_robot(self, robot_name: str) -> None:
        if robot_name in self._robots:
            r = self._robots[robot_name]
            r["position"] = (0.0, 0.0, 0.0)
            r["rotation"] = (0.0, 0.0, 0.0, 1.0)
            r["linear_velocity"] = (0.0, 0.0, 0.0)
            r["angular_velocity"] = (0.0, 0.0, 0.0)
            r["joint_positions"].clear()
            r["joint_velocities"].clear()
            r["joint_forces"].clear()

    def get_robot_state(self, robot_name: str) -> RobotState:
        if robot_name not in self._robots:
            raise KeyError(f"Robot not found: {robot_name}")
        r = self._robots[robot_name]
        return RobotState(
            robot_name=robot_name,
            position=r.get("position", (0.0, 0.0, 0.0)),
            rotation=r.get("rotation", (0.0, 0.0, 0.0, 1.0)),
            linear_velocity=r.get("linear_velocity", (0.0, 0.0, 0.0)),
            angular_velocity=r.get("angular_velocity", (0.0, 0.0, 0.0)),
            joint_positions=dict(r.get("joint_positions", {})),
            joint_velocities=dict(r.get("joint_velocities", {})),
            joint_forces=dict(r.get("joint_forces", {})),
            timestamp=time.time(),
        )

    def set_robot_pose(
        self,
        robot_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
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
        if robot_name in self._robots:
            r = self._robots[robot_name]
            r["joint_positions"][joint_name] = target_value
            r["joint_velocities"][joint_name] = velocity
            r["joint_forces"][joint_name] = force

    def apply_joint_force(self, robot_name: str, joint_name: str, force: float) -> None:
        if robot_name in self._robots:
            self._robots[robot_name]["joint_forces"][joint_name] = force

    def get_joint_state(self, robot_name: str, joint_name: str) -> Dict[str, float]:
        if robot_name in self._robots:
            r = self._robots[robot_name]
            return {
                "position": r.get("joint_positions", {}).get(joint_name, 0.0),
                "velocity": r.get("joint_velocities", {}).get(joint_name, 0.0),
                "force": r.get("joint_forces", {}).get(joint_name, 0.0),
            }
        return {"position": 0.0, "velocity": 0.0, "force": 0.0}

    def spawn_object(
        self,
        name: str,
        model_path: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
        scale: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        self._objects[name] = {
            "path": model_path,
            "position": position,
            "rotation": rotation,
            "scale": scale,
        }
        return name

    def remove_object(self, object_name: str) -> None:
        if object_name in self._objects:
            del self._objects[object_name]

    def get_object_state(self, object_name: str) -> ObjectState:
        if object_name not in self._objects:
            raise KeyError(f"Object not found: {object_name}")
        obj = self._objects[object_name]
        return ObjectState(
            object_name=object_name,
            position=obj.get("position", (0.0, 0.0, 0.0)),
            rotation=obj.get("rotation", (0.0, 0.0, 0.0, 1.0)),
            linear_velocity=(0.0, 0.0, 0.0),
            angular_velocity=(0.0, 0.0, 0.0),
            timestamp=time.time(),
        )

    def set_object_pose(
        self,
        object_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        if object_name in self._objects:
            self._objects[object_name]["position"] = position
            self._objects[object_name]["rotation"] = rotation

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
        return SensorData(
            sensor_name=sensor_id,
            sensor_type=self._sensors[sensor_id]["config"].sensor_type,
            timestamp=0.0,
            raw_data=b"",
        )

    def get_camera_image(
        self,
        robot_name: str,
        camera_name: str,
        include_depth: bool = False,
        include_segmentation: bool = False,
    ) -> Dict[str, Any]:
        return {"rgb": None}

    def get_lidar_scan(self, robot_name: str, lidar_name: str) -> Dict[str, Any]:
        return {"points": None, "num_points": 0}

    def get_imu_data(self, robot_name: str, imu_name: str) -> Dict[str, Any]:
        return {"accel": (0.0, 0.0, -9.81), "gyro": (0.0, 0.0, 0.0), "quat": (0.0, 0.0, 0.0, 1.0)}

    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        self._gravity = gravity

    def get_gravity(self) -> Tuple[float, float, float]:
        return getattr(self, "_gravity", (0.0, 0.0, -9.81))

    def set_timestep(self, timestep_ms: float) -> None:
        self._timestep_ms = timestep_ms

    def get_contacts(self) -> List[ContactInfo]:
        return []

    def raycast(
        self,
        origin: Tuple[float, float, float],
        direction: Tuple[float, float, float],
        max_distance: float = 1000.0,
    ) -> Optional[Dict[str, Any]]:
        return None

    def step(self, num_steps: int = 1) -> SimulationStep:
        if not self._initialized:
            raise RuntimeError("GazeboBackend is not initialized")
        if self._paused:
            raise RuntimeError("Cannot step while paused")
        for _ in range(num_steps):
            try:
                self._runtime.step()
            except Exception:
                logger.debug("Gazebo runtime step failed or not implemented")
            self._step_count += 1
        robot_states = {name: self.get_robot_state(name) for name in self._robots}
        object_states = {name: self.get_object_state(name) for name in self._objects}
        return SimulationStep(
            step_count=self._step_count,
            elapsed_time_sec=self._step_count * (getattr(self, "_timestep_ms", 1.0) / 1000.0),
            timestep_ms=getattr(self, "_timestep_ms", 1.0),
            robot_states=robot_states,
            object_states=object_states,
            contacts=[],
            sensor_data={},
        )

    def pause(self) -> None:
        self._paused = True
        if self._initialized:
            pause_fn = getattr(self._runtime, "pause", None)
            if callable(pause_fn):
                try:
                    pause_fn()
                except Exception:
                    pass

    def resume(self) -> None:
        self._paused = False
        if self._initialized:
            resume_fn = getattr(self._runtime, "resume", None)
            if callable(resume_fn):
                try:
                    resume_fn()
                except Exception:
                    pass

    def reset(self) -> None:
        self._step_count = 0
        for name in list(self._robots.keys()):
            self.reset_robot(name)
        if self._initialized:
            try:
                self._runtime.reset()
            except Exception:
                logger.debug("Gazebo runtime reset not implemented")

    def is_paused(self) -> bool:
        return self._paused

    def enable_rendering(self) -> None:
        self._rendering_enabled = True

    def disable_rendering(self) -> None:
        self._rendering_enabled = False

    def set_camera_view(
        self,
        position: Tuple[float, float, float],
        target: Tuple[float, float, float],
        up: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> None:
        self._camera_view = {"position": position, "target": target, "up": up}

    def render_frame(self) -> Optional[bytes]:
        return None

    def randomize_lighting(
        self,
        intensity_range: Tuple[float, float],
        color_range: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None,
    ) -> None:
        self._lighting = {"intensity_range": intensity_range, "color_range": color_range}

    def randomize_friction(self, object_name: str, friction_range: Tuple[float, float]) -> None:
        if object_name in self._objects:
            self._objects[object_name]["friction"] = (friction_range[0] + friction_range[1]) / 2.0

    def randomize_mass(self, object_name: str, mass_range: Tuple[float, float]) -> None:
        if object_name in self._objects:
            self._objects[object_name]["mass"] = (mass_range[0] + mass_range[1]) / 2.0

    def get_simulator_type(self) -> SimulatorType:
        return SimulatorType.GAZEBO

    def get_simulation_info(self) -> Dict[str, Any]:
        status = None
        if getattr(self, "_runtime_status", None) is not None:
            status = self._runtime_status.to_dict()
        elif self._runtime is not None:
            try:
                status = self._runtime.inspect().to_dict()
            except Exception:
                status = None
        return {
            "simulator": "gazebo",
            "step_count": self._step_count,
            "initialized": self._initialized,
            "runtime": status,
            "note": "Requires ROS 2 and Gazebo/ros_gz installed as system packages.",
        }

    def get_runtime_status(self):
        if getattr(self, "_runtime_status", None) is not None:
            return self._runtime_status
        if self._runtime is not None:
            try:
                return self._runtime.inspect()
            except Exception:
                return None
        return None

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
