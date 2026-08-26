"""Trajectory Extractor - Process raw poses into structured trajectories.

Extracts robot movement patterns from pose data:
- Trajectory segmentation
- Velocity/acceleration computation
- Path statistics (distance, duration, smoothness)
- Waypoint detection
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from math import sqrt

from src.realtoism.rosbag_parser import RosPose

logger = logging.getLogger(__name__)


@dataclass
class Waypoint:
    """Navigation waypoint along trajectory."""
    waypoint_id: str
    timestamp_sec: float
    position: Tuple[float, float, float]
    orientation: Tuple[float, float, float, float]
    velocity_magnitude: float = 0.0
    is_stopping_point: bool = False


@dataclass
class TrajectorySegment:
    """Contiguous trajectory segment."""
    segment_id: str
    start_time_sec: float
    end_time_sec: float
    start_position: Tuple[float, float, float]
    end_position: Tuple[float, float, float]
    waypoints: List[Waypoint] = field(default_factory=list)
    distance_m: float = 0.0
    duration_sec: float = 0.0
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    smoothness: float = 1.0  # 0-1, 1 = perfectly smooth


@dataclass
class TrajectoryMetrics:
    """Statistics about entire trajectory."""
    total_distance_m: float = 0.0
    total_time_sec: float = 0.0
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    avg_acceleration: float = 0.0
    max_acceleration: float = 0.0
    path_smoothness: float = 1.0  # 0-1
    stop_count: int = 0
    segment_count: int = 0


class TrajectoryExtractor:
    """Extracts and analyzes robot trajectories from pose data."""

    def __init__(self, velocity_threshold: float = 0.01, smoothness_window: int = 5):
        """Initialize extractor.

        Args:
            velocity_threshold: Velocity below this is considered stopped (m/s)
            smoothness_window: Window size for smoothness computation
        """
        self._velocity_threshold = velocity_threshold
        self._smoothness_window = smoothness_window

    def extract_trajectory(self, poses: List[RosPose]) -> Tuple[List[TrajectorySegment], TrajectoryMetrics]:
        """Extract trajectory from pose sequence.

        Args:
            poses: Ordered list of poses

        Returns:
            Tuple of (segments, metrics)
        """
        if len(poses) < 2:
            logger.warning("Need at least 2 poses to extract trajectory")
            return [], TrajectoryMetrics()

        logger.info(f"Extracting trajectory from {len(poses)} poses")

        # Compute velocities
        poses_with_velocity = self._compute_velocities(poses)

        # Detect waypoints (stopping points and direction changes)
        waypoints = self._detect_waypoints(poses_with_velocity)

        # Segment trajectory
        segments = self._segment_trajectory(poses_with_velocity, waypoints)

        # Compute metrics
        metrics = self._compute_metrics(poses_with_velocity, segments)

        logger.info(f"Extracted {len(segments)} segments, " +
                   f"total distance {metrics.total_distance_m:.1f}m, " +
                   f"avg velocity {metrics.avg_velocity:.2f}m/s")

        return segments, metrics

    def _compute_velocities(self, poses: List[RosPose]) -> List[Tuple[RosPose, float]]:
        """Compute velocity for each pose.

        Args:
            poses: Ordered list of poses

        Returns:
            List of (pose, velocity_magnitude) tuples
        """
        poses_with_vel = []

        for i, pose in enumerate(poses):
            if i == 0:
                velocity_mag = 0.0
            else:
                prev_pose = poses[i - 1]
                dt = pose.timestamp_sec - prev_pose.timestamp_sec

                if dt <= 0:
                    velocity_mag = 0.0
                else:
                    dx = pose.position[0] - prev_pose.position[0]
                    dy = pose.position[1] - prev_pose.position[1]
                    dz = pose.position[2] - prev_pose.position[2]

                    distance = sqrt(dx**2 + dy**2 + dz**2)
                    velocity_mag = distance / dt

            poses_with_vel.append((pose, velocity_mag))

        return poses_with_vel

    def _detect_waypoints(self, poses_with_velocity: List[Tuple[RosPose, float]]) -> List[Waypoint]:
        """Detect navigation waypoints from trajectory.

        Args:
            poses_with_velocity: Poses with computed velocities

        Returns:
            List of detected waypoints
        """
        waypoints = []
        waypoint_id = 0

        for i, (pose, velocity) in enumerate(poses_with_velocity):
            is_stopping = velocity < self._velocity_threshold

            # Detect waypoints at stops or direction changes
            if i == 0 or i == len(poses_with_velocity) - 1:
                is_waypoint = True
            elif is_stopping and waypoint_id > 0:
                # Stop point
                is_waypoint = True
            elif i > 0 and i < len(poses_with_velocity) - 1:
                # Check for direction change
                prev_pos = poses_with_velocity[i - 1][0].position
                curr_pos = pose.position
                next_pos = poses_with_velocity[i + 1][0].position

                # Compute angles
                dir1 = (
                    curr_pos[0] - prev_pos[0],
                    curr_pos[1] - prev_pos[1],
                    curr_pos[2] - prev_pos[2],
                )

                dir2 = (
                    next_pos[0] - curr_pos[0],
                    next_pos[1] - curr_pos[1],
                    next_pos[2] - curr_pos[2],
                )

                dot = sum(d1 * d2 for d1, d2 in zip(dir1, dir2))
                mag1 = sqrt(sum(d**2 for d in dir1))
                mag2 = sqrt(sum(d**2 for d in dir2))

                if mag1 > 0 and mag2 > 0:
                    cos_angle = dot / (mag1 * mag2)
                    # Direction change > 30 degrees
                    is_waypoint = cos_angle < 0.866
                else:
                    is_waypoint = False
            else:
                is_waypoint = False

            if is_waypoint:
                waypoint = Waypoint(
                    waypoint_id=f"wp_{waypoint_id}",
                    timestamp_sec=pose.timestamp_sec,
                    position=pose.position,
                    orientation=pose.orientation,
                    velocity_magnitude=velocity,
                    is_stopping_point=is_stopping,
                )

                waypoints.append(waypoint)
                waypoint_id += 1

        return waypoints

    def _segment_trajectory(
        self,
        poses_with_velocity: List[Tuple[RosPose, float]],
        waypoints: List[Waypoint],
    ) -> List[TrajectorySegment]:
        """Segment trajectory at waypoints.

        Args:
            poses_with_velocity: Poses with velocities
            waypoints: Detected waypoints

        Returns:
            List of trajectory segments
        """
        segments = []

        if len(waypoints) < 2:
            # Single segment
            if len(poses_with_velocity) > 0:
                poses = [p for p, _ in poses_with_velocity]
                segment = self._create_segment(
                    segment_id="seg_0",
                    poses=poses,
                    poses_with_velocity=poses_with_velocity,
                )
                segments.append(segment)
        else:
            # Segment between waypoints
            for seg_id in range(len(waypoints) - 1):
                wp1 = waypoints[seg_id]
                wp2 = waypoints[seg_id + 1]

                # Find poses in this segment
                segment_poses = [
                    (p, v) for p, v in poses_with_velocity
                    if wp1.timestamp_sec <= p.timestamp_sec <= wp2.timestamp_sec
                ]

                if segment_poses:
                    poses = [p for p, _ in segment_poses]
                    segment = self._create_segment(
                        segment_id=f"seg_{seg_id}",
                        poses=poses,
                        poses_with_velocity=segment_poses,
                    )
                    segments.append(segment)

        return segments

    def _create_segment(
        self,
        segment_id: str,
        poses: List[RosPose],
        poses_with_velocity: List[Tuple[RosPose, float]],
    ) -> TrajectorySegment:
        """Create trajectory segment from poses.

        Args:
            segment_id: Segment identifier
            poses: Ordered poses in segment
            poses_with_velocity: Poses with velocity data

        Returns:
            TrajectorySegment
        """
        if len(poses) < 1:
            return TrajectorySegment(
                segment_id=segment_id,
                start_time_sec=0.0,
                end_time_sec=0.0,
                start_position=(0.0, 0.0, 0.0),
                end_position=(0.0, 0.0, 0.0),
            )

        # Compute distance
        total_distance = 0.0
        for i in range(1, len(poses)):
            p1 = poses[i - 1].position
            p2 = poses[i].position
            dist = sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
            total_distance += dist

        duration = poses[-1].timestamp_sec - poses[0].timestamp_sec
        avg_velocity = total_distance / duration if duration > 0 else 0.0

        # Compute smoothness (normalized variance in acceleration)
        accelerations = []
        for i in range(1, len(poses_with_velocity) - 1):
            p_prev, v_prev = poses_with_velocity[i - 1]
            p_curr, v_curr = poses_with_velocity[i]
            p_next, v_next = poses_with_velocity[i + 1]

            dt1 = p_curr.timestamp_sec - p_prev.timestamp_sec
            dt2 = p_next.timestamp_sec - p_curr.timestamp_sec

            if dt1 > 0 and dt2 > 0:
                a = (v_next - v_prev) / (dt1 + dt2)
                accelerations.append(abs(a))

        if accelerations:
            avg_accel = sum(accelerations) / len(accelerations)
            variance = sum((a - avg_accel)**2 for a in accelerations) / len(accelerations)
            # Smoothness: lower acceleration variance = smoother
            smoothness = 1.0 / (1.0 + variance)
        else:
            smoothness = 1.0

        max_velocity = max((v for _, v in poses_with_velocity), default=0.0)

        return TrajectorySegment(
            segment_id=segment_id,
            start_time_sec=poses[0].timestamp_sec,
            end_time_sec=poses[-1].timestamp_sec,
            start_position=poses[0].position,
            end_position=poses[-1].position,
            waypoints=[],
            distance_m=total_distance,
            duration_sec=duration,
            avg_velocity=avg_velocity,
            max_velocity=max_velocity,
            smoothness=smoothness,
        )

    def _compute_metrics(
        self,
        poses_with_velocity: List[Tuple[RosPose, float]],
        segments: List[TrajectorySegment],
    ) -> TrajectoryMetrics:
        """Compute overall trajectory metrics.

        Args:
            poses_with_velocity: Poses with velocities
            segments: Trajectory segments

        Returns:
            TrajectoryMetrics
        """
        if not poses_with_velocity:
            return TrajectoryMetrics()

        total_distance = sum(seg.distance_m for seg in segments)
        total_time = poses_with_velocity[-1][0].timestamp_sec - poses_with_velocity[0][0].timestamp_sec

        velocities = [v for _, v in poses_with_velocity]
        max_velocity = max(velocities, default=0.0)
        avg_velocity = total_distance / total_time if total_time > 0 else 0.0

        # Compute acceleration statistics
        accelerations = []
        for i in range(1, len(poses_with_velocity) - 1):
            _, v_prev = poses_with_velocity[i - 1]
            p_curr, v_curr = poses_with_velocity[i]
            _, v_next = poses_with_velocity[i + 1]

            dt_prev = poses_with_velocity[i][0].timestamp_sec - poses_with_velocity[i - 1][0].timestamp_sec
            dt_next = poses_with_velocity[i + 1][0].timestamp_sec - poses_with_velocity[i][0].timestamp_sec

            if dt_prev > 0 and dt_next > 0:
                a = (v_next - v_prev) / (dt_prev + dt_next)
                accelerations.append(abs(a))

        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0.0
        max_acceleration = max(accelerations, default=0.0)

        stop_count = sum(1 for seg in segments if seg.end_position != seg.start_position and seg.avg_velocity < 0.1)

        # Path smoothness: average of segment smoothness
        avg_smoothness = sum(seg.smoothness for seg in segments) / len(segments) if segments else 1.0

        return TrajectoryMetrics(
            total_distance_m=total_distance,
            total_time_sec=total_time,
            avg_velocity=avg_velocity,
            max_velocity=max_velocity,
            avg_acceleration=avg_acceleration,
            max_acceleration=max_acceleration,
            path_smoothness=avg_smoothness,
            stop_count=stop_count,
            segment_count=len(segments),
        )
