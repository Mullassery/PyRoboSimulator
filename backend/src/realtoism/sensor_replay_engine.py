"""Sensor Replay Engine - Play back recorded sensor data in simulation.

Replays recorded sensor measurements for validation and replay scenarios.
Enables synchronization of multiple sensor streams.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.src.realtoism.rosbag_parser import (
    RosBagParser,
    RosImage,
    RosPointCloud,
    RosImu,
    RosGps,
)

logger = logging.getLogger(__name__)


@dataclass
class SensorReplayState:
    """State of sensor replay."""
    current_time_sec: float = 0.0
    is_playing: bool = False
    playback_speed: float = 1.0
    current_frame_idx: Dict[str, int] = None  # sensor_name -> frame index

    def __post_init__(self):
        if self.current_frame_idx is None:
            self.current_frame_idx = {}


class SensorReplayEngine:
    """Replays recorded sensor data synchronized to simulation time.

    Supports:
    - Image replay (camera frames)
    - Point cloud replay (LiDAR)
    - IMU replay (motion data)
    - GPS replay (position data)
    - Temporal synchronization across multiple sensors
    """

    def __init__(self, parser: RosBagParser):
        """Initialize replay engine.

        Args:
            parser: RosBagParser with loaded bag data
        """
        self._parser = parser
        self._state = SensorReplayState()
        self._callbacks: Dict[str, List[callable]] = {
            "image_frame": [],
            "point_cloud": [],
            "imu_measurement": [],
            "gps_measurement": [],
        }

    def start_replay(self, start_time_sec: float = 0.0) -> None:
        """Start sensor replay.

        Args:
            start_time_sec: Start time in seconds
        """
        self._state.is_playing = True
        self._state.current_time_sec = start_time_sec
        self._state.current_frame_idx.clear()

        logger.info(f"Started sensor replay at t={start_time_sec}s")

    def stop_replay(self) -> None:
        """Stop sensor replay."""
        self._state.is_playing = False
        logger.info("Stopped sensor replay")

    def pause_replay(self) -> None:
        """Pause sensor replay."""
        self._state.is_playing = False
        logger.info(f"Paused sensor replay at t={self._state.current_time_sec}s")

    def resume_replay(self) -> None:
        """Resume sensor replay."""
        self._state.is_playing = True
        logger.info(f"Resumed sensor replay from t={self._state.current_time_sec}s")

    def set_playback_speed(self, speed: float) -> None:
        """Set playback speed multiplier.

        Args:
            speed: Playback speed (1.0 = normal, 2.0 = 2x, 0.5 = 0.5x)
        """
        self._state.playback_speed = max(0.1, speed)
        logger.info(f"Set playback speed to {self._state.playback_speed}x")

    def seek_to_time(self, time_sec: float) -> None:
        """Seek to specific time in replay.

        Args:
            time_sec: Target time in seconds
        """
        self._state.current_time_sec = time_sec
        self._state.current_frame_idx.clear()

        logger.info(f"Seeked to t={time_sec}s")

    def update(self, elapsed_time_sec: float) -> Dict[str, Any]:
        """Update replay state and get current sensor data.

        Args:
            elapsed_time_sec: Elapsed simulation time in seconds

        Returns:
            Dictionary of available sensor data at current time
        """
        if not self._state.is_playing:
            return {}

        # Advance time
        self._state.current_time_sec += elapsed_time_sec * self._state.playback_speed

        sensor_data = {}

        # Get current image frames
        images = self._get_current_images()
        if images:
            sensor_data["images"] = images
            for callback in self._callbacks["image_frame"]:
                for img in images:
                    callback(img)

        # Get current point clouds
        clouds = self._get_current_point_clouds()
        if clouds:
            sensor_data["point_clouds"] = clouds
            for callback in self._callbacks["point_cloud"]:
                for cloud in clouds:
                    callback(cloud)

        # Get current IMU data
        imu_data = self._get_current_imu_data()
        if imu_data:
            sensor_data["imu"] = imu_data
            for callback in self._callbacks["imu_measurement"]:
                for imu in imu_data:
                    callback(imu)

        # Get current GPS data
        gps_data = self._get_current_gps_data()
        if gps_data:
            sensor_data["gps"] = gps_data
            for callback in self._callbacks["gps_measurement"]:
                for gps in gps_data:
                    callback(gps)

        return sensor_data

    def _get_current_images(self) -> List[RosImage]:
        """Get images at or after current time.

        Returns:
            List of images
        """
        images = self._parser.get_images()
        current_images = []

        sensor_name = "camera"
        start_idx = self._state.current_frame_idx.get(f"image_{sensor_name}", 0)

        for i in range(start_idx, len(images)):
            if images[i].timestamp_sec <= self._state.current_time_sec:
                current_images.append(images[i])
                self._state.current_frame_idx[f"image_{sensor_name}"] = i + 1
            else:
                break

        return current_images

    def _get_current_point_clouds(self) -> List[RosPointCloud]:
        """Get point clouds at or after current time.

        Returns:
            List of point clouds
        """
        clouds = self._parser.get_point_clouds()
        current_clouds = []

        sensor_name = "lidar"
        start_idx = self._state.current_frame_idx.get(f"cloud_{sensor_name}", 0)

        for i in range(start_idx, len(clouds)):
            if clouds[i].timestamp_sec <= self._state.current_time_sec:
                current_clouds.append(clouds[i])
                self._state.current_frame_idx[f"cloud_{sensor_name}"] = i + 1
            else:
                break

        return current_clouds

    def _get_current_imu_data(self) -> List[RosImu]:
        """Get IMU measurements at or after current time.

        Returns:
            List of IMU measurements
        """
        imu_list = self._parser.get_imu_data()
        current_imu = []

        sensor_name = "imu"
        start_idx = self._state.current_frame_idx.get(f"imu_{sensor_name}", 0)

        for i in range(start_idx, len(imu_list)):
            if imu_list[i].timestamp_sec <= self._state.current_time_sec:
                current_imu.append(imu_list[i])
                self._state.current_frame_idx[f"imu_{sensor_name}"] = i + 1
            else:
                break

        return current_imu

    def _get_current_gps_data(self) -> List[RosGps]:
        """Get GPS measurements at or after current time.

        Returns:
            List of GPS measurements
        """
        gps_list = self._parser.get_gps_data()
        current_gps = []

        sensor_name = "gps"
        start_idx = self._state.current_frame_idx.get(f"gps_{sensor_name}", 0)

        for i in range(start_idx, len(gps_list)):
            if gps_list[i].timestamp_sec <= self._state.current_time_sec:
                current_gps.append(gps_list[i])
                self._state.current_frame_idx[f"gps_{sensor_name}"] = i + 1
            else:
                break

        return current_gps

    def register_callback(self, sensor_type: str, callback: callable) -> None:
        """Register callback for sensor data.

        Args:
            sensor_type: "image_frame" | "point_cloud" | "imu_measurement" | "gps_measurement"
            callback: Function to call with sensor data
        """
        if sensor_type in self._callbacks:
            self._callbacks[sensor_type].append(callback)
            logger.info(f"Registered callback for {sensor_type}")

    def get_state(self) -> SensorReplayState:
        """Get current replay state.

        Returns:
            SensorReplayState
        """
        return self._state

    def get_duration(self) -> float:
        """Get total replay duration.

        Returns:
            Duration in seconds
        """
        metadata = self._parser.get_metadata()
        return metadata.duration_sec if metadata else 0.0

    def get_progress(self) -> float:
        """Get replay progress as fraction 0-1.

        Returns:
            Progress fraction
        """
        duration = self.get_duration()
        if duration <= 0:
            return 0.0

        return min(self._state.current_time_sec / duration, 1.0)

    def get_sensor_summary(self) -> Dict[str, Any]:
        """Get summary of available sensors in replay.

        Returns:
            Dictionary of sensor types and counts
        """
        return {
            "images": len(self._parser.get_images()),
            "point_clouds": len(self._parser.get_point_clouds()),
            "imu_measurements": len(self._parser.get_imu_data()),
            "gps_measurements": len(self._parser.get_gps_data()),
            "total_messages": len(self._parser.get_messages()),
        }
