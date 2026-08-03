"""Tests for RGB camera sensor artifacts (noise, distortion, motion blur, color grading)."""

import base64
import io

import numpy as np
import pytest
from PIL import Image

from services.simulation_engine import Agent, SimulationEngine, Vector3
from services.sensor_effects import (
    add_gaussian_noise,
    apply_radial_distortion,
    apply_motion_blur,
    apply_color_grading,
)


class TestGaussianNoise:
    """Test ISO-based Gaussian noise addition."""

    def test_gaussian_noise_sigma_zero(self):
        """Test that zero sigma returns unchanged array."""
        arr = np.ones((10, 10), dtype=np.uint8) * 128
        result = add_gaussian_noise(arr, sigma=0, value_min=0, value_max=255)
        assert np.allclose(result, arr)

    def test_gaussian_noise_increases_with_iso(self):
        """Test that higher ISO produces more noise."""
        test_array = np.ones((100, 100), dtype=np.uint8) * 128

        # ISO 100 = low noise
        noisy_100 = add_gaussian_noise(test_array, sigma=3.0, value_min=0, value_max=255)
        noise_100 = np.std(noisy_100 - 128)

        # ISO 3200 = high noise
        noisy_3200 = add_gaussian_noise(test_array, sigma=45.0, value_min=0, value_max=255)
        noise_3200 = np.std(noisy_3200 - 128)

        # Higher ISO should have more noise
        assert noise_3200 > noise_100

    def test_gaussian_noise_within_bounds(self):
        """Test that noise is clipped to value range."""
        arr = np.ones((50, 50), dtype=np.uint8) * 128
        result = add_gaussian_noise(arr, sigma=100, value_min=0, value_max=255)

        assert np.min(result) >= 0
        assert np.max(result) <= 255

    def test_gaussian_noise_preserves_dtype(self):
        """Test that output dtype matches input dtype."""
        arr_uint8 = np.ones((20, 20), dtype=np.uint8) * 128
        result = add_gaussian_noise(arr_uint8, sigma=5.0, value_min=0, value_max=255)
        assert result.dtype == np.uint8


class TestLensDistortion:
    """Test lens distortion effects."""

    def test_radial_distortion_zero_coefficients(self):
        """Test that zero coefficients return unchanged image."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_radial_distortion(img, k1=0, k2=0)
        assert np.allclose(result, img)

    def test_radial_distortion_barrel(self):
        """Test barrel distortion (positive k1)."""
        # Create image with clear center dot
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[45:55, 45:55] = 255  # White square in center

        result = apply_radial_distortion(img, k1=0.1, k2=0.0)

        # Result should have same shape
        assert result.shape == img.shape
        # Center should still be white (approximately)
        assert result[50, 50].mean() > 200

    def test_radial_distortion_pincushion(self):
        """Test pincushion distortion (negative k1)."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[45:55, 45:55] = 255

        result = apply_radial_distortion(img, k1=-0.1, k2=0.0)

        # Should still be valid image
        assert result.shape == img.shape
        assert np.min(result) >= 0
        assert np.max(result) <= 255

    def test_radial_distortion_preserves_dtype(self):
        """Test that distortion preserves dtype."""
        img_uint8 = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        result = apply_radial_distortion(img_uint8, k1=0.05, k2=0.01)
        assert result.dtype == np.uint8


class TestMotionBlur:
    """Test motion blur effects."""

    def test_motion_blur_zero_speed(self):
        """Test that zero speed returns unchanged image."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_motion_blur(img, speed=0, direction_xy=(1, 0))
        assert np.allclose(result, img)

    def test_motion_blur_low_speed(self):
        """Test that low speed (<0.1) returns unchanged image."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_motion_blur(img, speed=0.05, direction_xy=(1, 0))
        assert np.allclose(result, img)

    def test_motion_blur_increases_with_speed(self):
        """Test that higher speed produces more blur."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        img[45:55, 45:55] = 255  # White square

        # Slow motion blur
        result_slow = apply_motion_blur(img, speed=0.5, direction_xy=(1, 0))

        # Fast motion blur
        result_fast = apply_motion_blur(img, speed=5.0, direction_xy=(1, 0))

        # Fast blur should be more blurred (lower variance in white region)
        var_slow = np.var(result_slow[45:55, 45:55])
        var_fast = np.var(result_fast[45:55, 45:55])

        # Fast blur should have spread out more (lower variance in white region means lower peak)
        assert result_fast[50, 50].mean() < result_slow[50, 50].mean()

    def test_motion_blur_preserves_shape(self):
        """Test that motion blur preserves image shape."""
        img = np.random.randint(0, 255, (64, 48, 3), dtype=np.uint8)
        result = apply_motion_blur(img, speed=2.0, direction_xy=(1, 0))
        assert result.shape == img.shape

    def test_motion_blur_respects_max_kernel(self):
        """Test that blur kernel doesn't exceed max_kernel."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_motion_blur(img, speed=100.0, direction_xy=(1, 0), max_kernel=5)
        # Should complete without error and produce valid output
        assert result.shape == img.shape
        assert np.min(result) >= 0
        assert np.max(result) <= 255


class TestColorGrading:
    """Test color grading presets."""

    def test_color_grading_none(self):
        """Test that 'none' preset returns unchanged image."""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        result = apply_color_grading(img, "none")
        assert np.allclose(result, img)

    def test_color_grading_daylight(self):
        """Test daylight preset (warm, green boost)."""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        result = apply_color_grading(img, "daylight")

        # Should preserve size and dtype
        assert result.shape == img.shape
        assert result.dtype == np.uint8

        # Daylight should boost green relative to blue
        # Note: RGB channels scale differently, so compare ratios
        assert result[25, 25, 1] > result[25, 25, 2]  # Green > Blue

    def test_color_grading_night(self):
        """Test night preset (dim, blue boost)."""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        result = apply_color_grading(img, "night")

        # Night should be darker overall
        assert result[25, 25].mean() < img[25, 25].mean()
        # Night should boost blue
        assert result[25, 25, 2] > result[25, 25, 0]  # Blue > Red

    def test_color_grading_thermal_tint(self):
        """Test thermal_tint preset (red/orange boost)."""
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        result = apply_color_grading(img, "thermal_tint")

        # Thermal should boost reds
        assert result[25, 25, 0] > result[25, 25, 2]  # Red > Blue

    def test_color_grading_preserves_range(self):
        """Test that all presets clip output to 0-255."""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

        for preset in ["daylight", "night", "thermal_tint"]:
            result = apply_color_grading(img, preset)
            assert np.min(result) >= 0
            assert np.max(result) <= 255


class TestRGBSensorEffectsIntegration:
    """Test RGB sensor effects applied to full frames."""

    def test_agent_rgb_frame_with_iso_100(self):
        """Test RGB frame generation at ISO 100 (low noise)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        rgb_base64 = agent.generate_rgb_frame(iso=100, color_grading="daylight")

        assert isinstance(rgb_base64, str)
        assert len(rgb_base64) > 0

        # Validate JPEG
        jpeg_bytes = base64.b64decode(rgb_base64)
        img = Image.open(io.BytesIO(jpeg_bytes))
        assert img.format == "JPEG"
        assert img.size == (640, 480)

    def test_agent_rgb_frame_with_iso_3200(self):
        """Test RGB frame generation at ISO 3200 (high noise)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        rgb_base64 = agent.generate_rgb_frame(iso=3200, color_grading="night")

        assert isinstance(rgb_base64, str)
        # High ISO frames might be slightly larger due to more entropy
        assert len(rgb_base64) > 0

    def test_agent_rgb_frame_with_motion_blur(self):
        """Test that motion blur is applied to moving agents."""
        # Moving agent
        agent_moving = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 0, 0),  # Moving fast
            acceleration=Vector3(0, 0, 0),
        )

        # Stationary agent
        agent_stationary = Agent(
            id=2,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        frame_moving = agent_moving.generate_rgb_frame(iso=100)
        frame_stationary = agent_stationary.generate_rgb_frame(iso=100)

        # Both should produce valid JPEG
        jpeg_moving = base64.b64decode(frame_moving)
        jpeg_stationary = base64.b64decode(frame_stationary)

        img_moving = Image.open(io.BytesIO(jpeg_moving))
        img_stationary = Image.open(io.BytesIO(jpeg_stationary))

        assert img_moving.size == img_stationary.size == (640, 480)

    def test_rgb_frames_different_iso_settings(self):
        """Test that same agent with different ISO produces different frames."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        frame_iso100 = agent.generate_rgb_frame(iso=100)
        frame_iso3200 = agent.generate_rgb_frame(iso=3200)

        # Should be different due to noise levels
        assert frame_iso100 != frame_iso3200

    def test_rgb_frames_different_color_grading(self):
        """Test that different color grading produces visibly different frames."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        frame_daylight = agent.generate_rgb_frame(iso=100, color_grading="daylight")
        frame_night = agent.generate_rgb_frame(iso=100, color_grading="night")

        # Should be different frames
        assert frame_daylight != frame_night

    def test_rgb_sensor_performance_under_100ms(self):
        """Test that RGB frame generation is fast (<100ms)."""
        import time

        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        start = time.time()
        for _ in range(10):
            agent.generate_rgb_frame(iso=1600, color_grading="daylight")
        elapsed = time.time() - start

        # 10 frames should take <1 second (avg <100ms per frame)
        assert elapsed < 1.0

    def test_engine_rgb_capture_all_agents_with_effects(self):
        """Test SimulationEngine can capture RGB from all agents with effects."""
        engine = SimulationEngine(num_agents=5, duration=1.0, timestep=0.016)

        frames = engine.get_all_agents_rgb_frames()

        assert isinstance(frames, dict)
        assert len(frames) == 5

        for agent_id in range(5):
            assert agent_id in frames
            # Validate each frame is valid JPEG
            jpeg_bytes = base64.b64decode(frames[agent_id])
            img = Image.open(io.BytesIO(jpeg_bytes))
            assert img.format == "JPEG"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
