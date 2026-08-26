"""Analytics Engine - Unified analytics and monitoring system.

Integrates metrics collection, validation, and visualization.
Provides high-level API for simulation monitoring.
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from src.analytics.metrics_collector import (
    MetricsCollector,
    SimulationMetrics,
    PerformanceMetrics,
    NarrativeMetrics,
    SensorMetrics,
    ValidationMetrics,
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Unified analytics engine for simulation monitoring.

    Coordinates:
    - Real-time metrics collection
    - Performance tracking
    - Narrative progress monitoring
    - Sensor health tracking
    - Sim/real validation
    """

    def __init__(self):
        """Initialize analytics engine."""
        self._collector = MetricsCollector()
        self._event_callbacks: Dict[str, List[Callable]] = {
            "simulation_update": [],
            "narrative_progress": [],
            "constraint_violation": [],
            "validation_complete": [],
            "sensor_update": [],
        }
        self._active = False

    def start(self) -> None:
        """Start analytics tracking."""
        self._active = True
        logger.info("Analytics engine started")

    def stop(self) -> None:
        """Stop analytics tracking."""
        self._active = False
        logger.info("Analytics engine stopped")

    def update_simulation(
        self,
        elapsed_time_sec: float,
        current_position: tuple,
        current_velocity: float,
        current_acceleration: float,
        distance_traveled: float,
        goals_completed: int,
        goals_total: int,
        constraints_violated: int = 0,
        sensor_frames_received: int = 0,
        simulation_speed: float = 1.0,
    ) -> None:
        """Update simulation metrics.

        Args:
            elapsed_time_sec: Simulation elapsed time
            current_position: (x, y, z) tuple
            current_velocity: Current velocity m/s
            current_acceleration: Current acceleration m/s^2
            distance_traveled: Total distance traveled m
            goals_completed: Number of completed goals
            goals_total: Total number of goals
            constraints_violated: Number of constraint violations
            sensor_frames_received: Number of sensor frames received
            simulation_speed: Simulation speed multiplier
        """
        if not self._active:
            return

        metrics = SimulationMetrics(
            timestamp_sec=datetime.now().timestamp(),
            elapsed_time_sec=elapsed_time_sec,
            current_position=current_position,
            current_velocity=current_velocity,
            current_acceleration=current_acceleration,
            distance_traveled=distance_traveled,
            goals_completed=goals_completed,
            goals_total=goals_total,
            constraints_violated=constraints_violated,
            sensor_frames_received=sensor_frames_received,
            simulation_speed=simulation_speed,
        )

        self._collector.record_simulation_metrics(metrics)

        # Trigger callback
        for callback in self._event_callbacks["simulation_update"]:
            callback(metrics)

    def update_performance(
        self,
        simulation_fps: float,
        average_frame_time_ms: float,
        cpu_usage_pct: float,
        memory_usage_mb: float,
        total_events_processed: int,
        events_per_second: float,
    ) -> None:
        """Update performance metrics.

        Args:
            simulation_fps: Frames per second
            average_frame_time_ms: Average frame time in ms
            cpu_usage_pct: CPU usage percentage
            memory_usage_mb: Memory usage in MB
            total_events_processed: Total events processed
            events_per_second: Events per second
        """
        if not self._active:
            return

        metrics = PerformanceMetrics(
            simulation_fps=simulation_fps,
            average_frame_time_ms=average_frame_time_ms,
            cpu_usage_pct=cpu_usage_pct,
            memory_usage_mb=memory_usage_mb,
            total_events_processed=total_events_processed,
            events_per_second=events_per_second,
        )

        self._collector.record_performance_metrics(metrics)

    def update_narrative(
        self,
        narrative_id: str,
        narrative_type: str,
        current_sequence: int,
        total_sequences: int,
        sequence_progress_pct: float,
        events_triggered: int,
        total_events: int,
        goal_progress: Optional[Dict[str, float]] = None,
        active_constraints: Optional[List[str]] = None,
    ) -> None:
        """Update narrative progress metrics.

        Args:
            narrative_id: Narrative identifier
            narrative_type: Type of narrative
            current_sequence: Current sequence index
            total_sequences: Total sequences
            sequence_progress_pct: Progress percentage 0-100
            events_triggered: Number of events triggered
            total_events: Total events
            goal_progress: Optional goal progress mapping
            active_constraints: Optional active constraints list
        """
        if not self._active:
            return

        metrics = NarrativeMetrics(
            narrative_id=narrative_id,
            narrative_type=narrative_type,
            current_sequence=current_sequence,
            total_sequences=total_sequences,
            sequence_progress_pct=sequence_progress_pct,
            events_triggered=events_triggered,
            total_events=total_events,
            goal_progress=goal_progress or {},
            active_constraints=active_constraints or [],
        )

        self._collector.set_narrative_metrics(metrics)

        # Trigger callback
        for callback in self._event_callbacks["narrative_progress"]:
            callback(metrics)

    def update_sensor(
        self,
        sensor_name: str,
        sensor_type: str,
        total_frames: int,
        fps: float,
        frame_latency_ms: float,
        data_rate_mbps: float,
        is_active: bool = True,
    ) -> None:
        """Update sensor metrics.

        Args:
            sensor_name: Sensor identifier
            sensor_type: Type (camera, lidar, imu, gps)
            total_frames: Total frames received
            fps: Frames per second
            frame_latency_ms: Frame latency in ms
            data_rate_mbps: Data rate in Mbps
            is_active: Whether sensor is active
        """
        if not self._active:
            return

        metrics = SensorMetrics(
            sensor_name=sensor_name,
            sensor_type=sensor_type,
            total_frames=total_frames,
            fps=fps,
            frame_latency_ms=frame_latency_ms,
            data_rate_mbps=data_rate_mbps,
            is_active=is_active,
        )

        self._collector.set_sensor_metrics(sensor_name, metrics)

        # Trigger callback
        for callback in self._event_callbacks["sensor_update"]:
            callback(metrics)

    def record_validation(
        self,
        real_vs_sim_distance_error: float,
        real_vs_sim_velocity_error: float,
        real_vs_sim_time_error: float,
        sensor_correlation: Optional[Dict[str, float]] = None,
        overall_similarity: float = 0.0,
        is_valid: bool = True,
    ) -> None:
        """Record validation results.

        Args:
            real_vs_sim_distance_error: Distance error percentage
            real_vs_sim_velocity_error: Velocity error percentage
            real_vs_sim_time_error: Time error percentage
            sensor_correlation: Optional sensor correlation mapping
            overall_similarity: Overall similarity 0-1
            is_valid: Whether validation passed
        """
        if not self._active:
            return

        metrics = ValidationMetrics(
            real_vs_sim_distance_error=real_vs_sim_distance_error,
            real_vs_sim_velocity_error=real_vs_sim_velocity_error,
            real_vs_sim_time_error=real_vs_sim_time_error,
            sensor_correlation=sensor_correlation or {},
            overall_similarity=overall_similarity,
            is_valid=is_valid,
        )

        self._collector.set_validation_metrics(metrics)

        # Trigger callback
        for callback in self._event_callbacks["validation_complete"]:
            callback(metrics)

    def record_constraint_violation(self, constraint_id: str, violation_value: float) -> None:
        """Record constraint violation.

        Args:
            constraint_id: Constraint identifier
            violation_value: Violation value
        """
        if not self._active:
            return

        # Trigger callback
        for callback in self._event_callbacks["constraint_violation"]:
            callback({"constraint_id": constraint_id, "value": violation_value})

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register event callback.

        Args:
            event_type: Event type to listen for
            callback: Callback function
        """
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].append(callback)
            logger.info(f"Registered callback for {event_type}")

    def get_collector(self) -> MetricsCollector:
        """Get metrics collector.

        Returns:
            MetricsCollector instance
        """
        return self._collector

    def get_summary(self) -> Dict[str, Any]:
        """Get complete analytics summary.

        Returns:
            Summary dictionary
        """
        return self._collector.get_summary()

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed statistics.

        Returns:
            Statistics dictionary
        """
        latest_sim = self._collector.get_latest_simulation_metrics()
        latest_perf = self._collector.get_latest_performance_metrics()
        narrative = self._collector.get_narrative_metrics()
        validation = self._collector.get_validation_metrics()

        stats = {
            "is_active": self._active,
            "metrics_recorded": len(self._collector._sim_metrics),
        }

        if latest_sim:
            stats["distance"] = latest_sim.distance_traveled
            stats["velocity_current"] = latest_sim.current_velocity
            stats["velocity_avg"] = self._collector.get_average_velocity()
            stats["velocity_max"] = self._collector.get_max_velocity()
            stats["acceleration"] = self._collector.get_average_acceleration()

        if latest_perf:
            stats["fps"] = latest_perf.simulation_fps
            stats["frame_time_ms"] = latest_perf.average_frame_time_ms
            stats["cpu_pct"] = latest_perf.cpu_usage_pct
            stats["memory_mb"] = latest_perf.memory_usage_mb

        if narrative:
            stats["narrative_progress"] = narrative.sequence_progress_pct
            stats["goals_completed"] = narrative.events_triggered

        if validation:
            stats["validation_similarity"] = validation.overall_similarity
            stats["validation_valid"] = validation.is_valid

        return stats

    def reset(self) -> None:
        """Reset all analytics data."""
        self._collector.reset()
        logger.info("Analytics engine reset")
