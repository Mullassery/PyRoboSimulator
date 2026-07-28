"""Tests for depth sensor functionality."""

import base64

import numpy as np
import pytest

from services.simulation_engine import Agent, SimulationEngine, Vector3


class TestDepthSensor:
    """Test depth sensor data capture."""

    def test_agent_depth_map_generation(self):
        """Test that agent can generate depth map."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_base64 = agent.generate_depth_map()

        assert isinstance(depth_base64, str)
        assert len(depth_base64) > 0
        # Valid base64 should decode
        depth_bytes = base64.b64decode(depth_base64)
        assert len(depth_bytes) == 512 * 512 * 4  # 512x512 float32

    def test_depth_map_is_float32_array(self):
        """Test that depth map contains valid float32 values."""
        agent = Agent(
            id=1,
            position=Vector3(50, 50, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_base64 = agent.generate_depth_map()
        depth_bytes = base64.b64decode(depth_base64)
        depth_array = np.frombuffer(depth_bytes, dtype=np.float32)

        assert depth_array.shape == (512 * 512,)
        # All values should be in valid range (0-300m)
        assert np.all(depth_array >= 0)
        assert np.all(depth_array <= 300)

    def test_depth_map_range(self):
        """Test depth values are within expected range."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_base64 = agent.generate_depth_map()
        depth_bytes = base64.b64decode(depth_base64)
        depth_array = np.frombuffer(depth_bytes, dtype=np.float32)

        min_depth = np.min(depth_array)
        max_depth = np.max(depth_array)

        assert min_depth >= 0
        assert max_depth <= 300

    def test_depth_map_varies_with_position(self):
        """Test that depth maps vary based on agent position."""
        agent1 = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent2 = Agent(
            id=2,
            position=Vector3(500, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth1 = agent1.generate_depth_map()
        depth2 = agent2.generate_depth_map()

        # Maps should be different due to position-based parallax
        assert depth1 != depth2


class TestSimulationEngineDepthCapture:
    """Test SimulationEngine depth capture methods."""

    @pytest.fixture
    def engine(self):
        """Create test simulation engine."""
        return SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
        )

    def test_get_agent_depth_map(self, engine):
        """Test getting depth map for a specific agent."""
        depth_map = engine.get_agent_depth_map(0)

        assert isinstance(depth_map, str)
        assert len(depth_map) > 0
        # Should be valid base64
        depth_bytes = base64.b64decode(depth_map)
        assert len(depth_bytes) == 512 * 512 * 4

    def test_get_agent_depth_map_invalid_id(self, engine):
        """Test getting depth map for non-existent agent."""
        depth_map = engine.get_agent_depth_map(999)
        assert depth_map is None

    def test_get_all_agents_depth_maps(self, engine):
        """Test getting depth maps for all agents."""
        maps = engine.get_all_agents_depth_maps()

        assert isinstance(maps, dict)
        assert len(maps) == 3
        for agent_id in range(3):
            assert agent_id in maps
            assert isinstance(maps[agent_id], str)
            # Each should be valid float32 array
            depth_bytes = base64.b64decode(maps[agent_id])
            depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
            assert depth_array.shape == (512 * 512,)

    def test_depth_capture_performance(self, engine):
        """Test that depth capture is fast (<100ms)."""
        import time

        start = time.time()
        engine.get_all_agents_depth_maps()
        elapsed = time.time() - start

        assert elapsed < 0.1  # <100ms for 3 agents

    def test_depth_maps_after_simulation_step(self, engine):
        """Test depth maps are available after simulation step."""
        engine.step()

        maps = engine.get_all_agents_depth_maps()
        assert len(maps) == 3

        # Each map should still be valid
        for map_b64 in maps.values():
            depth_bytes = base64.b64decode(map_b64)
            depth_array = np.frombuffer(depth_bytes, dtype=np.float32)
            assert depth_array.shape == (512 * 512,)
            assert np.all(depth_array >= 0)
            assert np.all(depth_array <= 300)


class TestDepthIntegration:
    """Test depth sensor integration with frame streaming."""

    def test_depth_data_in_world_frame(self):
        """Test that depth data flows through to WorldFrame."""
        from services.frame_streaming import SensorData, WorldFrame

        # Create sensor data with depth
        depth_bytes = np.zeros((512, 512), dtype=np.float32).tobytes()
        depth_base64 = base64.b64encode(depth_bytes).decode("utf-8")
        sensor_data = SensorData(depth=depth_base64)

        # Create world frame with sensors
        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            sensors={0: sensor_data},
        )

        frame_dict = frame.to_dict()
        assert "sensors" in frame_dict
        assert 0 in frame_dict["sensors"]
        assert "depth" in frame_dict["sensors"][0]
        assert frame_dict["sensors"][0]["depth"] == depth_base64

    def test_depth_msgpack_serialization(self):
        """Test that depth data serializes correctly in MessagePack."""
        from services.frame_streaming import SensorData, WorldFrame

        depth_bytes = np.random.randn(512, 512).astype(np.float32).tobytes()
        depth_base64 = base64.b64encode(depth_bytes).decode("utf-8")
        sensor_data = SensorData(depth=depth_base64)

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            sensors={0: sensor_data},
        )

        # Should serialize without error
        msgpack_bytes = frame.to_msgpack()
        assert len(msgpack_bytes) > 0
        assert isinstance(msgpack_bytes, bytes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
