"""Tests for Analytics & Monitoring Dashboard - Phase 10."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.src.analytics import (
    MetricsCollector,
    SimulationMetrics,
    PerformanceMetrics,
    NarrativeMetrics,
    SensorMetrics,
    ValidationMetrics,
    AnalyticsEngine,
)

# Try to import dashboard app (requires textual)
try:
    from backend.src.analytics.cli_dashboard import AnalyticsDashboardApp
    HAS_TEXTUAL = True
except (ImportError, TypeError):
    HAS_TEXTUAL = False
    # Mock class for testing
    class AnalyticsDashboardApp:
        def __init__(self, collector=None):
            pass
        def get_collector(self):
            return MetricsCollector()
        def print_summary(self):
            pass


class TestMetricsCollector:
    """Test metrics collector."""

    def test_collector_initialization(self):
        """Test collector creation."""
        collector = MetricsCollector(history_size=100)

        assert collector._history_size == 100
        assert len(collector._sim_metrics) == 0

    def test_record_simulation_metrics(self):
        """Test recording simulation metrics."""
        collector = MetricsCollector()

        metrics = SimulationMetrics(
            timestamp_sec=0.0,
            elapsed_time_sec=1.0,
            current_position=(1.0, 2.0, 3.0),
            current_velocity=0.5,
            current_acceleration=0.1,
            distance_traveled=1.0,
            goals_completed=0,
            goals_total=1,
            constraints_violated=0,
            sensor_frames_received=30,
            simulation_speed=1.0,
        )

        collector.record_simulation_metrics(metrics)

        assert len(collector._sim_metrics) == 1
        assert collector.get_latest_simulation_metrics() == metrics

    def test_record_performance_metrics(self):
        """Test recording performance metrics."""
        collector = MetricsCollector()

        metrics = PerformanceMetrics(
            simulation_fps=60.0,
            average_frame_time_ms=16.67,
            cpu_usage_pct=50.0,
            memory_usage_mb=256.0,
            total_events_processed=1000,
            events_per_second=100.0,
        )

        collector.record_performance_metrics(metrics)

        assert len(collector._perf_metrics) == 1
        assert collector.get_latest_performance_metrics() == metrics

    def test_narrative_metrics(self):
        """Test narrative metrics."""
        collector = MetricsCollector()

        metrics = NarrativeMetrics(
            narrative_id="narr_0",
            narrative_type="delivery",
            current_sequence=1,
            total_sequences=5,
            sequence_progress_pct=20.0,
            events_triggered=3,
            total_events=15,
            goal_progress={"goal_0": 0.5},
            active_constraints=["safety"],
        )

        collector.set_narrative_metrics(metrics)

        assert collector.get_narrative_metrics() == metrics

    def test_sensor_metrics(self):
        """Test sensor metrics."""
        collector = MetricsCollector()

        metrics = SensorMetrics(
            sensor_name="camera_0",
            sensor_type="camera",
            total_frames=100,
            fps=30.0,
            frame_latency_ms=5.0,
            data_rate_mbps=50.0,
            is_active=True,
        )

        collector.set_sensor_metrics("camera_0", metrics)

        sensors = collector.get_sensor_metrics()
        assert "camera_0" in sensors
        assert sensors["camera_0"] == metrics

    def test_validation_metrics(self):
        """Test validation metrics."""
        collector = MetricsCollector()

        metrics = ValidationMetrics(
            real_vs_sim_distance_error=2.5,
            real_vs_sim_velocity_error=3.0,
            real_vs_sim_time_error=1.5,
            sensor_correlation={"lidar": 0.95},
            overall_similarity=0.92,
            is_valid=True,
        )

        collector.set_validation_metrics(metrics)

        assert collector.get_validation_metrics() == metrics

    def test_average_velocity(self):
        """Test average velocity computation."""
        collector = MetricsCollector()

        for i in range(5):
            metrics = SimulationMetrics(
                timestamp_sec=float(i),
                elapsed_time_sec=float(i),
                current_position=(float(i), 0.0, 0.0),
                current_velocity=1.0 + (i * 0.1),
                current_acceleration=0.1,
                distance_traveled=float(i),
                goals_completed=0,
                goals_total=1,
                constraints_violated=0,
                sensor_frames_received=0,
                simulation_speed=1.0,
            )

            collector.record_simulation_metrics(metrics)

        avg_vel = collector.get_average_velocity(duration_sec=10.0)

        assert avg_vel > 0.0

    def test_get_summary(self):
        """Test getting summary."""
        collector = MetricsCollector()

        metrics = SimulationMetrics(
            timestamp_sec=0.0,
            elapsed_time_sec=10.0,
            current_position=(5.0, 0.0, 0.0),
            current_velocity=0.5,
            current_acceleration=0.1,
            distance_traveled=5.0,
            goals_completed=1,
            goals_total=2,
            constraints_violated=0,
            sensor_frames_received=300,
            simulation_speed=1.0,
        )

        collector.record_simulation_metrics(metrics)

        summary = collector.get_summary()

        assert "simulation" in summary
        assert summary["simulation"]["distance"] == 5.0
        assert summary["simulation"]["goals"] == "1/2"

    def test_reset(self):
        """Test reset."""
        collector = MetricsCollector()

        metrics = SimulationMetrics(
            timestamp_sec=0.0,
            elapsed_time_sec=1.0,
            current_position=(0.0, 0.0, 0.0),
            current_velocity=0.0,
            current_acceleration=0.0,
            distance_traveled=0.0,
            goals_completed=0,
            goals_total=1,
            constraints_violated=0,
            sensor_frames_received=0,
            simulation_speed=1.0,
        )

        collector.record_simulation_metrics(metrics)
        assert len(collector._sim_metrics) > 0

        collector.reset()
        assert len(collector._sim_metrics) == 0


class TestAnalyticsEngine:
    """Test analytics engine."""

    def test_engine_initialization(self):
        """Test engine creation."""
        engine = AnalyticsEngine()

        assert not engine._active
        assert engine._collector is not None

    def test_start_stop(self):
        """Test starting and stopping."""
        engine = AnalyticsEngine()

        engine.start()
        assert engine._active

        engine.stop()
        assert not engine._active

    def test_update_simulation(self):
        """Test updating simulation metrics."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_simulation(
            elapsed_time_sec=1.0,
            current_position=(1.0, 0.0, 0.0),
            current_velocity=1.0,
            current_acceleration=0.1,
            distance_traveled=1.0,
            goals_completed=0,
            goals_total=1,
        )

        summary = engine.get_summary()
        assert "simulation" in summary

    def test_update_performance(self):
        """Test updating performance metrics."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_performance(
            simulation_fps=60.0,
            average_frame_time_ms=16.67,
            cpu_usage_pct=50.0,
            memory_usage_mb=256.0,
            total_events_processed=1000,
            events_per_second=100.0,
        )

        summary = engine.get_summary()
        assert "performance" in summary

    def test_update_narrative(self):
        """Test updating narrative metrics."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_narrative(
            narrative_id="narr_0",
            narrative_type="delivery",
            current_sequence=1,
            total_sequences=5,
            sequence_progress_pct=20.0,
            events_triggered=3,
            total_events=15,
            goal_progress={"goal_0": 0.5},
        )

        summary = engine.get_summary()
        assert "narrative" in summary

    def test_update_sensor(self):
        """Test updating sensor metrics."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_sensor(
            sensor_name="camera_0",
            sensor_type="camera",
            total_frames=100,
            fps=30.0,
            frame_latency_ms=5.0,
            data_rate_mbps=50.0,
        )

        collector = engine.get_collector()
        sensors = collector.get_sensor_metrics()

        assert "camera_0" in sensors

    def test_record_validation(self):
        """Test recording validation."""
        engine = AnalyticsEngine()
        engine.start()

        engine.record_validation(
            real_vs_sim_distance_error=2.5,
            real_vs_sim_velocity_error=3.0,
            real_vs_sim_time_error=1.5,
            sensor_correlation={"lidar": 0.95},
            overall_similarity=0.92,
            is_valid=True,
        )

        summary = engine.get_summary()
        assert "validation" in summary

    def test_callback_registration(self):
        """Test callback registration."""
        engine = AnalyticsEngine()

        callback = Mock()
        engine.register_callback("simulation_update", callback)

        assert callback in engine._event_callbacks["simulation_update"]

    def test_callbacks_triggered(self):
        """Test callbacks are triggered."""
        engine = AnalyticsEngine()
        engine.start()

        callback = Mock()
        engine.register_callback("simulation_update", callback)

        engine.update_simulation(
            elapsed_time_sec=1.0,
            current_position=(0.0, 0.0, 0.0),
            current_velocity=1.0,
            current_acceleration=0.1,
            distance_traveled=1.0,
            goals_completed=0,
            goals_total=1,
        )

        callback.assert_called_once()

    def test_constraint_violation(self):
        """Test recording constraint violation."""
        engine = AnalyticsEngine()
        engine.start()

        callback = Mock()
        engine.register_callback("constraint_violation", callback)

        engine.record_constraint_violation("safety", 0.5)

        callback.assert_called_once()

    def test_get_stats(self):
        """Test getting statistics."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_simulation(
            elapsed_time_sec=5.0,
            current_position=(2.0, 0.0, 0.0),
            current_velocity=0.4,
            current_acceleration=0.1,
            distance_traveled=2.0,
            goals_completed=0,
            goals_total=1,
        )

        engine.update_performance(
            simulation_fps=60.0,
            average_frame_time_ms=16.67,
            cpu_usage_pct=50.0,
            memory_usage_mb=256.0,
            total_events_processed=1000,
            events_per_second=100.0,
        )

        stats = engine.get_stats()

        assert "distance" in stats
        assert stats["distance"] == 2.0
        assert "fps" in stats
        assert stats["fps"] == 60.0

    def test_reset(self):
        """Test reset."""
        engine = AnalyticsEngine()
        engine.start()

        engine.update_simulation(
            elapsed_time_sec=1.0,
            current_position=(0.0, 0.0, 0.0),
            current_velocity=1.0,
            current_acceleration=0.1,
            distance_traveled=1.0,
            goals_completed=0,
            goals_total=1,
        )

        engine.reset()

        collector = engine.get_collector()
        assert len(collector._sim_metrics) == 0


@pytest.mark.skipif(not HAS_TEXTUAL, reason="Textual not installed")
class TestAnalyticsDashboardApp:
    """Test dashboard app."""

    def test_app_initialization(self):
        """Test app creation."""
        app = AnalyticsDashboardApp()

        assert app._collector is not None

    def test_app_with_collector(self):
        """Test app with provided collector."""
        collector = MetricsCollector()
        app = AnalyticsDashboardApp(collector)

        assert app.get_collector() == collector

    def test_get_collector(self):
        """Test getting collector from app."""
        app = AnalyticsDashboardApp()
        collector = app.get_collector()

        assert isinstance(collector, MetricsCollector)

    def test_print_summary(self):
        """Test printing summary."""
        app = AnalyticsDashboardApp()

        collector = app.get_collector()
        collector.record_simulation_metrics(
            SimulationMetrics(
                timestamp_sec=0.0,
                elapsed_time_sec=1.0,
                current_position=(1.0, 0.0, 0.0),
                current_velocity=1.0,
                current_acceleration=0.1,
                distance_traveled=1.0,
                goals_completed=0,
                goals_total=1,
                constraints_violated=0,
                sensor_frames_received=30,
                simulation_speed=1.0,
            )
        )

        # Should not raise
        app.print_summary()


class TestAnalyticsDashboardIntegration:
    """Integration tests for analytics dashboard."""

    def test_complete_analytics_workflow(self):
        """Test complete analytics workflow."""
        # Create engine
        engine = AnalyticsEngine()
        engine.start()

        # Simulate execution
        for i in range(10):
            engine.update_simulation(
                elapsed_time_sec=float(i),
                current_position=(float(i) * 0.5, 0.0, 0.0),
                current_velocity=0.5 + (i * 0.01),
                current_acceleration=0.1,
                distance_traveled=float(i) * 0.5,
                goals_completed=min(i // 5, 2),
                goals_total=2,
                constraints_violated=0,
                sensor_frames_received=i * 30,
            )

            engine.update_performance(
                simulation_fps=60.0 - (i * 0.5),
                average_frame_time_ms=16.67 + (i * 0.1),
                cpu_usage_pct=40.0 + (i * 0.5),
                memory_usage_mb=200.0 + (i * 2.0),
                total_events_processed=i * 100,
                events_per_second=100.0,
            )

        # Record narrative
        engine.update_narrative(
            narrative_id="test_narr",
            narrative_type="delivery",
            current_sequence=3,
            total_sequences=5,
            sequence_progress_pct=60.0,
            events_triggered=9,
            total_events=15,
            goal_progress={"goal_0": 1.0, "goal_1": 0.0},
        )

        # Record sensors
        engine.update_sensor(
            sensor_name="camera",
            sensor_type="camera",
            total_frames=300,
            fps=30.0,
            frame_latency_ms=5.0,
            data_rate_mbps=50.0,
        )

        # Record validation
        engine.record_validation(
            real_vs_sim_distance_error=1.5,
            real_vs_sim_velocity_error=2.0,
            real_vs_sim_time_error=1.0,
            sensor_correlation={"camera": 0.95},
            overall_similarity=0.94,
            is_valid=True,
        )

        # Get summary
        summary = engine.get_summary()

        assert "simulation" in summary
        assert "performance" in summary
        assert "narrative" in summary
        assert "validation" in summary

        # Get stats
        stats = engine.get_stats()

        assert stats["distance"] > 0
        assert stats["fps"] > 0
        assert stats["validation_similarity"] > 0.9

        # Create dashboard app (if textual available)
        if HAS_TEXTUAL:
            app = AnalyticsDashboardApp(engine.get_collector())
            app_collector = app.get_collector()

            assert app_collector.get_latest_simulation_metrics() is not None
            assert app_collector.get_narrative_metrics() is not None
