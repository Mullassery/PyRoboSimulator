"""Gazebo/ROS 2 runtime adapter with lazy imports and safe fallbacks.

Real Gazebo integration requires ROS 2 (rclpy) and Gazebo/ros_gz bridge.
All imports are deferred so the package loads without ROS 2 installed.
Supports dependency injection for tests.
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

GAZEBO_DOCS = "https://gazebosim.org/docs"
ROS2_DOCS = "https://docs.ros.org/"

PROBE_MODULES = (
    ("rclpy", "rclpy"),
    ("rclpy.node", None),
    ("rosgraph_msgs", None),
    ("geometry_msgs", None),
    ("sensor_msgs", None),
    ("std_srvs", None),
    ("ros_gz_interfaces", "ros_gz_interfaces"),
    ("ros_gz_bridge", None),
    ("gz.transport", "gz_transport"),
    ("gz.msgs", "gz_msgs"),
)


class GazeboRuntimeUnavailable(RuntimeError):
    """Raised when ROS 2/Gazebo runtime is not importable."""


@dataclass(frozen=True)
class GazeboRuntimeStatus:
    available: bool
    reason: str
    modules: Dict[str, bool]
    has_ros2: bool
    has_gz: bool
    has_bridge: bool
    env_vars: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "reason": self.reason,
            "modules": dict(self.modules),
            "has_ros2": self.has_ros2,
            "has_gz": self.has_gz,
            "has_bridge": self.has_bridge,
            "env_vars": dict(self.env_vars),
        }


def _import_if_available(module_name: str) -> Optional[Any]:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


class GazeboRuntime:
    def __init__(self, factory: Optional[Callable[[], Any]] = None):
        self._factory = factory
        self._node = None
        self._gz_node = None
        self._initialized = False

    def inspect(self) -> GazeboRuntimeStatus:
        modules = {}
        for module_name, key in PROBE_MODULES:
            available = _import_if_available(module_name) is not None
            if key is not None:
                modules[key] = available
            modules[module_name] = available

        has_ros2 = modules.get("rclpy", False)
        has_gz = modules.get("gz.transport", False) or modules.get("gz.msgs", False)
        has_bridge = modules.get("ros_gz_interfaces", False)

        env_vars = {}
        for key in ("ROS_DISTRO", "AMENT_PREFIX_PATH", "GZ_VERSION", "IGNITION_VERSION"):
            if key in os.environ:
                env_vars[key] = os.environ[key]

        if has_ros2 and (has_gz or has_bridge):
            reason = "ROS 2 and Gazebo/ros_gz detected. Real integration available via runtime."
            available = True
        elif has_ros2:
            reason = "rclpy detected but Gazebo/ros_gz bridge not found. Install ros_gz packages."
            available = False
        elif has_gz:
            reason = "Gazebo transport detected but ROS 2 not found. ROS 2 integration requires rclpy."
            available = False
        else:
            reason = "No ROS 2 or Gazebo runtime found. Requires ROS 2 + Gazebo/ros_gz installation."
            available = False

        return GazeboRuntimeStatus(
            available=available,
            reason=reason,
            modules=modules,
            has_ros2=has_ros2,
            has_gz=has_gz,
            has_bridge=has_bridge,
            env_vars=env_vars,
        )

    def ensure_available(self) -> None:
        status = self.inspect()
        if not status.available:
            raise GazeboRuntimeUnavailable(
                f"{status.reason} See {ROS2_DOCS} and {GAZEBO_DOCS}."
            )

    def initialize(self, **kwargs: Any) -> Any:
        if self._initialized:
            return self._node or self._gz_node

        if self._factory is not None:
            result = self._factory()
            self._initialized = True
            return result

        self.ensure_available()
        status = self.inspect()

        # Try ROS 2 first
        if status.has_ros2:
            try:
                rclpy = importlib.import_module("rclpy")
                if not rclpy.ok():
                    rclpy.init(args=kwargs.get("args"))
                self._node = rclpy.create_node(kwargs.get("node_name", "pyrobosimulator_gazebo"))
                self._initialized = True
                logger.info("Gazebo backend initialized via ROS 2 runtime")
                return self._node
            except Exception as exc:
                raise GazeboRuntimeUnavailable(f"Failed to initialize ROS 2 node: {exc}") from exc

        # Try Gazebo transport
        if status.has_gz:
            try:
                gz_transport = importlib.import_module("gz.transport")
                self._gz_node = gz_transport.Node()
                self._initialized = True
                logger.info("Gazebo backend initialized via Gazebo transport")
                return self._gz_node
            except Exception as exc:
                raise GazeboRuntimeUnavailable(f"Failed to initialize Gazebo transport: {exc}") from exc

        raise GazeboRuntimeUnavailable("No supported Gazebo runtime available")

    def step(self) -> None:
        if self._factory is not None and callable(getattr(self._node, "step", None)):
            self._node.step()
            return
        if self._node is not None:
            try:
                import rclpy
                rclpy.spin_once(self._node, timeout_sec=0.001)
            except Exception:
                pass

    def shutdown(self) -> None:
        if self._factory is not None and callable(getattr(self._node, "close", None)):
            try:
                self._node.close()
            except Exception:
                pass
        if self._node is not None:
            try:
                self._node.destroy_node()
            except Exception:
                pass
        try:
            import rclpy
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
        self._node = None
        self._gz_node = None
        self._initialized = False

    @staticmethod
    def environment_error_message() -> str:
        return (
            "Gazebo backend requires ROS 2 (rclpy) and Gazebo/ros_gz packages "
            "installed as system packages. Not available via pip in this environment."
        )
