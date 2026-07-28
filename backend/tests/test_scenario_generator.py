"""Tests for scenario generation and world configuration."""

import pytest
from src.services.scenario_generator import (
    ScenarioBuilder,
    WorldConfig,
    SpawnZone,
    Obstacle,
)


class TestSpawnZone:
    """Spawn zone configuration tests."""

    def test_spawn_zone_creation(self) -> None:
        """Test spawn zone initialization."""
        zone = SpawnZone(x=100, y=100, radius=50, max_agents=100)

        assert zone.x == 100
        assert zone.y == 100
        assert zone.radius == 50
        assert zone.max_agents == 100

    def test_spawn_zone_sampling(self) -> None:
        """Test random position sampling within zone."""
        zone = SpawnZone(x=0, y=0, radius=10, max_agents=10)

        # Sample 10 positions
        positions = [zone.sample_position() for _ in range(10)]

        # All should be within zone
        for x, y in positions:
            distance = (x**2 + y**2) ** 0.5
            assert distance <= zone.radius + 0.1

    def test_spawn_zone_to_dict(self) -> None:
        """Test zone serialization."""
        zone = SpawnZone(x=100, y=100, radius=50, max_agents=100)
        data = zone.to_dict()

        assert data["x"] == 100
        assert data["radius"] == 50
        assert data["max_agents"] == 100


class TestObstacle:
    """Obstacle configuration tests."""

    def test_obstacle_creation(self) -> None:
        """Test obstacle initialization."""
        obstacle = Obstacle(x=500, y=500, radius=50)

        assert obstacle.x == 500
        assert obstacle.y == 500
        assert obstacle.radius == 50

    def test_obstacle_to_dict(self) -> None:
        """Test obstacle serialization."""
        obstacle = Obstacle(x=500, y=500, radius=50)
        data = obstacle.to_dict()

        assert data["x"] == 500
        assert data["radius"] == 50


class TestWorldConfig:
    """World configuration tests."""

    def test_world_config_creation(self) -> None:
        """Test world configuration initialization."""
        world = WorldConfig(
            x_min=0,
            x_max=1000,
            y_min=0,
            y_max=1000,
            grid_size=50.0,
        )

        assert world.x_max == 1000
        assert world.grid_size == 50.0

    def test_add_spawn_zone(self) -> None:
        """Test adding spawn zones."""
        world = WorldConfig()
        world.add_spawn_zone(100, 100, 50, 100)

        assert len(world.spawn_zones) == 1
        assert world.spawn_zones[0].x == 100

    def test_add_obstacle(self) -> None:
        """Test adding obstacles."""
        world = WorldConfig()
        world.add_obstacle(500, 500, 50)

        assert len(world.obstacles) == 1
        assert world.obstacles[0].radius == 50

    def test_get_spawn_capacity(self) -> None:
        """Test total spawn capacity calculation."""
        world = WorldConfig()
        world.add_spawn_zone(100, 100, 50, 100)
        world.add_spawn_zone(200, 200, 50, 200)

        capacity = world.get_total_spawn_capacity()
        assert capacity == 300

    def test_world_config_to_dict(self) -> None:
        """Test world configuration serialization."""
        world = WorldConfig(x_max=500, y_max=500)
        world.add_spawn_zone(100, 100, 50, 100)
        world.add_obstacle(250, 250, 50)

        data = world.to_dict()

        assert data["bounds"]["x_max"] == 500
        assert len(data["spawn_zones"]) == 1
        assert len(data["obstacles"]) == 1

    def test_world_config_from_dict(self) -> None:
        """Test deserializing world configuration."""
        data = {
            "bounds": {"x_min": 0, "x_max": 1000, "y_min": 0, "y_max": 1000},
            "grid_size": 50.0,
            "spawn_zones": [{"x": 100, "y": 100, "radius": 50, "max_agents": 100}],
            "obstacles": [{"x": 500, "y": 500, "radius": 50}],
            "weather": "sunny",
            "time_of_day": "noon",
        }

        world = ScenarioBuilder.from_dict(data)

        assert world.x_max == 1000
        assert len(world.spawn_zones) == 1
        assert len(world.obstacles) == 1


class TestScenarioBuilder:
    """Scenario builder tests."""

    def test_parking_lot_scenario(self) -> None:
        """Test parking lot scenario generation."""
        world = ScenarioBuilder.parking_lot()

        assert world.x_max == 200
        assert world.y_max == 200
        assert len(world.spawn_zones) == 20  # 4x5 grid
        assert len(world.obstacles) >= 1

    def test_warehouse_scenario(self) -> None:
        """Test warehouse scenario generation."""
        world = ScenarioBuilder.warehouse()

        assert world.x_max == 500
        assert world.y_max == 500
        assert len(world.spawn_zones) == 4  # 4 corners
        assert len(world.obstacles) >= 4  # Shelves

    def test_urban_street_scenario(self) -> None:
        """Test urban street scenario generation."""
        world = ScenarioBuilder.urban_street()

        assert world.x_max == 1000
        assert world.y_max == 1000
        assert len(world.spawn_zones) >= 4  # Multiple intersections
        assert len(world.obstacles) >= 4  # Buildings

    def test_random_world_scenario(self) -> None:
        """Test random world generation."""
        world = ScenarioBuilder.random_world(
            num_agents=500,
            width=1000,
            height=1000,
            num_obstacles=20,
        )

        assert world.x_max == 1000
        assert world.y_max == 1000
        assert len(world.spawn_zones) >= 1
        assert len(world.obstacles) == 20

    def test_random_world_spawn_capacity(self) -> None:
        """Test random world has sufficient spawn capacity."""
        num_agents = 1000
        world = ScenarioBuilder.random_world(
            num_agents=num_agents,
            width=1000,
            height=1000,
            num_obstacles=10,
        )

        capacity = world.get_total_spawn_capacity()
        assert capacity >= num_agents

    def test_scenario_serialization_roundtrip(self) -> None:
        """Test scenario can be serialized and deserialized."""
        original = ScenarioBuilder.parking_lot()
        data = original.to_dict()
        restored = ScenarioBuilder.from_dict(data)

        assert restored.x_max == original.x_max
        assert restored.y_max == original.y_max
        assert len(restored.spawn_zones) == len(original.spawn_zones)
        assert len(restored.obstacles) == len(original.obstacles)
