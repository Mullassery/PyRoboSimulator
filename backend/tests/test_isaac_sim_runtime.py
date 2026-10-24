"""Contract tests for Isaac Sim runtime adapter and backend integration."""

import pytest

from src.integrations.isaac_sim_runtime import IsaacSimRuntime, IsaacSimRuntimeUnavailable
from src.simulators.backend_interface import (
    PhysicsEngineType,
    RenderingBackend,
    SimulatorConfig,
    SimulatorType,
)
from src.simulators.isaac_sim_backend import IsaacSimBackend


class FakeWorld:
    def __init__(self):
        self.steps = 0
        self.resets = 0

    def step(self, render=True):
        self.steps += 1

    def reset(self):
        self.resets += 1


class FakeRuntime(IsaacSimRuntime):
    def __init__(self):
        super().__init__(factory=self._make)
        self.world = FakeWorld()
        self.initialized = False
        self.shutdown_called = False

    def _make(self):
        self.initialized = True
        return self.world

    def shutdown(self):
        self.shutdown_called = True
        super().shutdown()


def test_runtime_inspect_no_omniverse():
    runtime = IsaacSimRuntime()
    status = runtime.inspect()
    assert status.available is False
    assert "Omniverse" in status.reason or "Isaac Sim" in status.reason


def test_backend_with_fake_runtime_initializes():
    runtime = FakeRuntime()
    backend = IsaacSimBackend(runtime=runtime)
    config = SimulatorConfig(
        simulator_type=SimulatorType.ISAAC_SIM,
        physics_engine=PhysicsEngineType.PHYSX,
        rendering_backend=RenderingBackend.RTX,
        headless_mode=True,
    )
    backend.initialize(config)
    assert backend.is_running() is True
    assert runtime.initialized is True
    step = backend.step(3)
    assert step.step_count == 3
    backend.pause()
    assert backend.is_paused() is True
    backend.resume()
    backend.reset()
    assert backend.list_robots() == []
    info = backend.get_simulation_info()
    assert info["simulator"] == "isaac_sim"
    backend.shutdown()
    assert runtime.shutdown_called is True


def test_backend_without_runtime_still_fails_honestly():
    backend = IsaacSimBackend(runtime=IsaacSimRuntime())
    config = SimulatorConfig(
        simulator_type=SimulatorType.ISAAC_SIM,
        physics_engine=PhysicsEngineType.PHYSX,
        rendering_backend=RenderingBackend.RTX,
    )
    with pytest.raises(EnvironmentError, match="Omniverse"):
        backend.initialize(config)
    assert backend.is_running() is False
    assert "MuJoCoBackend" in backend.get_last_error()
