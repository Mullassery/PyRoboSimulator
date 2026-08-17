"""PyRoboSimulator: AI-native world simulation engine for robotics, narratives, and agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyrobosimulator")
except PackageNotFoundError:  # pragma: no cover - only when running from source, unpackaged
    __version__ = "0.0.0+unknown"

try:
    from ._core import World, Agent, AgentType, Mission, NarrativeEngine, ROS2Bridge
except ImportError:
    pass

__all__ = ["World", "Agent", "AgentType", "Mission", "NarrativeEngine", "ROS2Bridge"]
