"""Tests for Validation & Reporting Framework (Phase 3.2)."""

import time

import pytest

from src.services.validation_and_reporting import (
    ComprehensiveReportGenerator,
    MetricType,
    PerformanceMetric,
    PerformanceMetricsCollector,
    RootCauseAnalysis,
    RootCauseAnalyzer,
    SeverityLevel,
    ValidationFramework,
    ValidationResult,
    ValidationStatus,
    ViolationDetector,
    ViolationEvent,
)


class TestPerformanceMetric:
    """Test performance metric."""

    def test_metric_creation(self):
        """Test creating metric."""
        metric = PerformanceMetric(
            name="mission_time",
            metric_type=MetricType.MISSION_SUCCESS,
            value=45.5,
            unit="seconds",
            timestamp=time.time(),
        )

        assert metric.name == "mission_time"
        assert metric.value == 45.5
        assert metric.unit == "seconds"


class TestPerformanceMetricsCollector:
    """Test performance metrics collector."""

    def test_collector_creation(self):
        """Test creating collector."""
        collector = PerformanceMetricsCollector()

        assert len(collector.metrics) == 0
        assert len(collector.metric_aggregates) == 0

    def test_record_metric(self):
        """Test recording metric."""
        collector = PerformanceMetricsCollector()

        metric = collector.record_metric(
            "path_length",
            MetricType.EFFICIENCY,
            100.5,
            "meters",
            {"robot_id": "robot_1"},
        )

        assert len(collector.metrics) == 1
        assert metric.name == "path_length"
        assert metric.value == 100.5

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        collector = PerformanceMetricsCollector()

        for i in range(10):
            collector.record_metric(
                "speed", MetricType.EFFICIENCY, 1.0 + i * 0.1, "m/s"
            )

        assert len(collector.metrics) == 10

    def test_get_metric_statistics(self):
        """Test getting statistics."""
        collector = PerformanceMetricsCollector()

        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for val in values:
            collector.record_metric("latency", MetricType.SAFETY, val, "ms")

        stats = collector.get_metric_statistics(MetricType.SAFETY)

        assert stats["count"] == 5
        assert stats["sum"] == 150.0
        assert stats["mean"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0

    def test_get_metric_statistics_empty(self):
        """Test statistics for empty collector."""
        collector = PerformanceMetricsCollector()

        stats = collector.get_metric_statistics()

        assert stats == {}

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = PerformanceMetricsCollector()

        collector.record_metric("metric1", MetricType.EFFICIENCY, 10.0)
        collector.record_metric("metric2", MetricType.SAFETY, 20.0)

        all_metrics = collector.get_all_metrics()

        assert len(all_metrics) == 2


class TestValidationFramework:
    """Test validation framework."""

    def test_framework_creation(self):
        """Test creating framework."""
        framework = ValidationFramework()

        assert len(framework.validation_results) == 0
        assert len(framework.validation_rules) == 0

    def test_validate_mission_completion_passed(self):
        """Test mission completion validation (passed)."""
        framework = ValidationFramework()

        result = framework.validate_mission_completion(
            goal_reached=True, goal_distance=0.1
        )

        assert result.passed
        assert result.status == ValidationStatus.PASSED
        assert len(framework.validation_results) == 1

    def test_validate_mission_completion_failed(self):
        """Test mission completion validation (failed)."""
        framework = ValidationFramework()

        result = framework.validate_mission_completion(
            goal_reached=False, goal_distance=10.0, tolerance=0.5
        )

        assert not result.passed
        assert result.status == ValidationStatus.FAILED

    def test_validate_mission_completion_within_tolerance(self):
        """Test mission completion within tolerance."""
        framework = ValidationFramework()

        result = framework.validate_mission_completion(
            goal_reached=False, goal_distance=0.4, tolerance=0.5
        )

        assert result.passed
        assert result.status == ValidationStatus.PASSED

    def test_validate_safety_perfect(self):
        """Test safety validation (perfect)."""
        framework = ValidationFramework()

        result = framework.validate_safety(
            collisions=0, near_misses=0, safety_violations=0
        )

        assert result.passed
        assert result.severity == SeverityLevel.LOW

    def test_validate_safety_with_collisions(self):
        """Test safety validation with collisions."""
        framework = ValidationFramework()

        result = framework.validate_safety(
            collisions=2, near_misses=3, safety_violations=0
        )

        assert not result.passed
        assert result.severity == SeverityLevel.CRITICAL

    def test_validate_safety_with_near_misses(self):
        """Test safety validation with near misses."""
        framework = ValidationFramework()

        result = framework.validate_safety(
            collisions=0, near_misses=5, safety_violations=0
        )

        assert result.passed
        assert result.severity == SeverityLevel.MEDIUM

    def test_validate_efficiency_good(self):
        """Test efficiency validation (good)."""
        framework = ValidationFramework()

        result = framework.validate_efficiency(
            path_length=100.0, optimal_path_length=90.0, execution_time=50.0, time_limit=40.0
        )

        assert result.passed
        assert "path" in result.details
        assert "time" in result.details

    def test_validate_efficiency_poor_path(self):
        """Test efficiency validation (poor path)."""
        framework = ValidationFramework()

        result = framework.validate_efficiency(
            path_length=200.0,
            optimal_path_length=90.0,
            execution_time=50.0,
            time_limit=40.0,
        )

        assert not result.passed

    def test_validate_robustness_good(self):
        """Test robustness validation (good)."""
        framework = ValidationFramework()

        result = framework.validate_robustness(
            recovery_attempts=5, successful_recoveries=4, total_failures=5
        )

        assert result.passed
        assert result.details["recovery_rate"] == 0.8

    def test_validate_robustness_poor(self):
        """Test robustness validation (poor)."""
        framework = ValidationFramework()

        result = framework.validate_robustness(
            recovery_attempts=5, successful_recoveries=1, total_failures=5
        )

        assert not result.passed

    def test_validate_robustness_no_failures(self):
        """Test robustness with no failures."""
        framework = ValidationFramework()

        result = framework.validate_robustness(
            recovery_attempts=0, successful_recoveries=0, total_failures=0
        )

        assert result.passed

    def test_get_validation_report(self):
        """Test getting validation report."""
        framework = ValidationFramework()

        framework.validate_mission_completion(True, 0.1)
        framework.validate_safety(0, 0, 0)
        framework.validate_efficiency(100.0, 90.0, 50.0, 40.0)

        report = framework.get_validation_report()

        assert report["total_checks"] == 3
        assert report["passed"] >= 2
        assert "by_severity" in report
        assert "results" in report

    def test_get_validation_report_empty(self):
        """Test validation report for empty framework."""
        framework = ValidationFramework()

        report = framework.get_validation_report()

        assert report == {}


class TestViolationDetector:
    """Test violation detector."""

    def test_detector_creation(self):
        """Test creating detector."""
        detector = ViolationDetector()

        assert len(detector.violations) == 0
        assert len(detector.violation_counts) == 0

    def test_detect_violation(self):
        """Test detecting violation."""
        detector = ViolationDetector()

        violation = detector.detect_violation(
            violation_type="collision",
            severity=SeverityLevel.CRITICAL,
            description="Robot collided with obstacle",
            scenario_id="scenario_1",
            robot_state={"position": [10.0, 20.0]},
            environment_state={"obstacles": 5},
        )

        assert len(detector.violations) == 1
        assert violation.violation_type == "collision"
        assert violation.severity == SeverityLevel.CRITICAL

    def test_detect_multiple_violations(self):
        """Test detecting multiple violations."""
        detector = ViolationDetector()

        for i in range(3):
            detector.detect_violation(
                "collision" if i < 2 else "gps_loss",
                SeverityLevel.HIGH,
                f"Violation {i}",
                "scenario_1",
                {},
                {},
            )

        assert len(detector.violations) == 3
        assert detector.violation_counts["collision"] == 2
        assert detector.violation_counts["gps_loss"] == 1

    def test_get_violation_summary(self):
        """Test getting violation summary."""
        detector = ViolationDetector()

        detector.detect_violation("collision", SeverityLevel.CRITICAL, "test", "s1", {}, {})
        detector.detect_violation("gps_loss", SeverityLevel.HIGH, "test", "s1", {}, {})
        detector.detect_violation("collision", SeverityLevel.MEDIUM, "test", "s1", {}, {})

        summary = detector.get_violation_summary()

        assert summary["total_violations"] == 3
        assert summary["by_type"]["collision"] == 2
        assert summary["by_type"]["gps_loss"] == 1
        assert summary["critical_count"] == 1

    def test_get_violation_summary_empty(self):
        """Test violation summary for empty detector."""
        detector = ViolationDetector()

        summary = detector.get_violation_summary()

        assert summary == {}


class TestRootCauseAnalyzer:
    """Test root cause analyzer."""

    def test_analyzer_creation(self):
        """Test creating analyzer."""
        analyzer = RootCauseAnalyzer()

        assert len(analyzer.analyses) == 0

    def test_analyze_collision_violation(self):
        """Test analyzing collision violation."""
        analyzer = RootCauseAnalyzer()

        violation = ViolationEvent(
            violation_id="vio_1",
            violation_type="collision",
            severity=SeverityLevel.CRITICAL,
            description="Collision with obstacle",
            timestamp=time.time(),
            scenario_id="scenario_1",
            robot_state={},
            environment_state={},
        )

        analysis = analyzer.analyze_violation(violation, [])

        assert analysis.violation_id == "vio_1"
        assert "collision" in analysis.primary_cause.lower()
        assert analysis.confidence > 0.5

    def test_analyze_gps_violation(self):
        """Test analyzing GPS violation."""
        analyzer = RootCauseAnalyzer()

        violation = ViolationEvent(
            violation_id="vio_2",
            violation_type="gps_loss",
            severity=SeverityLevel.HIGH,
            description="GPS unavailable",
            timestamp=time.time(),
            scenario_id="scenario_1",
            robot_state={},
            environment_state={},
        )

        analysis = analyzer.analyze_violation(violation, [])

        assert "gps" in analysis.primary_cause.lower()
        assert analysis.recommended_mitigation is not None

    def test_analyze_with_event_history(self):
        """Test analysis with event history."""
        analyzer = RootCauseAnalyzer()

        violation = ViolationEvent(
            violation_id="vio_3",
            violation_type="motor_failure",
            severity=SeverityLevel.CRITICAL,
            description="Motor failure",
            timestamp=time.time(),
            scenario_id="scenario_1",
            robot_state={},
            environment_state={},
        )

        event_history = [
            {"type": "sensor_failure"},
            {"type": "power_surge"},
            {"type": "motor_overheat"},
        ]

        analysis = analyzer.analyze_violation(violation, event_history)

        assert len(analysis.contributing_factors) > 0
        assert analysis.confidence > 0.5

    def test_analyze_multiple_violations(self):
        """Test analyzing multiple violations."""
        analyzer = RootCauseAnalyzer()

        for i in range(3):
            violation = ViolationEvent(
                violation_id=f"vio_{i}",
                violation_type="collision" if i < 2 else "timeout",
                severity=SeverityLevel.HIGH,
                description=f"Violation {i}",
                timestamp=time.time(),
                scenario_id="scenario_1",
                robot_state={},
                environment_state={},
            )

            analyzer.analyze_violation(violation, [])

        assert len(analyzer.analyses) == 3

    def test_get_root_cause_report(self):
        """Test getting root cause report."""
        analyzer = RootCauseAnalyzer()

        violation = ViolationEvent(
            violation_id="vio_1",
            violation_type="collision",
            severity=SeverityLevel.CRITICAL,
            description="Collision",
            timestamp=time.time(),
            scenario_id="scenario_1",
            robot_state={},
            environment_state={},
        )

        analyzer.analyze_violation(violation, [])

        report = analyzer.get_root_cause_report()

        assert report["total_analyses"] == 1
        assert "primary_causes" in report
        assert "average_confidence" in report

    def test_get_root_cause_report_empty(self):
        """Test root cause report for empty analyzer."""
        analyzer = RootCauseAnalyzer()

        report = analyzer.get_root_cause_report()

        assert report == {}


class TestComprehensiveReportGenerator:
    """Test comprehensive report generator."""

    def test_generator_creation(self):
        """Test creating report generator."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)

        assert generator.metrics_collector == metrics
        assert generator.validation_framework == validation

    def test_generate_executive_summary(self):
        """Test generating executive summary."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)

        # Add some data
        metrics.record_metric("latency", MetricType.EFFICIENCY, 50.0, "ms")
        validation.validate_mission_completion(True, 0.1)

        summary = generator.generate_executive_summary()

        assert "timestamp" in summary
        assert "overall_status" in summary
        assert "validation_summary" in summary

    def test_generate_detailed_report(self):
        """Test generating detailed report."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)

        # Add comprehensive data
        metrics.record_metric("path_length", MetricType.EFFICIENCY, 100.0)
        validation.validate_mission_completion(True, 0.1)
        validation.validate_safety(0, 0, 0)

        report = generator.generate_detailed_report()

        assert "timestamp" in report
        assert "executive_summary" in report
        assert "validation_report" in report
        assert "performance_metrics" in report

    def test_generate_dashboard_data(self):
        """Test generating dashboard data."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)

        # Add violation data
        violation = violations.detect_violation(
            "collision", SeverityLevel.CRITICAL, "test", "s1", {}, {}
        )

        analyzer.analyze_violation(violation, [])

        dashboard = generator.generate_dashboard_data()

        assert "timestamp" in dashboard
        assert "violation_timeline" in dashboard
        assert "severity_breakdown" in dashboard
        assert "mitigation_recommendations" in dashboard


class TestValidationAndReportingIntegration:
    """Integration tests for validation and reporting."""

    def test_full_validation_pipeline(self):
        """Test full validation pipeline."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        # Record metrics
        metrics.record_metric("path_length", MetricType.EFFICIENCY, 95.0)
        metrics.record_metric("execution_time", MetricType.EFFICIENCY, 45.0)

        # Run validations
        validation.validate_mission_completion(goal_reached=True, goal_distance=0.2)
        validation.validate_safety(collisions=0, near_misses=2, safety_violations=0)
        validation.validate_efficiency(
            path_length=95.0, optimal_path_length=90.0, execution_time=45.0, time_limit=60.0
        )
        validation.validate_robustness(
            recovery_attempts=2, successful_recoveries=2, total_failures=2
        )

        # Detect violations
        violation = violations.detect_violation(
            "gps_loss",
            SeverityLevel.MEDIUM,
            "GPS signal weak",
            "scenario_1",
            {"x": 10.0},
            {"weather": "rain"},
        )

        # Analyze root cause
        analyzer.analyze_violation(violation, [{"type": "cloud_cover"}])

        # Generate report
        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)
        report = generator.generate_detailed_report()

        # Verify report completeness
        assert "executive_summary" in report
        assert report["executive_summary"]["overall_status"] in ["PASSED", "FAILED"]
        assert len(report["validation_report"]["results"]) == 4
        assert len(report["root_cause_report"]["analyses"]) == 1

    def test_performance_tracking_and_reporting(self):
        """Test performance tracking and reporting."""
        metrics = PerformanceMetricsCollector()
        validation = ValidationFramework()
        violations = ViolationDetector()
        analyzer = RootCauseAnalyzer()

        # Track performance over multiple scenarios
        for i in range(5):
            metrics.record_metric(
                f"scenario_{i}_time", MetricType.EFFICIENCY, 40.0 + i * 2
            )
            metrics.record_metric(f"scenario_{i}_distance", MetricType.EFFICIENCY, 90.0 + i)

        generator = ComprehensiveReportGenerator(metrics, validation, violations, analyzer)
        report = generator.generate_detailed_report()

        stats = report["performance_metrics"]["statistics"]
        assert stats["count"] == 10
        assert stats["mean"] > 80.0
