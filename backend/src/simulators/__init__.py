"""Simulator Backend System - Multi-backend orchestration layer.

This package provides a unified interface for different robotics simulators.
Supports Isaac Sim, Gazebo, MuJoCo, PyBullet, and custom backends.
"""

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
    SimulatorBackend,
    SimulatorConfig,
    SimulatorType,
    WorldConfig,
)
from src.simulators.backend_manager import BackendContext, BackendFactory, BackendManager
from src.simulators.gazebo_backend import GazeboBackend
from src.simulators.isaac_sim_backend import IsaacSimBackend
from src.simulators.mock_backend import MockBackend
from src.simulators.mujoco_backend import MuJoCoBackend

__all__ = [
    # Enums
    "SimulatorType",
    "RobotType",
    "SensorType",
    "PhysicsEngineType",
    "RenderingBackend",
    # Config classes
    "SimulatorConfig",
    "RobotConfig",
    "SensorConfig",
    "CameraConfig",
    "LidarConfig",
    "IMUConfig",
    "WorldConfig",
    # State classes
    "RobotState",
    "ObjectState",
    "SensorData",
    "SimulationStep",
    "ContactInfo",
    # Backend classes
    "SimulatorBackend",
    "BackendFactory",
    "BackendManager",
    "BackendContext",
    # Backends
    "MockBackend",
    "MuJoCoBackend",
    "GazeboBackend",
    "IsaacSimBackend",
]

__version__ = "0.10.0"
__doc__ = __doc__
