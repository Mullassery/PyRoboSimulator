"""Sensor simulation implementations (RGB, Depth, Lidar, Thermal)."""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class SensorConfig:
    """Base sensor configuration."""

    sensor_id: str
    agent_id: int
    update_frequency: int  # Hz


@dataclass
class RGBConfig(SensorConfig):
    """RGB camera configuration."""

    width: int = 1920
    height: int = 1080
    fov_horizontal: float = 90.0  # degrees
    fov_vertical: float = 60.0
    exposure_time: float = 0.033  # 30ms for 30fps


@dataclass
class DepthConfig(SensorConfig):
    """Depth camera configuration."""

    width: int = 512
    height: int = 512
    min_range: float = 0.1  # meters
    max_range: float = 300.0  # 300 meters
    fov_horizontal: float = 90.0


@dataclass
class LidarConfig(SensorConfig):
    """Lidar configuration."""

    num_rays_horizontal: int = 512
    num_layers_vertical: int = 16
    max_range: float = 300.0  # meters
    fov_horizontal: float = 360.0  # degrees
    fov_vertical: float = 30.0


@dataclass
class ThermalConfig(SensorConfig):
    """Thermal camera configuration."""

    width: int = 256
    height: int = 256
    min_temp: float = -20.0  # Celsius
    max_temp: float = 60.0
    fov_horizontal: float = 60.0


class RGBSensor:
    """RGB camera sensor simulation."""

    def __init__(self, config: RGBConfig):
        """Initialize RGB sensor.

        Args:
            config: RGBConfig with camera parameters
        """
        self.config = config
        self.frame_count = 0

    def capture_frame(self) -> bytes:
        """Capture RGB frame from camera.

        Returns:
            JPEG-encoded image data
        """
        # In real implementation, this would capture from UE5
        # For now, return dummy data
        frame_data = np.zeros(
            (self.config.height, self.config.width, 3),
            dtype=np.uint8,
        )
        self.frame_count += 1
        return frame_data.tobytes()

    def set_exposure(self, exposure_time: float) -> None:
        """Set camera exposure time.

        Args:
            exposure_time: Exposure time in seconds
        """
        self.config.exposure_time = exposure_time

    def set_fov(self, horizontal: float, vertical: float) -> None:
        """Set field of view.

        Args:
            horizontal: Horizontal FOV in degrees
            vertical: Vertical FOV in degrees
        """
        self.config.fov_horizontal = horizontal
        self.config.fov_vertical = vertical


class DepthSensor:
    """Depth camera sensor simulation."""

    def __init__(self, config: DepthConfig):
        """Initialize depth sensor.

        Args:
            config: DepthConfig with camera parameters
        """
        self.config = config
        self.frame_count = 0

    def capture_depth_map(self) -> np.ndarray:
        """Capture depth map.

        Returns:
            Depth map as float32 array (normalized 0-1, or raw meters)
        """
        # Depth values normalized to 0-1 range
        depth_map = np.random.uniform(
            0,
            1,
            size=(self.config.height, self.config.width),
            dtype=np.float32,
        )
        self.frame_count += 1
        return depth_map

    def get_depth_at_pixel(self, x: int, y: int) -> float:
        """Get depth value at pixel coordinates.

        Args:
            x: Pixel X coordinate
            y: Pixel Y coordinate

        Returns:
            Depth value in meters
        """
        # Return depth in meters (0 to max_range)
        # In real implementation, query depth map or physics
        return np.random.uniform(0, self.config.max_range)

    def set_range(self, min_range: float, max_range: float) -> None:
        """Set depth range.

        Args:
            min_range: Minimum range in meters
            max_range: Maximum range in meters
        """
        self.config.min_range = min_range
        self.config.max_range = max_range


class LidarSensor:
    """Lidar (3D laser scanner) sensor simulation."""

    def __init__(self, config: LidarConfig):
        """Initialize lidar sensor.

        Args:
            config: LidarConfig with lidar parameters
        """
        self.config = config
        self.frame_count = 0

    def capture_point_cloud(self) -> List[Tuple[float, float, float]]:
        """Capture point cloud scan.

        Returns:
            List of (x, y, z) points in meters
        """
        num_points = self.config.num_rays_horizontal * self.config.num_layers_vertical
        points = []

        for layer in range(self.config.num_layers_vertical):
            # Vertical angle for this layer
            vertical_angle = (
                -self.config.fov_vertical / 2
                + (layer / self.config.num_layers_vertical) * self.config.fov_vertical
            )

            for ray in range(self.config.num_rays_horizontal):
                # Horizontal angle for this ray
                horizontal_angle = (
                    (ray / self.config.num_rays_horizontal) * self.config.fov_horizontal
                )

                # Random distance for demo
                distance = np.random.uniform(0, self.config.max_range)

                # Convert spherical to cartesian
                vert_rad = np.radians(vertical_angle)
                horz_rad = np.radians(horizontal_angle)

                x = distance * np.cos(vert_rad) * np.cos(horz_rad)
                y = distance * np.cos(vert_rad) * np.sin(horz_rad)
                z = distance * np.sin(vert_rad)

                points.append((float(x), float(y), float(z)))

        self.frame_count += 1
        return points

    def raycast(self, ray_index: int, layer_index: int) -> Tuple[float, bool]:
        """Perform single raycast.

        Args:
            ray_index: Ray index (0 to num_rays_horizontal)
            layer_index: Layer index (0 to num_layers_vertical)

        Returns:
            (distance, hit) tuple where distance is in meters
        """
        # Simulate raycast
        hit = np.random.random() > 0.3  # 70% hit probability
        distance = np.random.uniform(0, self.config.max_range) if hit else self.config.max_range
        return (distance, hit)

    def set_fov(self, horizontal: float, vertical: float) -> None:
        """Set field of view.

        Args:
            horizontal: Horizontal FOV in degrees
            vertical: Vertical FOV in degrees
        """
        self.config.fov_horizontal = horizontal
        self.config.fov_vertical = vertical


class ThermalSensor:
    """Thermal (infrared) camera sensor simulation."""

    def __init__(self, config: ThermalConfig):
        """Initialize thermal sensor.

        Args:
            config: ThermalConfig with camera parameters
        """
        self.config = config
        self.frame_count = 0

    def capture_thermal_image(self) -> np.ndarray:
        """Capture thermal image.

        Returns:
            Thermal image as float32 array (temperature in Celsius)
        """
        # Random temperature values in range
        thermal_image = np.random.uniform(
            self.config.min_temp,
            self.config.max_temp,
            size=(self.config.height, self.config.width),
            dtype=np.float32,
        )
        self.frame_count += 1
        return thermal_image

    def get_temperature_at_pixel(self, x: int, y: int) -> float:
        """Get temperature at pixel coordinates.

        Args:
            x: Pixel X coordinate
            y: Pixel Y coordinate

        Returns:
            Temperature in Celsius
        """
        return np.random.uniform(self.config.min_temp, self.config.max_temp)

    def set_temperature_range(self, min_temp: float, max_temp: float) -> None:
        """Set temperature range.

        Args:
            min_temp: Minimum temperature in Celsius
            max_temp: Maximum temperature in Celsius
        """
        self.config.min_temp = min_temp
        self.config.max_temp = max_temp


class SensorManager:
    """Manages all sensors for an agent."""

    def __init__(self, agent_id: int):
        """Initialize sensor manager.

        Args:
            agent_id: Agent ID
        """
        self.agent_id = agent_id
        self.rgb_sensor: RGBSensor = None
        self.depth_sensor: DepthSensor = None
        self.lidar_sensor: LidarSensor = None
        self.thermal_sensor: ThermalSensor = None

    def add_rgb_sensor(self, config: RGBConfig = None) -> RGBSensor:
        """Add RGB camera.

        Args:
            config: RGBConfig (uses defaults if None)

        Returns:
            Configured RGB sensor
        """
        if config is None:
            config = RGBConfig(sensor_id="rgb", agent_id=self.agent_id, update_frequency=30)
        self.rgb_sensor = RGBSensor(config)
        return self.rgb_sensor

    def add_depth_sensor(self, config: DepthConfig = None) -> DepthSensor:
        """Add depth camera.

        Args:
            config: DepthConfig (uses defaults if None)

        Returns:
            Configured depth sensor
        """
        if config is None:
            config = DepthConfig(sensor_id="depth", agent_id=self.agent_id, update_frequency=30)
        self.depth_sensor = DepthSensor(config)
        return self.depth_sensor

    def add_lidar_sensor(self, config: LidarConfig = None) -> LidarSensor:
        """Add lidar.

        Args:
            config: LidarConfig (uses defaults if None)

        Returns:
            Configured lidar sensor
        """
        if config is None:
            config = LidarConfig(sensor_id="lidar", agent_id=self.agent_id, update_frequency=30)
        self.lidar_sensor = LidarSensor(config)
        return self.lidar_sensor

    def add_thermal_sensor(self, config: ThermalConfig = None) -> ThermalSensor:
        """Add thermal camera.

        Args:
            config: ThermalConfig (uses defaults if None)

        Returns:
            Configured thermal sensor
        """
        if config is None:
            config = ThermalConfig(
                sensor_id="thermal",
                agent_id=self.agent_id,
                update_frequency=30,
            )
        self.thermal_sensor = ThermalSensor(config)
        return self.thermal_sensor

    def get_all_sensor_readings(self) -> dict:
        """Get readings from all installed sensors.

        Returns:
            Dictionary with sensor readings
        """
        readings = {
            "agent_id": self.agent_id,
            "timestamp": None,  # Would be filled by UE5
        }

        if self.rgb_sensor:
            readings["rgb"] = self.rgb_sensor.capture_frame()

        if self.depth_sensor:
            readings["depth"] = self.depth_sensor.capture_depth_map()

        if self.lidar_sensor:
            readings["lidar"] = self.lidar_sensor.capture_point_cloud()

        if self.thermal_sensor:
            readings["thermal"] = self.thermal_sensor.capture_thermal_image()

        return readings
