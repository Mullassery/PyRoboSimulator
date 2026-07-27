"""PyRoboSimulator: AI-native world simulation engine for robotics, narratives, and agents."""

__version__ = "0.1.0"

try:
    from ._core import World, Agent, Mission, NarrativeEngine
except ImportError:
    pass

__all__ = ["World", "Agent", "Mission", "NarrativeEngine"]
