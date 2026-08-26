"""Execution Log Converter - Convert ROS bag to Narrative scenarios.

Transforms real robot execution logs into narrative scenarios for
replay, analysis, and simulation validation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.narratives.narrative_definitions import (
    Narrative,
    NarrativeType,
    NarrativeEntity,
    NarrativeGoal,
    NarrativeEvent,
    NarrativeEventType,
    NarrativeSequence,
    NarrativeConstraint,
    AgentRole,
)
from src.realtoism.rosbag_parser import (
    RosBagParser,
    RosPose,
    RosImage,
    RosPointCloud,
)
from src.realtoism.trajectory_extractor import (
    TrajectoryExtractor,
    TrajectorySegment,
    TrajectoryMetrics,
)

logger = logging.getLogger(__name__)


class ExecutionLogConverter:
    """Converts ROS bag execution logs to narrative scenarios.

    Enables:
    - Replay of real robot executions in simulation
    - Analysis of real vs simulated behavior
    - Extraction of typical behaviors for curriculum learning
    """

    def __init__(self):
        """Initialize converter."""
        self._parser = RosBagParser()
        self._extractor = TrajectoryExtractor()

    def convert_rosbag_to_narrative(
        self,
        bag_path: str,
        robot_name: str = "robot_0",
        mission_type: str = "replay",
    ) -> Narrative:
        """Convert ROS bag to narrative scenario.

        Args:
            bag_path: Path to .bag file
            robot_name: Name of robot being recorded
            mission_type: Type of mission (replay, analysis, training)

        Returns:
            Narrative scenario
        """
        logger.info(f"Converting ROS bag to narrative: {bag_path}")

        # Parse bag file
        metadata = self._parser.parse_rosbag(bag_path)

        if not metadata:
            raise ValueError(f"Failed to parse bag file: {bag_path}")

        # Extract trajectory
        poses = self._parser.get_poses()

        if not poses:
            raise ValueError(f"No pose data in bag file: {bag_path}")

        segments, metrics = self._extractor.extract_trajectory(poses)

        # Create narrative
        narrative = self._create_narrative_from_execution(
            robot_name=robot_name,
            metadata=metadata,
            poses=poses,
            segments=segments,
            metrics=metrics,
            mission_type=mission_type,
        )

        logger.info(f"Converted to narrative: {narrative.title} " +
                   f"({len(narrative.entities)} entities, {len(narrative.sequences)} sequences)")

        return narrative

    def _create_narrative_from_execution(
        self,
        robot_name: str,
        metadata: Any,
        poses: List[RosPose],
        segments: List[TrajectorySegment],
        metrics: Any,
        mission_type: str,
    ) -> Narrative:
        """Create narrative from execution data.

        Args:
            robot_name: Robot identifier
            metadata: Bag metadata
            poses: Robot poses
            segments: Trajectory segments
            metrics: Trajectory metrics
            mission_type: Type of mission

        Returns:
            Narrative
        """
        narrative_type = self._infer_narrative_type(mission_type, metrics)

        narrative = Narrative(
            narrative_id=f"replay_{metadata.filename}",
            title=f"Real Execution: {robot_name}",
            description=f"Replay of real robot execution from {metadata.filename}",
            narrative_type=narrative_type,
            difficulty_level=self._compute_difficulty(metrics),
            environment_type="real_world",
            time_of_day="unknown",
        )

        # Add robot entity
        if poses:
            robot_entity = NarrativeEntity(
                entity_id=robot_name,
                entity_type="robot",
                name=robot_name,
                role=AgentRole.PROTAGONIST,
                initial_position=poses[0].position,
                initial_orientation=poses[0].orientation,
                description=f"Real {robot_name} from execution",
                sensor_suite=self._infer_sensor_suite(metadata),
            )

            narrative.add_entity(robot_entity)

        # Infer goal from trajectory
        if segments:
            final_segment = segments[-1]
            goal = NarrativeGoal(
                goal_id="goal_0",
                description=f"Execute recorded trajectory",
                goal_type="follow_path",
                target={
                    "start_position": segments[0].start_position,
                    "end_position": final_segment.end_position,
                    "total_distance": metrics.total_distance_m,
                },
                priority=1.0,
                time_limit_sec=metrics.total_time_sec * 1.5,
                success_criteria={
                    "path_followed": True,
                    "end_position_reached": True,
                },
            )

            narrative.add_goal(goal)

        # Create sequence from segments
        sequence = self._create_sequence_from_segments(segments, poses)
        narrative.add_sequence(sequence)

        # Add execution constraints (actual observed behavior)
        constraints = self._create_constraints_from_metrics(metrics)
        for constraint in constraints:
            narrative.add_constraint(constraint)

        return narrative

    def _create_sequence_from_segments(
        self,
        segments: List[TrajectorySegment],
        poses: List[RosPose],
    ) -> NarrativeSequence:
        """Create narrative sequence from trajectory segments.

        Args:
            segments: Trajectory segments
            poses: Robot poses

        Returns:
            NarrativeSequence
        """
        sequence = NarrativeSequence(
            sequence_id="seq_0",
            name="Recorded Execution",
            description="Sequence of recorded robot movements",
        )

        # Add start event
        if poses:
            start_event = NarrativeEvent(
                event_id="start",
                event_type=NarrativeEventType.AGENT_ACTION,
                timestamp_sec=poses[0].timestamp_sec,
                description=f"Start execution at {poses[0].position}",
                triggering_entity="robot_0",
                parameters={
                    "action": "start_execution",
                    "position": poses[0].position,
                },
            )

            sequence.add_event(start_event)

        # Add waypoint events
        for seg_id, segment in enumerate(segments):
            # Movement event
            move_event = NarrativeEvent(
                event_id=f"move_{seg_id}",
                event_type=NarrativeEventType.AGENT_ACTION,
                timestamp_sec=segment.start_time_sec,
                description=f"Move segment {seg_id}: {segment.distance_m:.1f}m in {segment.duration_sec:.1f}s",
                triggering_entity="robot_0",
                affected_entities=["robot_0"],
                parameters={
                    "action": "navigate",
                    "start_position": segment.start_position,
                    "end_position": segment.end_position,
                    "distance": segment.distance_m,
                    "duration": segment.duration_sec,
                    "velocity": segment.avg_velocity,
                    "smoothness": segment.smoothness,
                },
                confidence=0.95,
            )

            sequence.add_event(move_event)

            # Stop event if applicable
            if segment.avg_velocity < 0.1:
                stop_event = NarrativeEvent(
                    event_id=f"stop_{seg_id}",
                    event_type=NarrativeEventType.AGENT_ACTION,
                    timestamp_sec=segment.end_time_sec,
                    description=f"Stop at {segment.end_position}",
                    triggering_entity="robot_0",
                    parameters={"action": "stop", "position": segment.end_position},
                    confidence=0.95,
                )

                sequence.add_event(stop_event)

        # Add completion event
        if poses:
            complete_event = NarrativeEvent(
                event_id="complete",
                event_type=NarrativeEventType.OUTCOME,
                timestamp_sec=poses[-1].timestamp_sec,
                description="Execution completed",
                triggering_entity="robot_0",
                parameters={"outcome": "completed"},
                confidence=1.0,
            )

            sequence.add_event(complete_event)

        return sequence

    def _create_constraints_from_metrics(self, metrics: Any) -> List[NarrativeConstraint]:
        """Create constraints from observed metrics.

        Args:
            metrics: Trajectory metrics

        Returns:
            List of constraints
        """
        constraints = []

        # Velocity constraint
        if metrics.max_velocity > 0:
            constraint = NarrativeConstraint(
                constraint_id="velocity",
                description=f"Robot velocity should match recorded execution",
                constraint_type="realism",
                rule=f"velocity <= {metrics.max_velocity * 1.1:.2f} m/s",
                violation_penalty=-0.3,
            )

            constraints.append(constraint)

        # Smoothness constraint
        if metrics.path_smoothness > 0:
            constraint = NarrativeConstraint(
                constraint_id="smoothness",
                description=f"Path should be reasonably smooth (observed: {metrics.path_smoothness:.2f})",
                constraint_type="realism",
                rule=f"smoothness >= {metrics.path_smoothness * 0.8:.2f}",
                violation_penalty=-0.2,
            )

            constraints.append(constraint)

        return constraints

    def _infer_narrative_type(self, mission_type: str, metrics: Any) -> NarrativeType:
        """Infer narrative type from execution characteristics.

        Args:
            mission_type: User-specified mission type
            metrics: Trajectory metrics

        Returns:
            NarrativeType
        """
        if mission_type == "delivery":
            return NarrativeType.DELIVERY_MISSION
        elif mission_type == "inspection":
            return NarrativeType.INSPECTION
        elif mission_type == "exploration":
            return NarrativeType.EXPLORATION
        elif metrics.stop_count > 3:
            return NarrativeType.INSPECTION
        else:
            return NarrativeType.CUSTOM

    def _infer_sensor_suite(self, metadata: Any) -> str:
        """Infer sensor suite from bag topics.

        Args:
            metadata: Bag metadata

        Returns:
            Sensor suite name
        """
        topics = metadata.topics.keys() if hasattr(metadata, 'topics') else []
        topics_str = str(topics).lower()

        if "lidar" in topics_str and "camera" in topics_str:
            return "mobile"
        elif "camera" in topics_str:
            return "mobile"
        elif "lidar" in topics_str:
            return "mobile"
        else:
            return "mobile"

    def _compute_difficulty(self, metrics: Any) -> float:
        """Compute difficulty level from execution metrics.

        Args:
            metrics: Trajectory metrics

        Returns:
            Difficulty 0-1
        """
        # Difficulty based on distance, time, and smoothness
        distance_difficulty = min(metrics.total_distance_m / 100.0, 0.3)
        smoothness_difficulty = (1.0 - metrics.path_smoothness) * 0.3
        time_difficulty = min(metrics.total_time_sec / 600.0, 0.2)

        return min(distance_difficulty + smoothness_difficulty + time_difficulty, 1.0)
