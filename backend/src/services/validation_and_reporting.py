"""Validation & Reporting Framework for Phase 3.2.

Comprehensive validation, performance metrics, violation dashboards,
and root cause analysis for simulated robotics scenarios.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""

    MISSION_SUCCESS = "mission_success"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    RECOVERY = "recovery"
    LEARNING = "learning"


class ValidationStatus(Enum):
    """Validation status."""

    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    ERROR = "error"


class SeverityLevel(Enum):
    """Severity levels for issues."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PerformanceMetric:
    """Single performance metric."""

    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation check."""

    check_name: str
    status: ValidationStatus
    passed: bool
    severity: SeverityLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ViolationEvent:
    """A detected violation event."""

    violation_id: str
    violation_type: str
    severity: SeverityLevel
    description: str
    timestamp: float
    scenario_id: str
    robot_state: Dict[str, Any]
    environment_state: Dict[str, Any]
    recovery_action: Optional[str] = None
    root_cause: Optional[str] = None


@dataclass
class RootCauseAnalysis:
    """Root cause analysis for a violation."""

    violation_id: str
    primary_cause: str
    contributing_factors: List[str]
    cascade_chain: List[str]  # Chain of events leading to violation
    probability_score: float
    confidence: float
    recommended_mitigation: str


class PerformanceMetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self):
        """Initialize collector."""
        self.metrics: List[PerformanceMetric] = []
        self.metric_aggregates: Dict[str, Dict[str, float]] = {}

    def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        unit: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PerformanceMetric:
        """Record a performance metric.

        Args:
            name: Metric name
            metric_type: Type of metric
            value: Metric value
            unit: Unit of measurement
            metadata: Optional metadata

        Returns:
            Recorded metric
        """
        if metadata is None:
            metadata = {}

        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=datetime.now().timestamp(),
            metadata=metadata,
        )

        self.metrics.append(metric)
        self._update_aggregates(metric)

        return metric

    def _update_aggregates(self, metric: PerformanceMetric) -> None:
        """Update aggregates for a metric.

        Args:
            metric: The metric to aggregate
        """
        key = f"{metric.metric_type.value}_{metric.name}"

        if key not in self.metric_aggregates:
            self.metric_aggregates[key] = {
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
            }

        agg = self.metric_aggregates[key]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)

    def get_metric_statistics(self, metric_type: Optional[MetricType] = None) -> Dict[str, Any]:
        """Get statistics for metrics.

        Args:
            metric_type: Optional filter by type

        Returns:
            Statistics dictionary
        """
        if metric_type:
            filtered_metrics = [m for m in self.metrics if m.metric_type == metric_type]
        else:
            filtered_metrics = self.metrics

        if not filtered_metrics:
            return {}

        values = [m.value for m in filtered_metrics]

        return {
            "count": len(values),
            "sum": sum(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "median": sorted(values)[len(values) // 2] if values else 0,
        }

    def get_all_metrics(self) -> List[PerformanceMetric]:
        """Get all recorded metrics.

        Returns:
            List of metrics
        """
        return self.metrics


class ValidationFramework:
    """Framework for comprehensive validation."""

    def __init__(self):
        """Initialize validation framework."""
        self.validation_results: List[ValidationResult] = []
        self.validation_rules: Dict[str, callable] = {}

    def register_validation_rule(self, name: str, rule_func: callable) -> None:
        """Register a validation rule.

        Args:
            name: Rule name
            rule_func: Callable that takes (scenario, result) and returns bool
        """
        self.validation_rules[name] = rule_func
        logger.info(f"Registered validation rule: {name}")

    def validate_mission_completion(
        self,
        goal_reached: bool,
        goal_distance: float,
        tolerance: float = 0.5,
    ) -> ValidationResult:
        """Validate mission completion.

        Args:
            goal_reached: Whether goal was reached
            goal_distance: Final distance to goal
            tolerance: Goal tolerance in meters

        Returns:
            Validation result
        """
        passed = goal_reached or (goal_distance <= tolerance)

        result = ValidationResult(
            check_name="mission_completion",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            passed=passed,
            severity=SeverityLevel.HIGH,
            message=f"Mission {'completed' if passed else 'failed'}"
            f" (distance: {goal_distance:.2f}m)",
            details={"goal_reached": goal_reached, "goal_distance": goal_distance},
        )

        self.validation_results.append(result)
        return result

    def validate_safety(
        self,
        collisions: int,
        near_misses: int,
        safety_violations: int,
    ) -> ValidationResult:
        """Validate safety metrics.

        Args:
            collisions: Number of collisions
            near_misses: Number of near misses
            safety_violations: Number of safety violations

        Returns:
            Validation result
        """
        has_violations = collisions > 0 or safety_violations > 0
        passed = collisions == 0 and safety_violations == 0

        severity = (
            SeverityLevel.CRITICAL
            if collisions > 0
            else SeverityLevel.MEDIUM if near_misses > 0 else SeverityLevel.LOW
        )

        result = ValidationResult(
            check_name="safety",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            passed=passed,
            severity=severity,
            message=f"Safety check: {collisions} collisions, "
            f"{near_misses} near misses, {safety_violations} violations",
            details={
                "collisions": collisions,
                "near_misses": near_misses,
                "safety_violations": safety_violations,
            },
        )

        self.validation_results.append(result)
        return result

    def validate_efficiency(
        self,
        path_length: float,
        optimal_path_length: float,
        execution_time: float,
        time_limit: float,
    ) -> ValidationResult:
        """Validate efficiency metrics.

        Args:
            path_length: Actual path length
            optimal_path_length: Theoretical optimal length
            execution_time: Time taken
            time_limit: Time limit

        Returns:
            Validation result
        """
        if optimal_path_length > 0:
            path_efficiency = optimal_path_length / path_length
        else:
            path_efficiency = 1.0

        time_efficiency = time_limit / execution_time if execution_time > 0 else 0
        passed = path_efficiency > 0.8 and time_efficiency > 1.0

        result = ValidationResult(
            check_name="efficiency",
            status=ValidationStatus.PASSED if passed else ValidationStatus.PARTIAL,
            passed=passed,
            severity=SeverityLevel.MEDIUM,
            message=f"Efficiency: path={path_efficiency:.2%}, time={time_efficiency:.2f}x limit",
            details={
                "path_efficiency": path_efficiency,
                "time_efficiency": time_efficiency,
                "path_length": path_length,
                "optimal_length": optimal_path_length,
                "execution_time": execution_time,
                "time_limit": time_limit,
            },
        )

        self.validation_results.append(result)
        return result

    def validate_robustness(
        self,
        recovery_attempts: int,
        successful_recoveries: int,
        total_failures: int,
    ) -> ValidationResult:
        """Validate robustness to failures.

        Args:
            recovery_attempts: Number of recovery attempts
            successful_recoveries: Successful recoveries
            total_failures: Total failures encountered

        Returns:
            Validation result
        """
        if total_failures == 0:
            recovery_rate = 1.0
            passed = True
        else:
            recovery_rate = successful_recoveries / total_failures if total_failures > 0 else 0
            passed = recovery_rate >= 0.7

        result = ValidationResult(
            check_name="robustness",
            status=ValidationStatus.PASSED if passed else ValidationStatus.FAILED,
            passed=passed,
            severity=SeverityLevel.HIGH,
            message=f"Robustness: {recovery_rate:.1%} recovery rate "
            f"({successful_recoveries}/{total_failures} failures)",
            details={
                "recovery_attempts": recovery_attempts,
                "successful_recoveries": successful_recoveries,
                "total_failures": total_failures,
                "recovery_rate": recovery_rate,
            },
        )

        self.validation_results.append(result)
        return result

    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report.

        Returns:
            Report dictionary
        """
        if not self.validation_results:
            return {}

        passed = sum(1 for r in self.validation_results if r.passed)
        failed = sum(1 for r in self.validation_results if not r.passed)

        by_severity = {}
        for result in self.validation_results:
            severity = result.severity.name
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(result.check_name)

        return {
            "total_checks": len(self.validation_results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.validation_results) if self.validation_results else 0,
            "by_severity": by_severity,
            "results": [
                {
                    "check": r.check_name,
                    "status": r.status.value,
                    "severity": r.severity.name,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.validation_results
            ],
        }


class ViolationDetector:
    """Detects and tracks violations."""

    def __init__(self):
        """Initialize detector."""
        self.violations: List[ViolationEvent] = []
        self.violation_counts: Dict[str, int] = {}

    def detect_violation(
        self,
        violation_type: str,
        severity: SeverityLevel,
        description: str,
        scenario_id: str,
        robot_state: Dict[str, Any],
        environment_state: Dict[str, Any],
    ) -> ViolationEvent:
        """Detect and record a violation.

        Args:
            violation_type: Type of violation
            severity: Severity level
            description: Description
            scenario_id: Scenario ID
            robot_state: Robot state at violation
            environment_state: Environment state at violation

        Returns:
            Recorded violation
        """
        violation_id = f"vio_{len(self.violations) + 1}"

        violation = ViolationEvent(
            violation_id=violation_id,
            violation_type=violation_type,
            severity=severity,
            description=description,
            timestamp=datetime.now().timestamp(),
            scenario_id=scenario_id,
            robot_state=robot_state,
            environment_state=environment_state,
        )

        self.violations.append(violation)

        # Update count
        self.violation_counts[violation_type] = (
            self.violation_counts.get(violation_type, 0) + 1
        )

        return violation

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get violation summary.

        Returns:
            Summary dictionary
        """
        if not self.violations:
            return {}

        by_severity = {level.name: 0 for level in SeverityLevel}
        for violation in self.violations:
            by_severity[violation.severity.name] += 1

        return {
            "total_violations": len(self.violations),
            "by_type": self.violation_counts,
            "by_severity": by_severity,
            "critical_count": by_severity["CRITICAL"],
        }


class RootCauseAnalyzer:
    """Analyzes root causes of violations."""

    def __init__(self):
        """Initialize analyzer."""
        self.analyses: List[RootCauseAnalysis] = []

    def analyze_violation(
        self,
        violation: ViolationEvent,
        event_history: List[Dict[str, Any]],
    ) -> RootCauseAnalysis:
        """Analyze root cause of violation.

        Args:
            violation: The violation event
            event_history: History of events leading to violation

        Returns:
            Root cause analysis
        """
        # Determine primary cause from violation type
        primary_cause_map = {
            "collision": "Obstacle detection failure",
            "gps_loss": "GPS signal unavailable",
            "motor_failure": "Motor malfunction",
            "communication_loss": "Communication channel disruption",
            "path_blocked": "Navigation path blocked",
            "timeout": "Mission timeout exceeded",
        }

        primary_cause = primary_cause_map.get(violation.violation_type, "Unknown cause")

        # Identify contributing factors from event history
        contributing_factors = []
        if event_history:
            # Analyze event chain
            for event in event_history[-5:]:  # Last 5 events
                if "failure" in str(event).lower():
                    contributing_factors.append(event.get("type", "failure"))

        # Build cascade chain
        cascade_chain = [
            "Initial trigger",
            "Propagation through system",
            "Recovery mechanism failure" if len(contributing_factors) > 2 else "Recovery attempted",
            "Final violation state",
        ]

        # Calculate probability and confidence
        probability_score = min(0.5 + len(contributing_factors) * 0.1, 1.0)
        confidence = min(0.7 + len(event_history) * 0.05, 1.0)

        # Generate mitigation
        mitigation_map = {
            "collision": "Improve obstacle detection or increase safety margins",
            "gps_loss": "Implement fallback navigation using inertial sensors",
            "motor_failure": "Add redundant motor control or predictive maintenance",
            "communication_loss": "Implement offline operation mode",
            "path_blocked": "Use dynamic replanning algorithm",
            "timeout": "Optimize pathfinding or increase time limits",
        }

        recommended_mitigation = mitigation_map.get(
            violation.violation_type, "Review system configuration and capabilities"
        )

        analysis = RootCauseAnalysis(
            violation_id=violation.violation_id,
            primary_cause=primary_cause,
            contributing_factors=contributing_factors,
            cascade_chain=cascade_chain,
            probability_score=probability_score,
            confidence=confidence,
            recommended_mitigation=recommended_mitigation,
        )

        self.analyses.append(analysis)
        return analysis

    def get_root_cause_report(self) -> Dict[str, Any]:
        """Get root cause analysis report.

        Returns:
            Report dictionary
        """
        if not self.analyses:
            return {}

        cause_frequency = {}
        for analysis in self.analyses:
            cause = analysis.primary_cause
            cause_frequency[cause] = cause_frequency.get(cause, 0) + 1

        avg_confidence = sum(a.confidence for a in self.analyses) / len(self.analyses)
        avg_probability = sum(a.probability_score for a in self.analyses) / len(self.analyses)

        return {
            "total_analyses": len(self.analyses),
            "primary_causes": cause_frequency,
            "average_confidence": avg_confidence,
            "average_probability": avg_probability,
            "top_cause": max(cause_frequency.items(), key=lambda x: x[1])[0]
            if cause_frequency
            else None,
            "analyses": [
                {
                    "violation_id": a.violation_id,
                    "primary_cause": a.primary_cause,
                    "contributing_factors": a.contributing_factors,
                    "confidence": a.confidence,
                    "mitigation": a.recommended_mitigation,
                }
                for a in self.analyses
            ],
        }


class ComprehensiveReportGenerator:
    """Generates comprehensive simulation reports."""

    def __init__(
        self,
        metrics_collector: PerformanceMetricsCollector,
        validation_framework: ValidationFramework,
        violation_detector: ViolationDetector,
        root_cause_analyzer: RootCauseAnalyzer,
    ):
        """Initialize report generator.

        Args:
            metrics_collector: Performance metrics collector
            validation_framework: Validation framework
            violation_detector: Violation detector
            root_cause_analyzer: Root cause analyzer
        """
        self.metrics_collector = metrics_collector
        self.validation_framework = validation_framework
        self.violation_detector = violation_detector
        self.root_cause_analyzer = root_cause_analyzer

    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary.

        Returns:
            Executive summary
        """
        validation_report = self.validation_framework.get_validation_report()
        violation_summary = self.violation_detector.get_violation_summary()
        metrics_stats = self.metrics_collector.get_metric_statistics()

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": (
                "PASSED" if validation_report.get("pass_rate", 0) > 0.8 else "FAILED"
            ),
            "validation_summary": {
                "total_checks": validation_report.get("total_checks", 0),
                "pass_rate": validation_report.get("pass_rate", 0),
            },
            "violation_summary": violation_summary,
            "performance": metrics_stats,
        }

    def generate_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed report.

        Returns:
            Detailed report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "executive_summary": self.generate_executive_summary(),
            "validation_report": self.validation_framework.get_validation_report(),
            "violation_report": self.violation_detector.get_violation_summary(),
            "root_cause_report": self.root_cause_analyzer.get_root_cause_report(),
            "performance_metrics": {
                "all_metrics": [
                    {
                        "name": m.name,
                        "type": m.metric_type.value,
                        "value": m.value,
                        "unit": m.unit,
                    }
                    for m in self.metrics_collector.get_all_metrics()
                ],
                "statistics": self.metrics_collector.get_metric_statistics(),
            },
        }

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for violation dashboard.

        Returns:
            Dashboard data
        """
        violations = self.violation_detector.violations
        analyses = self.root_cause_analyzer.analyses

        violation_timeline = sorted(violations, key=lambda v: v.timestamp)

        return {
            "timestamp": datetime.now().isoformat(),
            "violation_timeline": [
                {
                    "id": v.violation_id,
                    "type": v.violation_type,
                    "severity": v.severity.name,
                    "time": v.timestamp,
                    "scenario": v.scenario_id,
                }
                for v in violation_timeline
            ],
            "severity_breakdown": {
                level.name: len(
                    [v for v in violations if v.severity == level]
                )
                for level in SeverityLevel
            },
            "type_breakdown": self.violation_detector.violation_counts,
            "mitigation_recommendations": [
                {
                    "violation_id": a.violation_id,
                    "primary_cause": a.primary_cause,
                    "recommended_action": a.recommended_mitigation,
                    "confidence": a.confidence,
                }
                for a in analyses
            ],
        }
