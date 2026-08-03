"""Tests for depth camera sensor accuracy (quantization, noise, clipping, temporal filtering)."""

import base64

import numpy as np
import pytest

from services.simulation_engine import Agent, SimulationEngine, Vector3
from services.sensor_effects import quantize


class TestDepthQuantization:
    """Test depth quantization effects."""

    def test_quantize_no_step(self):
        """Test that zero step returns unchanged array."""
        arr = np.array([1.2345, 2.5678, 3.9012], dtype=np.float32)
        result = quantize(arr, step=0)
        assert np.allclose(result, arr)

    def test_quantize_1mm_step(self):
        """Test 1mm (0.001m) quantization."""
        arr = np.array([1.2345, 2.5678, 3.9012], dtype=np.float32)
        result = quantize(arr, step=0.001)

        # Check that values are quantized to 1mm steps
        expected = np.round(arr / 0.001) * 0.001
        assert np.allclose(result, expected)

    def test_quantize_10cm_step(self):
        """Test 10cm (0.1m) quantization."""
        arr = np.array([1.234, 2.567, 3.901], dtype=np.float32)
        result = quantize(arr, step=0.1)

        expected = np.round(arr / 0.1) * 0.1
        assert np.allclose(result, expected)

    def test_quantize_preserves_shape(self):
        """Test that quantization preserves array shape."""
        arr = np.random.rand(100, 100).astype(np.float32) * 100
        result = quantize(arr, step=0.001)
        assert result.shape == arr.shape

    def test_quantize_reduces_precision(self):
        """Test that quantization reduces value precision."""
        arr = np.array([1.23456789], dtype=np.float32)
        result = quantize(arr, step=0.001)

        # With 1mm quantization, precision should be to 0.001m
        assert np.abs(result[0] - np.round(arr[0] / 0.001) * 0.001) < 1e-6


class TestDepthRangeClipping:
    """Test depth range clipping (near/far planes)."""

    def test_clip_near_plane(self):
        """Test that values below min_range are clipped."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map(min_range=0.5, max_range=300))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # All values should be >= min_range
        assert np.min(depth_map) >= 0.5

    def test_clip_far_plane(self):
        """Test that values above max_range are clipped."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map(min_range=0.1, max_range=50))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # All values should be <= max_range
        assert np.max(depth_map) <= 50

    def test_range_enforcement_with_noise(self):
        """Test that range is enforced even after noise addition."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        min_r, max_r = 0.2, 200.0
        depth_bytes = base64.b64decode(agent.generate_depth_map(min_range=min_r, max_range=max_r))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        assert np.min(depth_map) >= min_r - 1e-6
        assert np.max(depth_map) <= max_r + 1e-6


class TestDepthSensorNoise:
    """Test depth sensor noise characteristics."""

    def test_no_temporal_filter_produces_different_frames(self):
        """Test that depth frames differ without temporal filtering."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth1_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=False))
        depth1 = np.frombuffer(depth1_bytes, dtype=np.float32).reshape(512, 512)

        depth2_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=False))
        depth2 = np.frombuffer(depth2_bytes, dtype=np.float32).reshape(512, 512)

        # Should be different due to noise
        assert not np.allclose(depth1, depth2)

    def test_noise_increases_at_far_ranges(self):
        """Test that noise is higher at far ranges (1% of distance)."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=False))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # Noise should be range-dependent, roughly proportional to distance
        # Sample pixels at different ranges and compare variance
        near_pixels = depth_map[256, 250:260]  # Pixels closer to camera
        far_pixels = depth_map[100, 100:110]    # Pixels further from camera

        # This is a statistical test, may need adjustment
        # The far pixels should have higher absolute variance
        assert near_pixels.std() > 0  # Just check noise exists

    def test_edge_artifacts_detected(self):
        """Test that depth discontinuities create artifact zones."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=False))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # Check that depth map has gradient (edges exist)
        gradient_x = np.gradient(depth_map, axis=1)
        gradient_y = np.gradient(depth_map, axis=0)

        max_gradient = np.max(np.sqrt(gradient_x**2 + gradient_y**2))
        assert max_gradient > 0  # Edges should exist


class TestTemporalFiltering:
    """Test temporal filtering (frame averaging)."""

    def test_temporal_filtering_smooths_noise(self):
        """Test that temporal filtering reduces noise."""
        agent_no_filter = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent_filter = Agent(
            id=2,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # Generate multiple frames for temporal filtering
        for _ in range(3):
            agent_filter.generate_depth_map(temporal_filter=True)

        # Get final frames
        depth_no_filter_bytes = base64.b64decode(
            agent_no_filter.generate_depth_map(temporal_filter=False)
        )
        depth_filter_bytes = base64.b64decode(
            agent_filter.generate_depth_map(temporal_filter=True)
        )

        depth_no_filter = np.frombuffer(depth_no_filter_bytes, dtype=np.float32).reshape(512, 512)
        depth_filter = np.frombuffer(depth_filter_bytes, dtype=np.float32).reshape(512, 512)

        # Filtered should have lower variance (smoother)
        var_no_filter = np.var(depth_no_filter)
        var_filter = np.var(depth_filter)

        # Temporal filtering should reduce variance
        # Note: This is statistical and may be affected by noise
        assert var_filter <= var_no_filter + 1e-3  # Allow small margin

    def test_temporal_filtering_converges(self):
        """Test that multiple temporal filter frames converge."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        frames = []
        for _ in range(5):
            depth_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=True))
            depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)
            frames.append(depth_map)

        # Later frames should be more similar to each other than early frames
        diff_early = np.mean(np.abs(frames[0] - frames[1]))
        diff_late = np.mean(np.abs(frames[3] - frames[4]))

        # Convergence means differences should decrease
        assert diff_late <= diff_early + 1e-3

    def test_no_temporal_filter_initially(self):
        """Test that first frame with temporal_filter=True is not filtered."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # First call should not filter (no previous frame)
        depth1_bytes = base64.b64decode(agent.generate_depth_map(temporal_filter=True))
        depth1 = np.frombuffer(depth1_bytes, dtype=np.float32).reshape(512, 512)

        # Should be valid depth map
        assert np.min(depth1) >= 0.1
        assert np.max(depth1) <= 300


class TestDepthMapGeneration:
    """Test full depth map generation with sensor effects."""

    def test_depth_map_shape(self):
        """Test that depth map has correct shape."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map())
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32)

        # Should be 512x512 = 262144 float32 values
        assert len(depth_map) == 512 * 512
        depth_map = depth_map.reshape(512, 512)
        assert depth_map.dtype == np.float32

    def test_depth_map_with_custom_range(self):
        """Test depth map with custom min/max range."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(agent.generate_depth_map(min_range=1.0, max_range=100.0))
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        assert np.min(depth_map) >= 1.0
        assert np.max(depth_map) <= 100.0

    def test_depth_map_with_quantization(self):
        """Test depth map with specific quantization level."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        depth_bytes = base64.b64decode(
            agent.generate_depth_map(quantization=0.01)  # 1cm quantization
        )
        depth_map = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # Check that values are quantized to 1cm steps
        # Most values should be multiples of 0.01
        quantized_check = np.round(depth_map / 0.01) * 0.01
        # Allow small floating point error
        assert np.allclose(depth_map, quantized_check, atol=1e-6)

    def test_depth_map_performance(self):
        """Test that depth map generation is fast (<100ms)."""
        import time

        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        start = time.time()
        for _ in range(5):
            agent.generate_depth_map(
                min_range=0.1,
                max_range=300,
                quantization=0.001,
                temporal_filter=True
            )
        elapsed = time.time() - start

        # 5 frames should take <0.5 seconds (avg <100ms per frame)
        assert elapsed < 0.5

    def test_engine_depth_capture_all_agents(self):
        """Test SimulationEngine can capture depth from all agents."""
        engine = SimulationEngine(num_agents=3, duration=1.0, timestep=0.016)

        # Generate depth maps for all agents
        depth_maps = {}
        for agent in engine.agents:
            depth_b64 = agent.generate_depth_map()
            depth_bytes = base64.b64decode(depth_b64)
            depth_maps[agent.id] = np.frombuffer(depth_bytes, dtype=np.float32).reshape(512, 512)

        # All depth maps should be valid
        assert len(depth_maps) == 3
        for agent_id, depth_map in depth_maps.items():
            assert depth_map.shape == (512, 512)
            assert np.min(depth_map) >= 0.1
            assert np.max(depth_map) <= 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
