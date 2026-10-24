"""Isaac Sim runtime adapter with lazy imports and safe fallbacks.

NVIDIA Isaac Sim is not distributed on PyPI. This module probes for the
available API surface across supported Isaac Sim versions, prefers the
newer experimental APIs when present, and falls back to the command-based
``omni.kit.commands`` interfaces otherwise. All imports are deferred so
the rest of the simulator can load without Omniverse installed.

The adapter never fabricates sensor readings or world state. When the
runtime is unavailable, ``IsaacSimRuntime``, ``IsaacSimRuntimeUnavailable``,
and ``IsaacSimBackend`` raise clear ``EnvironmentError``/exceptions that
point to Omniverse + a CUDA-capable GPU. A dependency-injected fake
runtime is supported so unit tests can exercise initialization/lifecycle
without Omniverse.
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

ISAAC_SIM_DOCS = "https://docs.isaacsim.omniverse.nvidia.com/"
ISAAC_SIM_LAUNCHER = "https://docs.omniverse.nvidia.com/isaacsim/latest/installation/install_workstation.html"

PROBE_MODULES = (
    ("isaacsim.core.experimental", "experimental_core"),
    ("isaacsim.core.api", "core_api"),
    ("isaacsim.sensors.experimental.rtx", "experimental_rtx"),
    ("isaacsim.sensors.rtx", "rtx_sensors"),
    ("isaacsim.sensors.experimental.physics", "experimental_physics"),
    ("isaacsim.sensors.physics", "physics_sensors"),
    ("isaacsim.robot.manipulators.examples.franka", None),
    ("omni.isaac.core", "omni_isaac_core"),
    ("omni.physx", "omni_physx"),
    ("omni.kit.commands", "omni_kit_commands"),
    ("isaacsim.core.utils.nucleus", None),
    ("isaacsim.storage.native", None),
)


class IsaacSimRuntimeUnavailable(RuntimeError):
    """Raised when the Isaac Sim Omniverse runtime is not importable."""


@dataclass(frozen=True)
class IsaacSimRuntimeStatus:
    """Observable Isaac Sim runtime availability."""

    available: bool
    reason: str
    modules: Dict[str, bool]
    has_omni: bool
    has_isaacsim: bool
    using_experimental_core: bool
    using_experimental_rtx: bool
    using_experimental_physics: bool
    env_vars: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "reason": self.reason,
            "modules": dict(self.modules),
            "has_omni": self.has_omni,
            "has_isaacsim": self.has_isaacsim,
            "using_experimental_core": self.using_experimental_core,
            "using_experimental_rtx": self.using_experimental_rtx,
            "using_experimental_physics": self.using_experimental_physics,
            "env_vars": dict(self.env_vars),
        }


def _import_if_available(module_name: str) -> Optional[Any]:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


class IsaacSimRuntime:
    """Probe Isaac Sim APIs and provide safe lifecycle hooks with fallbacks."""

    def __init__(self, factory: Optional[Callable[[], Any]] = None):
        self._factory = factory
        self._world = None
        self._simulation_app = None
        self._modules: Dict[str, Any] = {}
        self._using_experimental_core = False
        self._using_experimental_rtx = False
        self._using_experimental_physics = False

    def inspect(self) -> IsaacSimRuntimeStatus:
        modules = {}
        for module_name, key in PROBE_MODULES:
            available = _import_if_available(module_name) is not None
            if key is not None:
                modules[key] = available
            modules[module_name] = available

        has_omni = modules.get("omni.physx", False) or modules.get("omni.kit.commands", False)
        has_isaacsim = modules.get("isaacsim.core.api", False) or modules.get(
            "isaacsim.core.experimental", False
        )
        experimental_core = modules.get("isaacsim.core.experimental", False)
        experimental_rtx = modules.get("isaacsim.sensors.experimental.rtx", False)
        experimental_physics = modules.get("isaacsim.sensors.experimental.physics", False)

        env_vars = {}
        for key in ("ISAAC_SIM_PATH", "OMNI_KIT_PATH", "CARB_APP_PATH", "EXP_PATH"):
            if key in os.environ:
                env_vars[key] = os.environ[key]

        if has_omni and has_isaacsim:
            reason = (
                "Isaac Sim/Omniverse modules detected. API surface may vary by "
                "version; this adapter prefers experimental APIs with fallbacks."
            )
            available = True
        elif has_omni:
            reason = (
                "Omniverse/PhysX modules detected but Isaac Sim core packages not "
                "found. Install Isaac Sim (Omniverse Launcher) or set ISAAC_SIM_PATH."
            )
            available = False
        else:
            reason = (
                "No Isaac Sim/Omniverse Python packages importable. NVIDIA Isaac Sim "
                "requires installation via the Omniverse Launcher and a CUDA-capable "
                "NVIDIA GPU for PhysX/RTX. PyRoboSimulator does not bundle it."
            )
            available = False

        return IsaacSimRuntimeStatus(
            available=available,
            reason=reason,
            modules=modules,
            has_omni=has_omni,
            has_isaacsim=has_isaacsim,
            using_experimental_core=experimental_core,
            using_experimental_rtx=experimental_rtx,
            using_experimental_physics=experimental_physics,
            env_vars=env_vars,
        )

    def ensure_available(self) -> None:
        status = self.inspect()
        if not status.available:
            raise IsaacSimRuntimeUnavailable(
                f"{status.reason} See {ISAAC_SIM_LAUNCHER} and {ISAAC_SIM_DOCS}."
            )

    def initialize(self, *, headless: bool = False, **kwargs: Any) -> Any:
        """Initialize Isaac Sim world/app with version-aware fallbacks.

        An injectable ``factory`` can be provided for tests; when set it is
        used instead of importing from the Omniverse runtime.
        """
        if self._world is not None or self._simulation_app is not None:
            return self._world

        if self._factory is not None:
            result = self._factory()
            self._world = result
            return result

        self.ensure_available()
        status = self.inspect()
        self._using_experimental_core = status.using_experimental_core
        self._using_experimental_rtx = status.using_experimental_rtx
        self._using_experimental_physics = status.using_experimental_physics

        if status.using_experimental_core:
            return self._initialize_experimental(headless=headless, **kwargs)
        return self._initialize_core_api(headless=headless, **kwargs)

    def _initialize_experimental(self, **kwargs: Any) -> Any:
        base_sample = _import_if_available("isaacsim.examples.base.base_sample_experimental")
        if base_sample is None:
            raise IsaacSimRuntimeUnavailable(
                "isaacsim.core.experimental is importable but BaseSample was not "
                "found; Isaac Sim API surface differs from the version this "
                "adapter targets."
            )
        # Experimental API initialization is app-driven; expose capability
        # without instantiating a GUI app here.
        self._modules["base_sample_experimental"] = base_sample
        logger.info("Isaac Sim experimental core API detected")
        return {"api": "experimental", "modules": self._modules}

    def _initialize_core_api(self, **kwargs: Any) -> Any:
        world_mod = _import_if_available("isaacsim.core.api.world")
        if world_mod is None:
            raise IsaacSimRuntimeUnavailable(
                "isaacsim.core.api.world not importable despite isaacsim.core.api "
                "being present."
            )
        world_cls = getattr(world_mod, "World", None)
        if world_cls is None:
            raise IsaacSimRuntimeUnavailable("isaacsim.core.api.world.World not found")
        # Construction varies by version; defer to caller with detected API.
        self._modules["world"] = world_mod
        logger.info("Isaac Sim core API detected")
        return {"api": "core", "world_cls": world_cls}

    def step(self, render: bool = True) -> None:
        if self._factory is not None and callable(getattr(self._world, "step", None)):
            self._world.step(render=render)
            return
        if self._world is None:
            raise IsaacSimRuntimeUnavailable("Isaac Sim world not initialized")
        step_fn = getattr(self._world, "step", None)
        if step_fn is None:
            raise NotImplementedError("Isaac Sim world does not expose step()")
        step_fn(render=render)

    def reset(self) -> None:
        if self._factory is not None and callable(getattr(self._world, "reset", None)):
            self._world.reset()
            return
        if self._world is None:
            raise IsaacSimRuntimeUnavailable("Isaac Sim world not initialized")
        reset_fn = getattr(self._world, "reset", None)
        if reset_fn is None:
            raise NotImplementedError("Isaac Sim world does not expose reset()")
        reset_fn()

    def shutdown(self) -> None:
        if self._factory is not None and callable(getattr(self._world, "close", None)):
            try:
                self._world.close()
            except Exception:
                logger.exception("Error closing fake Isaac Sim runtime")
        if self._simulation_app is not None:
            close = getattr(self._simulation_app, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    logger.exception("Error closing Isaac Sim SimulationApp")
        self._world = None
        self._simulation_app = None

    def get_sensor_api(self) -> Dict[str, Any]:
        """Report available sensor APIs for camera/LiDAR/IMU/contact."""
        status = self.inspect()
        apis = {
            "camera": None,
            "lidar": None,
            "imu": None,
            "contact": None,
        }
        if status.using_experimental_rtx:
            apis["lidar"] = "isaacsim.sensors.experimental.rtx (Lidar/LidarSensor)"
            apis["camera"] = "isaacsim.sensors.experimental.rtx or RtxCamera"
        elif status.modules.get("isaacsim.sensors.rtx"):
            apis["lidar"] = "isaacsim.sensors.rtx (LidarRtx, deprecated in 5.0)"
            apis["camera"] = "isaacsim.sensors.camera.Camera (deprecated)"
        if status.using_experimental_physics:
            apis["imu"] = "isaacsim.sensors.experimental.physics.IMU/IMUSensor"
            apis["contact"] = "isaacsim.sensors.experimental.physics.Contact/ContactSensor"
        elif status.modules.get("isaacsim.sensors.physics"):
            apis["imu"] = "isaacsim.sensors.physics.IMU (deprecated)"
            apis["contact"] = "isaacsim.sensors.physics.ContactSensor (deprecated)"
        return apis

    @staticmethod
    def environment_error_message() -> str:
        return (
            "Isaac Sim backend requires NVIDIA Isaac Sim installed via the "
            "Omniverse Launcher (isaacsim/omni packages) and a CUDA-capable "
            "NVIDIA GPU for PhysX/RTX. It is not pip-installable and is not "
            "available in this environment. Use MuJoCoBackend for real, "
            "working physics simulation."
        )
