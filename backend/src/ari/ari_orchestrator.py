"""Autonomous Regional Intelligence - Main Orchestrator.

Coordinates the complete learning lifecycle:
discover → analyze → aggregate → validate → persist → integrate
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from backend.src.ari.ari_discovery import ARIDiscoveryEngine, DiscoverySource
from backend.src.ari.regional_knowledge import (
    EnvironmentType,
    KnowledgeStore,
    RegionalKnowledge,
    RoadCharacteristics,
    VehicleDistribution,
    PedestrianCharacteristics,
    TerrainCharacteristics,
    InfrastructureCharacteristics,
    WeatherCharacteristics,
)

logger = logging.getLogger(__name__)


@dataclass
class ARIConfig:
    """Configuration for ARI system."""

    auto_learn_threshold: float = 0.5  # Confidence below this triggers learning
    max_learning_iterations: int = 5  # Maximum times to refine knowledge
    source_diversity_required: int = 3  # Minimum sources
    temporal_span_days_minimum: int = 30  # Minimum temporal coverage
    geographic_spread_km_minimum: float = 10.0  # Minimum geographic coverage
    enable_youtube_learning: bool = True
    enable_osm_learning: bool = True
    enable_elevation_learning: bool = True
    enable_weather_learning: bool = True
    enable_traffic_learning: bool = True
    learning_timeout_seconds: Optional[int] = None  # No timeout if None


class ARIOrchestrator:
    """Orchestrates autonomous regional intelligence learning.

    Automatically discovers, learns, and stores environmental knowledge
    about unknown regions. Enables scenario generation to use learned
    characteristics.
    """

    def __init__(self, config: Optional[ARIConfig] = None, knowledge_store: Optional[KnowledgeStore] = None):
        """Initialize ARI orchestrator.

        Args:
            config: ARI configuration
            knowledge_store: Knowledge store for persistence
        """
        self._config = config or ARIConfig()
        self._knowledge_store = knowledge_store or KnowledgeStore()
        self._discovery_engine = ARIDiscoveryEngine()
        self._learning_history: Dict[str, Dict[str, Any]] = {}

    def needs_learning(self, region_name: str, country: str) -> bool:
        """Determine if region needs learning.

        Args:
            region_name: Region name
            country: Country name

        Returns:
            True if learning is needed
        """
        if not self._knowledge_store.has_knowledge(region_name, country):
            logger.info(f"ARI: No knowledge for {region_name}, {country} - learning needed")
            return True

        knowledge = self._knowledge_store.get(region_name, country)

        if knowledge and knowledge.get_confidence_score() < self._config.auto_learn_threshold:
            logger.info(
                f"ARI: Low confidence ({knowledge.get_confidence_score():.1%}) "
                f"for {region_name} - refinement needed"
            )
            return True

        return False

    def learn_region(
        self,
        region_name: str,
        country: str,
        coordinates: Tuple[float, float],
        environment_type: EnvironmentType = EnvironmentType.URBAN,
    ) -> RegionalKnowledge:
        """Learn about an unknown region through autonomous discovery.

        Complete workflow:
        1. Discover public data sources
        2. Sample and analyze data
        3. Extract statistical characteristics
        4. Calculate confidence
        5. Store knowledge
        6. Log learning history

        Args:
            region_name: Region name
            country: Country name
            coordinates: Lat/lon
            environment_type: Primary environment type

        Returns:
            Learned regional knowledge
        """
        region_key = f"{country}_{region_name}".lower().replace(" ", "_")

        logger.info(
            f"ARI: Starting autonomous learning for {region_name}, {country}. "
            f"Coordinates: {coordinates}"
        )

        # Initialize knowledge object
        knowledge = RegionalKnowledge(
            region_name=region_name,
            country=country,
            coordinates=coordinates,
            environment_type=environment_type,
        )

        learning_results = {
            "region": region_key,
            "discoveries": {},
            "analyses": {},
            "confidence": 0.0,
        }

        # Phase 1: YouTube Video Discovery
        if self._config.enable_youtube_learning:
            logger.info("ARI Discovery Phase: YouTube videos")

            videos = self._discovery_engine.discover_youtube_videos(
                region_name, country, coordinates
            )

            learning_results["discoveries"]["youtube"] = len(videos)

            # Sample and process top videos
            for video in videos[:3]:  # Top 3 most relevant
                frames = self._discovery_engine.process_youtube_frames(video.url)
                characteristics = self._discovery_engine.analyze_frame_batch(frames)

                # Update road characteristics
                if "road_type_distribution" in characteristics:
                    for road_type, prob in characteristics["road_type_distribution"].items():
                        knowledge.roads.road_type_distribution[road_type] = prob

                knowledge.roads.observations_count += len(frames)

                video.processed = True

        # Phase 2: OpenStreetMap Data
        if self._config.enable_osm_learning:
            logger.info("ARI Discovery Phase: OpenStreetMap data")

            osm_data = self._discovery_engine.discover_openstreetmap_data(
                region_name, country, coordinates
            )

            learning_results["discoveries"]["osm"] = True

            # Extract infrastructure from OSM
            osm_infra = osm_data.get("infrastructure", {})

            # Normalize to densities
            knowledge.infrastructure.street_lights = min(
                osm_infra.get("street_lights", 0) / 1000.0, 1.0
            )
            knowledge.infrastructure.traffic_signals = min(
                osm_infra.get("traffic_signals", 0) / 100.0, 1.0
            )
            knowledge.infrastructure.traffic_signs = min(
                osm_infra.get("traffic_signs", 0) / 500.0, 1.0
            )

            # Extract building density
            buildings = osm_data.get("buildings", {})
            knowledge.infrastructure.building_density = min(
                buildings.get("total", 0) / 10000.0, 1.0
            )
            knowledge.infrastructure.building_height_avg = buildings.get("avg_height_stories", 2.0)

            knowledge.infrastructure.observations_count += 1

        # Phase 3: Elevation Data
        if self._config.enable_elevation_learning:
            logger.info("ARI Discovery Phase: Elevation data")

            elevation_data = self._discovery_engine.discover_elevation_data(
                region_name, country, coordinates
            )

            learning_results["discoveries"]["elevation"] = True

            # Update terrain characteristics
            knowledge.terrain.elevation_range = (
                elevation_data.get("min_elevation_m", 0.0),
                elevation_data.get("max_elevation_m", 1000.0),
            )
            knowledge.terrain.terrain_type = elevation_data.get("terrain_type", "flat")

            # Set slope distribution
            avg_slope = elevation_data.get("avg_slope_degrees", 0.0)

            if avg_slope < 2:
                knowledge.terrain.slope_distribution["flat"] = 0.8
                knowledge.terrain.slope_distribution["gentle"] = 0.2
            elif avg_slope < 10:
                knowledge.terrain.slope_distribution["gentle"] = 0.6
                knowledge.terrain.slope_distribution["moderate"] = 0.4
            else:
                knowledge.terrain.slope_distribution["steep"] = 0.7
                knowledge.terrain.slope_distribution["moderate"] = 0.3

            knowledge.terrain.observations_count += 1

        # Phase 4: Weather Patterns
        if self._config.enable_weather_learning:
            logger.info("ARI Discovery Phase: Weather patterns")

            weather_data = self._discovery_engine.discover_weather_patterns(
                region_name, country, coordinates
            )

            learning_results["discoveries"]["weather"] = True

            # Update weather characteristics
            knowledge.weather.temperature_range = (
                weather_data.get("temperature_avg_min", 15.0),
                weather_data.get("temperature_avg_max", 35.0),
            )
            knowledge.weather.humidity_avg = weather_data.get("humidity_avg", 60.0)
            knowledge.weather.sunshine_hours_daily = (
                weather_data.get("sunshine_hours_annual", 2500) / 365.0
            )

            # Set seasonal variations
            seasons = weather_data.get("seasons", {})
            if seasons:
                knowledge.weather.seasonal_variations = {
                    season: {
                        "temp_min": data.get("temp_range", [0, 0])[0],
                        "temp_max": data.get("temp_range", [0, 0])[1],
                        "rainfall_mm": data.get("rainfall_mm", 0),
                    }
                    for season, data in seasons.items()
                }

            knowledge.weather.observations_count += 1

        # Phase 5: Traffic Patterns
        if self._config.enable_traffic_learning:
            logger.info("ARI Discovery Phase: Traffic patterns")

            traffic_data = self._discovery_engine.discover_traffic_patterns(
                region_name, country
            )

            learning_results["discoveries"]["traffic"] = True

            # Update vehicle distribution
            knowledge.vehicles.avg_vehicle_density = traffic_data.get("avg_vehicles_per_hour", 0.0)
            knowledge.vehicles.peak_hour_factor = traffic_data.get("peak_hour_factor", 1.5)

            # Update road characteristics
            knowledge.roads.lane_discipline_score = traffic_data.get("lane_discipline_score", 0.5)
            knowledge.roads.speed_limit_typical = traffic_data.get("speed_limit_typical", 50)

            # Update pedestrian characteristics
            knowledge.pedestrians.crossing_discipline = traffic_data.get(
                "lane_discipline_score", 0.5
            )

            knowledge.vehicles.observations_count += 1

        # Phase 6: Confidence Calculation
        logger.info("ARI Analysis Phase: Confidence calculation")

        source_count = sum(
            1 for key in learning_results["discoveries"] if learning_results["discoveries"][key]
        )

        confidence = self._discovery_engine.estimate_confidence(
            frame_count=knowledge.roads.observations_count,
            source_diversity=source_count,
            temporal_span_days=self._config.temporal_span_days_minimum,
            geographic_spread_km=self._config.geographic_spread_km_minimum,
        )

        knowledge.overall_confidence = confidence
        knowledge.learning_iterations = 1
        knowledge.observation_count = sum(
            [
                knowledge.roads.observations_count,
                knowledge.vehicles.observations_count,
                knowledge.pedestrians.observations_count,
                knowledge.terrain.observations_count,
                knowledge.infrastructure.observations_count,
                knowledge.weather.observations_count,
            ]
        )

        learning_results["confidence"] = confidence

        # Phase 7: Persistence
        logger.info("ARI Persistence Phase: Storing knowledge")

        self._knowledge_store.add_or_update(knowledge)
        self._learning_history[region_key] = learning_results

        logger.info(
            f"ARI: Learning complete for {region_name}, {country}. "
            f"Confidence: {confidence:.1%}. Sources: {source_count}. "
            f"Observations: {knowledge.observation_count}"
        )

        return knowledge

    def refine_knowledge(
        self, region_name: str, country: str
    ) -> Optional[RegionalKnowledge]:
        """Refine existing knowledge through additional learning.

        Performs another iteration of discovery to improve confidence.

        Args:
            region_name: Region name
            country: Country name

        Returns:
            Refined knowledge or None if not available
        """
        existing = self._knowledge_store.get(region_name, country)

        if not existing:
            logger.warning(f"ARI: No existing knowledge to refine for {region_name}")
            return None

        if existing.learning_iterations >= self._config.max_learning_iterations:
            logger.warning(
                f"ARI: Max learning iterations reached for {region_name}. "
                f"Consider manual review."
            )
            return None

        logger.info(
            f"ARI: Refining knowledge for {region_name}, {country}. "
            f"Iteration {existing.learning_iterations + 1}"
        )

        # Perform another learning pass
        new_knowledge = self.learn_region(
            region_name, country, existing.coordinates, existing.environment_type
        )

        # Merge with existing
        merged = self._knowledge_store.merge_knowledge(new_knowledge, existing)

        self._knowledge_store.add_or_update(merged)

        logger.info(
            f"ARI: Knowledge refined. New confidence: {merged.overall_confidence:.1%}. "
            f"Total observations: {merged.observation_count}"
        )

        return merged

    def get_learning_status(self, region_name: str, country: str) -> Dict[str, Any]:
        """Get learning status for a region.

        Args:
            region_name: Region name
            country: Country name

        Returns:
            Status dictionary
        """
        region_key = f"{country}_{region_name}".lower().replace(" ", "_")
        knowledge = self._knowledge_store.get(region_name, country)

        status = {
            "region": f"{region_name}, {country}",
            "known": knowledge is not None,
            "confidence": knowledge.overall_confidence if knowledge else 0.0,
            "learning_iterations": knowledge.learning_iterations if knowledge else 0,
            "observation_count": knowledge.observation_count if knowledge else 0,
            "needs_refinement": (
                knowledge and knowledge.overall_confidence < self._config.auto_learn_threshold
            ),
            "learning_history": self._learning_history.get(region_key),
        }

        return status

    def save_knowledge(self, filepath: str) -> None:
        """Save learned knowledge to file.

        Args:
            filepath: Path to save file
        """
        self._knowledge_store.save_to_json(filepath)
        logger.info(f"ARI: Saved knowledge to {filepath}")

    def load_knowledge(self, filepath: str) -> None:
        """Load knowledge from file.

        Args:
            filepath: Path to load file
        """
        self._knowledge_store.load_from_json(filepath)
        logger.info(f"ARI: Loaded knowledge from {filepath}")

    def get_knowledge_store(self) -> KnowledgeStore:
        """Get the knowledge store.

        Returns:
            KnowledgeStore instance
        """
        return self._knowledge_store
