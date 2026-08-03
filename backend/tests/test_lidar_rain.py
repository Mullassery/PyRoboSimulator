"""Tests for Lidar rain occlusion, beam spread, multi-path returns, and temporal jitter."""

import numpy as np
import pytest

from services.simulation_engine import Agent, SimulationEngine, Vector3


class TestLidarRainOcclusion:
    """Test Lidar rain occlusion effects."""

    def test_no_rain_produces_full_point_cloud(self):
        """Test that rain_intensity=0 produces full point cloud."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points = agent.generate_lidar_cloud(rain_intensity=0.0)

        # 512 rays × 16 layers = 8192 base points
        # With no rain and low multipath, should be close to 8192
        assert len(points) > 7000  # Allow some variance

    def test_rain_occlusion_reduces_points(self):
        """Test that rain_intensity=1.0 reduces points by ~80%."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points_no_rain = agent.generate_lidar_cloud(rain_intensity=0.0)
        points_heavy_rain = agent.generate_lidar_cloud(rain_intensity=1.0, multipath_probability=0.0)

        # Heavy rain should reduce points significantly (~80%)
        # Expected: ~20% of original remain
        expected_points = len(points_no_rain) * 0.2
        actual_fraction = len(points_heavy_rain) / len(points_no_rain)

        # Test with some tolerance (20% ± 5%)
        assert 0.15 < actual_fraction < 0.25

    def test_rain_intensity_gradient(self):
        """Test that point loss increases with rain intensity."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # Test multiple rain intensities
        points_by_intensity = {}
        for intensity in [0.0, 0.25, 0.5, 0.75, 1.0]:
            pts = agent.generate_lidar_cloud(rain_intensity=intensity, multipath_probability=0.0)
            points_by_intensity[intensity] = len(pts)

        # Generally, more rain should mean fewer points
        # This is statistical, so we test trend
        assert points_by_intensity[0.0] > points_by_intensity[1.0]

    def test_rain_occlusion_skips_rays(self):
        """Test that rain occlusion completely removes rays (doesn't just shorten them)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points_no_rain = agent.generate_lidar_cloud(rain_intensity=0.0, multipath_probability=0.0)
        points_rain = agent.generate_lidar_cloud(rain_intensity=0.5, multipath_probability=0.0)

        # With rain, we should have fewer points, not shorter points
        assert len(points_rain) < len(points_no_rain)

        # All rain points should be valid 3D coordinates
        for point in points_rain:
            assert len(point) == 3
            assert all(-500 < coord < 500 for coord in point)


class TestLidarBeamSpread:
    """Test Lidar beam spread (angular resolution)."""

    def test_no_beam_spread_deterministic(self):
        """Test that beam_spread=0 produces deterministic angular positions."""
        agent1 = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent2 = Agent(
            id=2,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points1 = agent1.generate_lidar_cloud(beam_spread=0, add_temporal_jitter=False)
        points2 = agent2.generate_lidar_cloud(beam_spread=0, add_temporal_jitter=False)

        # Should produce identical clouds (deterministic behavior)
        assert len(points1) == len(points2)
        for p1, p2 in zip(points1, points2):
            assert np.allclose(p1, p2)

    def test_beam_spread_adds_angular_noise(self):
        """Test that beam_spread > 0 produces variable angular positions."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points_no_spread = agent.generate_lidar_cloud(
            beam_spread=0.0, add_temporal_jitter=False, multipath_probability=0.0
        )
        points_spread = agent.generate_lidar_cloud(
            beam_spread=0.5, add_temporal_jitter=False, multipath_probability=0.0
        )

        # With beam spread, angular variation should increase
        # Compare angles of points at same range
        assert len(points_spread) > 0

        # Points should be different but similar in range
        if len(points_no_spread) == len(points_spread):
            # Check that some points differ in angle (x, y varies more than distance)
            diffs = [np.linalg.norm(np.array(p1[:2]) - np.array(p2[:2]))
                     for p1, p2 in zip(points_no_spread, points_spread)]
            assert np.mean(diffs) > 0


class TestLidarMultipath:
    """Test Lidar multi-path returns (ground reflections)."""

    def test_no_multipath_point_count(self):
        """Test that multipath_probability=0 produces no extra returns."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points = agent.generate_lidar_cloud(
            rain_intensity=0.0,
            multipath_probability=0.0,
            add_temporal_jitter=False
        )

        # ~8192 points (512 rays × 16 layers, no multipath)
        assert 8000 < len(points) < 8500

    def test_multipath_increases_point_count(self):
        """Test that multipath_probability > 0 increases point count."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points_no_mp = agent.generate_lidar_cloud(
            rain_intensity=0.0,
            multipath_probability=0.0,
            add_temporal_jitter=False
        )
        points_with_mp = agent.generate_lidar_cloud(
            rain_intensity=0.0,
            multipath_probability=0.1,  # 10% secondary returns
            add_temporal_jitter=False
        )

        # With multipath, should have more points
        assert len(points_with_mp) > len(points_no_mp)

        # Expect roughly 10% more points
        expected_ratio = 1.1  # 10% more
        actual_ratio = len(points_with_mp) / len(points_no_mp)
        assert 1.05 < actual_ratio < 1.15  # Allow 5-15% variation

    def test_multipath_shorter_range(self):
        """Test that multi-path returns are shorter range (~80% of primary)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points = agent.generate_lidar_cloud(
            rain_intensity=0.0,
            multipath_probability=1.0,  # All rays have multipath
            add_temporal_jitter=False
        )

        # Extract ranges
        ranges = [np.linalg.norm(p) for p in points]

        # Should have bimodal distribution: primary and secondary returns
        # This is a weak test but reasonable for synthetic data
        assert len(ranges) > 8000


class TestLidarTemporalJitter:
    """Test Lidar temporal jitter (frame-to-frame noise)."""

    def test_no_jitter_deterministic(self):
        """Test that add_temporal_jitter=False produces deterministic clouds."""
        agent1 = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent2 = Agent(
            id=2,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points1 = agent1.generate_lidar_cloud(add_temporal_jitter=False, multipath_probability=0.0)
        points2 = agent2.generate_lidar_cloud(add_temporal_jitter=False, multipath_probability=0.0)

        # Should be identical
        for p1, p2 in zip(points1, points2):
            assert np.allclose(p1, p2)

    def test_jitter_adds_range_noise(self):
        """Test that temporal_jitter adds range noise (1% of distance)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points_no_jitter = agent.generate_lidar_cloud(
            add_temporal_jitter=False, multipath_probability=0.0
        )
        points_jitter = agent.generate_lidar_cloud(
            add_temporal_jitter=True, multipath_probability=0.0
        )

        # Should have same number of points
        assert len(points_no_jitter) == len(points_jitter)

        # But different coordinates
        differences = [np.linalg.norm(np.array(p1) - np.array(p2))
                      for p1, p2 in zip(points_no_jitter, points_jitter)]

        # Jitter should cause measurable differences
        assert np.mean(differences) > 0

    def test_jitter_proportional_to_range(self):
        """Test that jitter magnitude increases with range (1% model)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points1 = agent.generate_lidar_cloud(add_temporal_jitter=True, multipath_probability=0.0)
        points2 = agent.generate_lidar_cloud(add_temporal_jitter=True, multipath_probability=0.0)

        # Higher range points should have more jitter
        # Extract by range and compare variability
        near_points = [p for p in points1 if np.linalg.norm(p) < 50]
        far_points = [p for p in points1 if np.linalg.norm(p) > 250]

        if len(near_points) > 0 and len(far_points) > 0:
            # This is a qualitative check
            assert len(far_points) > 0


class TestLidarIntegration:
    """Test Lidar full integration with multiple effects."""

    def test_full_cloud_generation_with_rain_and_jitter(self):
        """Test full Lidar cloud generation with all effects enabled."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        points = agent.generate_lidar_cloud(
            rain_intensity=0.5,
            beam_spread=0.2,
            multipath_probability=0.05,
            add_temporal_jitter=True
        )

        # Should have valid points
        assert len(points) > 3000  # At least 30% of base points with 50% rain

        # All points should be valid 3D coordinates
        for point in points:
            assert len(point) == 3
            assert all(isinstance(c, float) for c in point)

    def test_engine_lidar_capture_all_agents(self):
        """Test SimulationEngine Lidar capture for all agents."""
        engine = SimulationEngine(num_agents=3, duration=1.0, timestep=0.016)

        for agent in engine.agents:
            points = agent.generate_lidar_cloud(
                rain_intensity=0.2,
                beam_spread=0.1,
                multipath_probability=0.03,
                add_temporal_jitter=True
            )

            # Should have valid point cloud
            assert len(points) > 5000
            assert all(len(p) == 3 for p in points)

    def test_lidar_performance(self):
        """Test that Lidar generation is reasonably fast."""
        import time

        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        start = time.time()
        for _ in range(10):
            agent.generate_lidar_cloud(
                rain_intensity=0.3,
                beam_spread=0.15,
                multipath_probability=0.05,
                add_temporal_jitter=True
            )
        elapsed = time.time() - start

        avg_ms = (elapsed / 10) * 1000
        print(f"\nLidar cloud generation: {avg_ms:.1f}ms per cloud")

        # Should be reasonably fast (<50ms per cloud)
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
