"""Tests for Autonomous Regional Intelligence System (Phase 4.1)."""

import json
import pytest

from src.ari.ari_discovery import (
    ARIDiscoveryEngine,
    DiscoverySource,
    LearningPhase,
)
from src.ari.ari_orchestrator import ARIConfig, ARIOrchestrator
from src.ari.regional_knowledge import (
    EnvironmentType,
    KnowledgeStore,
    RegionalKnowledge,
    RoadType,
    VehicleType,
)


class TestRegionalKnowledge:
    """Test regional knowledge models."""

    def test_knowledge_creation(self):
        """Test creating regional knowledge."""
        knowledge = RegionalKnowledge(
            region_name="Leh",
            country="India",
            coordinates=(34.16, 77.58),
            environment_type=EnvironmentType.MOUNTAINOUS,
        )

        assert knowledge.region_name == "Leh"
        assert knowledge.country == "India"
        assert knowledge.coordinates == (34.16, 77.58)

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        knowledge = RegionalKnowledge(
            region_name="Test",
            country="Country",
            coordinates=(0.0, 0.0),
            environment_type=EnvironmentType.URBAN,
        )

        # Initially zero
        assert knowledge.get_confidence_score() == 0.0

        # Add some confidence
        knowledge.roads.confidence = 0.8
        knowledge.vehicles.confidence = 0.7

        confidence = knowledge.get_confidence_score()
        assert 0.7 < confidence < 0.8  # Average of 0.8 and 0.7

    def test_knowledge_serialization(self):
        """Test knowledge to/from JSON."""
        knowledge = RegionalKnowledge(
            region_name="Leh",
            country="India",
            coordinates=(34.16, 77.58),
            environment_type=EnvironmentType.MOUNTAINOUS,
        )

        knowledge.roads.confidence = 0.75
        knowledge.overall_confidence = 0.6

        # Serialize
        json_str = knowledge.to_json()
        assert "Leh" in json_str
        assert '"confidence": 0.75' in json_str

        # Deserialize
        data = json.loads(json_str)
        restored = RegionalKnowledge.from_dict(data)

        assert restored.region_name == "Leh"
        assert restored.roads.confidence == 0.75

    def test_knowledge_dict_conversion(self):
        """Test knowledge to/from dict."""
        knowledge = RegionalKnowledge(
            region_name="Tokyo",
            country="Japan",
            coordinates=(35.68, 139.69),
            environment_type=EnvironmentType.URBAN,
        )

        d = knowledge.to_dict()

        assert d["region_name"] == "Tokyo"
        assert d["country"] == "Japan"

        restored = RegionalKnowledge.from_dict(d)

        assert restored.region_name == "Tokyo"
        assert restored.country == "Japan"


class TestKnowledgeStore:
    """Test knowledge storage and retrieval."""

    def test_store_creation(self):
        """Test creating knowledge store."""
        store = KnowledgeStore()

        assert len(store.list_regions()) == 0

    def test_add_and_retrieve(self):
        """Test adding and retrieving knowledge."""
        store = KnowledgeStore()

        knowledge = RegionalKnowledge(
            region_name="Leh",
            country="India",
            coordinates=(34.16, 77.58),
            environment_type=EnvironmentType.MOUNTAINOUS,
        )

        store.add_or_update(knowledge)

        retrieved = store.get("Leh", "India")

        assert retrieved is not None
        assert retrieved.region_name == "Leh"

    def test_has_knowledge_with_confidence(self):
        """Test knowledge existence with confidence threshold."""
        store = KnowledgeStore()

        knowledge = RegionalKnowledge(
            region_name="Test",
            country="Country",
            coordinates=(0.0, 0.0),
            environment_type=EnvironmentType.URBAN,
        )

        knowledge.roads.confidence = 0.3
        knowledge.overall_confidence = 0.3

        store.add_or_update(knowledge)

        # Should have knowledge but below threshold
        assert not store.has_knowledge("Test", "Country", min_confidence=0.5)
        assert store.has_knowledge("Test", "Country", min_confidence=0.2)

    def test_merge_knowledge(self):
        """Test incremental knowledge merging."""
        store = KnowledgeStore()

        # First observation
        knowledge1 = RegionalKnowledge(
            region_name="Region",
            country="Country",
            coordinates=(0.0, 0.0),
            environment_type=EnvironmentType.URBAN,
        )

        knowledge1.roads.road_type_distribution["two_lane"] = 0.6
        knowledge1.roads.road_type_distribution["four_lane"] = 0.4
        knowledge1.roads.observations_count = 100

        store.add_or_update(knowledge1)

        # Second observation (refinement)
        knowledge2 = RegionalKnowledge(
            region_name="Region",
            country="Country",
            coordinates=(0.0, 0.0),
            environment_type=EnvironmentType.URBAN,
        )

        knowledge2.roads.road_type_distribution["two_lane"] = 0.5
        knowledge2.roads.road_type_distribution["four_lane"] = 0.5
        knowledge2.roads.observations_count = 100

        merged = store.merge_knowledge(knowledge2, knowledge1)

        # Should be averaged
        assert 0.5 <= merged.roads.road_type_distribution["two_lane"] <= 0.6
        assert merged.roads.observations_count == 200


class TestARIDiscoveryEngine:
    """Test ARI discovery engine."""

    def test_engine_creation(self):
        """Test creating discovery engine."""
        engine = ARIDiscoveryEngine()

        assert engine is not None

    def test_youtube_discovery(self):
        """Test YouTube video discovery."""
        engine = ARIDiscoveryEngine()

        videos = engine.discover_youtube_videos("Leh", "India", (34.16, 77.58))

        assert len(videos) > 0
        assert all(v.source == DiscoverySource.YOUTUBE for v in videos)

    def test_openstreetmap_discovery(self):
        """Test OSM data discovery."""
        engine = ARIDiscoveryEngine()

        osm_data = engine.discover_openstreetmap_data("Leh", "India", (34.16, 77.58))

        assert "roads" in osm_data
        assert "infrastructure" in osm_data
        assert "buildings" in osm_data

    def test_elevation_discovery(self):
        """Test elevation data discovery."""
        engine = ARIDiscoveryEngine()

        elevation = engine.discover_elevation_data("Leh", "India", (34.16, 77.58))

        assert "center_elevation_m" in elevation
        assert "terrain_type" in elevation

    def test_weather_discovery(self):
        """Test weather pattern discovery."""
        engine = ARIDiscoveryEngine()

        weather = engine.discover_weather_patterns("Leh", "India", (34.16, 77.58))

        assert "climate_type" in weather
        assert "seasons" in weather

    def test_traffic_discovery(self):
        """Test traffic pattern discovery."""
        engine = ARIDiscoveryEngine()

        traffic = engine.discover_traffic_patterns("Leh", "India")

        assert "peak_hour_factor" in traffic
        assert "lane_discipline_score" in traffic

    def test_frame_processing(self):
        """Test YouTube frame processing."""
        engine = ARIDiscoveryEngine()

        # Mock video URL
        frames = engine.process_youtube_frames("http://example.com/video", max_frames=20)

        assert len(frames) > 0
        assert all("detected_objects" in f for f in frames)

    def test_frame_analysis(self):
        """Test frame batch analysis."""
        engine = ARIDiscoveryEngine()

        frames = [
            {
                "frame_id": i,
                "road_type": "two_lane",
                "vehicle_count": 3,
                "pedestrian_count": 2,
                "infrastructure": ["traffic_light"],
            }
            for i in range(10)
        ]

        characteristics = engine.analyze_frame_batch(frames)

        assert "road_type_distribution" in characteristics
        assert "avg_vehicle_count" in characteristics
        assert characteristics["frame_analysis_count"] == 10

    def test_confidence_estimation(self):
        """Test confidence score estimation."""
        engine = ARIDiscoveryEngine()

        confidence = engine.estimate_confidence(
            frame_count=500,
            source_diversity=4,
            temporal_span_days=60,
            geographic_spread_km=15.0,
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high


class TestARIOrchestrator:
    """Test ARI orchestrator."""

    def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        orchestrator = ARIOrchestrator()

        assert orchestrator is not None

    def test_needs_learning_unknown_region(self):
        """Test learning needs for unknown region."""
        orchestrator = ARIOrchestrator()

        needs = orchestrator.needs_learning("Unknown", "Country")

        assert needs is True

    def test_learn_region(self):
        """Test learning a region."""
        orchestrator = ARIOrchestrator()

        knowledge = orchestrator.learn_region(
            "Leh",
            "India",
            (34.16, 77.58),
            EnvironmentType.MOUNTAINOUS,
        )

        assert knowledge.region_name == "Leh"
        assert knowledge.overall_confidence > 0.0
        assert knowledge.observation_count > 0

    def test_learn_and_store(self):
        """Test learning and storage integration."""
        orchestrator = ARIOrchestrator()

        knowledge = orchestrator.learn_region(
            "Tokyo",
            "Japan",
            (35.68, 139.69),
            EnvironmentType.URBAN,
        )

        # Should be in store
        assert orchestrator._knowledge_store.has_knowledge("Tokyo", "Japan")

        retrieved = orchestrator._knowledge_store.get("Tokyo", "Japan")

        assert retrieved.region_name == "Tokyo"

    def test_knowledge_persistence(self):
        """Test saving and loading knowledge."""
        import tempfile
        import os

        orchestrator = ARIOrchestrator()

        knowledge = orchestrator.learn_region(
            "Delhi",
            "India",
            (28.61, 77.21),
            EnvironmentType.URBAN,
        )

        # Save
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        orchestrator.save_knowledge(filepath)

        # Load in new orchestrator
        orchestrator2 = ARIOrchestrator()
        orchestrator2.load_knowledge(filepath)

        retrieved = orchestrator2._knowledge_store.get("Delhi", "India")

        assert retrieved is not None
        assert retrieved.region_name == "Delhi"

        # Cleanup
        os.unlink(filepath)

    def test_refine_knowledge(self):
        """Test knowledge refinement."""
        orchestrator = ARIOrchestrator()

        # Initial learning
        knowledge1 = orchestrator.learn_region(
            "Mumbai",
            "India",
            (19.08, 72.88),
            EnvironmentType.URBAN,
        )

        conf1 = knowledge1.overall_confidence
        iter1 = knowledge1.learning_iterations

        # Refine
        knowledge2 = orchestrator.refine_knowledge("Mumbai", "India")

        assert knowledge2 is not None
        assert knowledge2.learning_iterations > iter1

    def test_learning_status(self):
        """Test getting learning status."""
        orchestrator = ARIOrchestrator()

        # Unknown region
        status1 = orchestrator.get_learning_status("Unknown", "Country")
        assert not status1["known"]

        # Learn region
        orchestrator.learn_region("Bangalore", "India", (12.97, 77.59), EnvironmentType.URBAN)

        # Check status
        status2 = orchestrator.get_learning_status("Bangalore", "India")
        assert status2["known"]
        assert status2["confidence"] > 0.0

    def test_custom_config(self):
        """Test custom ARI configuration."""
        config = ARIConfig(
            auto_learn_threshold=0.6,
            max_learning_iterations=3,
            source_diversity_required=2,
        )

        orchestrator = ARIOrchestrator(config)

        assert orchestrator._config.auto_learn_threshold == 0.6
        assert orchestrator._config.max_learning_iterations == 3


class TestARIIntegration:
    """Integration tests for ARI system."""

    def test_complete_learning_workflow(self):
        """Test complete learning workflow."""
        orchestrator = ARIOrchestrator()

        # Step 1: Check if learning needed
        needs = orchestrator.needs_learning("NewCity", "NewCountry")
        assert needs is True

        # Step 2: Learn region
        knowledge = orchestrator.learn_region(
            "NewCity",
            "NewCountry",
            (0.0, 0.0),
            EnvironmentType.URBAN,
        )

        assert knowledge.observation_count > 0
        assert knowledge.overall_confidence > 0.0

        # Step 3: Check if still needs learning
        needs2 = orchestrator.needs_learning("NewCity", "NewCountry")
        assert not needs2  # Now we have knowledge

        # Step 4: Get status
        status = orchestrator.get_learning_status("NewCity", "NewCountry")
        assert status["known"]
        assert status["confidence"] > 0.0

    def test_multi_region_learning(self):
        """Test learning multiple regions."""
        orchestrator = ARIOrchestrator()

        regions = [
            ("Leh", "India", (34.16, 77.58)),
            ("Tokyo", "Japan", (35.68, 139.69)),
            ("Dubai", "UAE", (25.27, 55.36)),
        ]

        for region_name, country, coords in regions:
            knowledge = orchestrator.learn_region(region_name, country, coords)
            assert knowledge.region_name == region_name

        # Check all are stored
        stored_regions = orchestrator._knowledge_store.list_regions()
        assert len(stored_regions) >= 3

    def test_incremental_refinement(self):
        """Test iterative knowledge refinement."""
        orchestrator = ARIOrchestrator()

        # Initial learning
        knowledge = orchestrator.learn_region(
            "TestCity",
            "TestCountry",
            (0.0, 0.0),
            EnvironmentType.URBAN,
        )

        confidences = [knowledge.overall_confidence]

        # Multiple refinement iterations
        for _ in range(2):
            refined = orchestrator.refine_knowledge("TestCity", "TestCountry")

            if refined:
                confidences.append(refined.overall_confidence)

        # Confidence should improve or stay same (not decrease)
        for i in range(len(confidences) - 1):
            assert confidences[i + 1] >= confidences[i]
