"""Sensor Configuration and Awareness System - Phase 5.0-5.1.

Comprehensive sensor framework for PyRoboSimulator enabling:
- Sensor configuration as mandatory initialization phase
- Only selected sensors generate data during simulation  
- Automatic discovery of commercial robot sensor profiles
- Robot hardware knowledge base with 60+ profiles
- Documentation-driven sensor extraction
- Compute optimization based on sensor suite

Example:
    >>> from backend.src.sensors import SensorConfigurationManager, SensorAwareSimulationEngine
    >>> from backend.src.sensors import RobotHardwareKnowledgeBase
    >>> 
    >>> # Automatic discovery for known robot
    >>> kb = RobotHardwareKnowledgeBase()
    >>> spot_profile = kb.get_profile("boston_dynamics_spot")
    >>> 
    >>> # Or manual configuration
    >>> manager = SensorConfigurationManager()
    >>> suite = manager.create_standard_suite("robot_1", "mobile")
    >>> manager.register_suite(suite)
    >>> 
    >>> # Initialize simulation with constraints
    >>> engine = SensorAwareSimulationEngine(manager)
    >>> engine.initialize_simulation("robot_1")
"""

from src.sensors.sensor_definitions import (
    SensorCategory, SensorType, SensorSpec, SensorRegistry, SENSOR_REGISTRY,
)
from src.sensors.sensor_configuration import (
    SensorSuite, SensorConfigurationManager,
)
from src.sensors.sensor_aware_engine import (
    SensorAwarenessConstraint, SensorAwareSimulationEngine,
)
from src.sensors.robot_knowledge_base import (
    RobotProfile, RobotHardwareKnowledgeBase, DocumentationParser,
    AutomaticRobotDiscovery,
)

__all__ = [
    # Definitions
    "SensorCategory", "SensorType", "SensorSpec", "SensorRegistry", "SENSOR_REGISTRY",
    # Configuration
    "SensorSuite", "SensorConfigurationManager",
    # Simulation Awareness
    "SensorAwarenessConstraint", "SensorAwareSimulationEngine",
    # Robot Discovery
    "RobotProfile", "RobotHardwareKnowledgeBase", "DocumentationParser",
    "AutomaticRobotDiscovery",
]

__version__ = "0.9.0"
