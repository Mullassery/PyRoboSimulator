"""Sensor Configuration Manager - Phase 5.0.

Manages robot sensor configuration. Mandatory initialization phase.
Only selected sensors generate data during simulation.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.sensors.sensor_definitions import (
    SensorCategory,
    SensorType,
    SensorSpec,
    SensorRegistry,
    SENSOR_REGISTRY,
)

logger = logging.getLogger(__name__)


@dataclass
class SensorSuite:
    """Complete sensor configuration for a robot."""

    robot_name: str
    sensors: Dict[str, SensorSpec] = field(default_factory=dict)
    creation_timestamp: float = field(default_factory=lambda: 0.0)

    def add_sensor(self, sensor_id: str, sensor_spec: SensorSpec) -> None:
        """Add sensor to suite.

        Args:
            sensor_id: Unique sensor ID
            sensor_spec: Sensor specification
        """
        self.sensors[sensor_id] = sensor_spec
        logger.info(f"Added sensor {sensor_id} ({sensor_spec.name}) to {self.robot_name}")

    def remove_sensor(self, sensor_id: str) -> bool:
        """Remove sensor from suite.

        Args:
            sensor_id: Sensor ID to remove

        Returns:
            True if removed, False if not found
        """
        if sensor_id in self.sensors:
            del self.sensors[sensor_id]
            logger.info(f"Removed sensor {sensor_id} from {self.robot_name}")
            return True

        return False

    def get_sensor(self, sensor_id: str) -> Optional[SensorSpec]:
        """Get sensor specification.

        Args:
            sensor_id: Sensor ID

        Returns:
            Sensor spec or None
        """
        return self.sensors.get(sensor_id)

    def get_sensors_by_type(self, sensor_type: SensorType) -> List[SensorSpec]:
        """Get all sensors of a type.

        Args:
            sensor_type: Sensor type

        Returns:
            List of matching sensors
        """
        return [s for s in self.sensors.values() if s.sensor_type == sensor_type]

    def get_sensors_by_category(self, category: SensorCategory) -> List[SensorSpec]:
        """Get all sensors in a category.

        Args:
            category: Sensor category

        Returns:
            List of matching sensors
        """
        return [s for s in self.sensors.values() if s.category == category]

    def has_sensor_category(self, category: SensorCategory) -> bool:
        """Check if suite has sensors in category.

        Args:
            category: Sensor category

        Returns:
            True if any sensor in category
        """
        return len(self.get_sensors_by_category(category)) > 0

    def get_sensor_count(self) -> int:
        """Get total sensor count.

        Returns:
            Number of sensors
        """
        return len(self.sensors)

    def get_active_sensor_count(self) -> int:
        """Get count of actively recording sensors.

        Returns:
            Count of recording sensors
        """
        return sum(1 for s in self.sensors.values() if s.record_enabled)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "robot_name": self.robot_name,
            "sensor_count": self.get_sensor_count(),
            "recording_count": self.get_active_sensor_count(),
            "sensors": {
                sid: spec.to_dict()
                for sid, spec in self.sensors.items()
            },
            "categories": {
                category.value: len(self.get_sensors_by_category(category))
                for category in SensorCategory
            },
        }


class SensorConfigurationManager:
    """Manages sensor configuration during simulation initialization.

    This is a mandatory initialization phase. The user must complete
    sensor configuration before simulation begins.
    """

    def __init__(self, sensor_registry: Optional[SensorRegistry] = None):
        """Initialize configuration manager.

        Args:
            sensor_registry: Sensor registry (uses global if not provided)
        """
        self._registry = sensor_registry or SENSOR_REGISTRY
        self._configured_suites: Dict[str, SensorSuite] = {}
        self._validation_rules: List[callable] = []

    def create_empty_suite(self, robot_name: str) -> SensorSuite:
        """Create empty sensor suite for robot.

        Args:
            robot_name: Robot name

        Returns:
            Empty sensor suite
        """
        suite = SensorSuite(robot_name=robot_name)
        logger.info(f"Created empty sensor suite for {robot_name}")
        return suite

    def create_standard_suite(
        self, robot_name: str, platform_type: str = "mobile"
    ) -> SensorSuite:
        """Create standard sensor suite based on platform type.

        Args:
            robot_name: Robot name
            platform_type: "mobile", "aerial", "humanoid", "manipulator", "aquatic"

        Returns:
            Pre-configured sensor suite
        """
        suite = SensorSuite(robot_name=robot_name)

        # Mobile robot: RGB camera, LiDAR, IMU, GPS, wheel encoders
        if platform_type == "mobile":
            suite.add_sensor("rgb_front", self._create_sensor_instance(
                SensorType.RGB_CAMERA, "rgb_front"
            ))
            suite.add_sensor("lidar_main", self._create_sensor_instance(
                SensorType.VELODYNE_LIDAR, "lidar_main"
            ))
            suite.add_sensor("imu", self._create_sensor_instance(
                SensorType.IMU, "imu"
            ))
            suite.add_sensor("gps", self._create_sensor_instance(
                SensorType.GPS, "gps"
            ))
            suite.add_sensor("wheel_encoders", self._create_sensor_instance(
                SensorType.WHEEL_ENCODER, "wheel_encoders"
            ))

        # Aerial robot: RGB camera, thermal, IMU, GPS, wind sensor
        elif platform_type == "aerial":
            suite.add_sensor("rgb_main", self._create_sensor_instance(
                SensorType.RGB_CAMERA, "rgb_main"
            ))
            suite.add_sensor("thermal", self._create_sensor_instance(
                SensorType.THERMAL_CAMERA, "thermal"
            ))
            suite.add_sensor("imu", self._create_sensor_instance(
                SensorType.IMU, "imu"
            ))
            suite.add_sensor("gps", self._create_sensor_instance(
                SensorType.GPS, "gps"
            ))
            suite.add_sensor("wind_sensor", self._create_sensor_instance(
                SensorType.WIND_SENSOR, "wind_sensor"
            ))

        # Humanoid robot: stereo, IMU, force-torque sensors, tactile
        elif platform_type == "humanoid":
            suite.add_sensor("stereo_vision", self._create_sensor_instance(
                SensorType.STEREO_CAMERA, "stereo_vision"
            ))
            suite.add_sensor("imu_torso", self._create_sensor_instance(
                SensorType.IMU, "imu_torso"
            ))
            suite.add_sensor("ft_left_hand", self._create_sensor_instance(
                SensorType.FORCE_TORQUE_SENSOR, "ft_left_hand"
            ))
            suite.add_sensor("ft_right_hand", self._create_sensor_instance(
                SensorType.FORCE_TORQUE_SENSOR, "ft_right_hand"
            ))
            suite.add_sensor("tactile_hands", self._create_sensor_instance(
                SensorType.TACTILE_SENSOR, "tactile_hands"
            ))

        # Manipulator: force-torque, joint encoders, tactile
        elif platform_type == "manipulator":
            suite.add_sensor("ft_wrist", self._create_sensor_instance(
                SensorType.FORCE_TORQUE_SENSOR, "ft_wrist"
            ))
            suite.add_sensor("joint_encoders", self._create_sensor_instance(
                SensorType.STEERING_ENCODER, "joint_encoders"
            ))
            suite.add_sensor("tactile_gripper", self._create_sensor_instance(
                SensorType.TACTILE_SENSOR, "tactile_gripper"
            ))

        # Aquatic robot: sonar, depth sensor, DVL
        elif platform_type == "aquatic":
            suite.add_sensor("sonar", self._create_sensor_instance(
                SensorType.SONAR, "sonar"
            ))
            suite.add_sensor("depth_sensor", self._create_sensor_instance(
                SensorType.TIME_OF_FLIGHT, "depth_sensor"
            ))
            suite.add_sensor("dvl", self._create_sensor_instance(
                SensorType.DVL, "dvl"
            ))

        logger.info(f"Created standard {platform_type} sensor suite for {robot_name}")
        return suite

    def _create_sensor_instance(self, sensor_type: SensorType, instance_id: str) -> SensorSpec:
        """Create sensor instance from registry spec.

        Args:
            sensor_type: Sensor type
            instance_id: Instance identifier

        Returns:
            Sensor spec with instance ID
        """
        base_spec = self._registry.get_sensor_spec(sensor_type)

        if not base_spec:
            raise ValueError(f"Unknown sensor type: {sensor_type.value}")

        # Create a copy with instance ID
        spec = SensorSpec(
            sensor_id=instance_id,
            sensor_type=base_spec.sensor_type,
            category=base_spec.category,
            name=base_spec.name,
            description=base_spec.description,
            frequency_hz=base_spec.frequency_hz,
            resolution_x=base_spec.resolution_x,
            resolution_y=base_spec.resolution_y,
            field_of_view_h=base_spec.field_of_view_h,
            field_of_view_v=base_spec.field_of_view_v,
            detection_range_min=base_spec.detection_range_min,
            detection_range_max=base_spec.detection_range_max,
            mount_point=base_spec.mount_point,
            noise_model=base_spec.noise_model,
        )

        return spec

    def register_suite(self, suite: SensorSuite) -> None:
        """Register configured sensor suite.

        Args:
            suite: Sensor suite to register
        """
        self._configured_suites[suite.robot_name] = suite

        # Run validation
        errors = self.validate_suite(suite)

        if errors:
            logger.warning(f"Sensor suite validation warnings: {errors}")

        logger.info(f"Registered sensor suite for {suite.robot_name}: {suite.get_sensor_count()} sensors")

    def get_suite(self, robot_name: str) -> Optional[SensorSuite]:
        """Get registered sensor suite.

        Args:
            robot_name: Robot name

        Returns:
            Sensor suite or None
        """
        return self._configured_suites.get(robot_name)

    def validate_suite(self, suite: SensorSuite) -> List[str]:
        """Validate sensor suite configuration.

        Args:
            suite: Sensor suite to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check minimum sensors
        if suite.get_sensor_count() == 0:
            errors.append("Robot must have at least one sensor")

        # Run registered validation rules
        for rule in self._validation_rules:
            rule_errors = rule(suite)

            if rule_errors:
                errors.extend(rule_errors)

        return errors

    def add_validation_rule(self, rule: callable) -> None:
        """Add custom validation rule.

        Args:
            rule: Callable that takes SensorSuite and returns list of errors
        """
        self._validation_rules.append(rule)

    def get_configuration_summary(self, robot_name: str) -> Dict[str, Any]:
        """Get configuration summary for robot.

        Args:
            robot_name: Robot name

        Returns:
            Configuration summary
        """
        suite = self.get_suite(robot_name)

        if not suite:
            return {"status": "not_configured"}

        return {
            "status": "configured",
            "robot_name": robot_name,
            "total_sensors": suite.get_sensor_count(),
            "recording_sensors": suite.get_active_sensor_count(),
            "categories": {
                cat.value: len(suite.get_sensors_by_category(cat))
                for cat in SensorCategory
            },
            "sensors": suite.to_dict()["sensors"],
        }

    def list_configured_robots(self) -> List[str]:
        """List all configured robots.

        Returns:
            Robot names
        """
        return list(self._configured_suites.keys())
