"""Simulator Backend Interface - Abstract foundation for all simulator implementations.

Defines the contract that all simulator backends (Isaac Sim, Gazebo, MuJoCo, PyBullet)
must implement. This enables PyRoboSimulator to be simulator-agnostic.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SimulatorType(Enum):
    """Supported simulator types."""

    ISAAC_SIM = "isaac_sim"
    GAZEBO = "gazebo"
    MUJOCO = "mujoco"
    PYBULLET = "pybullet"
    CUSTOM = "custom"


class RobotType(Enum):
    """Robot platform types."""

    QUADRUPED = "quadruped"
    WHEELED_UGV = "wheeled_ugv"
    HUMANOID = "humanoid"
    MANIPULATOR_ARM = "manipulator_arm"
    MOBILE_MANIPULATOR = "mobile_manipulator"
    DRONE = "drone"
    CUSTOM = "custom"


class SensorType(Enum):
    """Sensor types available in simulation."""

    RGB_CAMERA = "rgb_camera"
    DEPTH_CAMERA = "depth_camera"
    SEMANTIC_CAMERA = "semantic_camera"
    INSTANCE_SEGMENTATION = "instance_segmentation"
    LIDAR = "lidar"
    IMU = "imu"
    GPS = "gps"
    RADAR = "radar"
    CONTACT_SENSOR = "contact_sensor"
    THERMAL_CAMERA = "thermal_camera"


class PhysicsEngineType(Enum):
    """Physics engine types."""

    PHYSX = "physx"
    BULLET = "bullet"
    ODE = "ode"
    MUJOCO_PHYSICS = "mujoco_physics"
    CUSTOM = "custom"


class RenderingBackend(Enum):
    """Rendering backend types."""

    RTX = "rtx"
    OPENGL = "opengl"
    HEADLESS = "headless"
    RAYTRACING = "raytracing"


@dataclass
class SimulatorConfig:
    """Configuration for simulator initialization."""

    simulator_type: SimulatorType
    physics_engine: PhysicsEngineType
    rendering_backend: RenderingBackend
    headless_mode: bool = False
    gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81)
    timestep_ms: float = 1.0  # milliseconds
    max_substeps: int = 5
    additional_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotConfig:
    """Configuration for spawning a robot."""

    name: str
    robot_type: RobotType
    model_path: str  # URDF, USD, or MJCF path
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # quaternion
    scale: float = 1.0
    fixed_base: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorConfig:
    """Configuration for a sensor on a robot."""

    name: str
    sensor_type: SensorType
    parent_link: str  # Link this sensor is attached to
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    properties: Dict[str, Any] = field(default_factory=dict)  # sensor-specific


@dataclass
class CameraConfig(SensorConfig):
    """Camera-specific configuration."""

    width: int = 640
    height: int = 480
    fov: float = 90.0  # degrees
    near_plane: float = 0.01
    far_plane: float = 100.0
    lens_distortion: bool = False


@dataclass
class LidarConfig(SensorConfig):
    """Lidar-specific configuration."""

    num_beams: int = 32  # rays per scan
    scan_rate_hz: int = 10
    max_range: float = 100.0
    min_range: float = 0.1
    horizontal_fov: float = 360.0  # degrees
    vertical_fov: float = 15.0  # degrees


@dataclass
class IMUConfig(SensorConfig):
    """IMU-specific configuration."""

    accel_noise_stddev: float = 0.001
    gyro_noise_stddev: float = 0.001
    accel_bias_instability: float = 0.0
    gyro_bias_instability: float = 0.0


@dataclass
class WorldConfig:
    """Configuration for loading/creating a world."""

    name: str
    world_file_path: Optional[str] = None  # If loading from file
    gravity: Tuple[float, float, float] = (0.0, 0.0, -9.81)
    default_physics: PhysicsEngineType = PhysicsEngineType.PHYSX
    lighting_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotState:
    """Complete robot state snapshot."""

    robot_name: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float, float]  # quaternion
    linear_velocity: Tuple[float, float, float]
    angular_velocity: Tuple[float, float, float]
    joint_positions: Dict[str, float]  # joint_name -> angle/position
    joint_velocities: Dict[str, float]
    joint_forces: Dict[str, float]
    timestamp: float


@dataclass
class ObjectState:
    """Object/asset state snapshot."""

    object_name: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float, float]
    linear_velocity: Tuple[float, float, float]
    angular_velocity: Tuple[float, float, float]
    timestamp: float


@dataclass
class ContactInfo:
    """Information about a contact between two bodies."""

    body_a: str
    body_b: str
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    distance: float
    force_magnitude: float


@dataclass
class SensorData:
    """Generic sensor data container."""

    sensor_name: str
    sensor_type: SensorType
    timestamp: float
    raw_data: Any  # Numpy array, bytes, or sensor-specific type
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationStep:
    """Result of a simulation step."""

    step_count: int
    elapsed_time_sec: float
    timestep_ms: float
    robot_states: Dict[str, RobotState]  # robot_name -> state
    object_states: Dict[str, ObjectState]
    contacts: List[ContactInfo]
    sensor_data: Dict[str, SensorData]  # sensor_name -> data


class SimulatorBackend(ABC):
    """Abstract base class for all simulator backends.

    Implementations must provide all abstract methods.
    This interface defines 30+ core operations covering:
    - Initialization & shutdown
    - Scene management
    - Robot & asset management
    - Sensors & perception
    - Physics & dynamics
    - Rendering & visualization
    - Data capture & export
    """

    # ==================== INITIALIZATION & LIFECYCLE ====================

    @abstractmethod
    def initialize(self, config: SimulatorConfig) -> None:
        """Initialize simulator with given configuration.

        Args:
            config: Simulator configuration

        Raises:
            RuntimeError: If initialization fails
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleanly shutdown the simulator."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if simulator is running."""
        pass

    # ==================== WORLD MANAGEMENT ====================

    @abstractmethod
    def create_world(self, config: WorldConfig) -> str:
        """Create a new world/scene.

        Args:
            config: World configuration

        Returns:
            World ID/name
        """
        pass

    @abstractmethod
    def load_world(self, world_path: str) -> str:
        """Load world from file (USD, SDF, URDF, etc).

        Args:
            world_path: Path to world file

        Returns:
            World ID/name

        Raises:
            FileNotFoundError: If world file not found
        """
        pass

    @abstractmethod
    def save_world(self, world_id: str, output_path: str) -> None:
        """Save current world to file.

        Args:
            world_id: World ID
            output_path: Path to save
        """
        pass

    @abstractmethod
    def get_world_info(self, world_id: str) -> Dict[str, Any]:
        """Get world metadata and statistics.

        Args:
            world_id: World ID

        Returns:
            World info dictionary
        """
        pass

    # ==================== ROBOT MANAGEMENT ====================

    @abstractmethod
    def spawn_robot(self, robot_config: RobotConfig) -> str:
        """Spawn a robot in the world.

        Args:
            robot_config: Robot configuration

        Returns:
            Robot ID/name

        Raises:
            ValueError: If robot config invalid
            RuntimeError: If spawn fails
        """
        pass

    @abstractmethod
    def remove_robot(self, robot_name: str) -> None:
        """Remove robot from world.

        Args:
            robot_name: Robot name/ID
        """
        pass

    @abstractmethod
    def reset_robot(self, robot_name: str) -> None:
        """Reset robot to initial state (zero velocities, home pose).

        Args:
            robot_name: Robot name/ID
        """
        pass

    @abstractmethod
    def get_robot_state(self, robot_name: str) -> RobotState:
        """Get current state of robot.

        Args:
            robot_name: Robot name/ID

        Returns:
            Robot state
        """
        pass

    @abstractmethod
    def set_robot_pose(
        self,
        robot_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        """Set robot position and orientation.

        Args:
            robot_name: Robot name/ID
            position: XYZ position
            rotation: Quaternion rotation (x, y, z, w)
        """
        pass

    @abstractmethod
    def set_joint_target(
        self,
        robot_name: str,
        joint_name: str,
        target_value: float,
        velocity: float = 0.0,
        force: float = 1000.0,
    ) -> None:
        """Set target for a joint (position or velocity control).

        Args:
            robot_name: Robot name/ID
            joint_name: Joint name
            target_value: Target position/velocity
            velocity: Max velocity (for position control)
            force: Max force/torque
        """
        pass

    @abstractmethod
    def apply_joint_force(
        self, robot_name: str, joint_name: str, force: float
    ) -> None:
        """Apply force/torque directly to a joint.

        Args:
            robot_name: Robot name/ID
            joint_name: Joint name
            force: Force/torque value
        """
        pass

    @abstractmethod
    def get_joint_state(
        self, robot_name: str, joint_name: str
    ) -> Dict[str, float]:
        """Get joint state (position, velocity, force).

        Args:
            robot_name: Robot name/ID
            joint_name: Joint name

        Returns:
            Dictionary with position, velocity, force
        """
        pass

    # ==================== OBJECT/ASSET MANAGEMENT ====================

    @abstractmethod
    def spawn_object(
        self,
        name: str,
        model_path: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
        scale: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Spawn an object/asset in the world.

        Args:
            name: Object name
            model_path: Path to model file (USD, URDF, OBJ, etc)
            position: XYZ position
            rotation: Quaternion rotation
            scale: Scale factor
            metadata: Additional metadata

        Returns:
            Object ID/name
        """
        pass

    @abstractmethod
    def remove_object(self, object_name: str) -> None:
        """Remove object from world.

        Args:
            object_name: Object name/ID
        """
        pass

    @abstractmethod
    def get_object_state(self, object_name: str) -> ObjectState:
        """Get state of object.

        Args:
            object_name: Object name/ID

        Returns:
            Object state
        """
        pass

    @abstractmethod
    def set_object_pose(
        self,
        object_name: str,
        position: Tuple[float, float, float],
        rotation: Tuple[float, float, float, float],
    ) -> None:
        """Set object position and orientation.

        Args:
            object_name: Object name/ID
            position: XYZ position
            rotation: Quaternion rotation
        """
        pass

    # ==================== SENSOR MANAGEMENT ====================

    @abstractmethod
    def attach_sensor(
        self, robot_name: str, sensor_config: SensorConfig
    ) -> str:
        """Attach sensor to robot.

        Args:
            robot_name: Robot name/ID
            sensor_config: Sensor configuration

        Returns:
            Sensor ID/name
        """
        pass

    @abstractmethod
    def remove_sensor(self, robot_name: str, sensor_name: str) -> None:
        """Remove sensor from robot.

        Args:
            robot_name: Robot name/ID
            sensor_name: Sensor name/ID
        """
        pass

    @abstractmethod
    def get_sensor_data(self, robot_name: str, sensor_name: str) -> SensorData:
        """Get latest data from sensor.

        Args:
            robot_name: Robot name/ID
            sensor_name: Sensor name/ID

        Returns:
            Sensor data

        Raises:
            KeyError: If sensor not found
        """
        pass

    @abstractmethod
    def get_camera_image(
        self,
        robot_name: str,
        camera_name: str,
        include_depth: bool = False,
        include_segmentation: bool = False,
    ) -> Dict[str, Any]:
        """Get camera image(s) from robot.

        Args:
            robot_name: Robot name/ID
            camera_name: Camera name/ID
            include_depth: Include depth channel
            include_segmentation: Include semantic segmentation

        Returns:
            Dictionary with 'rgb' (HxWx3 uint8), optional 'depth', 'segmentation'
        """
        pass

    @abstractmethod
    def get_lidar_scan(
        self, robot_name: str, lidar_name: str
    ) -> Dict[str, Any]:
        """Get Lidar scan points.

        Args:
            robot_name: Robot name/ID
            lidar_name: Lidar name/ID

        Returns:
            Dictionary with 'points' (Nx3 float array), 'intensities', 'timestamps'
        """
        pass

    @abstractmethod
    def get_imu_data(self, robot_name: str, imu_name: str) -> Dict[str, Any]:
        """Get IMU data.

        Args:
            robot_name: Robot name/ID
            imu_name: IMU name/ID

        Returns:
            Dictionary with 'accel', 'gyro', 'quat', timestamp
        """
        pass

    # ==================== PHYSICS & DYNAMICS ====================

    @abstractmethod
    def set_gravity(self, gravity: Tuple[float, float, float]) -> None:
        """Set gravity vector.

        Args:
            gravity: Gravity XYZ
        """
        pass

    @abstractmethod
    def get_gravity(self) -> Tuple[float, float, float]:
        """Get current gravity vector.

        Returns:
            Gravity XYZ
        """
        pass

    @abstractmethod
    def set_timestep(self, timestep_ms: float) -> None:
        """Set simulation timestep.

        Args:
            timestep_ms: Timestep in milliseconds
        """
        pass

    @abstractmethod
    def get_contacts(self) -> List[ContactInfo]:
        """Get all current contacts in the world.

        Returns:
            List of contact information
        """
        pass

    @abstractmethod
    def raycast(
        self,
        origin: Tuple[float, float, float],
        direction: Tuple[float, float, float],
        max_distance: float = 1000.0,
    ) -> Optional[Dict[str, Any]]:
        """Cast a ray and find first intersection.

        Args:
            origin: Ray origin
            direction: Ray direction (should be normalized)
            max_distance: Max ray length

        Returns:
            Hit info (body_name, position, normal, distance) or None
        """
        pass

    # ==================== SIMULATION CONTROL ====================

    @abstractmethod
    def step(self, num_steps: int = 1) -> SimulationStep:
        """Advance simulation by one or more steps.

        Args:
            num_steps: Number of steps to advance

        Returns:
            Simulation step result with all state information
        """
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause simulation (keep state but don't advance)."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume paused simulation."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset entire simulation to initial state."""
        pass

    @abstractmethod
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        pass

    # ==================== RENDERING & VISUALIZATION ====================

    @abstractmethod
    def enable_rendering(self) -> None:
        """Enable rendering (if supported)."""
        pass

    @abstractmethod
    def disable_rendering(self) -> None:
        """Disable rendering for performance."""
        pass

    @abstractmethod
    def set_camera_view(
        self,
        position: Tuple[float, float, float],
        target: Tuple[float, float, float],
        up: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> None:
        """Set viewport camera position for rendering.

        Args:
            position: Camera position
            target: Look-at target
            up: Up vector
        """
        pass

    @abstractmethod
    def render_frame(self) -> Optional[bytes]:
        """Render and return current frame as image bytes.

        Returns:
            Frame data (PNG or other format), or None if headless
        """
        pass

    # ==================== DOMAIN RANDOMIZATION ====================

    @abstractmethod
    def randomize_lighting(
        self,
        intensity_range: Tuple[float, float],
        color_range: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None,
    ) -> None:
        """Randomize lighting in scene.

        Args:
            intensity_range: (min, max) light intensity
            color_range: ((r_min, g_min, b_min), (r_max, g_max, b_max))
        """
        pass

    @abstractmethod
    def randomize_friction(
        self, object_name: str, friction_range: Tuple[float, float]
    ) -> None:
        """Randomize friction for object.

        Args:
            object_name: Object name
            friction_range: (min, max) friction coefficient
        """
        pass

    @abstractmethod
    def randomize_mass(
        self, object_name: str, mass_range: Tuple[float, float]
    ) -> None:
        """Randomize mass for object.

        Args:
            object_name: Object name
            mass_range: (min, max) mass in kg
        """
        pass

    # ==================== UTILITIES & INFO ====================

    @abstractmethod
    def get_simulator_type(self) -> SimulatorType:
        """Get type of this simulator backend.

        Returns:
            SimulatorType enum
        """
        pass

    @abstractmethod
    def get_simulation_info(self) -> Dict[str, Any]:
        """Get overall simulation statistics and info.

        Returns:
            Info dictionary (step count, elapsed time, object count, etc)
        """
        pass

    @abstractmethod
    def list_robots(self) -> List[str]:
        """List all robots in world.

        Returns:
            Robot names/IDs
        """
        pass

    @abstractmethod
    def list_objects(self) -> List[str]:
        """List all objects in world.

        Returns:
            Object names/IDs
        """
        pass

    @abstractmethod
    def get_robot_info(self, robot_name: str) -> Dict[str, Any]:
        """Get detailed info about robot.

        Args:
            robot_name: Robot name/ID

        Returns:
            Info dictionary (joints, sensors, links, metadata)
        """
        pass

    # ==================== ERROR HANDLING & VALIDATION ====================

    @abstractmethod
    def validate_configuration(self, config: SimulatorConfig) -> bool:
        """Validate simulator configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            ValueError: If invalid
        """
        pass

    @abstractmethod
    def get_last_error(self) -> Optional[str]:
        """Get last error message if any.

        Returns:
            Error message or None
        """
        pass
