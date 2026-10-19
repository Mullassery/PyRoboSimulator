"""Determinism tests for seeded simulator randomness.

The RNG helper and MockBackend tests run without any optional dependency.
MuJoCo tests skip automatically when the ``mujoco`` package is unavailable.
"""

from typing import Any, Dict, Tuple

import numpy as np
import pytest

from src.simulators.backend_interface import (
    CameraConfig,
    PhysicsEngineType,
    RenderingBackend,
    RobotConfig,
    RobotType,
    SensorType,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)
from src.simulators.mock_backend import MockBackend
from src.simulators.rng import DEFAULT_SEED, make_rng

GRAVITY = (0.0, 0.0, -9.81)


# ==================== RNG HELPER ====================


class TestSeededRngHelper:
    def test_same_seed_produces_same_stream(self):
        first = make_rng(1234).random(100)
        second = make_rng(1234).random(100)
        np.testing.assert_array_equal(first, second)

    def test_different_seed_produces_different_stream(self):
        first = make_rng(1234).random(100)
        second = make_rng(5678).random(100)
        assert not np.array_equal(first, second)

    def test_none_seed_falls_back_to_deterministic_default(self):
        first = make_rng(None).random(100)
        second = make_rng(None).random(100)
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(first, make_rng(DEFAULT_SEED).random(100))


# ==================== MOCK BACKEND ====================


def _make_mock_backend(seed: int) -> MockBackend:
    backend = MockBackend()
    backend.initialize(
        SimulatorConfig(
            simulator_type=SimulatorType.CUSTOM,
            physics_engine=PhysicsEngineType.CUSTOM,
            rendering_backend=RenderingBackend.HEADLESS,
            seed=seed,
        )
    )
    backend.create_world(WorldConfig(name="determinism", gravity=GRAVITY, seed=seed))
    backend.spawn_robot(
        RobotConfig(
            name="sensor_robot",
            robot_type=RobotType.CUSTOM,
            model_path="primitive:box:0.1,0.1,0.1",
        )
    )
    backend.attach_sensor(
        "sensor_robot",
        CameraConfig(
            name="eye",
            sensor_type=SensorType.RGB_CAMERA,
            parent_link="root",
        ),
    )
    return backend


def _mock_visuals(seed: int) -> Tuple[np.ndarray, ...]:
    backend = _make_mock_backend(seed)
    camera = backend.get_camera_image(
        "sensor_robot", "eye", include_depth=True, include_segmentation=True
    )
    lidar = backend.get_lidar_scan("sensor_robot", "eye")
    return (
        camera["rgb"],
        camera["depth"],
        camera["segmentation"],
        lidar["points"],
        lidar["intensities"],
    )


class TestMockBackendDeterminism:
    def test_same_seed_reproduces_sensor_metadata(self):
        first = _mock_visuals(42)
        second = _mock_visuals(42)
        for a, b in zip(first, second):
            np.testing.assert_array_equal(a, b)

    def test_different_seed_changes_sensor_metadata(self):
        first = _mock_visuals(42)
        second = _mock_visuals(43)
        assert any(not np.array_equal(a, b) for a, b in zip(first, second))


# ==================== MUJOCO BACKEND ====================


def _mujoco_snapshot(seed: int) -> Dict[str, Any]:
    mujoco = pytest.importorskip("mujoco")
    from src.simulators.mujoco_backend import MuJoCoBackend

    backend = MuJoCoBackend()
    backend.initialize(
        SimulatorConfig(
            simulator_type=SimulatorType.MUJOCO,
            physics_engine=PhysicsEngineType.MUJOCO_PHYSICS,
            rendering_backend=RenderingBackend.HEADLESS,
            gravity=GRAVITY,
            seed=seed,
        )
    )
    backend.create_world(WorldConfig(name="determinism", gravity=GRAVITY))
    backend.spawn_object(
        "obj",
        "primitive:box:0.1,0.1,0.1:1.0",
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 0.0, 1.0),
    )

    backend.randomize_lighting(
        (0.2, 0.8),
        ((0.1, 0.2, 0.3), (0.9, 0.8, 0.7)),
    )
    backend.randomize_friction("obj", (0.2, 0.9))
    backend.randomize_mass("obj", (1.0, 5.0))

    entry = backend._objects["obj"]
    bid = mujoco.mj_name2id(backend._model, mujoco.mjtObj.mjOBJ_BODY, entry.body_name)
    snapshot: Dict[str, Any] = {
        "light_diffuse": backend._model.light_diffuse.copy(),
        "geom_friction": backend._model.geom_friction.copy(),
        "body_mass": backend._model.body_mass.copy(),
        "body_inertia": backend._model.body_inertia.copy(),
        "object_mass": float(backend._model.body_mass[bid]),
        "object_inertia": backend._model.body_inertia[bid].copy(),
    }
    backend.shutdown()
    return snapshot


class TestMuJoCoDeterminism:
    def test_same_seed_reproduces_visual_and_geometry_state(self):
        first = _mujoco_snapshot(2024)
        second = _mujoco_snapshot(2024)
        assert first.keys() == second.keys()
        for key in first:
            np.testing.assert_array_equal(first[key], second[key], err_msg=key)

    def test_different_seed_changes_randomized_state(self):
        first = _mujoco_snapshot(2024)
        second = _mujoco_snapshot(2025)
        assert any(not np.array_equal(first[key], second[key]) for key in first)
