"""Autonomous Regional Intelligence (ARI) System.

ARI automatically discovers and learns about unknown regions through
public data sources (YouTube, OpenStreetMap, elevation, weather).

Converts observations into statistical environmental models, never memorizing
individual frames or locations. Enables PyRoboSimulator to generate
realistic scenarios for any region, improving over time.

Example:
    >>> from backend.src.ari import ARIOrchestrator, ARIConfig
    >>> ari = ARIOrchestrator(ARIConfig())
    >>> if ari.needs_learning("Leh", "India"):
    ...     knowledge = ari.learn_region("Leh", "India", (34.16, 77.58))
    >>> ari.save_knowledge("regions.json")
"""

from backend.src.ari.ari_discovery import (
    ARIDiscoveryEngine,
    DiscoveryQuery,
    DiscoveredAsset,
    DiscoverySource,
    LearningPhase,
)
from backend.src.ari.ari_orchestrator import (
    ARIConfig,
    ARIOrchestrator,
)
from backend.src.ari.regional_knowledge import (
    EnvironmentType,
    KnowledgeStore,
    RegionalKnowledge,
    RoadCharacteristics,
    RoadType,
    VehicleDistribution,
    VehicleType,
    PedestrianCharacteristics,
    TerrainCharacteristics,
    InfrastructureCharacteristics,
    WeatherCharacteristics,
)

__all__ = [
    # Discovery
    "ARIDiscoveryEngine",
    "DiscoveryQuery",
    "DiscoveredAsset",
    "DiscoverySource",
    "LearningPhase",
    # Orchestrator
    "ARIOrchestrator",
    "ARIConfig",
    # Knowledge Models
    "RegionalKnowledge",
    "KnowledgeStore",
    "RoadCharacteristics",
    "VehicleDistribution",
    "PedestrianCharacteristics",
    "TerrainCharacteristics",
    "InfrastructureCharacteristics",
    "WeatherCharacteristics",
    # Enums
    "EnvironmentType",
    "RoadType",
    "VehicleType",
]

__version__ = "0.8.0"
