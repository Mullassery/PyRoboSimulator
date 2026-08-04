"""Metrics Collector - Real-time simulation metrics tracking.

Collects and aggregates metrics from:
- Simulation execution (poses, velocities, accelerations)
- Narrative progress (goals, constraints, events)
- Sensor data (frame counts, latency)
- Validation results (sim/real comparison)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SimulationMetrics:
    """Instantaneous simulation metrics."""
    timestamp_sec: float
    elapsed_time_sec: float
    current_position: tuple  # (x, y, z)
    current_velocity: float  # m/s
    current_acceleration: float  # m/s^2
    distance_traveled: float  # m
    goals_completed: int
    goals_total: int
    constraints_violated: int
    sensor_frames_received: int
    simulation_speed: float  # 1.0 = realtime, >1 = faster


@dataclass
class PerformanceMetrics:
    """Performance and efficiency metrics."""
    simulation_fps: float
    average_frame_time_ms: float
    cpu_usage_pct: float
    memory_usage_mb: float
    total_events_processed: int
    events_per_second: float


@dataclass
class NarrativeMetrics:
    """Narrative execution metrics."""
    narrative_id: str
    narrative_type: str
    current_sequence: int
    total_sequences: int
    sequence_progress_pct: float
    events_triggered: int
    total_events: int
    goal_progress: Dict[str, float] = field(default_factory=dict)
    active_constraints: List[str] = field(default_factory=list)


@dataclass
class SensorMetrics:
    """Sensor data metrics."""
    sensor_name: str
    sensor_type: str  # "camera", "lidar", "imu", "gps"
    total_frames: int
    fps: float
    frame_latency_ms: float
    data_rate_mbps: float
    is_active: bool


@dataclass
class ValidationMetrics:
    """Validation and error metrics."""
    real_vs_sim_distance_error: float  # %
    real_vs_sim_velocity_error: float  # %
    real_vs_sim_time_error: float  # %
    sensor_correlation: Dict[str, float] = field(default_factory=dict)
    overall_similarity: float = 0.0
    is_valid: bool = True


class MetricsCollector:
    """Collects and tracks simulation metrics over time.

    Maintains circular buffers for time-series metrics visualization.
    """

    def __init__(self, history_size: int = 1000):
        """Initialize collector.

        Args:
            history_size: Number of historical data points to keep
        """
        self._history_size = history_size
        self._sim_metrics: deque = deque(maxlen=history_size)
        self._perf_metrics: deque = deque(maxlen=history_size)
        self._narrative_metrics: Optional[NarrativeMetrics] = None
        self._sensor_metrics: Dict[str, SensorMetrics] = {}
        self._validation_metrics: Optional[ValidationMetrics] = None
        self._start_time = datetime.now()

    def record_simulation_metrics(self, metrics: SimulationMetrics) -> None:
        """Record simulation metrics.

        Args:
            metrics: Simulation metrics snapshot
        """
        self._sim_metrics.append(metrics)

    def record_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics.

        Args:
            metrics: Performance metrics snapshot
        """
        self._perf_metrics.append(metrics)

    def set_narrative_metrics(self, metrics: NarrativeMetrics) -> None:
        """Set current narrative metrics.

        Args:
            metrics: Narrative metrics
        """
        self._narrative_metrics = metrics

    def set_sensor_metrics(self, sensor_name: str, metrics: SensorMetrics) -> None:
        """Set sensor metrics.

        Args:
            sensor_name: Sensor identifier
            metrics: Sensor metrics
        """
        self._sensor_metrics[sensor_name] = metrics

    def set_validation_metrics(self, metrics: ValidationMetrics) -> None:
        """Set validation metrics.

        Args:
            metrics: Validation metrics
        """
        self._validation_metrics = metrics

    def get_latest_simulation_metrics(self) -> Optional[SimulationMetrics]:
        """Get most recent simulation metrics.

        Returns:
            Latest metrics or None
        """
        return self._sim_metrics[-1] if self._sim_metrics else None

    def get_latest_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent performance metrics.

        Returns:
            Latest metrics or None
        """
        return self._perf_metrics[-1] if self._perf_metrics else None

    def get_narrative_metrics(self) -> Optional[NarrativeMetrics]:
        """Get current narrative metrics.

        Returns:
            Narrative metrics or None
        """
        return self._narrative_metrics

    def get_sensor_metrics(self, sensor_name: Optional[str] = None) -> Dict[str, SensorMetrics]:
        """Get sensor metrics.

        Args:
            sensor_name: Optional sensor filter

        Returns:
            Dictionary of sensor metrics
        """
        if sensor_name:
            return {sensor_name: self._sensor_metrics[sensor_name]} if sensor_name in self._sensor_metrics else {}

        return self._sensor_metrics

    def get_validation_metrics(self) -> Optional[ValidationMetrics]:
        """Get validation metrics.

        Returns:
            Validation metrics or None
        """
        return self._validation_metrics

    def get_simulation_history(self, duration_sec: Optional[float] = None) -> List[SimulationMetrics]:
        """Get simulation metrics history.

        Args:
            duration_sec: Optional duration filter (last N seconds)

        Returns:
            List of metrics in time order
        """
        if not duration_sec:
            return list(self._sim_metrics)

        if not self._sim_metrics:
            return []

        cutoff_time = self._sim_metrics[-1].elapsed_time_sec - duration_sec

        return [m for m in self._sim_metrics if m.elapsed_time_sec >= cutoff_time]

    def get_average_velocity(self, duration_sec: float = 10.0) -> float:
        """Get average velocity over time period.

        Args:
            duration_sec: Time window

        Returns:
            Average velocity m/s
        """
        history = self.get_simulation_history(duration_sec)

        if not history:
            return 0.0

        velocities = [m.current_velocity for m in history]
        return sum(velocities) / len(velocities)

    def get_max_velocity(self, duration_sec: float = 10.0) -> float:
        """Get maximum velocity in time period.

        Args:
            duration_sec: Time window

        Returns:
            Max velocity m/s
        """
        history = self.get_simulation_history(duration_sec)

        if not history:
            return 0.0

        return max((m.current_velocity for m in history), default=0.0)

    def get_average_acceleration(self, duration_sec: float = 10.0) -> float:
        """Get average acceleration in time period.

        Args:
            duration_sec: Time window

        Returns:
            Average acceleration m/s^2
        """
        history = self.get_simulation_history(duration_sec)

        if not history:
            return 0.0

        accelerations = [m.current_acceleration for m in history]
        return sum(accelerations) / len(accelerations)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.

        Returns:
            Summary dictionary
        """
        latest_sim = self.get_latest_simulation_metrics()
        latest_perf = self.get_latest_performance_metrics()
        narrative = self.get_narrative_metrics()
        validation = self.get_validation_metrics()

        summary = {
            "uptime_sec": (datetime.now() - self._start_time).total_seconds(),
            "metrics_recorded": len(self._sim_metrics),
            "sensors_active": len([s for s in self._sensor_metrics.values() if s.is_active]),
        }

        if latest_sim:
            summary["simulation"] = {
                "elapsed_time": latest_sim.elapsed_time_sec,
                "position": latest_sim.current_position,
                "velocity": latest_sim.current_velocity,
                "distance": latest_sim.distance_traveled,
                "goals": f"{latest_sim.goals_completed}/{latest_sim.goals_total}",
                "constraints_violated": latest_sim.constraints_violated,
            }

        if latest_perf:
            summary["performance"] = {
                "fps": latest_perf.simulation_fps,
                "frame_time_ms": latest_perf.average_frame_time_ms,
                "cpu_pct": latest_perf.cpu_usage_pct,
                "memory_mb": latest_perf.memory_usage_mb,
            }

        if narrative:
            summary["narrative"] = {
                "type": narrative.narrative_type,
                "sequence": f"{narrative.current_sequence}/{narrative.total_sequences}",
                "progress": f"{narrative.sequence_progress_pct:.1f}%",
                "events": f"{narrative.events_triggered}/{narrative.total_events}",
            }

        if validation:
            summary["validation"] = {
                "distance_error": f"{validation.real_vs_sim_distance_error:.1f}%",
                "velocity_error": f"{validation.real_vs_sim_velocity_error:.1f}%",
                "time_error": f"{validation.real_vs_sim_time_error:.1f}%",
                "similarity": f"{validation.overall_similarity:.1%}",
                "valid": validation.is_valid,
            }

        return summary

    def reset(self) -> None:
        """Reset all metrics."""
        self._sim_metrics.clear()
        self._perf_metrics.clear()
        self._narrative_metrics = None
        self._sensor_metrics.clear()
        self._validation_metrics = None
        self._start_time = datetime.now()

        logger.info("Metrics collector reset")
