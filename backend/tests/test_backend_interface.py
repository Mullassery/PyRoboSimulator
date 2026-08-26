"""Tests for Simulator Backend Interface (Phase 4.0)."""

import pytest

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
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)
from src.simulators.backend_manager import BackendFactory, BackendManager
from src.simulators.mock_backend import MockBackend


class TestSimulatorConfig:
    """Test simulator configuration."""

    def test_basic_config(self):
        """Test basic config creation."""
        config = SimulatorConfig(
            simulator_type=SimulatorType.ISAAC_SIM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.RTX,
        )

        assert config.simulator_type == SimulatorType.ISAAC_SIM
        assert config.physics_engine == PhysicsEngineType.PHYSX
        assert config.gravity == (0.0, 0.0, -9.81)
        assert config.timestep_ms == 1.0

    def test_custom_config(self):
        """Test custom config."""
        config = SimulatorConfig(
            simulator_type=SimulatorType.GAZEBO,
            physics_engine=PhysicsEngineType.ODE,
            rendering_backend=RenderingBackend.OPENGL,
            headless_mode=True,
            gravity=(0.0, 0.0, -10.0),
            timestep_ms=2.0,
        )

        assert config.headless_mode
        assert config.gravity == (0.0, 0.0, -10.0)
        assert config.timestep_ms == 2.0


class TestRobotConfig:
    """Test robot configuration."""

    def test_basic_robot_config(self):
        """Test basic robot config."""
        config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
        )

        assert config.name == "robot_1"
        assert config.robot_type == RobotType.QUADRUPED
        assert config.position == (0.0, 0.0, 0.0)
        assert config.fixed_base is False

    def test_custom_robot_config(self):
        """Test custom robot config."""
        config = RobotConfig(
            name="arm_1",
            robot_type=RobotType.MANIPULATOR_ARM,
            model_path="/path/to/arm.usd",
            position=(1.0, 2.0, 3.0),
            rotation=(0.0, 0.0, 0.7071, 0.7071),
            fixed_base=True,
            metadata={"max_speed": 2.0},
        )

        assert config.position == (1.0, 2.0, 3.0)
        assert config.fixed_base is True
        assert config.metadata["max_speed"] == 2.0


class TestSensorConfig:
    """Test sensor configurations."""

    def test_basic_sensor_config(self):
        """Test basic sensor config."""
        config = SensorConfig(
            name="camera_1",
            sensor_type=SensorType.RGB_CAMERA,
            parent_link="head",
        )

        assert config.name == "camera_1"
        assert config.sensor_type == SensorType.RGB_CAMERA
        assert config.parent_link == "head"

    def test_camera_config(self):
        """Test camera config."""
        config = CameraConfig(
            name="front_camera",
            sensor_type=SensorType.RGB_CAMERA,
            parent_link="head",
            width=1280,
            height=720,
            fov=60.0,
        )

        assert config.width == 1280
        assert config.height == 720
        assert config.fov == 60.0

    def test_lidar_config(self):
        """Test Lidar config."""
        config = LidarConfig(
            name="lidar_1",
            sensor_type=SensorType.LIDAR,
            parent_link="body",
            num_beams=64,
            max_range=50.0,
        )

        assert config.num_beams == 64
        assert config.max_range == 50.0

    def test_imu_config(self):
        """Test IMU config."""
        config = IMUConfig(
            name="imu_1",
            sensor_type=SensorType.IMU,
            parent_link="body",
            accel_noise_stddev=0.01,
            gyro_noise_stddev=0.01,
        )

        assert config.accel_noise_stddev == 0.01
        assert config.gyro_noise_stddev == 0.01


class TestRobotState:
    """Test robot state."""

    def test_robot_state_creation(self):
        """Test creating robot state."""
        state = RobotState(
            robot_name="robot_1",
            position=(1.0, 2.0, 3.0),
            rotation=(0.0, 0.0, 0.0, 1.0),
            linear_velocity=(0.5, 0.0, 0.0),
            angular_velocity=(0.0, 0.0, 0.1),
            joint_positions={"joint_1": 0.5, "joint_2": 1.0},
            joint_velocities={"joint_1": 0.1, "joint_2": 0.2},
            joint_forces={"joint_1": 10.0, "joint_2": 20.0},
            timestamp=100.0,
        )

        assert state.robot_name == "robot_1"
        assert state.position == (1.0, 2.0, 3.0)
        assert len(state.joint_positions) == 2


class TestObjectState:
    """Test object state."""

    def test_object_state_creation(self):
        """Test creating object state."""
        state = ObjectState(
            object_name="object_1",
            position=(5.0, 6.0, 7.0),
            rotation=(0.0, 0.0, 0.0, 1.0),
            linear_velocity=(1.0, 0.0, 0.0),
            angular_velocity=(0.0, 0.0, 0.0),
            timestamp=100.0,
        )

        assert state.object_name == "object_1"
        assert state.position == (5.0, 6.0, 7.0)


class TestBackendFactory:
    """Test backend factory."""

    def test_factory_creation(self):
        """Test creating factory."""
        factory = BackendFactory()

        assert len(factory.get_registered_backends()) == 0

    def test_register_backend(self):
        """Test registering backend."""
        factory = BackendFactory()

        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        assert factory.is_registered(SimulatorType.CUSTOM)

    def test_create_backend(self):
        """Test creating backend."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend = factory.create_backend(config)

        assert backend is not None
        assert isinstance(backend, MockBackend)

    def test_create_unregistered_backend_error(self):
        """Test error for unregistered backend."""
        factory = BackendFactory()

        config = SimulatorConfig(
            simulator_type=SimulatorType.ISAAC_SIM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.RTX,
        )

        with pytest.raises(ValueError):
            factory.create_backend(config)

    def test_register_invalid_backend_error(self):
        """Test error for invalid backend class."""
        factory = BackendFactory()

        class NotABackend:
            pass

        with pytest.raises(ValueError):
            factory.register_backend(SimulatorType.CUSTOM, NotABackend)


class TestBackendManager:
    """Test backend manager."""

    def test_manager_creation(self):
        """Test creating manager."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        assert not manager.is_initialized()

    def test_initialize_backend(self):
        """Test initializing backend."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend = manager.initialize(config)

        assert manager.is_initialized()
        assert backend is not None
        assert manager.get_backend() == backend

    def test_double_initialize_error(self):
        """Test error on double initialize."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        manager.initialize(config)

        with pytest.raises(RuntimeError):
            manager.initialize(config)

    def test_shutdown_backend(self):
        """Test shutting down backend."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        manager.initialize(config)
        assert manager.is_initialized()

        manager.shutdown()
        assert not manager.is_initialized()

    def test_switch_backend(self):
        """Test switching backends."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        config1 = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend1 = manager.initialize(config1)
        assert manager.get_current_simulator_type() == SimulatorType.CUSTOM

        # Switch (creates new backend, shuts down old one)
        config2 = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.BULLET,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend2 = manager.switch_backend(config2)

        assert manager.is_initialized()
        assert backend1 is not backend2

    def test_get_backend_not_initialized(self):
        """Test error when getting uninitialized backend."""
        manager = BackendManager()

        with pytest.raises(RuntimeError):
            manager.get_backend()


class TestMockBackendBasics:
    """Test MockBackend basic functionality."""

    @pytest.fixture
    def backend(self):
        """Create and initialize mock backend."""
        backend = MockBackend()

        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend.initialize(config)
        return backend

    def test_backend_initialization(self, backend):
        """Test backend is initialized."""
        assert backend.is_running()

    def test_world_creation(self, backend):
        """Test creating world."""
        config = WorldConfig(name="test_world")

        world_id = backend.create_world(config)

        assert world_id == "test_world"
        assert backend.is_running()

    def test_robot_spawn_and_state(self, backend):
        """Test spawning robot and getting state."""
        robot_config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
            position=(1.0, 2.0, 3.0),
        )

        robot_id = backend.spawn_robot(robot_config)

        assert robot_id == "robot_1"
        assert "robot_1" in backend.list_robots()

        state = backend.get_robot_state("robot_1")

        assert state.robot_name == "robot_1"
        assert state.position == (1.0, 2.0, 3.0)

    def test_object_spawn_and_state(self, backend):
        """Test spawning object and getting state."""
        obj_id = backend.spawn_object(
            name="obj_1",
            model_path="/path/to/object.usd",
            position=(5.0, 6.0, 7.0),
            rotation=(0.0, 0.0, 0.0, 1.0),
        )

        assert obj_id == "obj_1"
        assert "obj_1" in backend.list_objects()

        state = backend.get_object_state("obj_1")

        assert state.object_name == "obj_1"
        assert state.position == (5.0, 6.0, 7.0)

    def test_sensor_attachment(self, backend):
        """Test attaching sensor to robot."""
        robot_config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
        )

        backend.spawn_robot(robot_config)

        sensor_config = CameraConfig(
            name="camera_1",
            sensor_type=SensorType.RGB_CAMERA,
            parent_link="head",
        )

        sensor_id = backend.attach_sensor("robot_1", sensor_config)

        assert "robot_1" in sensor_id
        assert "camera_1" in sensor_id

    def test_simulation_step(self, backend):
        """Test simulation step."""
        robot_config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
        )

        backend.spawn_robot(robot_config)

        step = backend.step(num_steps=10)

        assert step.step_count == 10
        assert "robot_1" in step.robot_states

    def test_pause_resume(self, backend):
        """Test pause and resume."""
        assert not backend.is_paused()

        backend.pause()
        assert backend.is_paused()

        backend.resume()
        assert not backend.is_paused()

    def test_validation(self, backend):
        """Test configuration validation."""
        valid_config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
            timestep_ms=2.0,
        )

        assert backend.validate_configuration(valid_config)

        invalid_config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
            timestep_ms=-1.0,  # Invalid
        )

        assert not backend.validate_configuration(invalid_config)


class TestBackendIntegration:
    """Integration tests for backend system."""

    def test_full_workflow(self):
        """Test full backend workflow."""
        # Create factory and register backend
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        # Create manager
        manager = BackendManager(factory)

        # Initialize
        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend = manager.initialize(config)

        # Create world
        world_config = WorldConfig(name="test_world")
        backend.create_world(world_config)

        # Spawn robot
        robot_config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
        )

        backend.spawn_robot(robot_config)

        # Spawn object
        backend.spawn_object(
            name="object_1",
            model_path="/path/to/object.usd",
            position=(5.0, 0.0, 0.0),
            rotation=(0.0, 0.0, 0.0, 1.0),
        )

        # Attach sensor
        sensor_config = CameraConfig(
            name="camera_1",
            sensor_type=SensorType.RGB_CAMERA,
            parent_link="head",
        )

        backend.attach_sensor("robot_1", sensor_config)

        # Step simulation
        step = backend.step(num_steps=100)

        assert step.step_count == 100
        assert len(step.robot_states) == 1
        assert len(step.object_states) == 1

        # Shutdown
        manager.shutdown()
        assert not manager.is_initialized()

    def test_multi_backend_switching(self):
        """Test switching between backends."""
        factory = BackendFactory()
        factory.register_backend(SimulatorType.CUSTOM, MockBackend)

        manager = BackendManager(factory)

        # Use context manager for cleaner switching
        config = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend1 = manager.initialize(config)
        robot_config = RobotConfig(
            name="robot_1",
            robot_type=RobotType.QUADRUPED,
            model_path="/path/to/model.urdf",
        )

        backend1.spawn_robot(robot_config)

        # Switch to different physics
        config2 = SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.BULLET,
            rendering_backend=RenderingBackend.HEADLESS,
        )

        backend2 = manager.switch_backend(config2)

        # New backend should be clean
        assert len(backend2.list_robots()) == 0
