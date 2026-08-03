"""Tests for sensor fusion pipeline (timestamp sync, coordinate transforms, latency)."""

import base64
import time

import numpy as np
import pytest

from services.simulation_engine import Agent, Vector3
from services.sensor_fusion import (
    SensorFusionPipeline,
    RGBReading,
    DepthReading,
    LidarReading,
    ThermalReading,
)


class TestTimestampSynchronization:
    """Test timestamp synchronization across sensors."""

    def test_synchronized_sensors_fuse(self):
        """Test that synchronized sensors produce fused frame."""
        fusion = SensorFusionPipeline(agent_id=1, max_sync_deviation_ms=10.0)

        # Generate synchronized sensor data (same timestamp)
        base_time = 1000.0
        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)
        lidar_points = [[float(i), float(i), float(i)] for i in range(100)]
        thermal_data = np.random.uniform(-20, 60, (256, 256), dtype=np.float32)

        # Push synchronized readings
        fusion.push_rgb_reading(rgb_data, base_time)
        fusion.push_depth_reading(depth_data, base_time)
        fusion.push_lidar_reading(lidar_points, base_time)
        fusion.push_thermal_reading(thermal_data, base_time)

        # Fuse
        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert fused.rgb is not None
        assert fused.depth is not None
        assert fused.lidar is not None
        assert fused.thermal is not None
        assert fused.num_sensors_fused == 4

    def test_out_of_sync_sensors_rejected(self):
        """Test that out-of-sync sensors are rejected."""
        fusion = SensorFusionPipeline(agent_id=1, max_sync_deviation_ms=5.0)

        # Generate out-of-sync sensor data (>5ms deviation)
        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1010.0)  # 10ms deviation > 5ms threshold

        # Fuse should fail
        fused = fusion.fuse((100, 100, 0))
        assert fused is None

    def test_timestamp_deviation_measured(self):
        """Test that timestamp deviation is measured correctly."""
        fusion = SensorFusionPipeline(agent_id=1, max_sync_deviation_ms=10.0)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1005.0)  # 5ms deviation

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert abs(fused.timestamp_deviation_ms - 5.0) < 0.01

    def test_timestamp_averaging(self):
        """Test that fused frame timestamp is average of sensor timestamps."""
        fusion = SensorFusionPipeline(agent_id=1, max_sync_deviation_ms=10.0)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1004.0)

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        expected_timestamp = (1000.0 + 1004.0) / 2
        assert abs(fused.timestamp_ms - expected_timestamp) < 0.01


class TestCoordinateTransforms:
    """Test coordinate transformation from agent frame to world frame."""

    def test_transformation_matrix_created(self):
        """Test that coordinate transformation matrices are created."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1000.0)

        fused = fusion.fuse((100, 200, 50))

        assert fused is not None
        assert fused.rgb_to_world is not None
        assert fused.depth_to_world is not None
        assert fused.rgb_to_world.shape == (4, 4)

    def test_translation_in_transform(self):
        """Test that agent position is in transformation matrix."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        fusion.push_rgb_reading(rgb_data, 1000.0)

        agent_pos = (123.45, 234.56, 345.67)
        fused = fusion.fuse(agent_pos)

        assert fused is not None
        # Check translation components of transform
        assert np.allclose(fused.rgb_to_world[0:3, 3], agent_pos)

    def test_same_transform_all_sensors(self):
        """Test that all sensors get same transformation (same mounting)."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)
        lidar_points = [[1, 2, 3]]
        thermal_data = np.ones((256, 256), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1000.0)
        fusion.push_lidar_reading(lidar_points, 1000.0)
        fusion.push_thermal_reading(thermal_data, 1000.0)

        fused = fusion.fuse((100, 200, 300))

        # All transforms should be identical
        assert np.allclose(fused.rgb_to_world, fused.depth_to_world)
        assert np.allclose(fused.depth_to_world, fused.lidar_to_world)
        assert np.allclose(fused.lidar_to_world, fused.thermal_to_world)


class TestSensorFusionLatency:
    """Test sensor fusion pipeline latency."""

    def test_fusion_latency_measured(self):
        """Test that fusion latency is measured."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1000.0)

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert fused.fusion_latency_ms > 0

    def test_fusion_latency_under_50ms(self):
        """Test that fusion latency is under 50ms target."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)
        lidar_points = [[float(i), float(i), float(i)] for i in range(1000)]
        thermal_data = np.random.uniform(-20, 60, (256, 256), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1000.0)
        fusion.push_lidar_reading(lidar_points, 1000.0)
        fusion.push_thermal_reading(thermal_data, 1000.0)

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert fused.fusion_latency_ms < 50  # <50ms target

    def test_batch_fusion_performance(self):
        """Test fusion performance with multiple frames."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)
        lidar_points = [[float(i), float(i), float(i)] for i in range(500)]
        thermal_data = np.random.uniform(-20, 60, (256, 256), dtype=np.float32)

        total_latency = 0
        for i in range(10):
            timestamp = 1000.0 + i * 33.33  # ~30 FPS

            fusion.push_rgb_reading(rgb_data, timestamp)
            fusion.push_depth_reading(depth_data, timestamp)
            fusion.push_lidar_reading(lidar_points, timestamp)
            fusion.push_thermal_reading(thermal_data, timestamp)

            fused = fusion.fuse((100, 100, 0))
            if fused:
                total_latency += fused.fusion_latency_ms

        avg_latency = total_latency / 10
        print(f"\nAverage fusion latency: {avg_latency:.2f}ms")

        # Average should be <50ms
        assert avg_latency < 50


class TestMultiSensorFusion:
    """Test fusion with partial sensor data."""

    def test_single_sensor_fusion(self):
        """Test fusion with only one sensor."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        fusion.push_rgb_reading(rgb_data, 1000.0)

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert fused.num_sensors_fused == 1
        assert fused.rgb is not None
        assert fused.depth is None

    def test_partial_sensor_fusion(self):
        """Test fusion with some sensors missing."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth_data = np.random.uniform(0.1, 300, (512, 512), dtype=np.float32)

        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.push_depth_reading(depth_data, 1000.0)
        # Lidar and thermal not pushed

        fused = fusion.fuse((100, 100, 0))

        assert fused is not None
        assert fused.num_sensors_fused == 2
        assert fused.rgb is not None
        assert fused.depth is not None
        assert fused.lidar is None
        assert fused.thermal is None

    def test_no_sensors_returns_none(self):
        """Test that fusion returns None with no sensor data."""
        fusion = SensorFusionPipeline(agent_id=1)

        # Don't push any sensor data
        fused = fusion.fuse((100, 100, 0))

        assert fused is None


class TestFusionStatistics:
    """Test fusion pipeline statistics."""

    def test_fusion_stats_collected(self):
        """Test that fusion statistics are collected."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        for i in range(5):
            fusion.push_rgb_reading(rgb_data, 1000.0 + i * 10)
            fusion.fuse((100, 100, 0))

        stats = fusion.get_fusion_stats()

        assert stats["frames_fused"] == 5
        assert stats["avg_latency_ms"] > 0
        assert stats["max_latency_ms"] > 0
        assert stats["min_latency_ms"] > 0

    def test_stats_empty_initially(self):
        """Test that stats are empty before fusion."""
        fusion = SensorFusionPipeline(agent_id=1)

        stats = fusion.get_fusion_stats()

        assert stats["frames_fused"] == 0
        assert stats["avg_latency_ms"] == 0

    def test_reset_clears_stats(self):
        """Test that reset clears statistics."""
        fusion = SensorFusionPipeline(agent_id=1)

        rgb_data = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        fusion.push_rgb_reading(rgb_data, 1000.0)
        fusion.fuse((100, 100, 0))

        # Verify stats collected
        assert fusion.frame_count == 1

        # Reset
        fusion.reset()

        # Verify stats cleared
        assert fusion.frame_count == 0
        stats = fusion.get_fusion_stats()
        assert stats["frames_fused"] == 0


class TestIntegrationWithAgents:
    """Test sensor fusion integration with agent sensors."""

    def test_agent_sensor_fusion(self):
        """Test fusing data from agent sensors."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        fusion = SensorFusionPipeline(agent_id=agent.id, max_sync_deviation_ms=10.0)

        # Generate sensor data from agent
        base_time = 1000.0
        rgb_b64 = agent.generate_rgb_frame(iso=100)
        depth_b64 = agent.generate_depth_map()
        lidar_points = agent.generate_lidar_cloud()
        thermal_b64 = agent.generate_thermal_image()

        # Decode and push to fusion
        rgb_bytes = base64.b64decode(rgb_b64)
        from PIL import Image
        import io

        rgb_img = Image.open(io.BytesIO(rgb_bytes))
        rgb_data = np.array(rgb_img)

        depth_bytes = base64.b64decode(depth_b64)
        depth_data = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_data = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        fusion.push_rgb_reading(rgb_data, base_time)
        fusion.push_depth_reading(depth_data, base_time)
        fusion.push_lidar_reading(lidar_points, base_time)
        fusion.push_thermal_reading(thermal_data, base_time)

        # Fuse
        fused = fusion.fuse((agent.position.x, agent.position.y, agent.position.z))

        assert fused is not None
        assert fused.num_sensors_fused == 4
        assert fused.fusion_latency_ms < 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
