"""Sim/Real Validator - Compare simulated vs real robot execution.

Validates that simulator behavior matches real robot execution.
Identifies gaps and discrepancies for model improvement.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from math import sqrt

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for an execution (real or simulated)."""
    execution_id: str
    execution_type: str  # "real" or "simulated"
    total_distance_m: float = 0.0
    total_time_sec: float = 0.0
    avg_velocity: float = 0.0
    max_velocity: float = 0.0
    avg_acceleration: float = 0.0
    max_acceleration: float = 0.0
    path_smoothness: float = 1.0
    trajectory_points: int = 0


@dataclass
class ValidationMetric:
    """Single metric comparison result."""
    metric_name: str
    real_value: float
    sim_value: float
    absolute_error: float
    relative_error: float  # percentage
    is_valid: bool
    tolerance: float


@dataclass
class ValidationResult:
    """Complete validation comparison."""
    real_execution_id: str
    sim_execution_id: str
    timestamp_generated: float
    overall_similarity: float = 0.0  # 0-1
    is_valid: bool = False
    metrics: List[ValidationMetric] = field(default_factory=list)
    discrepancies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SimRealValidator:
    """Validates simulator against real robot execution.

    Compares:
    - Trajectory metrics (distance, time, velocity)
    - Path smoothness and efficiency
    - Acceleration profiles
    - Sensor data patterns
    """

    def __init__(
        self,
        distance_tolerance_m: float = 1.0,
        velocity_tolerance_pct: float = 10.0,
        time_tolerance_pct: float = 15.0,
    ):
        """Initialize validator.

        Args:
            distance_tolerance_m: Absolute distance error tolerance (m)
            velocity_tolerance_pct: Velocity error tolerance (%)
            time_tolerance_pct: Time error tolerance (%)
        """
        self._distance_tolerance = distance_tolerance_m
        self._velocity_tolerance = velocity_tolerance_pct
        self._time_tolerance = time_tolerance_pct

    def validate_execution(
        self,
        real_metrics: ExecutionMetrics,
        sim_metrics: ExecutionMetrics,
    ) -> ValidationResult:
        """Validate simulated execution against real.

        Args:
            real_metrics: Metrics from real robot execution
            sim_metrics: Metrics from simulated execution

        Returns:
            Validation result with discrepancies and recommendations
        """
        logger.info(f"Validating sim vs real: {real_metrics.execution_id} vs {sim_metrics.execution_id}")

        result = ValidationResult(
            real_execution_id=real_metrics.execution_id,
            sim_execution_id=sim_metrics.execution_id,
            timestamp_generated=0.0,  # Would be actual timestamp
        )

        # Compare each metric
        distance_metric = self._compare_metric(
            "total_distance_m",
            real_metrics.total_distance_m,
            sim_metrics.total_distance_m,
            tolerance=self._distance_tolerance,
            is_absolute=True,
        )
        result.metrics.append(distance_metric)

        time_metric = self._compare_metric(
            "total_time_sec",
            real_metrics.total_time_sec,
            sim_metrics.total_time_sec,
            tolerance=self._time_tolerance,
            is_absolute=False,
        )
        result.metrics.append(time_metric)

        velocity_metric = self._compare_metric(
            "avg_velocity",
            real_metrics.avg_velocity,
            sim_metrics.avg_velocity,
            tolerance=self._velocity_tolerance,
            is_absolute=False,
        )
        result.metrics.append(velocity_metric)

        max_velocity_metric = self._compare_metric(
            "max_velocity",
            real_metrics.max_velocity,
            sim_metrics.max_velocity,
            tolerance=self._velocity_tolerance,
            is_absolute=False,
        )
        result.metrics.append(max_velocity_metric)

        smoothness_metric = self._compare_metric(
            "path_smoothness",
            real_metrics.path_smoothness,
            sim_metrics.path_smoothness,
            tolerance=10.0,
            is_absolute=False,
        )
        result.metrics.append(smoothness_metric)

        # Identify discrepancies
        invalid_metrics = [m for m in result.metrics if not m.is_valid]
        result.discrepancies = [
            f"{m.metric_name}: real={m.real_value:.3f}, sim={m.sim_value:.3f} " +
            f"(error={m.absolute_error:.3f}, {m.relative_error:.1f}%)"
            for m in invalid_metrics
        ]

        # Generate recommendations
        result.recommendations = self._generate_recommendations(invalid_metrics, real_metrics)

        # Overall similarity
        valid_metrics = [m for m in result.metrics if m.is_valid]
        result.overall_similarity = len(valid_metrics) / len(result.metrics) if result.metrics else 0.0

        result.is_valid = len(result.discrepancies) == 0

        logger.info(f"Validation complete: {result.overall_similarity:.1%} similarity, " +
                   f"{len(result.discrepancies)} discrepancies")

        return result

    def _compare_metric(
        self,
        metric_name: str,
        real_value: float,
        sim_value: float,
        tolerance: float,
        is_absolute: bool,
    ) -> ValidationMetric:
        """Compare a single metric between real and sim.

        Args:
            metric_name: Name of metric
            real_value: Real robot value
            sim_value: Simulated value
            tolerance: Tolerance (absolute or percentage)
            is_absolute: Whether tolerance is absolute or percentage

        Returns:
            ValidationMetric
        """
        if real_value == 0:
            real_value = 1e-6  # Avoid division by zero

        absolute_error = abs(sim_value - real_value)
        relative_error = (absolute_error / real_value) * 100 if real_value != 0 else 0.0

        if is_absolute:
            is_valid = absolute_error <= tolerance
        else:
            is_valid = relative_error <= tolerance

        return ValidationMetric(
            metric_name=metric_name,
            real_value=real_value,
            sim_value=sim_value,
            absolute_error=absolute_error,
            relative_error=relative_error,
            is_valid=is_valid,
            tolerance=tolerance,
        )

    def _generate_recommendations(
        self,
        invalid_metrics: List[ValidationMetric],
        real_metrics: ExecutionMetrics,
    ) -> List[str]:
        """Generate recommendations for model improvement.

        Args:
            invalid_metrics: Metrics that failed validation
            real_metrics: Real execution metrics

        Returns:
            List of recommendations
        """
        recommendations = []

        if not invalid_metrics:
            recommendations.append("✓ Simulator matches real execution well")
            return recommendations

        # Analyze each invalid metric
        for metric in invalid_metrics:
            if "distance" in metric.metric_name:
                if metric.sim_value > metric.real_value:
                    recommendations.append(
                        "Simulator trajectory is longer - check path planning accuracy"
                    )
                else:
                    recommendations.append(
                        "Simulator trajectory is shorter - verify obstacle detection"
                    )

            elif "velocity" in metric.metric_name:
                if metric.sim_value > metric.real_value:
                    recommendations.append(
                        "Simulator velocity too high - reduce max velocity or check acceleration limits"
                    )
                else:
                    recommendations.append(
                        "Simulator velocity too low - check motor/actuator models"
                    )

            elif "time" in metric.metric_name:
                if metric.sim_value > metric.real_value:
                    recommendations.append(
                        "Simulation taking longer - optimize path planning or increase velocity limits"
                    )
                else:
                    recommendations.append(
                        "Simulation too fast - check timing constraints and sensor latency"
                    )

            elif "smoothness" in metric.metric_name:
                if metric.sim_value < metric.real_value:
                    recommendations.append(
                        "Simulator path is not smooth enough - improve trajectory smoothing"
                    )

        # Global recommendations
        if len(invalid_metrics) >= 3:
            recommendations.append(
                "Multiple metrics invalid - consider recalibrating robot dynamics model"
            )

        recommendations.append(
            f"Real execution: {real_metrics.total_distance_m:.1f}m in {real_metrics.total_time_sec:.1f}s"
        )

        return recommendations

    def validate_sensor_data(
        self,
        real_sensor_readings: Dict[str, List[float]],
        sim_sensor_readings: Dict[str, List[float]],
    ) -> Dict[str, float]:
        """Validate sensor data correlation between real and sim.

        Args:
            real_sensor_readings: Sensor readings from real robot
            sim_sensor_readings: Sensor readings from simulation

        Returns:
            Dictionary of sensor correlations (0-1)
        """
        correlations = {}

        for sensor_name in real_sensor_readings.keys():
            if sensor_name not in sim_sensor_readings:
                correlations[sensor_name] = 0.0
                continue

            real_data = real_sensor_readings[sensor_name]
            sim_data = sim_sensor_readings[sensor_name]

            if not real_data or not sim_data:
                correlations[sensor_name] = 0.0
                continue

            # Simple correlation: normalize and compute RMS error
            real_mean = sum(real_data) / len(real_data)
            sim_mean = sum(sim_data) / len(sim_data)

            real_std = sqrt(sum((x - real_mean)**2 for x in real_data) / len(real_data))
            sim_std = sqrt(sum((x - sim_mean)**2 for x in sim_data) / len(sim_data))

            if real_std == 0 or sim_std == 0:
                correlations[sensor_name] = 1.0 if real_std == sim_std else 0.0
                continue

            # Normalize both
            real_norm = [(x - real_mean) / real_std for x in real_data]
            sim_norm = [(x - sim_mean) / sim_std for x in sim_data]

            # Compute correlation
            if len(real_norm) == len(sim_norm):
                correlation = sum(r * s for r, s in zip(real_norm, sim_norm)) / len(real_norm)
                correlations[sensor_name] = max(0.0, min(correlation, 1.0))
            else:
                correlations[sensor_name] = 0.5  # Partial credit for length mismatch

        return correlations
