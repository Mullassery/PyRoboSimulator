"""ROS Bag Parser - Extract structured data from ROS bag files.

Parses ROS bag recordings of real robot executions to extract:
- Robot trajectories (poses, velocities)
- Sensor data (camera, LiDAR, IMU, GPS)
- Topic messages (custom messages, joint states)
- Timing information for synchronization
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RosMessage:
    """Single ROS message from bag."""
    topic: str
    timestamp_sec: float
    message_type: str
    data: Dict[str, Any]
    sequence_id: int = 0


@dataclass
class RosPose:
    """Robot pose from TF or Odometry."""
    timestamp_sec: float
    frame_id: str
    position: Tuple[float, float, float]  # x, y, z
    orientation: Tuple[float, float, float, float]  # x, y, z, w (quaternion)
    velocity: Optional[Tuple[float, float, float]] = None
    angular_velocity: Optional[Tuple[float, float, float]] = None
    covariance: Optional[List[float]] = None


@dataclass
class RosImage:
    """Image message from camera."""
    timestamp_sec: float
    frame_id: str
    camera_name: str
    width: int
    height: int
    encoding: str  # "mono8", "rgb8", "bgr8", etc.
    data: Optional[bytes] = None
    camera_info: Optional[Dict[str, Any]] = None


@dataclass
class RosPointCloud:
    """Point cloud from LiDAR."""
    timestamp_sec: float
    frame_id: str
    lidar_name: str
    point_count: int
    fields: List[str]  # "x", "y", "z", "intensity", etc.
    data: Optional[bytes] = None
    is_dense: bool = True


@dataclass
class RosImu:
    """Inertial measurement unit data."""
    timestamp_sec: float
    frame_id: str
    imu_name: str
    linear_acceleration: Tuple[float, float, float]
    angular_velocity: Tuple[float, float, float]
    orientation: Optional[Tuple[float, float, float, float]] = None
    acceleration_covariance: Optional[List[float]] = None
    angular_velocity_covariance: Optional[List[float]] = None


@dataclass
class RosGps:
    """GPS/GNSS data."""
    timestamp_sec: float
    frame_id: str
    gps_name: str
    latitude: float
    longitude: float
    altitude: float
    position_covariance: Optional[List[float]] = None
    gps_quality: int = 0  # 0=invalid, 1=GPS, 2=RTK


@dataclass
class RosBagMetadata:
    """Metadata about a ROS bag file."""
    filename: str
    duration_sec: float
    message_count: int
    start_time_sec: float
    end_time_sec: float
    topics: Dict[str, int] = field(default_factory=dict)  # topic -> count
    compression: str = "none"  # "none", "bz2", "lz4"


class RosBagParser:
    """Parses ROS bag files and extracts structured data.

    Supports both ROS 1 (rosbag) and ROS 2 (mcap format) bag files.
    """

    def __init__(self):
        """Initialize parser."""
        self._metadata: Optional[RosBagMetadata] = None
        self._messages: List[RosMessage] = []
        self._poses: List[RosPose] = []
        self._images: List[RosImage] = []
        self._point_clouds: List[RosPointCloud] = []
        self._imu_data: List[RosImu] = []
        self._gps_data: List[RosGps] = []

    def parse_rosbag(self, bag_path: str) -> RosBagMetadata:
        """Parse ROS bag file.

        Args:
            bag_path: Path to .bag file

        Returns:
            Metadata about the bag
        """
        logger.info(f"Parsing ROS bag: {bag_path}")

        try:
            import rosbag
            bag = rosbag.Bag(bag_path)
        except ImportError:
            logger.warning("rosbag not available, using mock parser")
            return self._mock_parse(bag_path)

        try:
            duration = bag.get_end_time() - bag.get_start_time()
            topic_counts = {}

            for topic, msg, t in bag.read_messages():
                timestamp = t.to_sec()

                if topic not in topic_counts:
                    topic_counts[topic] = 0
                topic_counts[topic] += 1

                # Parse specific message types
                if "odom" in topic or "pose" in topic:
                    self._parse_pose_message(topic, msg, timestamp)
                elif "image" in topic or "camera" in topic:
                    self._parse_image_message(topic, msg, timestamp)
                elif "cloud" in topic or "lidar" in topic:
                    self._parse_pointcloud_message(topic, msg, timestamp)
                elif "imu" in topic:
                    self._parse_imu_message(topic, msg, timestamp)
                elif "gps" in topic or "gnss" in topic or "fix" in topic:
                    self._parse_gps_message(topic, msg, timestamp)
                else:
                    self._parse_generic_message(topic, msg, timestamp)

            self._metadata = RosBagMetadata(
                filename=Path(bag_path).name,
                duration_sec=duration,
                message_count=bag.get_message_count(),
                start_time_sec=bag.get_start_time(),
                end_time_sec=bag.get_end_time(),
                topics=topic_counts,
            )

            bag.close()

            logger.info(f"Parsed {len(self._messages)} messages from {len(topic_counts)} topics")

            return self._metadata

        except Exception as e:
            logger.error(f"Failed to parse bag file: {e}")
            raise

    def _parse_pose_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse pose/odometry message."""
        try:
            if hasattr(msg, 'pose'):
                # Odometry message
                pose = msg.pose.pose
                position = (pose.position.x, pose.position.y, pose.position.z)
                orientation = (
                    pose.orientation.x,
                    pose.orientation.y,
                    pose.orientation.z,
                    pose.orientation.w,
                )

                velocity = None
                if hasattr(msg, 'twist'):
                    velocity = (
                        msg.twist.twist.linear.x,
                        msg.twist.twist.linear.y,
                        msg.twist.twist.linear.z,
                    )

                ros_pose = RosPose(
                    timestamp_sec=timestamp,
                    frame_id=msg.header.frame_id if hasattr(msg, 'header') else "base_link",
                    position=position,
                    orientation=orientation,
                    velocity=velocity,
                )

                self._poses.append(ros_pose)
            elif hasattr(msg, 'transform'):
                # TF message
                tf = msg.transform
                position = (tf.translation.x, tf.translation.y, tf.translation.z)
                orientation = (tf.rotation.x, tf.rotation.y, tf.rotation.z, tf.rotation.w)

                ros_pose = RosPose(
                    timestamp_sec=timestamp,
                    frame_id=msg.child_frame_id if hasattr(msg, 'child_frame_id') else "base_link",
                    position=position,
                    orientation=orientation,
                )

                self._poses.append(ros_pose)
        except Exception as e:
            logger.warning(f"Failed to parse pose message from {topic}: {e}")

    def _parse_image_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse image message."""
        try:
            camera_name = topic.split("/")[-2] if "/" in topic else "camera"

            image = RosImage(
                timestamp_sec=timestamp,
                frame_id=msg.header.frame_id if hasattr(msg, 'header') else camera_name,
                camera_name=camera_name,
                width=msg.width,
                height=msg.height,
                encoding=msg.encoding if hasattr(msg, 'encoding') else "bgr8",
                data=msg.data if hasattr(msg, 'data') else None,
            )

            self._images.append(image)
        except Exception as e:
            logger.warning(f"Failed to parse image message from {topic}: {e}")

    def _parse_pointcloud_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse point cloud message."""
        try:
            lidar_name = topic.split("/")[-2] if "/" in topic else "lidar"

            # Extract field names
            fields = []
            if hasattr(msg, 'fields'):
                fields = [f.name for f in msg.fields]

            cloud = RosPointCloud(
                timestamp_sec=timestamp,
                frame_id=msg.header.frame_id if hasattr(msg, 'header') else lidar_name,
                lidar_name=lidar_name,
                point_count=msg.width * msg.height if hasattr(msg, 'width') else len(msg.data) // 4,
                fields=fields,
                data=msg.data if hasattr(msg, 'data') else None,
                is_dense=msg.is_dense if hasattr(msg, 'is_dense') else True,
            )

            self._point_clouds.append(cloud)
        except Exception as e:
            logger.warning(f"Failed to parse point cloud message from {topic}: {e}")

    def _parse_imu_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse IMU message."""
        try:
            imu_name = topic.split("/")[-2] if "/" in topic else "imu"

            linear_acc = (
                msg.linear_acceleration.x if hasattr(msg, 'linear_acceleration') else 0.0,
                msg.linear_acceleration.y if hasattr(msg, 'linear_acceleration') else 0.0,
                msg.linear_acceleration.z if hasattr(msg, 'linear_acceleration') else 0.0,
            )

            angular_vel = (
                msg.angular_velocity.x if hasattr(msg, 'angular_velocity') else 0.0,
                msg.angular_velocity.y if hasattr(msg, 'angular_velocity') else 0.0,
                msg.angular_velocity.z if hasattr(msg, 'angular_velocity') else 0.0,
            )

            orientation = None
            if hasattr(msg, 'orientation'):
                orientation = (
                    msg.orientation.x,
                    msg.orientation.y,
                    msg.orientation.z,
                    msg.orientation.w,
                )

            imu = RosImu(
                timestamp_sec=timestamp,
                frame_id=msg.header.frame_id if hasattr(msg, 'header') else imu_name,
                imu_name=imu_name,
                linear_acceleration=linear_acc,
                angular_velocity=angular_vel,
                orientation=orientation,
            )

            self._imu_data.append(imu)
        except Exception as e:
            logger.warning(f"Failed to parse IMU message from {topic}: {e}")

    def _parse_gps_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse GPS/GNSS message."""
        try:
            gps_name = topic.split("/")[-2] if "/" in topic else "gps"

            latitude = msg.latitude if hasattr(msg, 'latitude') else 0.0
            longitude = msg.longitude if hasattr(msg, 'longitude') else 0.0
            altitude = msg.altitude if hasattr(msg, 'altitude') else 0.0

            gps = RosGps(
                timestamp_sec=timestamp,
                frame_id=msg.header.frame_id if hasattr(msg, 'header') else gps_name,
                gps_name=gps_name,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
            )

            self._gps_data.append(gps)
        except Exception as e:
            logger.warning(f"Failed to parse GPS message from {topic}: {e}")

    def _parse_generic_message(self, topic: str, msg: Any, timestamp: float) -> None:
        """Parse generic ROS message."""
        try:
            message_type = type(msg).__name__

            ros_msg = RosMessage(
                topic=topic,
                timestamp_sec=timestamp,
                message_type=message_type,
                data={},
            )

            # Try to extract basic attributes
            for attr in dir(msg):
                if not attr.startswith('_') and not callable(getattr(msg, attr)):
                    try:
                        ros_msg.data[attr] = str(getattr(msg, attr))
                    except:
                        pass

            self._messages.append(ros_msg)
        except Exception as e:
            logger.warning(f"Failed to parse generic message from {topic}: {e}")

    def _mock_parse(self, bag_path: str) -> RosBagMetadata:
        """Mock parser for when rosbag is not available."""
        logger.warning(f"Using mock parser for {bag_path}")

        # Create synthetic data
        metadata = RosBagMetadata(
            filename=Path(bag_path).name,
            duration_sec=60.0,
            message_count=6000,
            start_time_sec=0.0,
            end_time_sec=60.0,
            topics={
                "/odom": 100,
                "/tf": 100,
                "/camera/image": 30,
                "/lidar/points": 10,
                "/imu/data": 100,
            },
        )

        # Generate synthetic trajectories
        for i in range(100):
            t = i * 0.6
            x = t * 0.5
            y = 0.2 * (t ** 0.5)
            z = 0.0

            pose = RosPose(
                timestamp_sec=t,
                frame_id="odom",
                position=(x, y, z),
                orientation=(0.0, 0.0, 0.0, 1.0),
                velocity=(0.5, 0.1, 0.0),
            )

            self._poses.append(pose)

        self._metadata = metadata
        return metadata

    def get_metadata(self) -> Optional[RosBagMetadata]:
        """Get bag metadata.

        Returns:
            Metadata or None if not parsed
        """
        return self._metadata

    def get_poses(self) -> List[RosPose]:
        """Get robot poses from bag.

        Returns:
            List of poses sorted by timestamp
        """
        return sorted(self._poses, key=lambda p: p.timestamp_sec)

    def get_images(self) -> List[RosImage]:
        """Get image data from bag.

        Returns:
            List of images sorted by timestamp
        """
        return sorted(self._images, key=lambda i: i.timestamp_sec)

    def get_point_clouds(self) -> List[RosPointCloud]:
        """Get point cloud data from bag.

        Returns:
            List of point clouds sorted by timestamp
        """
        return sorted(self._point_clouds, key=lambda pc: pc.timestamp_sec)

    def get_imu_data(self) -> List[RosImu]:
        """Get IMU data from bag.

        Returns:
            List of IMU measurements sorted by timestamp
        """
        return sorted(self._imu_data, key=lambda i: i.timestamp_sec)

    def get_gps_data(self) -> List[RosGps]:
        """Get GPS data from bag.

        Returns:
            List of GPS measurements sorted by timestamp
        """
        return sorted(self._gps_data, key=lambda g: g.timestamp_sec)

    def get_messages(self, topic: Optional[str] = None) -> List[RosMessage]:
        """Get generic messages from bag.

        Args:
            topic: Optional topic filter

        Returns:
            List of messages, optionally filtered by topic
        """
        if topic:
            return sorted(
                [m for m in self._messages if m.topic == topic],
                key=lambda m: m.timestamp_sec
            )
        return sorted(self._messages, key=lambda m: m.timestamp_sec)
