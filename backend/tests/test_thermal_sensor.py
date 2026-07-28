"""Tests for thermal sensor functionality."""

import base64

import numpy as np
import pytest

from services.simulation_engine import Agent, SimulationEngine, Vector3


class TestThermalSensor:
    """Test thermal sensor data capture."""

    def test_agent_thermal_image_generation(self):
        """Test that agent can generate thermal image."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_base64 = agent.generate_thermal_image()

        assert isinstance(thermal_base64, str)
        assert len(thermal_base64) > 0
        thermal_bytes = base64.b64decode(thermal_base64)
        assert len(thermal_bytes) == 256 * 256 * 4

    def test_thermal_image_is_float32_array(self):
        """Test that thermal image contains valid float32 values."""
        agent = Agent(
            id=1,
            position=Vector3(50, 50, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_base64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_base64)
        thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32)

        assert thermal_array.shape == (256 * 256,)
        assert np.all(thermal_array >= -20)
        assert np.all(thermal_array <= 60)

    def test_thermal_temperature_range(self):
        """Test thermal values are within expected range (-20 to +60C)."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_base64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_base64)
        thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32)

        min_temp = np.min(thermal_array)
        max_temp = np.max(thermal_array)

        assert min_temp >= -20
        assert max_temp <= 60

    def test_thermal_image_varies_with_position(self):
        """Test that thermal images vary based on agent position."""
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

        thermal1 = agent1.generate_thermal_image()
        thermal2 = agent2.generate_thermal_image()

        assert thermal1 != thermal2

    def test_thermal_image_resolution(self):
        """Test thermal image is 256x256."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_base64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_base64)

        expected_size = 256 * 256 * 4
        assert len(thermal_bytes) == expected_size


class TestSimulationEngineThermalCapture:
    """Test SimulationEngine thermal capture methods."""

    @pytest.fixture
    def engine(self):
        """Create test simulation engine."""
        return SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
        )

    def test_get_agent_thermal_image(self, engine):
        """Test getting thermal image for a specific agent."""
        thermal_image = engine.get_agent_thermal_image(0)

        assert isinstance(thermal_image, str)
        assert len(thermal_image) > 0
        thermal_bytes = base64.b64decode(thermal_image)
        assert len(thermal_bytes) == 256 * 256 * 4

    def test_get_agent_thermal_image_invalid_id(self, engine):
        """Test getting thermal image for non-existent agent."""
        thermal_image = engine.get_agent_thermal_image(999)
        assert thermal_image is None

    def test_get_all_agents_thermal_images(self, engine):
        """Test getting thermal images for all agents."""
        images = engine.get_all_agents_thermal_images()

        assert isinstance(images, dict)
        assert len(images) == 3
        for agent_id in range(3):
            assert agent_id in images
            assert isinstance(images[agent_id], str)
            thermal_bytes = base64.b64decode(images[agent_id])
            thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32)
            assert thermal_array.shape == (256 * 256,)

    def test_thermal_capture_performance(self, engine):
        """Test that thermal capture is fast (<100ms for 3 agents)."""
        import time

        start = time.time()
        engine.get_all_agents_thermal_images()
        elapsed = time.time() - start

        assert elapsed < 0.1

    def test_thermal_images_after_simulation_step(self, engine):
        """Test thermal images are available after simulation step."""
        engine.step()

        images = engine.get_all_agents_thermal_images()
        assert len(images) == 3

        for image_b64 in images.values():
            thermal_bytes = base64.b64decode(image_b64)
            thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32)
            assert thermal_array.shape == (256 * 256,)
            assert np.all(thermal_array >= -20)
            assert np.all(thermal_array <= 60)


class TestThermalIntegration:
    """Test thermal sensor integration with frame streaming."""

    def test_thermal_data_in_world_frame(self):
        """Test that thermal data flows through to WorldFrame."""
        from services.frame_streaming import SensorData, WorldFrame

        thermal_bytes = np.zeros((256, 256), dtype=np.float32).tobytes()
        thermal_base64 = base64.b64encode(thermal_bytes).decode("utf-8")
        sensor_data = SensorData(thermal=thermal_base64)

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
        assert "thermal" in frame_dict["sensors"][0]
        assert frame_dict["sensors"][0]["thermal"] == thermal_base64

    def test_thermal_msgpack_serialization(self):
        """Test that thermal data serializes correctly in MessagePack."""
        from services.frame_streaming import SensorData, WorldFrame

        thermal_bytes = np.random.randn(256, 256).astype(np.float32).tobytes()
        thermal_base64 = base64.b64encode(thermal_bytes).decode("utf-8")
        sensor_data = SensorData(thermal=thermal_base64)

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            sensors={0: sensor_data},
        )

        msgpack_bytes = frame.to_msgpack()
        assert len(msgpack_bytes) > 0
        assert isinstance(msgpack_bytes, bytes)

    def test_all_sensors_together(self):
        """Test all four sensor types together."""
        from services.frame_streaming import SensorData, WorldFrame

        rgb_data = base64.b64encode(b"fake_jpeg_data").decode("utf-8")
        depth_bytes = np.zeros((512, 512), dtype=np.float32).tobytes()
        depth_data = base64.b64encode(depth_bytes).decode("utf-8")
        lidar_points = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        thermal_bytes = np.zeros((256, 256), dtype=np.float32).tobytes()
        thermal_data = base64.b64encode(thermal_bytes).decode("utf-8")

        sensor_data = SensorData(
            rgb=rgb_data, depth=depth_data, lidar=lidar_points, thermal=thermal_data
        )

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            sensors={0: sensor_data},
        )

        frame_dict = frame.to_dict()
        assert frame_dict["sensors"][0]["rgb"] == rgb_data
        assert frame_dict["sensors"][0]["depth"] == depth_data
        assert frame_dict["sensors"][0]["lidar"] == lidar_points
        assert frame_dict["sensors"][0]["thermal"] == thermal_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
