"""
Realistic sensor noise and distortion models for simulation accuracy.
"""

import numpy as np
from typing import Tuple
from dataclasses import dataclass


@dataclass
class NoiseParameters:
    """Parameters for sensor noise generation."""
    mean: float = 0.0
    std_dev: float = 1.0
    bias: float = 0.0
    min_val: float = -np.inf
    max_val: float = np.inf


class GaussianNoiseGenerator:
    """Generate Gaussian noise with optional bias."""

    def __init__(self, mean: float = 0.0, std_dev: float = 1.0):
        """Initialize noise generator.

        Args:
            mean: Mean of Gaussian distribution
            std_dev: Standard deviation
        """
        self.mean = mean
        self.std_dev = std_dev

    def generate(self, shape: Tuple) -> np.ndarray:
        """Generate Gaussian noise.

        Args:
            shape: Shape of output noise array

        Returns:
            Noise array
        """
        return np.random.normal(self.mean, self.std_dev, shape)

    def apply(self, data: np.ndarray, clip: bool = False) -> np.ndarray:
        """Apply noise to data.

        Args:
            data: Input data
            clip: Whether to clip to [0, 255] for images

        Returns:
            Noisy data
        """
        noise = self.generate(data.shape)
        noisy = data + noise
        if clip:
            noisy = np.clip(noisy, 0, 255)
        return noisy


class LensDistortionModel:
    """Model lens distortion effects in camera images."""

    def __init__(self, k1: float = -0.2, k2: float = 0.1):
        """Initialize lens distortion model.

        Args:
            k1: Radial distortion coefficient (barrel < 0, pincushion > 0)
            k2: Radial distortion coefficient (second order)
        """
        self.k1 = k1
        self.k2 = k2

    def apply(self, image: np.ndarray) -> np.ndarray:
        """Apply lens distortion to image.

        Args:
            image: Input image (H, W, C)

        Returns:
            Distorted image
        """
        h, w = image.shape[:2]
        cx, cy = w / 2, h / 2

        # Create coordinate grids
        x, y = np.meshgrid(np.arange(w), np.arange(h))

        # Normalize to [-1, 1] with center at (0, 0)
        x_norm = (x - cx) / cx
        y_norm = (y - cy) / cy

        # Calculate radial distance
        r2 = x_norm ** 2 + y_norm ** 2

        # Apply distortion formula
        distortion_factor = 1 + self.k1 * r2 + self.k2 * r2 ** 2

        # Map distorted coordinates back to original image
        x_distorted = (x_norm * distortion_factor * cx + cx).astype(int)
        y_distorted = (y_norm * distortion_factor * cy + cy).astype(int)

        # Clamp to image bounds
        x_distorted = np.clip(x_distorted, 0, w - 1)
        y_distorted = np.clip(y_distorted, 0, h - 1)

        # Apply distortion by sampling from original image
        distorted = image[y_distorted, x_distorted]
        return distorted


class DepthSensorNoise:
    """Realistic depth sensor noise model."""

    def __init__(self, gaussian_std: float = 0.005, systematic_bias: float = 0.01):
        """Initialize depth noise model.

        Args:
            gaussian_std: Gaussian noise std dev (meters)
            systematic_bias: Systematic bias as fraction of depth
        """
        self.gaussian_std = gaussian_std
        self.systematic_bias = systematic_bias
        self.gaussian_gen = GaussianNoiseGenerator(0, gaussian_std)

    def apply(self, depth_map: np.ndarray) -> np.ndarray:
        """Apply realistic depth noise.

        Args:
            depth_map: Depth values in meters (H, W)

        Returns:
            Noisy depth map
        """
        # Add systematic bias (proportional to depth)
        systematic_noise = depth_map * self.systematic_bias

        # Add Gaussian noise
        gaussian_noise = self.gaussian_gen.generate(depth_map.shape)

        # Combine noise sources
        noisy_depth = depth_map + systematic_noise + gaussian_noise

        # Clip to valid range [0, inf)
        noisy_depth = np.maximum(noisy_depth, 0)

        return noisy_depth


class LidarSimulator:
    """Realistic Lidar simulator with multipath and rain effects."""

    def __init__(self, num_channels: int = 16):
        """Initialize Lidar simulator.

        Args:
            num_channels: Number of Lidar channels (16, 32, 64)
        """
        self.num_channels = num_channels
        self.max_range = 120.0  # meters

    def apply_multipath_error(self, ranges: np.ndarray) -> np.ndarray:
        """Simulate multipath error (reflections off surfaces).

        Args:
            ranges: Range measurements (num_channels, num_points)

        Returns:
            Ranges with multipath errors
        """
        multipath_probability = 0.05  # 5% of points affected

        # Randomly select points with multipath error
        mask = np.random.random(ranges.shape) < multipath_probability

        # Add multipath error: distance appears shorter due to reflections
        multipath_error = np.random.uniform(-0.5, -0.1, ranges.shape)
        ranges_with_error = ranges.copy()
        ranges_with_error[mask] = ranges[mask] + multipath_error[mask]

        # Clip to valid range
        ranges_with_error = np.clip(ranges_with_error, 0, self.max_range)

        return ranges_with_error

    def apply_rain_effect(self, ranges: np.ndarray, rain_intensity: float = 0.0) -> np.ndarray:
        """Simulate rain scatter effect on Lidar.

        Args:
            ranges: Range measurements (num_channels, num_points)
            rain_intensity: 0.0 (no rain) to 1.0 (heavy rain)

        Returns:
            Ranges with rain effects
        """
        if rain_intensity <= 0:
            return ranges

        # Rain causes point loss and false detections
        point_loss_probability = rain_intensity * 0.5  # Up to 50% loss at heavy rain
        false_detection_probability = rain_intensity * 0.1  # Up to 10% false points

        ranges_affected = ranges.copy()

        # Remove points (point loss)
        loss_mask = np.random.random(ranges.shape) < point_loss_probability
        ranges_affected[loss_mask] = np.inf

        # Add false detections (rain droplets)
        false_mask = np.random.random(ranges.shape) < false_detection_probability
        ranges_affected[false_mask] = np.random.uniform(1, 20, np.sum(false_mask))

        return ranges_affected

    def add_noise(
        self,
        ranges: np.ndarray,
        range_noise_std: float = 0.02,
        angle_noise_std: float = 0.01,
    ) -> np.ndarray:
        """Add noise to Lidar measurements.

        Args:
            ranges: Range measurements
            range_noise_std: Range noise standard deviation (meters)
            angle_noise_std: Angular noise standard deviation (degrees)

        Returns:
            Noisy ranges
        """
        # Range noise (Gaussian)
        range_noise = np.random.normal(0, range_noise_std, ranges.shape)
        noisy_ranges = ranges + range_noise

        # Angular noise affects effective range (small angle approximation)
        # At 10m distance, 0.01 degree error ~ 0.002m range error
        angle_noise = np.random.normal(0, np.radians(angle_noise_std), ranges.shape)
        angle_range_error = angle_noise * ranges

        noisy_ranges += angle_range_error

        return np.clip(noisy_ranges, 0, self.max_range)


class ThermalEmissivityModel:
    """Thermal camera emissivity lookup for realistic temperature rendering."""

    # Typical emissivity values at room temperature (20°C)
    MATERIAL_EMISSIVITY = {
        'asphalt': 0.95,
        'concrete': 0.92,
        'metal': 0.10,
        'water': 0.96,
        'grass': 0.98,
        'tree': 0.97,
        'building': 0.90,
        'sky': 0.85,
        'car': 0.85,
        'person': 0.98,
        'default': 0.90,
    }

    def __init__(self, ambient_temp_c: float = 20.0):
        """Initialize thermal emissivity model.

        Args:
            ambient_temp_c: Ambient temperature in Celsius
        """
        self.ambient_temp_c = ambient_temp_c
        self.ambient_temp_k = ambient_temp_c + 273.15

    def get_emissivity(self, material: str) -> float:
        """Get emissivity for a material.

        Args:
            material: Material name

        Returns:
            Emissivity value (0-1)
        """
        return self.MATERIAL_EMISSIVITY.get(material, self.MATERIAL_EMISSIVITY['default'])

    def apparent_temperature(
        self,
        object_temp_c: float,
        material: str,
        camera_temp_c: float = 20.0,
    ) -> float:
        """Calculate apparent temperature seen by thermal camera.

        Args:
            object_temp_c: Object's actual temperature (Celsius)
            material: Material type
            camera_temp_c: Camera temperature (for reflected radiation)

        Returns:
            Apparent temperature (Celsius)
        """
        emissivity = self.get_emissivity(material)

        # Convert to Kelvin
        object_temp_k = object_temp_c + 273.15
        camera_temp_k = camera_temp_c + 273.15

        # Simplified thermal equation
        # T_apparent = sqrt[epsilon * T_object^4 + (1-epsilon) * T_camera^4]
        apparent_temp_k4 = (
            emissivity * object_temp_k ** 4 +
            (1 - emissivity) * camera_temp_k ** 4
        )

        apparent_temp_k = np.power(apparent_temp_k4, 0.25)
        apparent_temp_c = apparent_temp_k - 273.15

        return apparent_temp_c

    def add_noise(
        self,
        thermal_image: np.ndarray,
        temp_noise_std_c: float = 0.5,
    ) -> np.ndarray:
        """Add realistic thermal camera noise.

        Args:
            thermal_image: Thermal image in Celsius (H, W)
            temp_noise_std_c: Temperature noise std dev (Celsius)

        Returns:
            Noisy thermal image
        """
        noise = np.random.normal(0, temp_noise_std_c, thermal_image.shape)
        noisy = thermal_image + noise
        return noisy


class SensorNoiseFactory:
    """Factory for creating sensor noise models."""

    _instances = {}

    @staticmethod
    def get_rgb_noise_generator(gaussian_std: float = 5.0) -> GaussianNoiseGenerator:
        """Get RGB camera noise generator.

        Args:
            gaussian_std: Gaussian noise std dev (0-255 scale)

        Returns:
            Noise generator
        """
        return GaussianNoiseGenerator(mean=0, std_dev=gaussian_std)

    @staticmethod
    def get_depth_noise_model(
        gaussian_std: float = 0.005,
        systematic_bias: float = 0.01,
    ) -> DepthSensorNoise:
        """Get depth sensor noise model.

        Args:
            gaussian_std: Gaussian noise std dev (meters)
            systematic_bias: Systematic bias fraction

        Returns:
            Depth noise model
        """
        return DepthSensorNoise(gaussian_std, systematic_bias)

    @staticmethod
    def get_lidar_simulator(num_channels: int = 16) -> LidarSimulator:
        """Get Lidar simulator.

        Args:
            num_channels: Number of channels

        Returns:
            Lidar simulator
        """
        return LidarSimulator(num_channels)

    @staticmethod
    def get_thermal_model(ambient_temp_c: float = 20.0) -> ThermalEmissivityModel:
        """Get thermal camera model.

        Args:
            ambient_temp_c: Ambient temperature

        Returns:
            Thermal model
        """
        return ThermalEmissivityModel(ambient_temp_c)

    @staticmethod
    def get_lens_distortion_model(k1: float = -0.2, k2: float = 0.1) -> LensDistortionModel:
        """Get lens distortion model.

        Args:
            k1: Radial distortion coefficient 1
            k2: Radial distortion coefficient 2

        Returns:
            Lens distortion model
        """
        return LensDistortionModel(k1, k2)
