"""Tests for RGB camera sensor functionality."""

import base64
import io

import pytest
from PIL import Image

from services.simulation_engine import Agent, SimulationEngine, Vector3


class TestRGBSensor:
    """Test RGB camera sensor data capture."""

    def test_agent_rgb_frame_generation(self):
        """Test that agent can generate RGB JPEG frame."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        rgb_base64 = agent.generate_rgb_frame()

        assert isinstance(rgb_base64, str)
        assert len(rgb_base64) > 0
        # Valid base64 should decode
        jpeg_bytes = base64.b64decode(rgb_base64)
        assert len(jpeg_bytes) > 0

    def test_rgb_frame_is_valid_jpeg(self):
        """Test that generated RGB frame is valid JPEG."""
        agent = Agent(
            id=1,
            position=Vector3(50, 50, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        rgb_base64 = agent.generate_rgb_frame()
        jpeg_bytes = base64.b64decode(rgb_base64)

        # Should be able to open with PIL
        img = Image.open(io.BytesIO(jpeg_bytes))
        assert img.format == "JPEG"
        assert img.size == (640, 480)

    def test_rgb_color_by_state_idle(self):
        """Test RGB color is blue for idle state."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            state="idle",
        )

        color = agent._get_color_by_state()
        assert color == (0, 150, 255)  # Blue

    def test_rgb_color_by_state_moving(self):
        """Test RGB color is green for moving state."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 0, 0),
            acceleration=Vector3(0, 0, 0),
            state="moving",
        )

        color = agent._get_color_by_state()
        assert color == (0, 255, 0)  # Green

    def test_rgb_color_by_state_goal_reached(self):
        """Test RGB color is yellow for goal_reached state."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            state="goal_reached",
        )

        color = agent._get_color_by_state()
        assert color == (255, 255, 0)  # Yellow

    def test_rgb_color_by_state_collision(self):
        """Test RGB color is red for collision state."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            state="collision",
        )

        color = agent._get_color_by_state()
        assert color == (255, 0, 0)  # Red

    def test_rgb_frame_count_increments(self):
        """Test that frame count increments with each capture."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        initial_count = agent._rgb_frame_count
        agent.generate_rgb_frame()
        assert agent._rgb_frame_count == initial_count + 1
        agent.generate_rgb_frame()
        assert agent._rgb_frame_count == initial_count + 2

    def test_rgb_frames_are_different(self):
        """Test that successive RGB frames are different (due to noise)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        frame1 = agent.generate_rgb_frame()
        frame2 = agent.generate_rgb_frame()

        # Should be different due to noise
        assert frame1 != frame2


class TestSimulationEngineRGBCapture:
    """Test SimulationEngine RGB capture methods."""

    @pytest.fixture
    def engine(self):
        """Create test simulation engine."""
        return SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
        )

    def test_get_agent_rgb_frame(self, engine):
        """Test getting RGB frame for a specific agent."""
        rgb_frame = engine.get_agent_rgb_frame(0)

        assert isinstance(rgb_frame, str)
        assert len(rgb_frame) > 0
        # Should be valid base64
        jpeg_bytes = base64.b64decode(rgb_frame)
        assert len(jpeg_bytes) > 0

    def test_get_agent_rgb_frame_invalid_id(self, engine):
        """Test getting RGB frame for non-existent agent."""
        rgb_frame = engine.get_agent_rgb_frame(999)
        assert rgb_frame is None

    def test_get_all_agents_rgb_frames(self, engine):
        """Test getting RGB frames for all agents."""
        frames = engine.get_all_agents_rgb_frames()

        assert isinstance(frames, dict)
        assert len(frames) == 5
        for agent_id in range(5):
            assert agent_id in frames
            assert isinstance(frames[agent_id], str)
            # Each should be valid JPEG
            jpeg_bytes = base64.b64decode(frames[agent_id])
            img = Image.open(io.BytesIO(jpeg_bytes))
            assert img.format == "JPEG"

    def test_rgb_capture_performance(self, engine):
        """Test that RGB capture is fast (<100ms)."""
        import time

        start = time.time()
        engine.get_all_agents_rgb_frames()
        elapsed = time.time() - start

        assert elapsed < 0.1  # <100ms for 5 agents

    def test_rgb_frames_after_simulation_step(self, engine):
        """Test RGB frames are available after simulation step."""
        engine.step()

        frames = engine.get_all_agents_rgb_frames()
        assert len(frames) == 5

        # Each frame should still be valid
        for frame_b64 in frames.values():
            jpeg_bytes = base64.b64decode(frame_b64)
            img = Image.open(io.BytesIO(jpeg_bytes))
            assert img.format == "JPEG"

    def test_agent_state_updates_before_rgb_capture(self, engine):
        """Test that agent state is updated before RGB capture."""
        agent = engine.agents[0]
        agent.velocity = Vector3(5, 0, 0)

        # Step to update states
        engine.step()

        # Check that agent state is "moving"
        assert agent.state == "moving"

        # Check RGB frame reflects state (green)
        rgb_frame = engine.get_agent_rgb_frame(0)
        assert rgb_frame is not None


class TestRGBFrameIntegration:
    """Test RGB frame integration with frame streaming."""

    def test_rgb_data_in_world_frame(self):
        """Test that RGB data flows through to WorldFrame."""
        from services.frame_streaming import SensorData, WorldFrame

        # Create sensor data with RGB
        sensor_data = SensorData(
            rgb="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

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
        assert "rgb" in frame_dict["sensors"][0]
        assert frame_dict["sensors"][0]["rgb"] == sensor_data.rgb

    def test_rgb_msgpack_serialization(self):
        """Test that RGB data serializes correctly in MessagePack."""
        from services.frame_streaming import SensorData, WorldFrame

        sensor_data = SensorData(
            rgb="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

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
