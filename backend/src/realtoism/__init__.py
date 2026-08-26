"""Real-to-Sim Bridge - Phase 7.

Converts real robot execution logs to simulation scenarios and validates sim/real equivalence.
"""

from src.realtoism.rosbag_parser import (
    RosBagParser,
    RosBagMetadata,
    RosMessage,
    RosPose,
    RosImage,
    RosPointCloud,
    RosImu,
    RosGps,
)
from src.realtoism.trajectory_extractor import (
    TrajectoryExtractor,
    TrajectorySegment,
    TrajectoryMetrics,
    Waypoint,
)
from src.realtoism.execution_log_converter import ExecutionLogConverter
from src.realtoism.sensor_replay_engine import (
    SensorReplayEngine,
    SensorReplayState,
)
from src.realtoism.simreal_validator import (
    SimRealValidator,
    ExecutionMetrics,
    ValidationMetric,
    ValidationResult,
)

__all__ = [
    "RosBagParser",
    "RosBagMetadata",
    "RosMessage",
    "RosPose",
    "RosImage",
    "RosPointCloud",
    "RosImu",
    "RosGps",
    "TrajectoryExtractor",
    "TrajectorySegment",
    "TrajectoryMetrics",
    "Waypoint",
    "ExecutionLogConverter",
    "SensorReplayEngine",
    "SensorReplayState",
    "SimRealValidator",
    "ExecutionMetrics",
    "ValidationMetric",
    "ValidationResult",
]
