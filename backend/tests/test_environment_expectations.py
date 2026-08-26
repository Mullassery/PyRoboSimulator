"""Tests for Environment Expectation Modeling Framework (Phase 3)."""

import time
import pytest

from src.services.environment_expectations import (
    EnvironmentProfile,
    EnvironmentType,
    Expectation,
    ExpectationEngine,
    ExpectationSeverity,
    ExpectationType,
    ExpectationValidator,
    ExpectationViolationSimulator,
    FleetLearningModule,
    GeographicProfile,
    RegionType,
)


class TestExpectation:
    """Test expectation definition."""

    def test_expectation_creation(self):
        """Test creating expectation."""
        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.PHYSICAL,
            description="Road is drivable",
            condition="road_drivable",
            probability=0.95,
            frequency=1.0,
            severity=ExpectationSeverity.HIGH,
            duration_min_s=10.0,
            duration_max_s=100.0,
            spatial_extent_m=100.0,
        )

        assert exp.id == "exp_1"
        assert exp.expectation_type == ExpectationType.PHYSICAL
        assert exp.probability == 0.95

    def test_expectation_should_apply(self):
        """Test expectation applicability."""
        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.WEATHER,
            description="Heavy rain",
            condition="heavy_rain",
            probability=0.8,
            frequency=1.0,
            severity=ExpectationSeverity.MEDIUM,
            duration_min_s=60.0,
            duration_max_s=600.0,
            spatial_extent_m=500.0,
            geographic_applicability=[RegionType.SOUTH_INDIA],
        )

        # Should apply to south india
        applies = exp.should_apply(time.time(), RegionType.SOUTH_INDIA, "rain")
        assert isinstance(applies, bool)

    def test_expectation_cascading_effects(self):
        """Test expectation with cascading effects."""
        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.WEATHER,
            description="Power outage",
            condition="power_outage",
            probability=0.01,
            frequency=0.1,
            severity=ExpectationSeverity.CRITICAL,
            duration_min_s=300.0,
            duration_max_s=3600.0,
            spatial_extent_m=1000.0,
            cascading_effects=["gps_unavailable", "cellular_unavailable", "traffic_lights_off"],
        )

        assert len(exp.cascading_effects) == 3
        assert "gps_unavailable" in exp.cascading_effects


class TestEnvironmentProfile:
    """Test environment profile."""

    def test_warehouse_profile(self):
        """Test warehouse environment profile."""
        profile = EnvironmentProfile(
            environment_type=EnvironmentType.WAREHOUSE,
            name="Standard Warehouse",
            description="Large scale logistics warehouse",
            default_weather="clear",
            gps_quality=0.3,  # GPS poor indoors
            network_availability=0.95,
            human_density_per_m2=0.5,
            noise_level_db=75.0,
        )

        assert profile.environment_type == EnvironmentType.WAREHOUSE
        assert profile.gps_quality == 0.3
        assert len(profile.expectations) == 0

    def test_urban_road_profile(self):
        """Test urban road profile."""
        profile = EnvironmentProfile(
            environment_type=EnvironmentType.URBAN_ROAD,
            name="City Street",
            description="Busy urban street",
            default_weather="clear",
            gps_quality=0.8,
            network_availability=0.98,
            human_density_per_m2=5.0,
            vehicle_density_per_m2=0.5,
            noise_level_db=85.0,
        )

        assert profile.human_density_per_m2 == 5.0
        assert profile.vehicle_density_per_m2 == 0.5

    def test_profile_to_dict(self):
        """Test profile serialization."""
        profile = EnvironmentProfile(
            environment_type=EnvironmentType.HOSPITAL,
            name="Hospital Corridor",
            description="Hospital internal corridor",
        )

        d = profile.to_dict()
        assert d["environment_type"] == "hospital"
        assert d["expectation_count"] == 0


class TestGeographicProfile:
    """Test geographic profile."""

    def test_north_india_profile(self):
        """Test North India geographic profile."""
        profile = GeographicProfile(
            region=RegionType.NORTH_INDIA,
            name="North India Roads",
            description="Dense mixed traffic, poor lane discipline",
            infrastructure_quality=0.6,
            human_cooperation_factor=0.7,
            gps_availability=0.85,
        )

        assert profile.region == RegionType.NORTH_INDIA
        assert profile.infrastructure_quality == 0.6
        assert profile.human_cooperation_factor == 0.7

    def test_tokyo_profile(self):
        """Test Tokyo geographic profile."""
        profile = GeographicProfile(
            region=RegionType.TOKYO,
            name="Tokyo Urban",
            description="High compliance, dense pedestrian traffic",
            infrastructure_quality=0.95,
            human_cooperation_factor=0.95,
            gps_availability=0.98,
        )

        assert profile.human_cooperation_factor == 0.95

    def test_profile_to_dict(self):
        """Test geographic profile serialization."""
        profile = GeographicProfile(
            region=RegionType.DUBAI,
            name="Dubai",
            description="Desert highways",
        )

        d = profile.to_dict()
        assert d["region"] == "dubai"


class TestExpectationEngine:
    """Test expectation engine."""

    def test_engine_creation(self):
        """Test creating engine."""
        engine = ExpectationEngine()
        assert len(engine.active_expectations) == 0

    def test_add_expectation(self):
        """Test adding expectations."""
        engine = ExpectationEngine()

        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.PHYSICAL,
            description="test",
            condition="test",
            probability=0.8,
            frequency=1.0,
            severity=ExpectationSeverity.MEDIUM,
            duration_min_s=10.0,
            duration_max_s=100.0,
            spatial_extent_m=50.0,
        )

        engine.add_expectation(exp)
        assert len(engine.active_expectations) == 1

    def test_evaluate_expectation_satisfied(self):
        """Test evaluating satisfied expectation."""
        engine = ExpectationEngine()

        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.PHYSICAL,
            description="road is drivable",
            condition="road_drivable",
            probability=1.0,  # Always applies
            frequency=1.0,
            severity=ExpectationSeverity.HIGH,
            duration_min_s=10.0,
            duration_max_s=100.0,
            spatial_extent_m=100.0,
            geographic_applicability=[RegionType.NEW_YORK],
        )

        engine.add_expectation(exp)

        # Evaluate when condition is met
        violated, reason = engine.evaluate_expectation(
            exp, time.time(), RegionType.NEW_YORK, "clear", actual_condition=True
        )

        assert not violated
        assert reason is None

    def test_evaluate_expectation_violated(self):
        """Test evaluating violated expectation."""
        engine = ExpectationEngine()

        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.INFRASTRUCTURE,
            description="gps available",
            condition="gps_available",
            probability=1.0,  # Always applies
            frequency=1.0,
            severity=ExpectationSeverity.CRITICAL,
            duration_min_s=10.0,
            duration_max_s=100.0,
            spatial_extent_m=100.0,
            geographic_applicability=[RegionType.TOKYO],
        )

        engine.add_expectation(exp)

        # Evaluate when condition is NOT met
        violated, reason = engine.evaluate_expectation(
            exp, time.time(), RegionType.TOKYO, "clear", actual_condition=False
        )

        assert violated
        assert "expected" in reason.lower()

    def test_get_violation_report(self):
        """Test getting violation report."""
        engine = ExpectationEngine()

        exp = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.SENSOR,
            description="camera working",
            condition="camera_functional",
            probability=1.0,
            frequency=1.0,
            severity=ExpectationSeverity.MEDIUM,
            duration_min_s=10.0,
            duration_max_s=100.0,
            spatial_extent_m=50.0,
        )

        engine.add_expectation(exp)

        # Trigger some violations
        for _ in range(3):
            engine.evaluate_expectation(exp, time.time(), RegionType.NEW_YORK, "clear", False)

        report = engine.get_violation_report()
        assert report["total_violations"] == 3


class TestExpectationViolationSimulator:
    """Test expectation violation simulator."""

    def test_trigger_violation(self):
        """Test triggering violation."""
        sim = ExpectationViolationSimulator()

        sim.trigger_violation(
            "vio_1",
            "gps_unavailable",
            {"accuracy": 0.0},
            duration_s=60.0,
        )

        assert sim.is_violation_active("vio_1")

    def test_violation_expiration(self):
        """Test violation expiration."""
        sim = ExpectationViolationSimulator()

        sim.trigger_violation(
            "vio_1",
            "gps_unavailable",
            {"accuracy": 0.0},
            duration_s=0.01,  # Very short
        )

        assert sim.is_violation_active("vio_1")

        # Wait for expiration
        time.sleep(0.1)

        assert not sim.is_violation_active("vio_1")

    def test_get_active_violations(self):
        """Test getting active violations."""
        sim = ExpectationViolationSimulator()

        sim.trigger_violation("vio_1", "gps_unavailable", {}, duration_s=60.0)
        sim.trigger_violation("vio_2", "camera_failure", {}, duration_s=60.0)

        active = sim.get_active_violations()
        assert len(active) == 2

    def test_end_violation_early(self):
        """Test ending violation early."""
        sim = ExpectationViolationSimulator()

        sim.trigger_violation("vio_1", "gps_unavailable", {}, duration_s=60.0)
        assert sim.is_violation_active("vio_1")

        sim.end_violation("vio_1")
        assert not sim.is_violation_active("vio_1")


class TestFleetLearningModule:
    """Test fleet learning."""

    def test_record_failed_expectation(self):
        """Test recording failed expectation."""
        module = FleetLearningModule()

        module.record_failed_expectation(
            "exp_1",
            EnvironmentType.WAREHOUSE,
            RegionType.NORTH_INDIA,
            {"timestamp": time.time()},
            "GPS signal lost",
        )

        assert len(module.failed_expectations) == 1

    def test_record_near_miss(self):
        """Test recording near miss."""
        module = FleetLearningModule()

        module.record_near_miss(
            "collision_avoidance",
            ExpectationSeverity.HIGH,
            "emergency_stop",
            "human_intervened",
        )

        assert len(module.near_misses) == 1

    def test_record_successful_recovery(self):
        """Test recording successful recovery."""
        module = FleetLearningModule()

        module.record_successful_recovery(
            "gps_loss",
            "inertial_navigation",
            recovery_time_s=30.0,
            mission_recovered=True,
        )

        assert len(module.successful_recoveries) == 1

    def test_generate_fleet_insights(self):
        """Test generating fleet insights."""
        module = FleetLearningModule()

        # Add some data
        for i in range(5):
            module.record_failed_expectation(
                f"exp_{i}",
                EnvironmentType.URBAN_ROAD,
                RegionType.NEW_YORK,
                {},
                "test",
            )

        insights = module.generate_fleet_insights()
        assert insights["total_failed_expectations"] == 5
        assert "high_risk_environments" in insights


class TestExpectationValidator:
    """Test expectation validator."""

    def test_create_validator(self):
        """Test creating validator."""
        engine = ExpectationEngine()
        validator = ExpectationValidator(engine)

        assert validator.expectation_engine == engine

    def test_validate_robot_action(self):
        """Test validating robot action."""
        engine = ExpectationEngine()
        validator = ExpectationValidator(engine)

        result = validator.validate_robot_action(
            "navigate_to_goal",
            {"environment": "warehouse"},
            ["goal_reached", "obstacles_avoided"],
            ["goal_reached", "obstacles_avoided"],
        )

        assert result["passed"]
        assert len(result["violations"]) == 0

    def test_validate_robot_action_failure(self):
        """Test validation failure."""
        engine = ExpectationEngine()
        validator = ExpectationValidator(engine)

        result = validator.validate_robot_action(
            "navigate_to_goal",
            {"environment": "warehouse"},
            ["goal_reached", "obstacles_avoided"],
            ["goal_reached"],  # Missing obstacle avoidance
        )

        assert not result["passed"]
        assert len(result["violations"]) > 0

    def test_get_validation_report(self):
        """Test getting validation report."""
        engine = ExpectationEngine()
        validator = ExpectationValidator(engine)

        # Validate multiple actions
        validator.validate_robot_action("move", {}, ["arrived"], ["arrived"])
        validator.validate_robot_action("stop", {}, ["stopped"], [])  # Failure

        report = validator.get_validation_report()
        assert report["total_validations"] == 2
        assert report["passed"] == 1
        assert report["failed"] == 1


class TestEnvironmentExpectationIntegration:
    """Integration tests for expectation system."""

    def test_full_scenario_with_expectations(self):
        """Test full scenario with expectations."""
        # Create profiles
        env_profile = EnvironmentProfile(
            environment_type=EnvironmentType.WAREHOUSE,
            name="Test Warehouse",
            description="Test warehouse",
        )

        geo_profile = GeographicProfile(
            region=RegionType.NORTH_INDIA,
            name="Test Region",
            description="Test region",
        )

        # Add expectations
        exp1 = Expectation(
            id="exp_1",
            expectation_type=ExpectationType.INFRASTRUCTURE,
            description="Network available",
            condition="network_available",
            probability=0.95,
            frequency=1.0,
            severity=ExpectationSeverity.MEDIUM,
            duration_min_s=60.0,
            duration_max_s=600.0,
            spatial_extent_m=100.0,
        )
        env_profile.expectations.append(exp1)

        # Create engine and add expectation
        engine = ExpectationEngine()
        engine.add_expectation(exp1)

        # Create violation simulator
        sim = ExpectationViolationSimulator()

        # Inject violation
        sim.trigger_violation("vio_1", "network_unavailable", {}, duration_s=30.0)

        # Verify violation is active
        assert sim.is_violation_active("vio_1")

        # Evaluate expectation (should be violated)
        violated, reason = engine.evaluate_expectation(
            exp1, time.time(), RegionType.NORTH_INDIA, "clear", actual_condition=False
        )

        assert violated

    def test_multi_expectation_scenario(self):
        """Test scenario with multiple expectation types."""
        engine = ExpectationEngine()

        expectations = [
            Expectation(
                id="exp_physical",
                expectation_type=ExpectationType.PHYSICAL,
                description="Road drivable",
                condition="road_drivable",
                probability=0.95,
                frequency=1.0,
                severity=ExpectationSeverity.HIGH,
                duration_min_s=10.0,
                duration_max_s=100.0,
                spatial_extent_m=50.0,
            ),
            Expectation(
                id="exp_weather",
                expectation_type=ExpectationType.WEATHER,
                description="No rain",
                condition="no_rain",
                probability=0.7,
                frequency=1.0,
                severity=ExpectationSeverity.LOW,
                duration_min_s=60.0,
                duration_max_s=600.0,
                spatial_extent_m=100.0,
            ),
            Expectation(
                id="exp_sensor",
                expectation_type=ExpectationType.SENSOR,
                description="GPS working",
                condition="gps_working",
                probability=0.9,
                frequency=1.0,
                severity=ExpectationSeverity.MEDIUM,
                duration_min_s=30.0,
                duration_max_s=300.0,
                spatial_extent_m=50.0,
            ),
        ]

        for exp in expectations:
            engine.add_expectation(exp)

        assert len(engine.active_expectations) == 3

        report = engine.get_violation_report()
        assert report["total_violations"] == 0
