"""Tests for Sensor Configuration and Awareness System - Phase 5.0."""

import pytest

from backend.src.sensors.sensor_definitions import (
    SensorCategory,
    SensorType,
    SensorSpec,
    SensorRegistry,
    SENSOR_REGISTRY,
)
from backend.src.sensors.sensor_configuration import (
    SensorSuite,
    SensorConfigurationManager,
)
from backend.src.sensors.sensor_aware_engine import (
    SensorAwarenessConstraint,
    SensorAwareSimulationEngine,
)


class TestSensorDefinitions:
    """Test sensor definitions and registry."""

    def test_sensor_category_enum(self):
        """Test sensor category enumerations."""
        assert SensorCategory.VISION.value == "vision"
        assert SensorCategory.LIDAR_3D.value == "lidar_3d"
        assert SensorCategory.THERMAL.value == "thermal"

    def test_sensor_type_enum(self):
        """Test sensor type enumerations."""
        assert SensorType.RGB_CAMERA.value == "rgb_camera"
        assert SensorType.VELODYNE_LIDAR.value == "velodyne_lidar"
        assert SensorType.THERMAL_CAMERA.value == "thermal_camera"

    def test_sensor_spec_creation(self):
        """Test creating sensor spec."""
        spec = SensorSpec(
            sensor_id="camera_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="Front RGB Camera",
            description="Main RGB camera",
            frequency_hz=30.0,
            resolution_x=1920,
            resolution_y=1080,
        )

        assert spec.sensor_id == "camera_1"
        assert spec.frequency_hz == 30.0
        assert spec.resolution_x == 1920

    def test_sensor_registry(self):
        """Test sensor registry."""
        registry = SensorRegistry()

        # Check defaults registered
        spec = registry.get_sensor_spec(SensorType.RGB_CAMERA)
        assert spec is not None
        assert spec.name == "RGB Camera"

        # Get sensors by category
        vision_sensors = registry.get_sensors_by_category(SensorCategory.VISION)
        assert len(vision_sensors) > 0

    def test_sensor_spec_serialization(self):
        """Test sensor spec serialization."""
        spec = SensorSpec(
            sensor_id="lidar_1",
            sensor_type=SensorType.VELODYNE_LIDAR,
            category=SensorCategory.LIDAR_3D,
            name="Velodyne HDL-32",
            description="32-channel LiDAR",
        )

        d = spec.to_dict()
        assert d["sensor_id"] == "lidar_1"
        assert d["sensor_type"] == "velodyne_lidar"
        assert d["name"] == "Velodyne HDL-32"


class TestSensorSuite:
    """Test sensor suite configuration."""

    def test_empty_suite_creation(self):
        """Test creating empty sensor suite."""
        suite = SensorSuite(robot_name="robot_1")

        assert suite.robot_name == "robot_1"
        assert suite.get_sensor_count() == 0

    def test_add_sensor(self):
        """Test adding sensors to suite."""
        suite = SensorSuite(robot_name="robot_1")

        spec = SensorSpec(
            sensor_id="rgb_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB Camera",
            description="",
        )

        suite.add_sensor("rgb_1", spec)

        assert suite.get_sensor_count() == 1
        assert suite.get_sensor("rgb_1") is not None

    def test_remove_sensor(self):
        """Test removing sensor from suite."""
        suite = SensorSuite(robot_name="robot_1")

        spec = SensorSpec(
            sensor_id="lidar_1",
            sensor_type=SensorType.VELODYNE_LIDAR,
            category=SensorCategory.LIDAR_3D,
            name="LiDAR",
            description="",
        )

        suite.add_sensor("lidar_1", spec)
        assert suite.get_sensor_count() == 1

        removed = suite.remove_sensor("lidar_1")
        assert removed is True
        assert suite.get_sensor_count() == 0

    def test_get_sensors_by_type(self):
        """Test getting sensors by type."""
        suite = SensorSuite(robot_name="robot_1")

        for i in range(3):
            spec = SensorSpec(
                sensor_id=f"camera_{i}",
                sensor_type=SensorType.RGB_CAMERA,
                category=SensorCategory.VISION,
                name=f"Camera {i}",
                description="",
            )

            suite.add_sensor(f"camera_{i}", spec)

        cameras = suite.get_sensors_by_type(SensorType.RGB_CAMERA)
        assert len(cameras) == 3

    def test_has_sensor_category(self):
        """Test checking for sensor category."""
        suite = SensorSuite(robot_name="robot_1")

        assert not suite.has_sensor_category(SensorCategory.VISION)

        spec = SensorSpec(
            sensor_id="rgb_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB",
            description="",
        )

        suite.add_sensor("rgb_1", spec)

        assert suite.has_sensor_category(SensorCategory.VISION)

    def test_suite_to_dict(self):
        """Test suite serialization."""
        suite = SensorSuite(robot_name="robot_1")

        spec = SensorSpec(
            sensor_id="imu_1",
            sensor_type=SensorType.IMU,
            category=SensorCategory.IMU,
            name="IMU",
            description="",
        )

        suite.add_sensor("imu_1", spec)

        d = suite.to_dict()
        assert d["robot_name"] == "robot_1"
        assert d["sensor_count"] == 1


class TestSensorConfigurationManager:
    """Test sensor configuration manager."""

    def test_manager_creation(self):
        """Test creating configuration manager."""
        manager = SensorConfigurationManager()

        assert len(manager.list_configured_robots()) == 0

    def test_create_empty_suite(self):
        """Test creating empty sensor suite."""
        manager = SensorConfigurationManager()

        suite = manager.create_empty_suite("robot_1")

        assert suite.robot_name == "robot_1"
        assert suite.get_sensor_count() == 0

    def test_create_standard_suite_mobile(self):
        """Test creating standard mobile sensor suite."""
        manager = SensorConfigurationManager()

        suite = manager.create_standard_suite("mobile_robot", platform_type="mobile")

        assert suite.get_sensor_count() > 0
        assert suite.has_sensor_category(SensorCategory.VISION)
        assert suite.has_sensor_category(SensorCategory.LIDAR_3D)
        assert suite.has_sensor_category(SensorCategory.IMU)

    def test_create_standard_suite_aerial(self):
        """Test creating standard aerial sensor suite."""
        manager = SensorConfigurationManager()

        suite = manager.create_standard_suite("drone", platform_type="aerial")

        assert suite.has_sensor_category(SensorCategory.VISION)
        assert suite.has_sensor_category(SensorCategory.THERMAL)
        assert suite.has_sensor_category(SensorCategory.GNSS)

    def test_register_and_retrieve_suite(self):
        """Test registering and retrieving suite."""
        manager = SensorConfigurationManager()

        suite = manager.create_standard_suite("robot_1", platform_type="mobile")
        manager.register_suite(suite)

        retrieved = manager.get_suite("robot_1")
        assert retrieved is not None
        assert retrieved.robot_name == "robot_1"

    def test_validate_suite(self):
        """Test suite validation."""
        manager = SensorConfigurationManager()

        # Empty suite should fail
        empty_suite = manager.create_empty_suite("robot_1")
        errors = manager.validate_suite(empty_suite)

        assert len(errors) > 0

        # Suite with sensors should pass
        suite = manager.create_standard_suite("robot_2", platform_type="mobile")
        errors = manager.validate_suite(suite)

        assert len(errors) == 0

    def test_configuration_summary(self):
        """Test getting configuration summary."""
        manager = SensorConfigurationManager()

        suite = manager.create_standard_suite("robot_1", platform_type="mobile")
        manager.register_suite(suite)

        summary = manager.get_configuration_summary("robot_1")

        assert summary["status"] == "configured"
        assert summary["total_sensors"] > 0
        assert "categories" in summary


class TestSensorAwarenessConstraint:
    """Test sensor awareness constraints."""

    def test_constraint_creation(self):
        """Test creating constraint from suite."""
        suite = SensorSuite(robot_name="robot_1")

        spec = SensorSpec(
            sensor_id="rgb_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB",
            description="",
        )

        suite.add_sensor("rgb_1", spec)

        constraint = SensorAwarenessConstraint(suite)

        assert constraint.can_generate_data("rgb")

    def test_data_type_capability(self):
        """Test checking data generation capability."""
        suite = SensorSuite(robot_name="robot_1")

        # No LiDAR
        constraint = SensorAwarenessConstraint(suite)
        assert not constraint.can_generate_data("lidar_3d")

        # Add LiDAR
        lidar_spec = SensorSpec(
            sensor_id="lidar_1",
            sensor_type=SensorType.VELODYNE_LIDAR,
            category=SensorCategory.LIDAR_3D,
            name="LiDAR",
            description="",
        )

        suite.add_sensor("lidar_1", lidar_spec)
        constraint = SensorAwarenessConstraint(suite)
        assert constraint.can_generate_data("lidar_3d")

    def test_rendering_modules(self):
        """Test rendering module initialization."""
        suite = SensorSuite(robot_name="robot_1")

        # Only RGB
        rgb_spec = SensorSpec(
            sensor_id="rgb_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB",
            description="",
        )

        suite.add_sensor("rgb_1", rgb_spec)

        constraint = SensorAwarenessConstraint(suite)
        rendering = constraint.get_rendering_modules()

        assert rendering["rgb_renderer"] is True
        assert rendering["depth_renderer"] is False
        assert rendering["lidar_engine"] is False

    def test_data_generation_modules(self):
        """Test data generation module selection."""
        manager = SensorConfigurationManager()
        suite = manager.create_standard_suite("robot_1", platform_type="mobile")

        constraint = SensorAwarenessConstraint(suite)
        generators = constraint.get_data_generation_modules()

        # Mobile robot should have these
        assert generators["rgb_generator"] is True
        assert generators["imu_generator"] is True
        assert generators["lidar_generator"] is True

        # But not thermal or audio
        assert generators["thermal_generator"] is False
        assert generators["audio_generator"] is False

    def test_compute_optimization_profile(self):
        """Test compute optimization profile."""
        suite = SensorSuite(robot_name="robot_1")

        spec = SensorSpec(
            sensor_id="rgb_1",
            sensor_type=SensorType.RGB_CAMERA,
            category=SensorCategory.VISION,
            name="RGB",
            description="",
        )

        suite.add_sensor("rgb_1", spec)

        constraint = SensorAwarenessConstraint(suite)
        profile = constraint.get_compute_optimization_profile()

        assert "active_renderers" in profile
        assert "active_generators" in profile
        assert "optimization_hints" in profile


class TestSensorAwareSimulationEngine:
    """Test sensor-aware simulation engine."""

    def test_engine_creation(self):
        """Test creating simulation engine."""
        manager = SensorConfigurationManager()
        engine = SensorAwareSimulationEngine(manager)

        assert len(engine.get_mandatory_initialization_status()["configured_robots"]) == 0

    def test_initialization_without_config(self):
        """Test initialization fails without configuration."""
        manager = SensorConfigurationManager()
        engine = SensorAwareSimulationEngine(manager)

        # Robot not configured yet
        result = engine.initialize_simulation("unconfigured_robot")
        assert result is False

    def test_initialization_with_config(self):
        """Test successful initialization with configuration."""
        manager = SensorConfigurationManager()
        suite = manager.create_standard_suite("robot_1", platform_type="mobile")
        manager.register_suite(suite)

        engine = SensorAwareSimulationEngine(manager)
        result = engine.initialize_simulation("robot_1")

        assert result is True

        constraint = engine.get_constraint("robot_1")
        assert constraint is not None

    def test_can_generate_data(self):
        """Test data generation capability checking."""
        manager = SensorConfigurationManager()
        suite = manager.create_standard_suite("robot_1", platform_type="mobile")
        manager.register_suite(suite)

        engine = SensorAwareSimulationEngine(manager)
        engine.initialize_simulation("robot_1")

        assert engine.can_generate_data("robot_1", "rgb")
        assert engine.can_generate_data("robot_1", "lidar_3d")
        assert not engine.can_generate_data("robot_1", "thermal")
        assert not engine.can_generate_data("robot_1", "radar")

    def test_simulation_profile(self):
        """Test getting complete simulation profile."""
        manager = SensorConfigurationManager()
        suite = manager.create_standard_suite("robot_1", platform_type="mobile")
        manager.register_suite(suite)

        engine = SensorAwareSimulationEngine(manager)
        engine.initialize_simulation("robot_1")

        profile = engine.get_simulation_profile("robot_1")

        assert profile["status"] == "configured_and_initialized"
        assert "available_outputs" in profile
        assert "compute_profile" in profile

    def test_initialization_status(self):
        """Test mandatory initialization status."""
        manager = SensorConfigurationManager()
        suite1 = manager.create_standard_suite("robot_1", platform_type="mobile")
        suite2 = manager.create_standard_suite("robot_2", platform_type="aerial")
        manager.register_suite(suite1)
        manager.register_suite(suite2)

        engine = SensorAwareSimulationEngine(manager)
        engine.initialize_simulation("robot_1")

        status = engine.get_mandatory_initialization_status()

        assert len(status["configured_robots"]) == 2
        assert len(status["initialized_robots"]) == 1
        assert "robot_2" in status["pending_initialization"]


class TestSensorAwarenessIntegration:
    """Integration tests for sensor awareness system."""

    def test_complete_sensor_configuration_workflow(self):
        """Test complete sensor configuration workflow."""
        # Step 1: Create configuration manager
        manager = SensorConfigurationManager()

        # Step 2: Create standard sensor suite
        suite = manager.create_standard_suite("delivery_robot", platform_type="mobile")

        # Step 3: Customize sensors
        # Remove GPS for indoor operation
        suite.remove_sensor("gps")

        # Step 4: Validate
        errors = manager.validate_suite(suite)
        assert len(errors) == 0

        # Step 5: Register
        manager.register_suite(suite)

        # Step 6: Initialize simulation engine
        engine = SensorAwareSimulationEngine(manager)
        result = engine.initialize_simulation("delivery_robot")
        assert result is True

        # Step 7: Check capabilities
        assert engine.can_generate_data("delivery_robot", "rgb")
        assert engine.can_generate_data("delivery_robot", "lidar_3d")
        assert not engine.can_generate_data("delivery_robot", "gnss")

        # Step 8: Get profile
        profile = engine.get_simulation_profile("delivery_robot")
        assert profile["status"] == "configured_and_initialized"

    def test_multiplatform_configuration(self):
        """Test configuring multiple robot platforms."""
        manager = SensorConfigurationManager()
        engine = SensorAwareSimulationEngine(manager)

        platforms = [
            ("mobile_1", "mobile"),
            ("aerial_1", "aerial"),
            ("manipulator_1", "manipulator"),
        ]

        for robot_name, platform_type in platforms:
            suite = manager.create_standard_suite(robot_name, platform_type=platform_type)
            manager.register_suite(suite)
            engine.initialize_simulation(robot_name)

        # Verify all initialized
        status = engine.get_mandatory_initialization_status()
        assert len(status["initialized_robots"]) == 3
