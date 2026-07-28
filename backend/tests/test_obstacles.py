"""Tests for obstacle visualization functionality."""

import pytest

from services.simulation_engine import SimulationEngine, Vector3
from services.frame_streaming import Obstacle, WorldFrame


class TestObstacleGeneration:
    """Test obstacle generation in SimulationEngine."""

    def test_obstacles_spawned(self):
        """Test that obstacles are created during initialization."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=10,
        )

        assert len(engine.obstacles) == 10

    def test_obstacle_properties(self):
        """Test that obstacles have correct properties."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        for obs in engine.obstacles:
            assert "id" in obs
            assert "position" in obs
            assert "size" in obs
            assert "type" in obs
            assert obs["type"] == "wall"

            pos = obs["position"]
            assert "x" in pos and "y" in pos and "z" in pos

            size = obs["size"]
            assert "x" in size and "y" in size and "z" in size
            assert size["z"] == 5  # Fixed height

    def test_obstacle_positions_in_bounds(self):
        """Test that obstacles spawn within world bounds."""
        world_bounds = (0, 1000, 0, 1000)
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            world_bounds=world_bounds,
            num_obstacles=10,
        )

        for obs in engine.obstacles:
            x = obs["position"]["x"]
            y = obs["position"]["y"]

            assert x > 50 and x < 950  # 50-unit margin
            assert y > 50 and y < 950

    def test_obstacle_sizes_reasonable(self):
        """Test that obstacle sizes are within expected ranges."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=10,
        )

        for obs in engine.obstacles:
            width = obs["size"]["x"]
            height = obs["size"]["y"]

            assert width >= 20 and width <= 80
            assert height >= 20 and height <= 80

    def test_get_obstacles_method(self):
        """Test getting obstacles from engine."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=7,
        )

        obstacles = engine.get_obstacles()
        assert len(obstacles) == 7
        assert all("id" in obs for obs in obstacles)

    def test_obstacle_ids_unique(self):
        """Test that each obstacle has a unique ID."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=15,
        )

        ids = [obs["id"] for obs in engine.obstacles]
        assert len(ids) == len(set(ids))

    def test_no_obstacles(self):
        """Test engine with zero obstacles."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        assert len(engine.obstacles) == 0
        assert engine.get_obstacles() == []


class TestObstacleFrameStreaming:
    """Test obstacles in frame streaming."""

    def test_obstacles_in_world_frame(self):
        """Test that obstacles appear in WorldFrame."""
        obstacles = [
            Obstacle(
                id=0,
                position=Vector3(100, 100, 0),
                size=Vector3(50, 50, 5),
                obstacle_type="wall",
            ),
            Obstacle(
                id=1,
                position=Vector3(200, 200, 0),
                size=Vector3(40, 60, 5),
                obstacle_type="wall",
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=obstacles,
        )

        assert len(frame.obstacles) == 2
        assert frame.obstacles[0].id == 0
        assert frame.obstacles[1].id == 1

    def test_obstacle_serialization(self):
        """Test obstacle serialization in frame dict."""
        obstacle = Obstacle(
            id=0,
            position=Vector3(100, 200, 0),
            size=Vector3(50, 60, 5),
            obstacle_type="wall",
        )

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=[obstacle],
        )

        frame_dict = frame.to_dict()
        assert "obstacles" in frame_dict
        assert len(frame_dict["obstacles"]) == 1

        obs_dict = frame_dict["obstacles"][0]
        assert obs_dict["id"] == 0
        assert obs_dict["pos"] == [100, 200, 0]
        assert obs_dict["size"] == [50, 60, 5]
        assert obs_dict["type"] == "wall"

    def test_obstacle_msgpack_serialization(self):
        """Test obstacles serialize correctly in MessagePack."""
        obstacles = [
            Obstacle(
                id=i,
                position=Vector3(100 + i * 50, 100 + i * 50, 0),
                size=Vector3(40, 40, 5),
                obstacle_type="wall",
            )
            for i in range(3)
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=obstacles,
        )

        msgpack_bytes = frame.to_msgpack()
        assert len(msgpack_bytes) > 0
        assert isinstance(msgpack_bytes, bytes)

    def test_empty_obstacles_list(self):
        """Test frame with empty obstacles list."""
        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=[],
        )

        frame_dict = frame.to_dict()
        assert frame_dict["obstacles"] == []

    def test_none_obstacles(self):
        """Test frame with None obstacles."""
        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=None,
        )

        frame_dict = frame.to_dict()
        assert frame_dict["obstacles"] == []


class TestObstacleIntegration:
    """Test obstacles integration with simulation."""

    def test_obstacles_persist_across_steps(self):
        """Test that obstacles remain constant across simulation steps."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        initial_obstacles = engine.get_obstacles()
        assert len(initial_obstacles) == 5

        # Run simulation steps
        engine.step()
        engine.step()
        engine.step()

        # Obstacles should be unchanged
        final_obstacles = engine.get_obstacles()
        assert len(final_obstacles) == 5

        for initial, final in zip(initial_obstacles, final_obstacles):
            assert initial["id"] == final["id"]
            assert initial["position"] == final["position"]
            assert initial["size"] == final["size"]

    def test_visualization_streamer_includes_obstacles(self):
        """Test that VisualizationStreamer includes obstacles in frames."""
        from services.visualization_integration import VisualizationStreamer

        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=3,
        )

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        assert frame.obstacles is not None
        assert len(frame.obstacles) == 3

        for obstacle in frame.obstacles:
            assert obstacle.id is not None
            assert obstacle.position is not None
            assert obstacle.size is not None
            assert obstacle.obstacle_type == "wall"

    def test_large_number_of_obstacles(self):
        """Test performance with many obstacles."""
        import time

        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=100,
        )

        start = time.time()
        obstacles = engine.get_obstacles()
        elapsed = time.time() - start

        assert len(obstacles) == 100
        assert elapsed < 0.01  # Should be fast


class TestObstacleTypes:
    """Test different obstacle types."""

    def test_obstacle_type_wall(self):
        """Test wall obstacle type."""
        obstacle = Obstacle(
            id=0,
            position=Vector3(100, 100, 0),
            size=Vector3(50, 50, 5),
            obstacle_type="wall",
        )

        assert obstacle.obstacle_type == "wall"

    def test_obstacle_to_dict(self):
        """Test Obstacle.to_dict() serialization."""
        obstacle = Obstacle(
            id=5,
            position=Vector3(150, 250, 0),
            size=Vector3(60, 70, 5),
            obstacle_type="wall",
        )

        obs_dict = obstacle.to_dict()
        assert obs_dict["id"] == 5
        assert obs_dict["pos"] == [150, 250, 0]
        assert obs_dict["size"] == [60, 70, 5]
        assert obs_dict["type"] == "wall"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
