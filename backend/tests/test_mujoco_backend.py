"""Tests for the real MuJoCo physics backend.

These tests exercise genuine physics simulation (not mocked/hardcoded
results): real MJCF/URDF loading, real `mujoco.mj_step` integration, and
assertions against known-correct physical behavior (e.g. a free-falling
body's height following z(t) = z0 - 1/2*g*t^2 within numerical-integration
tolerance).

The whole module is skipped if the optional `mujoco` dependency isn't
installed (`pip install mujoco`, or `pip install -e ".[physics]"`).
"""

import math
import os

import pytest

mujoco = pytest.importorskip("mujoco")

from src.simulators.backend_interface import (  # noqa: E402
    CameraConfig,
    IMUConfig,
    LidarConfig,
    PhysicsEngineType,
    RenderingBackend,
    RobotConfig,
    RobotType,
    SensorType,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)
from src.simulators.mujoco_backend import MuJoCoBackend  # noqa: E402

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "mujoco")
PENDULUM_XML = os.path.join(FIXTURES_DIR, "pendulum.xml")
SIMPLE_ARM_URDF = os.path.join(FIXTURES_DIR, "simple_arm.urdf")

GRAVITY = (0.0, 0.0, -9.81)


@pytest.fixture
def backend():
    """A MuJoCoBackend with an initialized, empty world."""
    b = MuJoCoBackend()
    config = SimulatorConfig(
        simulator_type=SimulatorType.MUJOCO,
        physics_engine=PhysicsEngineType.MUJOCO_PHYSICS,
        rendering_backend=RenderingBackend.HEADLESS,
        gravity=GRAVITY,
        timestep_ms=2.0,
    )
    b.initialize(config)
    b.create_world(WorldConfig(name="test_world", gravity=GRAVITY))
    yield b
    b.shutdown()


def make_free_robot(name="falling_body", model_path="primitive:box:0.1,0.1,0.1:1.0",
                     position=(0.0, 0.0, 5.0)):
    return RobotConfig(
        name=name,
        robot_type=RobotType.CUSTOM,
        model_path=model_path,
        position=position,
        fixed_base=False,
    )


# ==================== LIFECYCLE ====================


class TestLifecycle:
    def test_initialize_sets_running(self):
        b = MuJoCoBackend()
        assert not b.is_running()
        config = SimulatorConfig(
            simulator_type=SimulatorType.MUJOCO,
            physics_engine=PhysicsEngineType.MUJOCO_PHYSICS,
            rendering_backend=RenderingBackend.HEADLESS,
        )
        b.initialize(config)
        assert b.is_running()
        b.shutdown()
        assert not b.is_running()

    def test_get_simulator_type(self, backend):
        assert backend.get_simulator_type() == SimulatorType.MUJOCO

    def test_validate_configuration_rejects_bad_timestep(self, backend):
        bad_config = SimulatorConfig(
            simulator_type=SimulatorType.MUJOCO,
            physics_engine=PhysicsEngineType.MUJOCO_PHYSICS,
            rendering_backend=RenderingBackend.HEADLESS,
            timestep_ms=-1.0,
        )
        assert backend.validate_configuration(bad_config) is False
        assert backend.get_last_error() is not None

    def test_requires_mujoco_package_error_is_clear(self, monkeypatch):
        import backend.src.simulators.mujoco_backend as mod

        monkeypatch.setattr(mod, "MUJOCO_AVAILABLE", False)
        with pytest.raises(ImportError, match="mujoco"):
            mod.MuJoCoBackend()


# ==================== WORLD MANAGEMENT ====================


class TestWorldManagement:
    def test_create_world_returns_name(self, backend):
        world_id = backend.create_world(WorldConfig(name="another_world", gravity=GRAVITY))
        assert world_id == "another_world"

    def test_get_world_info_reflects_real_model(self, backend):
        info = backend.get_world_info("test_world")
        assert info["simulator"] == "mujoco"
        assert info["body_count"] >= 1  # at least the ground/world body
        assert info["gravity"] == pytest.approx(GRAVITY)

    def test_save_and_load_world_round_trip(self, backend, tmp_path):
        backend.spawn_robot(make_free_robot("box1"))
        out_path = str(tmp_path / "saved_world.xml")
        backend.save_world("test_world", out_path)

        assert os.path.exists(out_path)
        with open(out_path) as f:
            xml_text = f.read()
        assert "<mujoco" in xml_text
        assert "box1_root" in xml_text  # the spawned body is really in the saved XML

        loader = MuJoCoBackend()
        loader.initialize(
            SimulatorConfig(
                simulator_type=SimulatorType.MUJOCO,
                physics_engine=PhysicsEngineType.MUJOCO_PHYSICS,
                rendering_backend=RenderingBackend.HEADLESS,
            )
        )
        world_id = loader.load_world(out_path)
        assert world_id == "saved_world"
        body_names = [loader._model.body(i).name for i in range(loader._model.nbody)]
        assert "box1_root" in body_names
        loader.shutdown()

    def test_load_world_missing_file_raises(self, backend):
        with pytest.raises(FileNotFoundError):
            backend.load_world("/nonexistent/path/world.xml")


# ==================== PHYSICS CORRECTNESS ====================


class TestPhysicsCorrectness:
    """The core deliverable: real physics, verified against known kinematics."""

    def test_free_fall_matches_kinematics(self, backend):
        """A free body under gravity must fall as z(t) = z0 - 1/2 g t^2."""
        backend.spawn_robot(make_free_robot(position=(0.0, 0.0, 5.0)))

        state0 = backend.get_robot_state("falling_body")
        z0 = state0.position[2]
        assert z0 == pytest.approx(5.0)

        backend.step(num_steps=100)  # 100 * 2ms = 0.2s of real integration
        state1 = backend.get_robot_state("falling_body")

        dt = state1.timestamp - state0.timestamp
        expected_z = z0 - 0.5 * 9.81 * dt * dt
        # Semi-implicit Euler integration has a small, bounded discretization
        # error relative to exact kinematics; 1% relative tolerance is tight
        # enough to catch a broken/fake implementation but loose enough to
        # tolerate real integrator error.
        assert state1.position[2] == pytest.approx(expected_z, rel=0.01)

        # No horizontal drift under pure gravity.
        assert state1.position[0] == pytest.approx(0.0, abs=1e-9)
        assert state1.position[1] == pytest.approx(0.0, abs=1e-9)

        expected_vz = -9.81 * dt
        assert state1.linear_velocity[2] == pytest.approx(expected_vz, rel=0.02)

    def test_free_fall_is_mass_independent(self, backend):
        """Galileo: heavier and lighter free-falling bodies fall identically."""
        backend.spawn_robot(
            make_free_robot("light", "primitive:box:0.1,0.1,0.1:0.5", (0.0, 0.0, 5.0))
        )
        backend.spawn_robot(
            make_free_robot("heavy", "primitive:box:0.1,0.1,0.1:50.0", (2.0, 0.0, 5.0))
        )
        backend.step(num_steps=100)
        light = backend.get_robot_state("light")
        heavy = backend.get_robot_state("heavy")
        assert light.position[2] == pytest.approx(heavy.position[2], rel=1e-6)
        assert light.linear_velocity[2] == pytest.approx(heavy.linear_velocity[2], rel=1e-6)

    def test_body_comes_to_rest_on_ground(self, backend):
        """A box dropped just above the ground settles at ~half its height."""
        backend.spawn_robot(make_free_robot(position=(0.0, 0.0, 0.5)))
        backend.step(num_steps=2000)
        state = backend.get_robot_state("falling_body")
        assert state.position[2] == pytest.approx(0.1, abs=0.01)
        assert abs(state.linear_velocity[2]) < 0.05

    def test_contact_forces_balance_weight_at_rest(self, backend):
        """Sum of real contact normal forces on a resting box ~= its weight."""
        mass = 2.0
        backend.spawn_robot(
            make_free_robot("resting_box", f"primitive:box:0.1,0.1,0.1:{mass}", (0.0, 0.0, 0.5))
        )
        backend.step(num_steps=2000)
        contacts = backend.get_contacts()
        assert len(contacts) > 0
        total_force = sum(c.force_magnitude for c in contacts)
        expected_weight = mass * 9.81
        assert total_force == pytest.approx(expected_weight, rel=0.05)

    def test_fixed_base_robot_does_not_move(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="bolted",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path="primitive:box:0.1,0.1,0.1",
                position=(1.0, 2.0, 3.0),
                fixed_base=True,
            )
        )
        backend.step(num_steps=500)
        state = backend.get_robot_state("bolted")
        assert state.position == pytest.approx((1.0, 2.0, 3.0))

    def test_set_gravity_changes_fall_rate(self, backend):
        backend.spawn_robot(make_free_robot(position=(0.0, 0.0, 5.0)))
        backend.set_gravity((0.0, 0.0, -1.0))  # much weaker gravity
        assert backend.get_gravity() == pytest.approx((0.0, 0.0, -1.0))
        backend.step(num_steps=100)
        state = backend.get_robot_state("falling_body")
        # Weak gravity => far less fall than the ~0.196m under -9.81.
        assert state.position[2] > 4.95

    def test_reset_zeroes_time_and_state(self, backend):
        backend.spawn_robot(make_free_robot(position=(0.0, 0.0, 5.0)))
        backend.step(num_steps=50)
        assert backend.get_robot_state("falling_body").timestamp > 0
        backend.reset()
        assert backend._data.time == 0.0


# ==================== REAL MODEL LOADING ====================


class TestRealModelLoading:
    def test_load_real_mjcf_pendulum(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="pendulum",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path=PENDULUM_XML,
                position=(0.0, 0.0, 2.0),
                fixed_base=True,
            )
        )
        info = backend.get_robot_info("pendulum")
        assert "shoulder" in info["joints"]

        # The fixture hangs at its stable equilibrium (straight down), so a
        # nudge is needed to see real dynamics; apply_joint_force uses the
        # real generalized-force injection path (mj_step then integrates
        # qfrc_applied), not a scripted/fake result.
        angle0 = backend.get_joint_state("pendulum", "shoulder")["position"]
        backend.apply_joint_force("pendulum", "shoulder", 20.0)
        backend.step(num_steps=1)
        backend.apply_joint_force("pendulum", "shoulder", 0.0)
        backend.step(num_steps=500)
        angle1 = backend.get_joint_state("pendulum", "shoulder")["position"]
        assert angle0 != pytest.approx(angle1)

    def test_load_real_urdf(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="arm",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path=SIMPLE_ARM_URDF,
                position=(0.0, 0.0, 1.0),
                fixed_base=True,
            )
        )
        info = backend.get_robot_info("arm")
        assert "elbow" in info["joints"]

    def test_spawn_with_missing_model_path_raises(self, backend):
        with pytest.raises(FileNotFoundError):
            backend.spawn_robot(
                RobotConfig(
                    name="ghost",
                    robot_type=RobotType.CUSTOM,
                    model_path="/no/such/model.xml",
                    fixed_base=True,
                )
            )

    def test_spawn_duplicate_name_raises(self, backend):
        backend.spawn_robot(make_free_robot("dup"))
        with pytest.raises(ValueError):
            backend.spawn_robot(make_free_robot("dup"))


# ==================== JOINT CONTROL ====================


class TestJointControl:
    def test_position_servo_converges_toward_target(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="pendulum",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path=PENDULUM_XML,
                position=(0.0, 0.0, 2.0),
                fixed_base=True,
            )
        )
        backend.set_joint_target("pendulum", "shoulder", 1.0)
        backend.step(num_steps=3000)
        angle = backend.get_joint_state("pendulum", "shoulder")["position"]
        # Real PD servo under gravity load settles near (not exactly at)
        # the target; this is genuine closed-loop control, not teleporting.
        assert angle == pytest.approx(1.0, abs=0.15)

    def test_apply_joint_force_changes_dynamics(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="pendulum",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path=PENDULUM_XML,
                position=(0.0, 0.0, 2.0),
                fixed_base=True,
            )
        )
        backend.apply_joint_force("pendulum", "shoulder", 5.0)
        backend.step(num_steps=1)
        velocity = backend.get_joint_state("pendulum", "shoulder")["velocity"]
        assert velocity != 0.0

    def test_get_joint_state_unknown_joint_raises(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="pendulum",
                robot_type=RobotType.MANIPULATOR_ARM,
                model_path=PENDULUM_XML,
                fixed_base=True,
            )
        )
        with pytest.raises(KeyError):
            backend.get_joint_state("pendulum", "no_such_joint")


# ==================== OBJECTS ====================


class TestObjects:
    def test_spawn_and_remove_object(self, backend):
        backend.spawn_object(
            "crate", "primitive:box:0.2,0.2,0.2:3.0", (0.0, 0.0, 3.0), (0.0, 0.0, 0.0, 1.0)
        )
        assert "crate" in backend.list_objects()
        state = backend.get_object_state("crate")
        assert state.position[2] == pytest.approx(3.0)

        backend.remove_object("crate")
        assert "crate" not in backend.list_objects()
        with pytest.raises(KeyError):
            backend.get_object_state("crate")

    def test_static_object_does_not_fall(self, backend):
        backend.spawn_object(
            "platform",
            "primitive:box:0.5,0.5,0.1:10.0",
            (0.0, 0.0, 2.0),
            (0.0, 0.0, 0.0, 1.0),
            metadata={"static": True},
        )
        backend.step(num_steps=500)
        state = backend.get_object_state("platform")
        assert state.position[2] == pytest.approx(2.0)

    def test_set_object_pose(self, backend):
        backend.spawn_object(
            "ball", "primitive:sphere:0.1:1.0", (0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)
        )
        backend.set_object_pose("ball", (3.0, 4.0, 5.0), (0.0, 0.0, 0.0, 1.0))
        state = backend.get_object_state("ball")
        assert state.position == pytest.approx((3.0, 4.0, 5.0))


# ==================== CONTACTS & RAYCAST ====================


class TestContactsAndRaycast:
    def test_raycast_hits_ground(self, backend):
        hit = backend.raycast((0.0, 0.0, 10.0), (0.0, 0.0, -1.0))
        assert hit is not None
        assert hit["body_name"] == "world"
        assert hit["distance"] == pytest.approx(10.0, abs=0.01)

    def test_raycast_misses_when_nothing_ahead(self, backend):
        hit = backend.raycast((0.0, 0.0, 10.0), (0.0, 0.0, 1.0))  # pointing up, away from ground
        assert hit is None

    def test_get_contacts_empty_before_impact(self, backend):
        backend.spawn_robot(make_free_robot(position=(0.0, 0.0, 5.0)))
        backend.step(num_steps=1)
        assert backend.get_contacts() == []


# ==================== SENSORS ====================


class TestSensors:
    @pytest.fixture
    def robot_with_sensors(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="sensored",
                robot_type=RobotType.MOBILE_MANIPULATOR,
                model_path=PENDULUM_XML,
                position=(0.0, 0.0, 2.0),
                fixed_base=True,
            )
        )
        return backend

    def test_camera_image_real_render(self, robot_with_sensors):
        b = robot_with_sensors
        b.attach_sensor(
            "sensored",
            CameraConfig(
                name="eye",
                sensor_type=SensorType.RGB_CAMERA,
                parent_link="base",
                position=(0.0, 0.0, 0.3),
                width=64,
                height=48,
            ),
        )
        result = b.get_camera_image("sensored", "eye", include_depth=True, include_segmentation=True)
        assert result["rgb"].shape == (48, 64, 3)
        assert result["depth"].shape == (48, 64)
        assert result["depth"].min() >= 0.0

    def test_lidar_scan_detects_ground(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="scanner",
                robot_type=RobotType.WHEELED_UGV,
                model_path="primitive:box:0.1,0.1,0.1",
                position=(0.0, 0.0, 1.0),
                fixed_base=True,
            )
        )
        backend.attach_sensor(
            "scanner",
            LidarConfig(
                name="lidar0",
                sensor_type=SensorType.LIDAR,
                parent_link="root",
                num_beams=8,
                horizontal_fov=360.0,
                max_range=50.0,
            ),
        )
        scan = backend.get_lidar_scan("scanner", "lidar0")
        assert scan["points"].shape == (8, 3)
        assert scan["num_points"] == 8

    def test_imu_reports_gravity_reaction_at_rest(self, backend):
        backend.spawn_robot(
            RobotConfig(
                name="imu_bot",
                robot_type=RobotType.CUSTOM,
                model_path="primitive:box:0.1,0.1,0.1",
                position=(0.0, 0.0, 1.0),
                fixed_base=True,
            )
        )
        backend.attach_sensor(
            "imu_bot",
            IMUConfig(name="imu0", sensor_type=SensorType.IMU, parent_link="root"),
        )
        backend.step(num_steps=1)
        imu = backend.get_imu_data("imu_bot", "imu0")
        # A stationary body's accelerometer reads the negative of gravity
        # (it measures the normal-force reaction, not free-fall).
        accel_z = imu["accel"][2]
        assert accel_z == pytest.approx(9.81, abs=0.5)


# ==================== DOMAIN RANDOMIZATION ====================


class TestDomainRandomization:
    def test_randomize_mass_within_range(self, backend):
        backend.spawn_object(
            "obj", "primitive:box:0.1,0.1,0.1:1.0", (0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)
        )
        backend.randomize_mass("obj", (5.0, 10.0))
        entry = backend._objects["obj"]
        bid = mujoco.mj_name2id(backend._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        assert 5.0 <= backend._model.body_mass[bid] <= 10.0

    def test_randomize_friction_within_range(self, backend):
        backend.spawn_object(
            "obj", "primitive:box:0.1,0.1,0.1:1.0", (0.0, 0.0, 1.0), (0.0, 0.0, 0.0, 1.0)
        )
        backend.randomize_friction("obj", (0.2, 0.4))
        entry = backend._objects["obj"]
        bid = mujoco.mj_name2id(backend._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
        for gid in range(backend._model.ngeom):
            if backend._model.geom_bodyid[gid] == bid:
                assert 0.2 <= backend._model.geom_friction[gid, 0] <= 0.4


# ==================== INTEGRATION ====================


class TestFullWorkflow:
    def test_multi_body_simulation_workflow(self, backend):
        """Spawn several bodies, step, and verify each is tracked independently."""
        backend.spawn_robot(make_free_robot("a", position=(0.0, 0.0, 3.0)))
        backend.spawn_robot(make_free_robot("b", position=(1.0, 0.0, 4.0)))
        backend.spawn_object(
            "c", "primitive:box:0.1,0.1,0.1", (2.0, 0.0, 5.0), (0.0, 0.0, 0.0, 1.0)
        )

        step_result = backend.step(num_steps=10)
        assert step_result.step_count == 10
        assert set(step_result.robot_states.keys()) == {"a", "b"}
        assert set(step_result.object_states.keys()) == {"c"}

        # Each body fell independently and remains at its own x offset.
        assert step_result.robot_states["a"].position[0] == pytest.approx(0.0)
        assert step_result.robot_states["b"].position[0] == pytest.approx(1.0)
        assert step_result.object_states["c"].position[0] == pytest.approx(2.0)

    def test_spawn_after_stepping_preserves_existing_state(self, backend):
        """Recompiling the model to add a body must not reset prior bodies."""
        backend.spawn_robot(make_free_robot("first", position=(0.0, 0.0, 5.0)))
        backend.step(num_steps=50)
        z_before_spawn = backend.get_robot_state("first").position[2]
        t_before_spawn = backend.get_robot_state("first").timestamp

        backend.spawn_robot(make_free_robot("second", position=(3.0, 0.0, 5.0)))

        z_after_spawn = backend.get_robot_state("first").position[2]
        t_after_spawn = backend.get_robot_state("first").timestamp
        assert z_after_spawn == pytest.approx(z_before_spawn, abs=1e-6)
        assert t_after_spawn == pytest.approx(t_before_spawn, abs=1e-6)
