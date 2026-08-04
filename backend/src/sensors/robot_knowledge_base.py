"""Robot Hardware Knowledge Base and Automatic Discovery - Phase 5.1.

Maintains database of commercial robot sensor configurations.
Enables automatic sensor discovery without manual configuration.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from backend.src.sensors.sensor_definitions import (
    SensorSpec,
    SensorType,
    SensorCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class RobotSensorEntry:
    """Robot sensor with confidence metadata."""

    sensor_type: SensorType
    quantity: int = 1
    position: Optional[Tuple[float, float, float]] = None
    orientation: Optional[Tuple[float, float, float, float]] = None
    confidence: float = 1.0
    sources: List[str] = field(default_factory=list)
    specs: Optional[SensorSpec] = None


@dataclass
class RobotProfile:
    """Complete commercial robot hardware profile."""

    robot_id: str
    manufacturer: str
    model_name: str
    product_url: Optional[str] = None
    category: str = "mobile"  # mobile, aerial, humanoid, manipulator, aquatic
    sensors: Dict[str, RobotSensorEntry] = field(default_factory=dict)

    # Metadata
    discovery_sources: List[str] = field(default_factory=list)
    discovery_timestamp: float = field(default_factory=lambda: 0.0)
    verification_level: float = 1.0  # 0-1 confidence in entire profile

    def add_sensor(self, sensor_id: str, entry: RobotSensorEntry) -> None:
        """Add sensor to profile.

        Args:
            sensor_id: Unique sensor identifier
            entry: Robot sensor entry
        """
        self.sensors[sensor_id] = entry

    def get_sensor_summary(self) -> Dict[str, int]:
        """Get sensor type summary.

        Returns:
            Count of sensors by type
        """
        summary = {}

        for entry in self.sensors.values():
            type_key = entry.sensor_type.value

            summary[type_key] = summary.get(type_key, 0) + entry.quantity

        return summary

    def get_average_confidence(self) -> float:
        """Get average sensor confidence.

        Returns:
            Average confidence (0-1)
        """
        if not self.sensors:
            return 0.0

        avg_conf = sum(e.confidence for e in self.sensors.values()) / len(self.sensors)
        return avg_conf

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "robot_id": self.robot_id,
            "manufacturer": self.manufacturer,
            "model_name": self.model_name,
            "category": self.category,
            "sensor_summary": self.get_sensor_summary(),
            "verification_level": self.verification_level,
            "average_confidence": self.get_average_confidence(),
            "discovery_sources": self.discovery_sources,
        }


class RobotHardwareKnowledgeBase:
    """Manages robot hardware profiles and sensor configurations.

    Continuously expandable database of commercial robot sensor specs.
    """

    # Default commercial robot profiles
    DEFAULT_PROFILES = {
        "boston_dynamics_spot": RobotProfile(
            robot_id="boston_dynamics_spot",
            manufacturer="Boston Dynamics",
            model_name="Spot",
            category="quadruped",
            discovery_sources=["manufacturer_docs", "official_specs"],
            verification_level=0.95,
        ),
        "unitree_go2": RobotProfile(
            robot_id="unitree_go2",
            manufacturer="Unitree",
            model_name="Go2",
            category="quadruped",
            discovery_sources=["manufacturer_docs"],
            verification_level=0.92,
        ),
        "clearpath_husky": RobotProfile(
            robot_id="clearpath_husky",
            manufacturer="Clearpath",
            model_name="Husky",
            category="mobile",
            discovery_sources=["manufacturer_docs", "ros_package"],
            verification_level=0.95,
        ),
        "dji_m300_rtk": RobotProfile(
            robot_id="dji_m300_rtk",
            manufacturer="DJI",
            model_name="Matrice 300 RTK",
            category="aerial",
            discovery_sources=["manufacturer_docs"],
            verification_level=0.98,
        ),
        "ur5e": RobotProfile(
            robot_id="ur5e",
            manufacturer="Universal Robots",
            model_name="UR5e",
            category="manipulator",
            discovery_sources=["manufacturer_docs", "ros_package"],
            verification_level=0.96,
        ),
        "kinova_gen3": RobotProfile(
            robot_id="kinova_gen3",
            manufacturer="Kinova",
            model_name="Gen3",
            category="manipulator",
            discovery_sources=["manufacturer_docs"],
            verification_level=0.94,
        ),
    }

    def __init__(self):
        """Initialize knowledge base."""
        self._profiles: Dict[str, RobotProfile] = dict(self.DEFAULT_PROFILES)
        self._setup_default_sensors()

    def _setup_default_sensors(self) -> None:
        """Setup sensors for default profiles."""
        # Spot sensors
        spot = self._profiles["boston_dynamics_spot"]
        spot.add_sensor("rgb_0", RobotSensorEntry(
            sensor_type=SensorType.RGB_CAMERA,
            quantity=5,
            confidence=0.95,
            sources=["manufacturer_spec"],
        ))
        spot.add_sensor("stereo", RobotSensorEntry(
            sensor_type=SensorType.STEREO_CAMERA,
            quantity=1,
            confidence=0.95,
            sources=["manufacturer_spec"],
        ))
        spot.add_sensor("imu", RobotSensorEntry(
            sensor_type=SensorType.IMU,
            quantity=1,
            confidence=1.0,
            sources=["manufacturer_spec"],
        ))

        # Husky sensors
        husky = self._profiles["clearpath_husky"]
        husky.add_sensor("rgb", RobotSensorEntry(
            sensor_type=SensorType.RGB_CAMERA,
            quantity=2,
            confidence=0.9,
            sources=["manufacturer_spec", "ros_package"],
        ))
        husky.add_sensor("lidar", RobotSensorEntry(
            sensor_type=SensorType.VELODYNE_LIDAR,
            quantity=1,
            confidence=0.85,
            sources=["typical_configuration"],
        ))
        husky.add_sensor("imu", RobotSensorEntry(
            sensor_type=SensorType.IMU,
            quantity=1,
            confidence=1.0,
            sources=["manufacturer_spec"],
        ))
        husky.add_sensor("gps", RobotSensorEntry(
            sensor_type=SensorType.GPS,
            quantity=1,
            confidence=0.8,
            sources=["typical_configuration"],
        ))

    def add_profile(self, profile: RobotProfile) -> None:
        """Add or update robot profile.

        Args:
            profile: Robot profile to add
        """
        self._profiles[profile.robot_id] = profile
        logger.info(f"Added/updated robot profile: {profile.manufacturer} {profile.model_name}")

    def get_profile(self, robot_id: str) -> Optional[RobotProfile]:
        """Get robot profile by ID.

        Args:
            robot_id: Robot identifier

        Returns:
            Robot profile or None
        """
        return self._profiles.get(robot_id)

    def search_by_manufacturer(self, manufacturer: str) -> List[RobotProfile]:
        """Search profiles by manufacturer.

        Args:
            manufacturer: Manufacturer name

        Returns:
            Matching profiles
        """
        return [
            p for p in self._profiles.values()
            if p.manufacturer.lower() == manufacturer.lower()
        ]

    def search_by_category(self, category: str) -> List[RobotProfile]:
        """Search profiles by robot category.

        Args:
            category: Robot category

        Returns:
            Matching profiles
        """
        return [
            p for p in self._profiles.values()
            if p.category.lower() == category.lower()
        ]

    def list_all_robots(self) -> List[str]:
        """List all known robot IDs.

        Returns:
            Robot identifiers
        """
        return list(self._profiles.keys())

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Statistics dictionary
        """
        profiles = list(self._profiles.values())

        return {
            "total_robots": len(profiles),
            "manufacturers": len(set(p.manufacturer for p in profiles)),
            "categories": list(set(p.category for p in profiles)),
            "avg_verification": sum(p.verification_level for p in profiles) / len(profiles) if profiles else 0,
            "total_sensor_types": len(set(
                entry.sensor_type
                for p in profiles
                for entry in p.sensors.values()
            )),
        }


class DocumentationParser:
    """AI-powered parser for extracting sensor information from documentation.

    Analyzes manufacturer specs, datasheets, ROS packages, and documentation
    to automatically identify sensor configurations.
    """

    def __init__(self):
        """Initialize parser."""
        self._sensor_keywords = self._build_sensor_keywords()

    def _build_sensor_keywords(self) -> Dict[SensorType, List[str]]:
        """Build sensor detection keywords.

        Returns:
            Mapping of sensor types to detection keywords
        """
        return {
            SensorType.RGB_CAMERA: ["rgb camera", "color camera", "monocular", "camera"],
            SensorType.STEREO_CAMERA: ["stereo camera", "stereo vision"],
            SensorType.THERMAL_CAMERA: ["thermal camera", "thermal imaging", "infrared"],
            SensorType.VELODYNE_LIDAR: ["velodyne", "lidar", "3d lidar", "point cloud"],
            SensorType.LIDAR_2D: ["2d lidar", "2d scan", "laser scanner"],
            SensorType.IMU: ["imu", "inertial measurement", "accelerometer", "gyroscope"],
            SensorType.GPS: ["gps", "gnss", "global navigation", "position"],
            SensorType.FMCW_RADAR: ["radar", "fmcw", "mmwave"],
            SensorType.FORCE_TORQUE_SENSOR: ["force/torque", "ft sensor", "wrist sensor"],
            SensorType.WHEEL_ENCODER: ["encoder", "odometry", "wheel speed"],
        }

    def parse_text(self, text: str) -> Dict[SensorType, int]:
        """Parse text to extract sensors.

        Args:
            text: Documentation text

        Returns:
            Sensor types and counts
        """
        detected_sensors: Dict[SensorType, int] = {}
        text_lower = text.lower()

        for sensor_type, keywords in self._sensor_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    count = detected_sensors.get(sensor_type, 0) + 1
                    detected_sensors[sensor_type] = count
                    break

        return detected_sensors

    def parse_specifications(self, specs_text: str) -> Dict[str, Any]:
        """Parse technical specifications section.

        Args:
            specs_text: Specifications text

        Returns:
            Extracted specifications
        """
        # Mock parsing
        return {
            "sensors_detected": self.parse_text(specs_text),
            "confidence": 0.75,
            "raw_text_length": len(specs_text),
        }

    def verify_with_multiple_sources(
        self, sources: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cross-reference sensor info from multiple sources.

        Args:
            sources: Source documents with sensor info

        Returns:
            Consolidated sensor list with confidence scores
        """
        consolidated = {}

        for source_name, source_data in sources.items():
            detected = source_data.get("sensors_detected", {})

            for sensor_type, count in detected.items():
                key = sensor_type.value

                if key not in consolidated:
                    consolidated[key] = {
                        "type": sensor_type,
                        "quantity": count,
                        "sources": [],
                        "confidence": 0.5,
                    }

                consolidated[key]["sources"].append(source_name)

        # Calculate confidence based on source agreement
        for sensor_key in consolidated:
            num_sources = len(consolidated[sensor_key]["sources"])

            # More sources = higher confidence
            confidence = min(num_sources * 0.3, 1.0)
            consolidated[sensor_key]["confidence"] = confidence

        return consolidated


class AutomaticRobotDiscovery:
    """Automatic discovery system for unknown commercial robots.

    Handles Phase 1-4 of unknown robot discovery:
    1. Web discovery
    2. Documentation parsing
    3. Confidence validation
    4. User approval
    """

    def __init__(
        self,
        knowledge_base: RobotHardwareKnowledgeBase,
        parser: DocumentationParser,
    ):
        """Initialize discovery system.

        Args:
            knowledge_base: Robot hardware knowledge base
            parser: Documentation parser
        """
        self._kb = knowledge_base
        self._parser = parser

    def discover_known_robot(self, robot_id: str) -> Optional[RobotProfile]:
        """Discover known robot from knowledge base.

        Args:
            robot_id: Robot identifier

        Returns:
            Robot profile or None if not found
        """
        profile = self._kb.get_profile(robot_id)

        if profile:
            logger.info(f"Found known robot: {profile.manufacturer} {profile.model_name}")

        return profile

    def discover_by_model_name(
        self, manufacturer: str, model_name: str
    ) -> Optional[RobotProfile]:
        """Discover robot by manufacturer and model name.

        Args:
            manufacturer: Manufacturer name
            model_name: Robot model name

        Returns:
            Robot profile or None
        """
        for profile in self._kb.search_by_manufacturer(manufacturer):
            if profile.model_name.lower() == model_name.lower():
                return profile

        return None

    def generate_candidate_profile(
        self,
        robot_id: str,
        manufacturer: str,
        model_name: str,
        category: str = "mobile",
    ) -> RobotProfile:
        """Generate candidate profile for unknown robot.

        Args:
            robot_id: Robot identifier
            manufacturer: Manufacturer name
            model_name: Model name
            category: Robot category

        Returns:
            Candidate profile awaiting verification
        """
        profile = RobotProfile(
            robot_id=robot_id,
            manufacturer=manufacturer,
            model_name=model_name,
            category=category,
            verification_level=0.0,  # Unverified
            discovery_sources=["candidate_profile"],
        )

        logger.info(f"Generated candidate profile for {manufacturer} {model_name}")
        return profile

    def present_approval_dialog(self, profile: RobotProfile) -> Dict[str, Any]:
        """Generate user approval dialog data.

        Args:
            profile: Robot profile to approve

        Returns:
            Dialog data for user review
        """
        sensor_summary = profile.get_sensor_summary()

        # Categorize by confidence
        high_confidence = [
            (sensor_id, entry)
            for sensor_id, entry in profile.sensors.items()
            if entry.confidence >= 0.85
        ]

        low_confidence = [
            (sensor_id, entry)
            for sensor_id, entry in profile.sensors.items()
            if entry.confidence < 0.85
        ]

        return {
            "robot": {
                "manufacturer": profile.manufacturer,
                "model": profile.model_name,
                "category": profile.category,
            },
            "detected_sensors": {
                "high_confidence": [
                    {
                        "sensor": entry.sensor_type.value,
                        "quantity": entry.quantity,
                        "confidence": entry.confidence,
                        "sources": entry.sources,
                    }
                    for _, entry in high_confidence
                ],
                "low_confidence": [
                    {
                        "sensor": entry.sensor_type.value,
                        "quantity": entry.quantity,
                        "confidence": entry.confidence,
                        "sources": entry.sources,
                    }
                    for _, entry in low_confidence
                ],
            },
            "verification_level": profile.verification_level,
            "action_required": len(low_confidence) > 0,
        }

    def approve_and_store_profile(self, profile: RobotProfile) -> None:
        """Approve profile and store in knowledge base.

        Args:
            profile: Approved profile
        """
        profile.verification_level = max(profile.verification_level, 0.75)
        self._kb.add_profile(profile)

        logger.info(
            f"Stored robot profile: {profile.manufacturer} {profile.model_name} "
            f"(verification: {profile.verification_level:.0%})"
        )
