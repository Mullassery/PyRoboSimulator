"""Tests for Real-to-Sim Bridge Engine - Phase 7."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.src.realtoism import (
    RosBagParser,
    RosPose,
    RosImage,
    RosPointCloud,
    RosImu,
    RosGps,
    TrajectoryExtractor,
    TrajectorySegment,
    TrajectoryMetrics,
    Waypoint,
    ExecutionLogConverter,
    SensorReplayEngine,
    SensorReplayState,
    SimRealValidator,
    ExecutionMetrics,
    ValidationMetric,
)


class TestRosBagParser:
    """Test ROS bag parser."""

    def test_parser_initialization(self):
        """Test parser creation."""
        parser = RosBagParser()

        assert parser.get_poses() == []
        assert parser.get_images() == []

    def test_ros_pose_creation(self):
        """Test creating ROS pose."""
        pose = RosPose(
            timestamp_sec=1.0,
            frame_id="odom",
            position=(1.0, 2.0, 3.0),
            orientation=(0.0, 0.0, 0.0, 1.0),
            velocity=(0.5, 0.1, 0.0),
        )

        assert pose.timestamp_sec == 1.0
        assert pose.position == (1.0, 2.0, 3.0)
        assert pose.velocity == (0.5, 0.1, 0.0)

    def test_ros_image_creation(self):
        """Test creating ROS image."""
        image = RosImage(
            timestamp_sec=1.0,
            frame_id="camera",
            camera_name="front_camera",
            width=1920,
            height=1080,
            encoding="rgb8",
        )

        assert image.camera_name == "front_camera"
        assert image.width == 1920

    def test_ros_point_cloud_creation(self):
        """Test creating ROS point cloud."""
        cloud = RosPointCloud(
            timestamp_sec=1.0,
            frame_id="lidar",
            lidar_name="velodyne",
            point_count=100000,
            fields=["x", "y", "z", "intensity"],
        )

        assert cloud.lidar_name == "velodyne"
        assert cloud.point_count == 100000

    def test_ros_imu_creation(self):
        """Test creating ROS IMU."""
        imu = RosImu(
            timestamp_sec=1.0,
            frame_id="imu",
            imu_name="imu_0",
            linear_acceleration=(0.1, 0.2, 9.8),
            angular_velocity=(0.01, 0.02, 0.03),
        )

        assert imu.imu_name == "imu_0"
        assert imu.linear_acceleration == (0.1, 0.2, 9.8)

    def test_ros_gps_creation(self):
        """Test creating ROS GPS."""
        gps = RosGps(
            timestamp_sec=1.0,
            frame_id="gps",
            gps_name="gps_0",
            latitude=37.7749,
            longitude=-122.4194,
            altitude=10.0,
        )

        assert gps.latitude == 37.7749
        assert gps.gps_quality == 0

    def test_mock_parse_creates_data(self):
        """Test mock parser generates synthetic data."""
        parser = RosBagParser()
        metadata = parser._mock_parse("test.bag")

        assert metadata is not None
        assert metadata.duration_sec > 0
        assert len(parser.get_poses()) > 0


class TestTrajectoryExtractor:
    """Test trajectory extractor."""

    def test_extractor_initialization(self):
        """Test extractor creation."""
        extractor = TrajectoryExtractor()

        assert extractor._velocity_threshold == 0.01

    def test_compute_velocity_stationary(self):
        """Test velocity computation for stationary robot."""
        extractor = TrajectoryExtractor()

        poses = [
            RosPose(0.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(1.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(2.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ]

        poses_with_vel = extractor._compute_velocities(poses)

        assert len(poses_with_vel) == 3
        assert poses_with_vel[1][1] == 0.0  # No movement
        assert poses_with_vel[2][1] == 0.0

    def test_compute_velocity_moving(self):
        """Test velocity computation for moving robot."""
        extractor = TrajectoryExtractor()

        poses = [
            RosPose(0.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(1.0, "odom", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(2.0, "odom", (2.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ]

        poses_with_vel = extractor._compute_velocities(poses)

        assert poses_with_vel[1][1] == pytest.approx(1.0)  # 1m in 1s
        assert poses_with_vel[2][1] == pytest.approx(1.0)

    def test_extract_simple_trajectory(self):
        """Test extracting simple trajectory."""
        extractor = TrajectoryExtractor()

        poses = [
            RosPose(0.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(1.0, "odom", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(2.0, "odom", (2.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ]

        segments, metrics = extractor.extract_trajectory(poses)

        assert len(segments) > 0
        assert metrics.total_distance_m > 0
        assert metrics.total_time_sec == 2.0

    def test_trajectory_metrics(self):
        """Test trajectory metrics computation."""
        extractor = TrajectoryExtractor()

        poses = [
            RosPose(0.0, "odom", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(1.0, "odom", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(2.0, "odom", (2.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RosPose(3.0, "odom", (3.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ]

        segments, metrics = extractor.extract_trajectory(poses)

        assert metrics.total_time_sec == 3.0
        assert metrics.total_distance_m == 3.0
        assert metrics.avg_velocity == pytest.approx(1.0)
        assert metrics.segment_count > 0


class TestExecutionLogConverter:
    """Test execution log converter."""

    def test_converter_initialization(self):
        """Test converter creation."""
        converter = ExecutionLogConverter()

        assert converter._parser is not None
        assert converter._extractor is not None

    def test_infer_narrative_type(self):
        """Test narrative type inference."""
        converter = ExecutionLogConverter()
        metrics = TrajectoryMetrics(stop_count=5)

        narrative_type = converter._infer_narrative_type("delivery", metrics)

        from backend.src.narratives import NarrativeType
        assert narrative_type == NarrativeType.DELIVERY_MISSION

    def test_infer_sensor_suite(self):
        """Test sensor suite inference."""
        converter = ExecutionLogConverter()

        from backend.src.realtoism import RosBagMetadata
        metadata = RosBagMetadata(
            filename="test.bag",
            duration_sec=10.0,
            message_count=1000,
            start_time_sec=0.0,
            end_time_sec=10.0,
            topics={"/lidar": 100, "/camera": 30},
        )

        sensor_suite = converter._infer_sensor_suite(metadata)

        assert sensor_suite == "mobile"

    def test_compute_difficulty(self):
        """Test difficulty computation."""
        converter = ExecutionLogConverter()
        metrics = TrajectoryMetrics(
            total_distance_m=50.0,
            total_time_sec=100.0,
            path_smoothness=0.8,
        )

        difficulty = converter._compute_difficulty(metrics)

        assert 0.0 <= difficulty <= 1.0


class TestSensorReplayEngine:
    """Test sensor replay engine."""

    def test_replay_initialization(self):
        """Test replay engine creation."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        assert engine._state.is_playing is False
        assert engine._state.playback_speed == 1.0

    def test_start_stop_replay(self):
        """Test replay start/stop."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        engine.start_replay()
        assert engine._state.is_playing is True

        engine.stop_replay()
        assert engine._state.is_playing is False

    def test_pause_resume_replay(self):
        """Test replay pause/resume."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        engine.start_replay()
        engine.pause_replay()
        assert engine._state.is_playing is False

        engine.resume_replay()
        assert engine._state.is_playing is True

    def test_playback_speed(self):
        """Test setting playback speed."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        engine.set_playback_speed(2.0)
        assert engine._state.playback_speed == 2.0

        engine.set_playback_speed(0.5)
        assert engine._state.playback_speed == 0.5

    def test_seek_to_time(self):
        """Test seeking to time."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        engine.seek_to_time(5.0)
        assert engine._state.current_time_sec == 5.0

    def test_register_callback(self):
        """Test callback registration."""
        parser = RosBagParser()
        engine = SensorReplayEngine(parser)

        callback = Mock()
        engine.register_callback("image_frame", callback)

        assert callback in engine._callbacks["image_frame"]

    def test_sensor_summary(self):
        """Test sensor summary."""
        parser = RosBagParser()
        parser._mock_parse("test.bag")
        engine = SensorReplayEngine(parser)

        summary = engine.get_sensor_summary()

        assert "images" in summary
        assert "point_clouds" in summary


class TestSimRealValidator:
    """Test sim/real validator."""

    def test_validator_initialization(self):
        """Test validator creation."""
        validator = SimRealValidator()

        assert validator._distance_tolerance == 1.0
        assert validator._velocity_tolerance == 10.0

    def test_validate_matching_execution(self):
        """Test validating matching real and sim execution."""
        validator = SimRealValidator()

        real_metrics = ExecutionMetrics(
            execution_id="real_1",
            execution_type="real",
            total_distance_m=10.0,
            total_time_sec=10.0,
            avg_velocity=1.0,
            max_velocity=2.0,
            path_smoothness=0.9,
        )

        sim_metrics = ExecutionMetrics(
            execution_id="sim_1",
            execution_type="simulated",
            total_distance_m=10.0,
            total_time_sec=10.0,
            avg_velocity=1.0,
            max_velocity=2.0,
            path_smoothness=0.9,
        )

        result = validator.validate_execution(real_metrics, sim_metrics)

        assert result.is_valid
        assert result.overall_similarity > 0.8

    def test_validate_divergent_execution(self):
        """Test validating divergent real and sim execution."""
        validator = SimRealValidator()

        real_metrics = ExecutionMetrics(
            execution_id="real_1",
            execution_type="real",
            total_distance_m=10.0,
            total_time_sec=10.0,
            avg_velocity=1.0,
            max_velocity=2.0,
        )

        sim_metrics = ExecutionMetrics(
            execution_id="sim_1",
            execution_type="simulated",
            total_distance_m=15.0,  # Different
            total_time_sec=20.0,   # Different
            avg_velocity=0.75,     # Different
            max_velocity=1.5,
        )

        result = validator.validate_execution(real_metrics, sim_metrics)

        assert not result.is_valid
        assert len(result.discrepancies) > 0
        assert len(result.recommendations) > 0

    def test_compare_metric_absolute(self):
        """Test comparing metric with absolute tolerance."""
        validator = SimRealValidator()

        metric = validator._compare_metric(
            "distance",
            real_value=10.0,
            sim_value=10.5,
            tolerance=1.0,
            is_absolute=True,
        )

        assert metric.is_valid
        assert metric.absolute_error == pytest.approx(0.5)

    def test_compare_metric_percentage(self):
        """Test comparing metric with percentage tolerance."""
        validator = SimRealValidator()

        metric = validator._compare_metric(
            "velocity",
            real_value=1.0,
            sim_value=1.05,
            tolerance=10.0,
            is_absolute=False,
        )

        assert metric.is_valid
        assert metric.relative_error == pytest.approx(5.0)

    def test_sensor_data_correlation(self):
        """Test sensor data correlation computation."""
        validator = SimRealValidator()

        real_sensors = {"lidar": [1.0, 2.0, 3.0, 4.0, 5.0]}
        sim_sensors = {"lidar": [1.1, 2.1, 3.1, 4.1, 5.1]}

        correlations = validator.validate_sensor_data(real_sensors, sim_sensors)

        assert "lidar" in correlations
        assert correlations["lidar"] > 0.9  # Should be highly correlated


class TestRealToSimIntegration:
    """Integration tests for real-to-sim bridge."""

    def test_complete_realtoism_workflow(self):
        """Test complete real-to-sim workflow."""
        # Parse (mock) rosbag
        parser = RosBagParser()
        metadata = parser._mock_parse("test.bag")

        assert metadata is not None

        # Extract trajectory
        poses = parser.get_poses()
        extractor = TrajectoryExtractor()
        segments, metrics = extractor.extract_trajectory(poses)

        assert len(segments) > 0
        assert metrics.total_distance_m > 0

        # Convert to narrative
        converter = ExecutionLogConverter()
        narrative = converter._create_narrative_from_execution(
            robot_name="robot_0",
            metadata=metadata,
            poses=poses,
            segments=segments,
            metrics=metrics,
            mission_type="replay",
        )

        assert narrative is not None
        assert len(narrative.entities) > 0
        assert len(narrative.sequences) > 0

        # Replay sensors
        engine = SensorReplayEngine(parser)
        engine.start_replay()

        assert engine._state.is_playing is True

        # Validate
        validator = SimRealValidator()

        real_metrics = ExecutionMetrics(
            execution_id="real",
            execution_type="real",
            total_distance_m=metrics.total_distance_m,
            total_time_sec=metrics.total_time_sec,
            avg_velocity=metrics.avg_velocity,
            max_velocity=metrics.max_velocity,
            path_smoothness=metrics.path_smoothness,
        )

        sim_metrics = ExecutionMetrics(
            execution_id="sim",
            execution_type="simulated",
            total_distance_m=metrics.total_distance_m,
            total_time_sec=metrics.total_time_sec,
            avg_velocity=metrics.avg_velocity,
            max_velocity=metrics.max_velocity,
            path_smoothness=metrics.path_smoothness,
        )

        result = validator.validate_execution(real_metrics, sim_metrics)

        assert result.is_valid  # Should match since we're using same metrics
