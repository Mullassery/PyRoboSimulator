"""Autonomous Regional Intelligence - Knowledge Models and Storage.

Stores learned environmental characteristics as statistical distributions,
not memorized frames. Enables incremental learning and knowledge reuse.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Environment classification."""

    URBAN = "urban"
    SEMI_URBAN = "semi_urban"
    RURAL = "rural"
    INDUSTRIAL = "industrial"
    HIGHWAY = "highway"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    AGRICULTURAL = "agricultural"
    MOUNTAINOUS = "mountainous"
    COASTAL = "coastal"
    DESERT = "desert"
    FOREST = "forest"


class RoadType(Enum):
    """Road type classification."""

    SINGLE_LANE = "single_lane"
    TWO_LANE = "two_lane"
    FOUR_LANE = "four_lane"
    SIX_LANE = "six_lane"
    DIVIDED_HIGHWAY = "divided_highway"
    ROUNDABOUT = "roundabout"
    DIRT_ROAD = "dirt_road"
    PAVED_ROAD = "paved_road"


class VehicleType(Enum):
    """Vehicle type classification."""

    MOTORCYCLE = "motorcycle"
    CAR = "car"
    SUV = "suv"
    TRUCK = "truck"
    BUS = "bus"
    BICYCLE = "bicycle"
    SCOOTER = "scooter"
    TRACTOR = "tractor"
    RICKSHAW = "rickshaw"
    CONSTRUCTION_VEHICLE = "construction_vehicle"
    ANIMAL_DRAWN = "animal_drawn"


@dataclass
class RoadCharacteristics:
    """Learned characteristics of roads in a region."""

    road_type_distribution: Dict[str, float] = field(
        default_factory=lambda: {rt.value: 0.0 for rt in RoadType}
    )
    avg_lane_width: float = 3.5  # meters
    surface_quality_distribution: Dict[str, float] = field(
        default_factory=lambda: {
            "excellent": 0.0,
            "good": 0.0,
            "fair": 0.0,
            "poor": 0.0,
            "potholed": 0.0,
        }
    )
    pothole_frequency: float = 0.0  # potholes per km
    has_median: float = 0.0  # probability (0-1)
    has_sidewalk: float = 0.0
    speed_limit_typical: int = 50  # km/h
    lane_discipline_score: float = 0.5  # 0=chaotic, 1=disciplined
    intersection_density: float = 0.0  # intersections per km
    roundabout_frequency: float = 0.0  # roundabouts per km
    traffic_signal_coverage: float = 0.0  # 0-1
    observations_count: int = 0
    confidence: float = 0.0  # 0-1


@dataclass
class VehicleDistribution:
    """Learned vehicle type distribution in region."""

    distribution: Dict[str, float] = field(
        default_factory=lambda: {vt.value: 0.0 for vt in VehicleType}
    )
    avg_vehicle_density: float = 0.0  # vehicles per hour
    peak_hour_factor: float = 1.5  # multiplier during peak
    observations_count: int = 0
    confidence: float = 0.0


@dataclass
class PedestrianCharacteristics:
    """Learned pedestrian behavior in region."""

    avg_pedestrian_density: float = 0.0  # people per m²
    crossing_discipline: float = 0.5  # 0=chaotic, 1=disciplined
    sidewalk_usage: float = 0.5  # probability
    jaywalking_frequency: float = 0.3  # probability
    peak_hour_factor: float = 1.8
    common_crossing_locations: List[str] = field(default_factory=list)
    observations_count: int = 0
    confidence: float = 0.0


@dataclass
class TerrainCharacteristics:
    """Learned terrain characteristics."""

    terrain_type: str = "flat"  # flat, hilly, mountainous, desert
    elevation_range: Tuple[float, float] = (0.0, 1000.0)  # meters
    slope_distribution: Dict[str, float] = field(
        default_factory=lambda: {
            "flat": 0.0,
            "gentle": 0.0,
            "moderate": 0.0,
            "steep": 0.0,
        }
    )
    vegetation_distribution: Dict[str, float] = field(
        default_factory=lambda: {
            "urban": 0.0,
            "trees": 0.0,
            "grass": 0.0,
            "shrubs": 0.0,
            "agricultural": 0.0,
            "bare": 0.0,
        }
    )
    water_features: List[str] = field(default_factory=list)
    observations_count: int = 0
    confidence: float = 0.0


@dataclass
class InfrastructureCharacteristics:
    """Learned infrastructure in region."""

    street_lights: float = 0.5  # density 0-1
    utility_poles: float = 0.4
    traffic_signs: float = 0.3
    traffic_lights: float = 0.2
    guardrails: float = 0.1
    speed_breakers: float = 0.0  # frequency
    bridges: float = 0.0
    tunnels: float = 0.0
    rail_crossings: float = 0.0
    building_density: float = 0.3  # 0-1
    building_height_avg: float = 3.0  # stories
    observations_count: int = 0
    confidence: float = 0.0


@dataclass
class WeatherCharacteristics:
    """Learned weather patterns in region."""

    rainfall_distribution: Dict[str, float] = field(
        default_factory=lambda: {
            "none": 0.0,
            "light": 0.0,
            "moderate": 0.0,
            "heavy": 0.0,
        }
    )
    temperature_range: Tuple[float, float] = (15.0, 35.0)
    humidity_avg: float = 60.0
    fog_frequency: float = 0.0
    dust_frequency: float = 0.0
    snow_frequency: float = 0.0
    sunshine_hours_daily: float = 8.0
    seasonal_variations: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )
    observations_count: int = 0
    confidence: float = 0.0


@dataclass
class RegionalKnowledge:
    """Complete learned knowledge of a region."""

    region_name: str
    country: str
    coordinates: Tuple[float, float]  # lat, lon
    environment_type: EnvironmentType
    environment_distribution: Dict[str, float] = field(
        default_factory=lambda: {et.value: 0.0 for et in EnvironmentType}
    )

    # Component knowledge
    roads: RoadCharacteristics = field(default_factory=RoadCharacteristics)
    vehicles: VehicleDistribution = field(default_factory=VehicleDistribution)
    pedestrians: PedestrianCharacteristics = field(
        default_factory=PedestrianCharacteristics
    )
    terrain: TerrainCharacteristics = field(default_factory=TerrainCharacteristics)
    infrastructure: InfrastructureCharacteristics = field(
        default_factory=InfrastructureCharacteristics
    )
    weather: WeatherCharacteristics = field(default_factory=WeatherCharacteristics)

    # Metadata
    learning_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    update_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source_videos: List[str] = field(default_factory=list)
    source_datasets: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    learning_iterations: int = 0
    observation_count: int = 0

    def get_confidence_score(self) -> float:
        """Calculate overall confidence from component confidences.

        Returns:
            Average confidence (0-1)
        """
        confidences = [
            self.roads.confidence,
            self.vehicles.confidence,
            self.pedestrians.confidence,
            self.terrain.confidence,
            self.infrastructure.confidence,
            self.weather.confidence,
        ]

        valid_confidences = [c for c in confidences if c > 0]

        if not valid_confidences:
            return 0.0

        return sum(valid_confidences) / len(valid_confidences)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "region_name": self.region_name,
            "country": self.country,
            "coordinates": self.coordinates,
            "environment_type": self.environment_type.value,
            "roads": asdict(self.roads),
            "vehicles": asdict(self.vehicles),
            "pedestrians": asdict(self.pedestrians),
            "terrain": asdict(self.terrain),
            "infrastructure": asdict(self.infrastructure),
            "weather": asdict(self.weather),
            "learning_timestamp": self.learning_timestamp,
            "update_timestamp": self.update_timestamp,
            "overall_confidence": self.overall_confidence,
            "learning_iterations": self.learning_iterations,
            "observation_count": self.observation_count,
        }

    def to_json(self) -> str:
        """Serialize to JSON.

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "RegionalKnowledge":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            RegionalKnowledge instance
        """
        knowledge = RegionalKnowledge(
            region_name=data["region_name"],
            country=data["country"],
            coordinates=tuple(data["coordinates"]),
            environment_type=EnvironmentType(data["environment_type"]),
        )

        knowledge.roads = RoadCharacteristics(**data["roads"])
        knowledge.vehicles = VehicleDistribution(**data["vehicles"])
        knowledge.pedestrians = PedestrianCharacteristics(**data["pedestrians"])
        knowledge.terrain = TerrainCharacteristics(**data["terrain"])
        knowledge.infrastructure = InfrastructureCharacteristics(**data["infrastructure"])
        knowledge.weather = WeatherCharacteristics(**data["weather"])

        knowledge.learning_timestamp = data.get("learning_timestamp", "")
        knowledge.update_timestamp = data.get("update_timestamp", "")
        knowledge.overall_confidence = data.get("overall_confidence", 0.0)
        knowledge.learning_iterations = data.get("learning_iterations", 0)
        knowledge.observation_count = data.get("observation_count", 0)

        return knowledge


class KnowledgeStore:
    """Persistent knowledge storage and retrieval."""

    def __init__(self):
        """Initialize knowledge store."""
        self._knowledge: Dict[str, RegionalKnowledge] = {}
        self._cache_dirty = False

    def add_or_update(self, knowledge: RegionalKnowledge) -> None:
        """Add or update regional knowledge.

        Args:
            knowledge: Regional knowledge to store
        """
        key = f"{knowledge.country}_{knowledge.region_name}".lower().replace(" ", "_")
        self._knowledge[key] = knowledge
        self._cache_dirty = True

        logger.info(f"Stored knowledge for {knowledge.region_name}, {knowledge.country}")

    def get(self, region_name: str, country: str) -> Optional[RegionalKnowledge]:
        """Get knowledge for a region.

        Args:
            region_name: Region name
            country: Country name

        Returns:
            RegionalKnowledge or None
        """
        key = f"{country}_{region_name}".lower().replace(" ", "_")
        return self._knowledge.get(key)

    def has_knowledge(self, region_name: str, country: str, min_confidence: float = 0.5) -> bool:
        """Check if sufficient knowledge exists.

        Args:
            region_name: Region name
            country: Country name
            min_confidence: Minimum confidence threshold

        Returns:
            True if knowledge exists and meets confidence
        """
        knowledge = self.get(region_name, country)

        if not knowledge:
            return False

        return knowledge.get_confidence_score() >= min_confidence

    def list_regions(self) -> List[str]:
        """List all known regions.

        Returns:
            List of region names
        """
        return list(self._knowledge.keys())

    def get_all(self) -> Dict[str, RegionalKnowledge]:
        """Get all knowledge.

        Returns:
            Dictionary of all knowledge
        """
        return dict(self._knowledge)

    def save_to_json(self, filepath: str) -> None:
        """Save all knowledge to JSON file.

        Args:
            filepath: Path to save file
        """
        data = {key: knowledge.to_dict() for key, knowledge in self._knowledge.items()}

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(self._knowledge)} regions to {filepath}")

    def load_from_json(self, filepath: str) -> None:
        """Load knowledge from JSON file.

        Args:
            filepath: Path to load file
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        self._knowledge.clear()

        for key, region_data in data.items():
            knowledge = RegionalKnowledge.from_dict(region_data)
            self._knowledge[key] = knowledge

        logger.info(f"Loaded {len(self._knowledge)} regions from {filepath}")

    def merge_knowledge(
        self, new_knowledge: RegionalKnowledge, existing: Optional[RegionalKnowledge] = None
    ) -> RegionalKnowledge:
        """Merge new observations into existing knowledge (incremental learning).

        Args:
            new_knowledge: New observations
            existing: Existing knowledge (or retrieved if None)

        Returns:
            Merged knowledge
        """
        if existing is None:
            existing = self.get(new_knowledge.region_name, new_knowledge.country)

        if existing is None:
            return new_knowledge

        # Simple averaging of distributions (can be enhanced)
        merged = RegionalKnowledge(
            region_name=existing.region_name,
            country=existing.country,
            coordinates=existing.coordinates,
            environment_type=existing.environment_type,
        )

        # Merge roads
        merged.roads.observations_count = (
            existing.roads.observations_count + new_knowledge.roads.observations_count
        )
        for road_type in existing.roads.road_type_distribution:
            old_dist = existing.roads.road_type_distribution.get(road_type, 0.0)
            new_dist = new_knowledge.roads.road_type_distribution.get(road_type, 0.0)
            old_count = existing.roads.observations_count
            new_count = new_knowledge.roads.observations_count

            if old_count + new_count > 0:
                merged.roads.road_type_distribution[road_type] = (
                    old_dist * old_count + new_dist * new_count
                ) / (old_count + new_count)

        # Update confidence and metadata
        merged.overall_confidence = merged.get_confidence_score()
        merged.learning_iterations = existing.learning_iterations + 1
        merged.observation_count = (
            existing.observation_count + new_knowledge.observation_count
        )
        merged.update_timestamp = datetime.now().isoformat()

        return merged
