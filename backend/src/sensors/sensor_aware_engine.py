"""Sensor-Aware Simulation Engine - Phase 5.0.

Enforces sensor constraints throughout simulation.
Only generates data for configured sensors. Optimizes compute accordingly.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from backend.src.sensors.sensor_definitions import (
    SensorCategory,
    SensorType,
)
from backend.src.sensors.sensor_configuration import (
    SensorConfigurationManager,
    SensorSuite,
)

logger = logging.getLogger(__name__)


class SensorAwarenessConstraint:
    """Enforces sensor awareness constraints in simulation."""

    def __init__(self, sensor_suite: SensorSuite):
        """Initialize constraint.

        Args:
            sensor_suite: Robot sensor suite
        """
        self._sensor_suite = sensor_suite
        self._enabled_categories = self._compute_enabled_categories()
        self._enabled_types = self._compute_enabled_types()

    def _compute_enabled_categories(self) -> Set[SensorCategory]:
        """Compute enabled sensor categories.

        Returns:
            Set of enabled categories
        """
        enabled = set()

        for sensor in self._sensor_suite.sensors.values():
            if sensor.record_enabled:
                enabled.add(sensor.category)

        return enabled

    def _compute_enabled_types(self) -> Set[SensorType]:
        """Compute enabled sensor types.

        Returns:
            Set of enabled types
        """
        enabled = set()

        for sensor in self._sensor_suite.sensors.values():
            if sensor.record_enabled:
                enabled.add(sensor.sensor_type)

        return enabled

    def can_generate_data(self, data_type: str) -> bool:
        """Check if data type can be generated.

        Args:
            data_type: Data type ("rgb", "depth", "thermal", "lidar", etc)

        Returns:
            True if any sensor can provide this data
        """
        type_mapping = {
            "rgb": [SensorCategory.VISION],
            "stereo": [SensorCategory.VISION],
            "depth": [SensorCategory.DEPTH],
            "thermal": [SensorCategory.THERMAL],
            "infrared": [SensorCategory.INFRARED],
            "event": [SensorCategory.EVENT_CAMERA],
            "multispectral": [SensorCategory.MULTISPECTRAL],
            "hyperspectral": [SensorCategory.HYPERSPECTRAL],
            "lidar_2d": [SensorCategory.LIDAR_2D],
            "lidar_3d": [SensorCategory.LIDAR_3D],
            "radar": [SensorCategory.RADAR],
            "ultrasonic": [SensorCategory.ULTRASONIC],
            "imu": [SensorCategory.IMU],
            "gnss": [SensorCategory.GNSS],
            "compass": [SensorCategory.COMPASS],
            "audio": [SensorCategory.MICROPHONE],
        }

        required_categories = type_mapping.get(data_type, [])

        return any(cat in self._enabled_categories for cat in required_categories)

    def get_rendering_modules(self) -> Dict[str, bool]:
        """Get which rendering modules should be initialized.

        Returns:
            Dictionary of module_name -> should_initialize
        """
        return {
            "rgb_renderer": SensorCategory.VISION in self._enabled_categories,
            "depth_renderer": SensorCategory.DEPTH in self._enabled_categories,
            "thermal_engine": SensorCategory.THERMAL in self._enabled_categories,
            "lidar_engine": (
                SensorCategory.LIDAR_2D in self._enabled_categories
                or SensorCategory.LIDAR_3D in self._enabled_categories
            ),
            "radar_engine": SensorCategory.RADAR in self._enabled_categories,
            "audio_engine": SensorCategory.MICROPHONE in self._enabled_categories,
        }

    def get_data_generation_modules(self) -> Dict[str, bool]:
        """Get which data generation modules should be initialized.

        Returns:
            Dictionary of module_name -> should_initialize
        """
        return {
            "rgb_generator": self.can_generate_data("rgb"),
            "depth_generator": self.can_generate_data("depth"),
            "thermal_generator": self.can_generate_data("thermal"),
            "lidar_generator": (
                self.can_generate_data("lidar_2d")
                or self.can_generate_data("lidar_3d")
            ),
            "radar_generator": self.can_generate_data("radar"),
            "audio_generator": self.can_generate_data("audio"),
            "imu_generator": self.can_generate_data("imu"),
            "gnss_generator": self.can_generate_data("gnss"),
        }

    def get_synthetic_dataset_generators(self) -> Dict[str, bool]:
        """Get which synthetic data generators should be active.

        Returns:
            Dictionary of generator_name -> should_generate
        """
        return {
            "coco_detector": self.can_generate_data("rgb"),
            "yolo_detector": self.can_generate_data("rgb"),
            "segmentation": self.can_generate_data("rgb"),
            "depth_dataset": self.can_generate_data("depth"),
            "thermal_dataset": self.can_generate_data("thermal"),
            "lidar_dataset": (
                self.can_generate_data("lidar_2d")
                or self.can_generate_data("lidar_3d")
            ),
            "radar_dataset": self.can_generate_data("radar"),
            "multimodal_dataset": (
                self.can_generate_data("rgb")
                and self.can_generate_data("depth")
            ),
        }

    def get_available_outputs(self) -> Dict[str, List[str]]:
        """Get available simulation outputs for this sensor suite.

        Returns:
            Dictionary of output_type -> list of available streams
        """
        outputs = {}

        for sensor_id, sensor in self._sensor_suite.sensors.items():
            if not sensor.record_enabled:
                continue

            category = sensor.category.value

            if category not in outputs:
                outputs[category] = []

            outputs[category].append(sensor_id)

        return outputs

    def get_compute_optimization_profile(self) -> Dict[str, Any]:
        """Get compute optimization profile based on sensor suite.

        Returns:
            Optimization profile for simulation engine
        """
        rendering_mods = self.get_rendering_modules()
        data_gen_mods = self.get_data_generation_modules()

        enabled_renderers = sum(1 for v in rendering_mods.values() if v)
        enabled_generators = sum(1 for v in data_gen_mods.values() if v)

        return {
            "active_renderers": enabled_renderers,
            "active_generators": enabled_generators,
            "rendering_modules": rendering_mods,
            "data_generation_modules": data_gen_mods,
            "estimated_compute_fraction": min(
                (enabled_renderers + enabled_generators) / 16.0, 1.0
            ),  # Assume max 16 modules
            "optimization_hints": self._generate_optimization_hints(),
        }

    def _generate_optimization_hints(self) -> List[str]:
        """Generate optimization hints based on sensor suite.

        Returns:
            List of optimization hints
        """
        hints = []

        if not self.can_generate_data("rgb"):
            hints.append("RGB rendering disabled - save GPU memory")

        if not self.can_generate_data("lidar_3d"):
            hints.append("3D LiDAR point cloud generation disabled")

        if not self.can_generate_data("thermal"):
            hints.append("Thermal simulation engine disabled")

        if not self.can_generate_data("audio"):
            hints.append("Audio simulation engine disabled")

        if self._sensor_suite.get_sensor_count() < 3:
            hints.append("Minimal sensor suite - can run at higher speed")

        if self._sensor_suite.get_sensor_count() > 10:
            hints.append("Large sensor suite - consider distributed simulation")

        return hints


class SensorAwareSimulationEngine:
    """Simulation engine that respects sensor constraints.

    Ensures only configured sensors generate data.
    Optimizes compute based on sensor profile.
    """

    def __init__(self, config_manager: SensorConfigurationManager):
        """Initialize engine.

        Args:
            config_manager: Sensor configuration manager
        """
        self._config_manager = config_manager
        self._active_constraints: Dict[str, SensorAwarenessConstraint] = {}

    def initialize_simulation(self, robot_name: str) -> bool:
        """Initialize simulation for robot.

        Must complete sensor configuration before this step.

        Args:
            robot_name: Robot name

        Returns:
            True if initialization successful
        """
        suite = self._config_manager.get_suite(robot_name)

        if not suite:
            logger.error(f"Robot {robot_name} has no sensor configuration. " +
                        "Complete sensor configuration phase first.")
            return False

        # Validate suite
        errors = self._config_manager.validate_suite(suite)

        if errors:
            logger.error(f"Sensor configuration invalid for {robot_name}: {errors}")
            return False

        # Create constraint
        constraint = SensorAwarenessConstraint(suite)
        self._active_constraints[robot_name] = constraint

        logger.info(f"Initialized sensor-aware simulation for {robot_name}")
        logger.info(f"Sensor constraint: {suite.get_sensor_count()} sensors active")

        # Log optimization profile
        profile = constraint.get_compute_optimization_profile()
        logger.info(f"Compute optimization: {profile['active_renderers']} renderers, "
                   f"{profile['active_generators']} generators")

        for hint in profile["optimization_hints"]:
            logger.info(f"  → {hint}")

        return True

    def get_constraint(self, robot_name: str) -> Optional[SensorAwarenessConstraint]:
        """Get sensor constraint for robot.

        Args:
            robot_name: Robot name

        Returns:
            Constraint or None if not initialized
        """
        return self._active_constraints.get(robot_name)

    def can_generate_data(self, robot_name: str, data_type: str) -> bool:
        """Check if data can be generated for robot.

        Args:
            robot_name: Robot name
            data_type: Data type

        Returns:
            True if data can be generated
        """
        constraint = self.get_constraint(robot_name)

        if not constraint:
            return False

        return constraint.can_generate_data(data_type)

    def get_simulation_profile(self, robot_name: str) -> Dict[str, Any]:
        """Get complete simulation profile for robot.

        Includes sensor configuration, constraints, and compute optimization.

        Args:
            robot_name: Robot name

        Returns:
            Simulation profile
        """
        suite = self._config_manager.get_suite(robot_name)
        constraint = self.get_constraint(robot_name)

        if not suite or not constraint:
            return {"status": "not_configured"}

        return {
            "robot_name": robot_name,
            "status": "configured_and_initialized",
            "sensor_suite": suite.to_dict(),
            "available_outputs": constraint.get_available_outputs(),
            "compute_profile": constraint.get_compute_optimization_profile(),
            "rendering_modules": constraint.get_rendering_modules(),
            "data_generation_modules": constraint.get_data_generation_modules(),
            "synthetic_dataset_generators": constraint.get_synthetic_dataset_generators(),
        }

    def get_mandatory_initialization_status(self) -> Dict[str, Any]:
        """Get status of mandatory sensor configuration phase.

        Returns:
            Status dictionary
        """
        configured_robots = self._config_manager.list_configured_robots()
        initialized_robots = list(self._active_constraints.keys())

        return {
            "configured_robots": configured_robots,
            "initialized_robots": initialized_robots,
            "pending_initialization": [
                r for r in configured_robots
                if r not in initialized_robots
            ],
            "total_configured": len(configured_robots),
            "total_initialized": len(initialized_robots),
        }
