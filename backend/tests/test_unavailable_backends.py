"""Tests for the Gazebo and Isaac Sim backends' honest-failure behavior.

Neither backend can do real physics in this environment (Gazebo needs a
full ROS 2 + Gazebo system install; Isaac Sim needs NVIDIA Omniverse + a
CUDA GPU). Rather than silently succeeding and pretending to simulate,
`initialize()` must fail loudly and explain why. These tests guard against
someone re-introducing the old silent-success stub behavior.
"""

import pytest

from src.simulators.backend_interface import (
    PhysicsEngineType,
    RenderingBackend,
    SimulatorConfig,
    SimulatorType,
)
from src.simulators.gazebo_backend import GazeboBackend
from src.simulators.isaac_sim_backend import IsaacSimBackend


class TestGazeboBackendHonesty:
    def test_initialize_raises_environment_error(self):
        backend = GazeboBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.GAZEBO,
            physics_engine=PhysicsEngineType.ODE,
            rendering_backend=RenderingBackend.HEADLESS,
        )
        with pytest.raises(EnvironmentError, match="ROS 2"):
            backend.initialize(config)

    def test_backend_is_not_running_after_failed_initialize(self):
        backend = GazeboBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.GAZEBO,
            physics_engine=PhysicsEngineType.ODE,
            rendering_backend=RenderingBackend.HEADLESS,
        )
        with pytest.raises(EnvironmentError):
            backend.initialize(config)
        assert backend.is_running() is False

    def test_last_error_explains_the_real_gap(self):
        backend = GazeboBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.GAZEBO,
            physics_engine=PhysicsEngineType.ODE,
            rendering_backend=RenderingBackend.HEADLESS,
        )
        with pytest.raises(EnvironmentError):
            backend.initialize(config)
        assert "MuJoCoBackend" in backend.get_last_error()


class TestIsaacSimBackendHonesty:
    def test_initialize_raises_environment_error(self):
        backend = IsaacSimBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.ISAAC_SIM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.RTX,
        )
        with pytest.raises(EnvironmentError, match="Omniverse"):
            backend.initialize(config)

    def test_backend_is_not_running_after_failed_initialize(self):
        backend = IsaacSimBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.ISAAC_SIM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.RTX,
        )
        with pytest.raises(EnvironmentError):
            backend.initialize(config)
        assert backend.is_running() is False

    def test_last_error_explains_the_real_gap(self):
        backend = IsaacSimBackend()
        config = SimulatorConfig(
            simulator_type=SimulatorType.ISAAC_SIM,
            physics_engine=PhysicsEngineType.PHYSX,
            rendering_backend=RenderingBackend.RTX,
        )
        with pytest.raises(EnvironmentError):
            backend.initialize(config)
        assert "MuJoCoBackend" in backend.get_last_error()
