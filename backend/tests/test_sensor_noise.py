"""
Tests for sensor noise and distortion models.
"""

import pytest
import numpy as np
from src.sensors.noise_models import (
    GaussianNoiseGenerator,
    LensDistortionModel,
    DepthSensorNoise,
    LidarSimulator,
    ThermalEmissivityModel,
    SensorNoiseFactory,
)


class TestGaussianNoiseGenerator:
    """Test Gaussian noise generation."""

    def test_initialization(self):
        """Test noise generator initialization."""
        gen = GaussianNoiseGenerator(mean=0, std_dev=1.0)
        assert gen.mean == 0
        assert gen.std_dev == 1.0

    def test_generate_correct_shape(self):
        """Test that generated noise has correct shape."""
        gen = GaussianNoiseGenerator()
        noise = gen.generate((10, 20))
        assert noise.shape == (10, 20)

    def test_generate_statistics(self):
        """Test generated noise has correct statistics."""
        gen = GaussianNoiseGenerator(mean=0, std_dev=2.0)
        noise = gen.generate((10000, 1))

        # Check mean and std dev (with tolerance)
        assert abs(np.mean(noise) - 0) < 0.1
        assert abs(np.std(noise) - 2.0) < 0.1

    def test_apply_noise(self):
        """Test applying noise to data."""
        gen = GaussianNoiseGenerator(mean=0, std_dev=0.1)
        data = np.ones((10, 10)) * 100
        noisy = gen.apply(data)

        assert noisy.shape == data.shape
        assert not np.allclose(noisy, data)
        assert np.mean(noisy) < 105  # Should be around 100

    def test_apply_noise_with_clipping(self):
        """Test noise application with clipping."""
        gen = GaussianNoiseGenerator(mean=0, std_dev=50)
        data = np.ones((10, 10)) * 128
        noisy = gen.apply(data, clip=True)

        assert np.all(noisy >= 0)
        assert np.all(noisy <= 255)


class TestLensDistortionModel:
    """Test lens distortion model."""

    def test_initialization(self):
        """Test distortion model initialization."""
        model = LensDistortionModel(k1=-0.2, k2=0.1)
        assert model.k1 == -0.2
        assert model.k2 == 0.1

    def test_apply_distortion_barrel(self):
        """Test barrel distortion (negative k1)."""
        model = LensDistortionModel(k1=-0.3, k2=0)
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        distorted = model.apply(image)

        assert distorted.shape == image.shape
        assert distorted.dtype == image.dtype

    def test_apply_distortion_pincushion(self):
        """Test pincushion distortion (positive k1)."""
        model = LensDistortionModel(k1=0.2, k2=0)
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        distorted = model.apply(image)

        assert distorted.shape == image.shape

    def test_distortion_changes_image(self):
        """Test that distortion actually modifies the image."""
        model = LensDistortionModel(k1=-0.5, k2=0)
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        distorted = model.apply(image)

        # Distorted image should be different from original
        # (not guaranteed, but very likely with strong distortion)
        assert not np.allclose(image, distorted)


class TestDepthSensorNoise:
    """Test depth sensor noise model."""

    def test_initialization(self):
        """Test depth noise model initialization."""
        model = DepthSensorNoise(gaussian_std=0.01, systematic_bias=0.02)
        assert model.gaussian_std == 0.01
        assert model.systematic_bias == 0.02

    def test_apply_noise(self):
        """Test applying noise to depth map."""
        model = DepthSensorNoise(gaussian_std=0.001, systematic_bias=0.001)
        depth = np.ones((100, 100)) * 10.0  # 10 meters
        noisy = model.apply(depth)

        assert noisy.shape == depth.shape
        assert np.all(noisy >= 0)
        # Noisy should be close to original
        assert np.abs(np.mean(noisy) - 10.0) < 0.5

    def test_depth_noise_systematic_bias(self):
        """Test that systematic bias is proportional to depth."""
        model = DepthSensorNoise(gaussian_std=0.0, systematic_bias=0.1)

        # Test at different depths
        depth_shallow = np.ones((10, 10)) * 5.0
        depth_deep = np.ones((10, 10)) * 50.0

        noisy_shallow = model.apply(depth_shallow)
        noisy_deep = model.apply(depth_deep)

        # Deeper measurements should have more bias
        assert np.abs(np.mean(noisy_deep) - 50.0) > np.abs(np.mean(noisy_shallow) - 5.0)

    def test_depth_non_negative(self):
        """Test that depth stays non-negative."""
        model = DepthSensorNoise(gaussian_std=1.0, systematic_bias=-0.5)
        depth = np.ones((100, 100)) * 1.0  # Very shallow
        noisy = model.apply(depth)

        assert np.all(noisy >= 0)


class TestLidarSimulator:
    """Test Lidar simulator."""

    def test_initialization(self):
        """Test Lidar simulator initialization."""
        sim = LidarSimulator(num_channels=16)
        assert sim.num_channels == 16
        assert sim.max_range == 120.0

    def test_multipath_error(self):
        """Test multipath error simulation."""
        sim = LidarSimulator()
        ranges = np.ones((16, 1000)) * 50.0
        ranges_with_error = sim.apply_multipath_error(ranges)

        assert ranges_with_error.shape == ranges.shape
        assert np.all(ranges_with_error >= 0)
        assert np.all(ranges_with_error <= sim.max_range)

    def test_rain_effect_point_loss(self):
        """Test rain causes point loss."""
        sim = LidarSimulator()
        ranges = np.ones((16, 1000)) * 50.0
        ranges_with_rain = sim.apply_rain_effect(ranges, rain_intensity=0.5)

        # Some points should be marked as no-return (inf)
        inf_count = np.sum(np.isinf(ranges_with_rain))
        assert inf_count > 0

    def test_rain_no_effect_zero_intensity(self):
        """Test no rain effect with zero intensity."""
        sim = LidarSimulator()
        ranges = np.ones((16, 1000)) * 50.0
        ranges_no_rain = sim.apply_rain_effect(ranges, rain_intensity=0.0)

        assert np.allclose(ranges, ranges_no_rain)

    def test_rain_heavy_effect(self):
        """Test heavy rain has more effect."""
        sim = LidarSimulator()
        ranges = np.ones((16, 1000)) * 50.0

        light_rain = sim.apply_rain_effect(ranges.copy(), rain_intensity=0.2)
        heavy_rain = sim.apply_rain_effect(ranges.copy(), rain_intensity=0.8)

        # Heavy rain should have more invalid points
        light_inf = np.sum(np.isinf(light_rain))
        heavy_inf = np.sum(np.isinf(heavy_rain))

        assert heavy_inf >= light_inf

    def test_add_noise(self):
        """Test adding Gaussian noise to ranges."""
        sim = LidarSimulator()
        ranges = np.ones((16, 1000)) * 50.0
        noisy = sim.add_noise(ranges, range_noise_std=0.1, angle_noise_std=0.05)

        assert noisy.shape == ranges.shape
        assert np.all(noisy >= 0)
        assert not np.allclose(noisy, ranges)


class TestThermalEmissivityModel:
    """Test thermal camera emissivity model."""

    def test_initialization(self):
        """Test thermal model initialization."""
        model = ThermalEmissivityModel(ambient_temp_c=20.0)
        assert model.ambient_temp_c == 20.0

    def test_get_emissivity(self):
        """Test emissivity lookup."""
        model = ThermalEmissivityModel()

        assert model.get_emissivity('asphalt') == 0.95
        assert model.get_emissivity('metal') == 0.10
        assert model.get_emissivity('water') == 0.96
        assert model.get_emissivity('person') == 0.98

    def test_get_emissivity_default(self):
        """Test default emissivity for unknown material."""
        model = ThermalEmissivityModel()
        assert model.get_emissivity('unknown_material') == 0.90

    def test_apparent_temperature(self):
        """Test apparent temperature calculation."""
        model = ThermalEmissivityModel(ambient_temp_c=20.0)

        # High emissivity material at body temperature
        temp_person = model.apparent_temperature(37, 'person')
        assert 35 < temp_person < 39

        # Low emissivity material (metal) at same temperature
        temp_metal = model.apparent_temperature(37, 'metal')
        # Should see more ambient temperature reflected
        assert abs(temp_metal - 20.0) < abs(temp_person - 20.0)

    def test_apparent_temperature_high_emissivity(self):
        """Test that high emissivity materials show true temperature."""
        model = ThermalEmissivityModel(ambient_temp_c=20.0)

        # Water has high emissivity
        temp_water = model.apparent_temperature(50, 'water')

        # Should be close to actual temperature
        assert 48 < temp_water < 52

    def test_apparent_temperature_low_emissivity(self):
        """Test that low emissivity materials show ambient influence."""
        model = ThermalEmissivityModel(ambient_temp_c=20.0)

        # Metal has low emissivity
        temp_metal = model.apparent_temperature(50, 'metal')

        # Should be influenced by ambient (20°C)
        assert temp_metal < 45  # Should be significantly lower than 50

    def test_add_noise(self):
        """Test adding noise to thermal image."""
        model = ThermalEmissivityModel()
        thermal = np.ones((100, 100)) * 30.0
        noisy = model.add_noise(thermal, temp_noise_std_c=0.5)

        assert noisy.shape == thermal.shape
        assert not np.allclose(noisy, thermal)
        # Most values should be within 2 std devs
        assert np.mean(np.abs(noisy - thermal)) < 1.5


class TestSensorNoiseFactory:
    """Test sensor noise factory."""

    def test_get_rgb_noise_generator(self):
        """Test RGB noise generator creation."""
        gen = SensorNoiseFactory.get_rgb_noise_generator(gaussian_std=5.0)
        assert isinstance(gen, GaussianNoiseGenerator)
        assert gen.std_dev == 5.0

    def test_get_depth_noise_model(self):
        """Test depth noise model creation."""
        model = SensorNoiseFactory.get_depth_noise_model()
        assert isinstance(model, DepthSensorNoise)

    def test_get_lidar_simulator(self):
        """Test Lidar simulator creation."""
        sim = SensorNoiseFactory.get_lidar_simulator(num_channels=32)
        assert isinstance(sim, LidarSimulator)
        assert sim.num_channels == 32

    def test_get_thermal_model(self):
        """Test thermal model creation."""
        model = SensorNoiseFactory.get_thermal_model(ambient_temp_c=25.0)
        assert isinstance(model, ThermalEmissivityModel)
        assert model.ambient_temp_c == 25.0

    def test_get_lens_distortion_model(self):
        """Test lens distortion model creation."""
        model = SensorNoiseFactory.get_lens_distortion_model(k1=-0.3, k2=0.1)
        assert isinstance(model, LensDistortionModel)
        assert model.k1 == -0.3
        assert model.k2 == 0.1


@pytest.mark.integration
class TestSensorNoiseIntegration:
    """Integration tests for sensor noise system."""

    def test_rgb_with_distortion(self):
        """Test RGB image with noise and distortion."""
        rgb_gen = SensorNoiseFactory.get_rgb_noise_generator(gaussian_std=5.0)
        distortion = SensorNoiseFactory.get_lens_distortion_model()

        image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        # Apply noise
        noisy = rgb_gen.apply(image, clip=True)
        assert noisy.dtype == np.uint8

        # Apply distortion
        distorted = distortion.apply(noisy)
        assert distorted.shape == image.shape

    def test_depth_with_systematic_error(self):
        """Test depth measurement with systematic error."""
        depth_model = SensorNoiseFactory.get_depth_noise_model(
            gaussian_std=0.005,
            systematic_bias=0.02,
        )

        depth = np.random.uniform(1, 30, (480, 640))
        noisy = depth_model.apply(depth)

        assert noisy.shape == depth.shape
        assert np.all(noisy >= 0)

    def test_lidar_in_rain(self):
        """Test Lidar performance in rain."""
        lidar = SensorNoiseFactory.get_lidar_simulator(num_channels=32)

        ranges = np.random.uniform(1, 100, (32, 3600))

        # Apply multipath first
        ranges = lidar.apply_multipath_error(ranges)

        # Then apply rain
        ranges_rain = lidar.apply_rain_effect(ranges, rain_intensity=0.7)

        # Then add noise
        ranges_noisy = lidar.add_noise(ranges_rain)

        assert ranges_noisy.shape == ranges.shape
        assert np.all(ranges_noisy >= 0)

    def test_thermal_scene(self):
        """Test thermal camera on scene with different materials."""
        thermal = SensorNoiseFactory.get_thermal_model(ambient_temp_c=20.0)

        materials = ['asphalt', 'metal', 'water', 'person']
        temperatures = [40, 50, 15, 37]

        for material, temp in zip(materials, temperatures):
            apparent = thermal.apparent_temperature(temp, material)
            assert 10 < apparent < 60  # Reasonable temperature range
