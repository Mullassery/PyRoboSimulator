"""Sensor Definitions and Configuration - Phase 5.0.

Comprehensive sensor taxonomy for PyRoboSimulator. Defines all supported sensor types,
categories, and parameters. Only data from selected sensors is generated.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SensorCategory(Enum):
    """Top-level sensor categories."""

    VISION = "vision"
    DEPTH = "depth"
    THERMAL = "thermal"
    INFRARED = "infrared"
    EVENT_CAMERA = "event_camera"
    MULTISPECTRAL = "multispectral"
    HYPERSPECTRAL = "hyperspectral"
    LIDAR_2D = "lidar_2d"
    LIDAR_3D = "lidar_3d"
    RADAR = "radar"
    ULTRASONIC = "ultrasonic"
    IMU = "imu"
    GNSS = "gnss"
    COMPASS = "compass"
    BAROMETER = "barometer"
    WHEEL_ENCODER = "wheel_encoder"
    STEERING_ENCODER = "steering_encoder"
    MOTOR_SENSOR = "motor_sensor"
    FORCE_TORQUE = "force_torque"
    TACTILE = "tactile"
    PRESSURE = "pressure"
    PROXIMITY = "proximity"
    HALL_EFFECT = "hall_effect"
    ENVIRONMENTAL = "environmental"
    AIR_QUALITY = "air_quality"
    GAS = "gas"
    MICROPHONE = "microphone"
    VIBRATION = "vibration"
    BATTERY = "battery"
    SYSTEM_MONITOR = "system_monitor"
    SPECIALIZED = "specialized"
    VIRTUAL = "virtual"


class SensorType(Enum):
    """Specific sensor types."""

    # Vision
    RGB_CAMERA = "rgb_camera"
    STEREO_CAMERA = "stereo_camera"
    GLOBAL_SHUTTER = "global_shutter"
    ROLLING_SHUTTER = "rolling_shutter"
    WIDE_ANGLE = "wide_angle"
    TELEPHOTO = "telephoto"
    FISHEYE = "fisheye"

    # Depth
    STRUCTURED_LIGHT = "structured_light"
    TIME_OF_FLIGHT = "time_of_flight"
    STEREO_DEPTH = "stereo_depth"
    REALSENSE = "realsense"
    AZURE_KINECT = "azure_kinect"

    # Thermal
    THERMAL_CAMERA = "thermal_camera"

    # Infrared
    INFRARED_CAMERA = "infrared_camera"
    NIGHT_VISION = "night_vision"

    # Event Camera
    EVENT_CAMERA = "event_camera"

    # Multispectral/Hyperspectral
    MULTISPECTRAL_CAMERA = "multispectral_camera"
    HYPERSPECTRAL_CAMERA = "hyperspectral_camera"

    # LiDAR
    LIDAR_2D = "lidar_2d"
    VELODYNE_LIDAR = "velodyne_lidar"
    OUSTER_LIDAR = "ouster_lidar"
    HESAI_LIDAR = "hesai_lidar"
    LIVOX_LIDAR = "livox_lidar"
    SOLID_STATE_LIDAR = "solid_state_lidar"

    # Radar
    FMCW_RADAR = "fmcw_radar"
    IMAGING_RADAR = "imaging_radar"
    MILLIMETER_WAVE_RADAR = "millimeter_wave_radar"

    # Ultrasonic
    ULTRASONIC_SENSOR = "ultrasonic_sensor"

    # Navigation
    IMU = "imu"
    GPS = "gps"
    RTK_GPS = "rtk_gps"
    COMPASS = "compass"
    BAROMETER = "barometer"
    ALTIMETER = "altimeter"

    # Mobility
    WHEEL_ENCODER = "wheel_encoder"
    STEERING_ENCODER = "steering_encoder"
    MOTOR_RPM = "motor_rpm"
    MOTOR_TORQUE = "motor_torque"

    # Manipulation
    FORCE_TORQUE_SENSOR = "force_torque_sensor"
    TACTILE_SENSOR = "tactile_sensor"
    PRESSURE_SENSOR = "pressure_sensor"
    PROXIMITY_SENSOR = "proximity_sensor"
    HALL_EFFECT_SENSOR = "hall_effect_sensor"

    # Environmental
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    RAIN_SENSOR = "rain_sensor"
    WIND_SENSOR = "wind_sensor"
    UV_SENSOR = "uv_sensor"
    LIGHT_SENSOR = "light_sensor"

    # Air Quality / Gas
    CO2_SENSOR = "co2_sensor"
    VOC_SENSOR = "voc_sensor"
    PM_SENSOR = "pm_sensor"
    GAS_SENSOR = "gas_sensor"
    SMOKE_DETECTOR = "smoke_detector"

    # Audio
    MICROPHONE = "microphone"
    MICROPHONE_ARRAY = "microphone_array"

    # Health Monitoring
    VIBRATION_SENSOR = "vibration_sensor"
    BATTERY_MONITOR = "battery_monitor"
    SYSTEM_MONITOR = "system_monitor"

    # Specialized
    RADIATION_SENSOR = "radiation_sensor"
    CHEMICAL_SENSOR = "chemical_sensor"
    METAL_DETECTOR = "metal_detector"
    SOIL_MOISTURE = "soil_moisture"
    WATER_QUALITY = "water_quality"
    SONAR = "sonar"
    DVL = "dvl"  # Doppler Velocity Log
    ACOUSTIC_MODEM = "acoustic_modem"

    # Virtual
    GROUND_TRUTH_POSE = "ground_truth_pose"
    GROUND_TRUTH_VELOCITY = "ground_truth_velocity"
    SEMANTIC_SEGMENTATION = "semantic_segmentation"
    INSTANCE_SEGMENTATION = "instance_segmentation"
    OBJECT_DETECTION = "object_detection"
    OBJECT_TRACKING = "object_tracking"
    OPTICAL_FLOW = "optical_flow"
    OCCUPANCY_GRID = "occupancy_grid"
    TRAVERSABILITY_MAP = "traversability_map"
    SLAM_MAP = "slam_map"


@dataclass
class SensorParameter:
    """Configurable sensor parameter."""

    name: str
    type: str  # "float", "int", "bool", "string", "enum"
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    unit: str = ""
    enum_values: Optional[List[str]] = None


@dataclass
class SensorMountPoint:
    """Sensor mounting configuration."""

    frame: str  # "base_link", "chassis", "head", etc
    position: Tuple[float, float, float]  # x, y, z in meters
    orientation: Tuple[float, float, float, float]  # quaternion (x, y, z, w)
    mount_type: str = "fixed"  # "fixed", "articulated", "rotating"


@dataclass
class SensorNoiseModel:
    """Sensor noise and degradation model."""

    gaussian_noise: float = 0.0  # Standard deviation
    bias: float = 0.0  # Systematic bias
    drift: float = 0.0  # Time-dependent drift
    salt_pepper_probability: float = 0.0  # Random pixel errors
    dropout_probability: float = 0.0  # Occasional missing data
    motion_blur: bool = False
    thermal_noise: bool = False
    quantization_bits: Optional[int] = None
    latency_ms: float = 0.0


@dataclass
class SensorSpec:
    """Complete sensor specification."""

    sensor_id: str
    sensor_type: SensorType
    category: SensorCategory
    name: str
    description: str

    # Core parameters
    frequency_hz: float = 30.0
    resolution_x: int = 640
    resolution_y: int = 480
    field_of_view_h: float = 90.0
    field_of_view_v: float = 60.0
    detection_range_min: float = 0.1
    detection_range_max: float = 100.0

    # Mounting
    mount_point: SensorMountPoint = field(default_factory=lambda: SensorMountPoint(
        frame="base_link",
        position=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 1.0),
    ))

    # Noise and degradation
    noise_model: SensorNoiseModel = field(default_factory=SensorNoiseModel)

    # ROS configuration
    ros_topic: str = ""
    ros_frame_id: str = "base_link"
    message_type: str = ""

    # Output configuration
    output_format: str = "raw"  # "raw", "compressed", "custom"
    data_compression: Optional[str] = None  # "jpeg", "png", "h264", etc

    # Recording and logging
    record_enabled: bool = True
    record_rate_hz: Optional[float] = None  # None = same as frequency

    # Custom parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "category": self.category.value,
            "name": self.name,
            "frequency_hz": self.frequency_hz,
            "resolution": f"{self.resolution_x}x{self.resolution_y}",
            "fov": f"{self.field_of_view_h}H x {self.field_of_view_v}V",
            "range": f"{self.detection_range_min}-{self.detection_range_max}m",
        }


class SensorRegistry:
    """Registry of all supported sensor types and their specs."""

    # Default sensor specs
    DEFAULT_SPECS = {
        SensorType.RGB_CAMERA: SensorSpec(
            sensor_id="rgb_camera_default",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB Camera",
            description="Standard RGB camera",
            frequency_hz=30.0,
            resolution_x=1920,
            resolution_y=1080,
            field_of_view_h=68.0,
            field_of_view_v=41.0,
            detection_range_max=50.0,
        ),
        SensorType.VELODYNE_LIDAR: SensorSpec(
            sensor_id="lidar_3d_default",
            sensor_type=SensorType.VELODYNE_LIDAR,
            category=SensorCategory.LIDAR_3D,
            name="Velodyne 3D LiDAR",
            description="32-channel 3D LiDAR",
            frequency_hz=10.0,
            resolution_x=2048,
            resolution_y=32,
            field_of_view_h=360.0,
            field_of_view_v=40.0,
            detection_range_max=100.0,
        ),
        SensorType.IMU: SensorSpec(
            sensor_id="imu_default",
            sensor_type=SensorType.IMU,
            category=SensorCategory.IMU,
            name="IMU",
            description="9-DoF IMU (accel, gyro, mag)",
            frequency_hz=100.0,
            detection_range_max=0.0,  # N/A for IMU
        ),
        SensorType.THERMAL_CAMERA: SensorSpec(
            sensor_id="thermal_camera_default",
            sensor_type=SensorType.THERMAL_CAMERA,
            category=SensorCategory.THERMAL,
            name="Thermal Camera",
            description="Thermal imaging camera",
            frequency_hz=30.0,
            resolution_x=640,
            resolution_y=512,
            field_of_view_h=60.0,
            field_of_view_v=48.0,
            detection_range_max=500.0,
        ),
        SensorType.FMCW_RADAR: SensorSpec(
            sensor_id="radar_default",
            sensor_type=SensorType.FMCW_RADAR,
            category=SensorCategory.RADAR,
            name="FMCW Radar",
            description="77 GHz FMCW Radar",
            frequency_hz=20.0,
            field_of_view_h=120.0,
            field_of_view_v=30.0,
            detection_range_max=200.0,
        ),
    }

    def __init__(self):
        """Initialize registry."""
        self._registry: Dict[SensorType, SensorSpec] = dict(self.DEFAULT_SPECS)

    def register_sensor_spec(self, spec: SensorSpec) -> None:
        """Register a sensor specification.

        Args:
            spec: Sensor specification
        """
        self._registry[spec.sensor_type] = spec
        logger.info(f"Registered sensor: {spec.name}")

    def get_sensor_spec(self, sensor_type: SensorType) -> Optional[SensorSpec]:
        """Get sensor specification.

        Args:
            sensor_type: Sensor type

        Returns:
            Sensor spec or None
        """
        return self._registry.get(sensor_type)

    def get_sensors_by_category(self, category: SensorCategory) -> List[SensorSpec]:
        """Get all sensors in a category.

        Args:
            category: Sensor category

        Returns:
            List of sensor specs
        """
        return [spec for spec in self._registry.values() if spec.category == category]

    def list_all_sensors(self) -> List[str]:
        """List all registered sensor types.

        Returns:
            List of sensor type names
        """
        return [st.value for st in self._registry.keys()]


# Global registry instance
SENSOR_REGISTRY = SensorRegistry()
