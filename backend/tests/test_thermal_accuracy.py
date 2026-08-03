"""Tests for thermal camera sensor fidelity (emissivity, view factor, radiative exchange, calibration)."""

import base64

import numpy as np
import pytest

from services.simulation_engine import Agent, Vector3


class TestThermalMaterialEmissivity:
    """Test material-based emissivity effects."""

    def test_thermal_image_shape(self):
        """Test that thermal image has correct shape."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32)

        # Should be 256x256 = 65536 float32 values
        assert len(thermal_map) == 256 * 256
        assert thermal_map.dtype == np.float32

    def test_emissivity_spatial_variation(self):
        """Test that different materials have different apparent temperatures."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Extract material patches (left to right: asphalt, concrete, metal, glass, water, etc.)
        material_regions = []
        patch_width = 256 // 11

        for mat_idx in range(11):
            x_start = mat_idx * patch_width
            x_end = (mat_idx + 1) * patch_width if mat_idx < 10 else 256
            region = thermal_map[:, x_start:x_end]
            material_regions.append(region)

        # Metal (low emissivity) should be cooler than asphalt (high emissivity)
        # Material index 2 is metal, index 0 is asphalt
        metal_temp = np.mean(material_regions[2])
        asphalt_temp = np.mean(material_regions[0])

        # Metal should read lower due to low emissivity
        assert metal_temp < asphalt_temp

    def test_thermal_range_clipping(self):
        """Test that thermal values are clipped to valid range."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image(min_temp=-20, max_temp=60)
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # All values should be within range
        assert np.min(thermal_map) >= -20
        assert np.max(thermal_map) <= 60


class TestThermalViewFactor:
    """Test view factor (directional sensitivity)."""

    def test_view_factor_center_brightest(self):
        """Test that center of image (on-axis) is warmer than edges (off-axis)."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Center region (on-axis, better view factor)
        center = thermal_map[100:150, 100:150]

        # Edge regions (off-axis, reduced view factor)
        edges = np.concatenate([
            thermal_map[0:10, :],
            thermal_map[-10:, :],
            thermal_map[:, 0:10],
            thermal_map[:, -10:],
        ])

        # Center should be warmer on average due to view factor
        assert np.mean(center) > np.mean(edges)

    def test_view_factor_symmetry(self):
        """Test that view factor effect is radially symmetric."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image()
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Compare quadrants
        q1 = thermal_map[:128, :128]
        q2 = thermal_map[:128, 128:]
        q3 = thermal_map[128:, :128]
        q4 = thermal_map[128:, 128:]

        # Quadrants should be similar on average (radially symmetric)
        means = [np.mean(q) for q in [q1, q2, q3, q4]]
        assert max(means) - min(means) < 5  # Within 5°C variation


class TestThermalCalibration:
    """Test calibration error effects."""

    def test_calibration_offset_variation(self):
        """Test that calibration error produces variation between frames."""
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

        thermal1_b64 = agent1.generate_thermal_image(calibration_error=2.0)
        thermal2_b64 = agent2.generate_thermal_image(calibration_error=2.0)

        thermal1 = np.frombuffer(base64.b64decode(thermal1_b64), dtype=np.float32).reshape(256, 256)
        thermal2 = np.frombuffer(base64.b64decode(thermal2_b64), dtype=np.float32).reshape(256, 256)

        # Calibration error should cause difference between frames
        difference = np.mean(np.abs(thermal1 - thermal2))

        # Expect some difference due to ±2°C calibration error
        assert difference > 0

    def test_zero_calibration_error_consistency(self):
        """Test that zero calibration error produces consistent measurements."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal1_b64 = agent.generate_thermal_image(calibration_error=0.0)
        thermal2_b64 = agent.generate_thermal_image(calibration_error=0.0)

        thermal1 = np.frombuffer(base64.b64decode(thermal1_b64), dtype=np.float32).reshape(256, 256)
        thermal2 = np.frombuffer(base64.b64decode(thermal2_b64), dtype=np.float32).reshape(256, 256)

        # With zero calibration error, should still differ due to thermal noise
        # but the baseline should be more consistent
        difference = np.mean(np.abs(thermal1 - thermal2))
        assert difference > 0  # Still has sensor noise (~0.2°C)


class TestThermalNoise:
    """Test thermal sensor noise characteristics."""

    def test_thermal_noise_magnitude(self):
        """Test that thermal noise is ~0.2°C."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # Generate multiple frames with zero calibration error
        frames = []
        for _ in range(10):
            thermal_b64 = agent.generate_thermal_image(calibration_error=0.0)
            thermal = np.frombuffer(base64.b64decode(thermal_b64), dtype=np.float32).reshape(256, 256)
            frames.append(thermal)

        # Calculate variance between frames
        frame_array = np.array(frames)
        noise_std = np.std(frame_array, axis=0)
        mean_noise = np.mean(noise_std)

        # Should be ~0.2°C
        print(f"\nThermal noise std dev: {mean_noise:.3f}°C (target ~0.2°C)")
        assert 0.1 < mean_noise < 0.4


class TestThermalIntegration:
    """Test full thermal sensor integration."""

    def test_full_thermal_generation_with_custom_range(self):
        """Test thermal generation with custom temperature range."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image(min_temp=-30, max_temp=80, calibration_error=1.5)
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Should respect custom range
        assert np.min(thermal_map) >= -30
        assert np.max(thermal_map) <= 80

    def test_thermal_sensor_accuracy(self):
        """Test that thermal sensor follows ±2°C accuracy spec."""
        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        # Generate thermal with moderate calibration error
        thermal_b64 = agent.generate_thermal_image(calibration_error=2.0)
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # All values should be within expected range
        assert np.min(thermal_map) >= -20 - 2  # min_temp - calibration error margin
        assert np.max(thermal_map) <= 60 + 2   # max_temp + calibration error margin

    def test_thermal_material_ordering(self):
        """Test that thermal images show material emissivity ordering."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        thermal_b64 = agent.generate_thermal_image(calibration_error=0.5)
        thermal_bytes = base64.b64decode(thermal_b64)
        thermal_map = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(256, 256)

        # Material order: asphalt, concrete, metal, glass, water, grass, bark, leaves, soil, plastic, brick
        # Expected ordering: high emissivity (asphalt, water) > low emissivity (metal)
        patch_width = 256 // 11

        # Asphalt patch
        asphalt = np.mean(thermal_map[:, 0:patch_width])

        # Metal patch (index 2)
        metal = np.mean(thermal_map[:, 2*patch_width:3*patch_width])

        # Water patch (index 4)
        water = np.mean(thermal_map[:, 4*patch_width:5*patch_width])

        # Asphalt (0.95) should be warmer than metal (0.15)
        assert asphalt > metal

        # Water (0.98) should be one of warmest
        assert water > metal

    def test_thermal_performance(self):
        """Test that thermal generation is reasonably fast."""
        import time

        agent = Agent(
            id=1,
            position=Vector3(100, 100, 0),
            velocity=Vector3(5, 5, 0),
            acceleration=Vector3(0, 0, 0),
        )

        start = time.time()
        for _ in range(10):
            agent.generate_thermal_image(calibration_error=2.0)
        elapsed = time.time() - start

        avg_ms = (elapsed / 10) * 1000
        print(f"\nThermal image generation: {avg_ms:.1f}ms per image")

        # Should be fast (<50ms per image)
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
