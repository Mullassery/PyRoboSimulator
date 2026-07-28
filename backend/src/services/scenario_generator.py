"""Scenario generation and world configuration."""

from typing import Any, Dict, List, Tuple

import numpy as np


class SpawnZone:
    """Defines a zone where agents can spawn."""

    def __init__(self, x: float, y: float, radius: float, max_agents: int):
        """Initialize spawn zone.

        Args:
            x, y: Center coordinates
            radius: Zone radius in meters
            max_agents: Maximum agents that can spawn here
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.max_agents = max_agents

    def sample_position(self) -> Tuple[float, float]:
        """Sample random position within spawn zone."""
        angle = np.random.uniform(0, 2 * np.pi)
        r = np.random.uniform(0, self.radius)
        x = self.x + r * np.cos(angle)
        y = self.y + r * np.sin(angle)
        return (x, y)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "max_agents": self.max_agents,
        }


class Obstacle:
    """Static obstacle in world."""

    def __init__(self, x: float, y: float, radius: float):
        """Initialize obstacle.

        Args:
            x, y: Center coordinates
            radius: Obstacle radius
        """
        self.x = x
        self.y = y
        self.radius = radius

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {"x": self.x, "y": self.y, "radius": self.radius}


class WorldConfig:
    """World configuration for a scenario."""

    def __init__(
        self,
        x_min: float = 0,
        x_max: float = 1000,
        y_min: float = 0,
        y_max: float = 1000,
        grid_size: float = 50.0,
    ):
        """Initialize world config.

        Args:
            x_min, x_max: World X bounds
            y_min, y_max: World Y bounds
            grid_size: Grid cell size for spatial partitioning
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.grid_size = grid_size

        self.spawn_zones: List[SpawnZone] = []
        self.obstacles: List[Obstacle] = []
        self.weather = "sunny"
        self.time_of_day = "noon"

    def add_spawn_zone(
        self,
        x: float,
        y: float,
        radius: float,
        max_agents: int,
    ) -> None:
        """Add a spawn zone."""
        zone = SpawnZone(x, y, radius, max_agents)
        self.spawn_zones.append(zone)

    def add_obstacle(self, x: float, y: float, radius: float) -> None:
        """Add an obstacle."""
        obstacle = Obstacle(x, y, radius)
        self.obstacles.append(obstacle)

    def get_total_spawn_capacity(self) -> int:
        """Get total capacity of all spawn zones."""
        return sum(zone.max_agents for zone in self.spawn_zones)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "bounds": {
                "x_min": self.x_min,
                "x_max": self.x_max,
                "y_min": self.y_min,
                "y_max": self.y_max,
            },
            "grid_size": self.grid_size,
            "spawn_zones": [z.to_dict() for z in self.spawn_zones],
            "obstacles": [o.to_dict() for o in self.obstacles],
            "weather": self.weather,
            "time_of_day": self.time_of_day,
        }


class ScenarioBuilder:
    """Builder for creating scenarios."""

    @staticmethod
    def parking_lot() -> WorldConfig:
        """Create a parking lot scenario.

        Returns:
            WorldConfig for a parking lot
        """
        world = WorldConfig(
            x_min=0,
            x_max=200,
            y_min=0,
            y_max=200,
            grid_size=50.0,
        )

        # Spawn zones (parking spaces)
        for row in range(0, 4):
            for col in range(0, 5):
                x = 20 + col * 40
                y = 20 + row * 40
                world.add_spawn_zone(x, y, 10, max_agents=2)

        # Center obstacles
        world.add_obstacle(100, 100, 20)

        world.weather = "sunny"
        return world

    @staticmethod
    def warehouse() -> WorldConfig:
        """Create a warehouse scenario.

        Returns:
            WorldConfig for a warehouse
        """
        world = WorldConfig(
            x_min=0,
            x_max=500,
            y_min=0,
            y_max=500,
            grid_size=50.0,
        )

        # Spawn zones (corners)
        world.add_spawn_zone(50, 50, 30, max_agents=50)
        world.add_spawn_zone(450, 50, 30, max_agents=50)
        world.add_spawn_zone(50, 450, 30, max_agents=50)
        world.add_spawn_zone(450, 450, 30, max_agents=50)

        # Obstacles (shelves)
        for x in [100, 200, 300, 400]:
            for y in [100, 200, 300, 400]:
                world.add_obstacle(x, y, 15)

        return world

    @staticmethod
    def urban_street() -> WorldConfig:
        """Create an urban street scenario.

        Returns:
            WorldConfig for urban street
        """
        world = WorldConfig(
            x_min=0,
            x_max=1000,
            y_min=0,
            y_max=1000,
            grid_size=100.0,
        )

        # Spawn zones (intersections)
        for x in [100, 500, 900]:
            for y in [100, 500, 900]:
                world.add_spawn_zone(x, y, 50, max_agents=20)

        # Obstacles (buildings)
        world.add_obstacle(250, 250, 100)
        world.add_obstacle(750, 250, 100)
        world.add_obstacle(250, 750, 100)
        world.add_obstacle(750, 750, 100)

        world.weather = "partly_cloudy"
        return world

    @staticmethod
    def random_world(
        num_agents: int,
        width: float = 1000,
        height: float = 1000,
        num_obstacles: int = 10,
    ) -> WorldConfig:
        """Generate a random scenario.

        Args:
            num_agents: Total agents to spawn
            width: World width
            height: World height
            num_obstacles: Number of random obstacles

        Returns:
            Randomly generated WorldConfig
        """
        world = WorldConfig(
            x_min=0,
            x_max=width,
            y_min=0,
            y_max=height,
            grid_size=width / 10,
        )

        # Create spawn zones that can fit all agents
        num_zones = max(1, num_agents // 100)
        agents_per_zone = num_agents // num_zones

        for i in range(num_zones):
            # Distribute zones across world
            x = (width / (num_zones + 1)) * (i + 1)
            y = height / 2
            world.add_spawn_zone(x, y, 50, max_agents=agents_per_zone + 10)

        # Add random obstacles
        for _ in range(num_obstacles):
            x = np.random.uniform(width * 0.1, width * 0.9)
            y = np.random.uniform(height * 0.1, height * 0.9)
            radius = np.random.uniform(20, 50)
            world.add_obstacle(x, y, radius)

        return world

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> WorldConfig:
        """Create WorldConfig from dict.

        Args:
            config_dict: Configuration dictionary

        Returns:
            WorldConfig instance
        """
        bounds = config_dict.get("bounds", {})
        world = WorldConfig(
            x_min=bounds.get("x_min", 0),
            x_max=bounds.get("x_max", 1000),
            y_min=bounds.get("y_min", 0),
            y_max=bounds.get("y_max", 1000),
            grid_size=config_dict.get("grid_size", 50.0),
        )

        # Add spawn zones
        for zone_data in config_dict.get("spawn_zones", []):
            world.add_spawn_zone(
                zone_data["x"],
                zone_data["y"],
                zone_data["radius"],
                zone_data["max_agents"],
            )

        # Add obstacles
        for obstacle_data in config_dict.get("obstacles", []):
            world.add_obstacle(
                obstacle_data["x"],
                obstacle_data["y"],
                obstacle_data["radius"],
            )

        world.weather = config_dict.get("weather", "sunny")
        world.time_of_day = config_dict.get("time_of_day", "noon")

        return world
