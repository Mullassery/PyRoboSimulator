"""Contract tests for Gazebo runtime and backend integration."""

import pytest

from src.integrations.gazebo_runtime import GazeboRuntime
from src.simulators.backend_interface import (
    PhysicsEngineType,
    RenderingBackend,
    SimulatorConfig,
    SimulatorType,
)
from src.simulators.gazebo_backend import GazeboBackend


class FakeGazeboRuntime(GazeboRuntime):
    def __init__(self):
        super().__init__(factory=self._make)
        self.initialized = False
        self.shutdown_called = False

    def _make(self):
        self.initialized = True
        return object()

    def shutdown(self):
        self.shutdown_called = True
        super().shutdown()


def test_gazebo_runtime_inspect_no_ros():
    runtime = GazeboRuntime()
    status = runtime.inspect()
    assert status.available is False


def test_gazebo_backend_with_fake_runtime_initializes():
    runtime = FakeGazeboRuntime()
    backend = GazeboBackend(runtime=runtime)
    config = SimulatorConfig(
        simulator_type=SimulatorType.GAZEBO,
        physics_engine=PhysicsEngineType.ODE,
        rendering_backend=RenderingBackend.HEADLESS,
        headless_mode=True,
    )
    backend.initialize(config)
    assert backend.is_running() is True
    assert runtime.initialized is True
    step = backend.step(2)
    assert step.step_count == 2
    backend.pause()
    assert backend.is_paused() is True
    backend.resume()
    backend.reset()
    info = backend.get_simulation_info()
    assert info["simulator"] == "gazebo"
    backend.shutdown()
    assert runtime.shutdown_called is True


def test_gazebo_backend_without_runtime_still_fails_honestly():
    backend = GazeboBackend(runtime=GazeboRuntime())
    config = SimulatorConfig(
        simulator_type=SimulatorType.GAZEBO,
        physics_engine=PhysicsEngineType.ODE,
        rendering_backend=RenderingBackend.HEADLESS,
    )
    with pytest.raises(EnvironmentError, match="ROS 2"):
        backend.initialize(config)
    assert backend.is_running() is False
    assert "MuJoCoBackend" in backend.get_last_error()
