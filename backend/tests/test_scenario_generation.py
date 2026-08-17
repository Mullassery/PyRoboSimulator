"""Tests for Advanced Scenario Generation Engine (Phase 3.1)."""

import pytest

from backend.src.services.scenario_generation import (
    AdvancedScenarioGenerator,
    CurriculumLesson,
    DifficultyLevel,
    GeneratedScenario,
    ScenarioClass,
)


class TestDifficultyLevel:
    """Test difficulty levels."""

    def test_difficulty_values(self):
        """Test difficulty level values."""
        assert DifficultyLevel.TRIVIAL.value == 0.1
        assert DifficultyLevel.EASY.value == 0.3
        assert DifficultyLevel.MEDIUM.value == 0.5
        assert DifficultyLevel.HARD.value == 0.7
        assert DifficultyLevel.EXPERT.value == 0.9
        assert DifficultyLevel.EXTREME.value == 1.0

    def test_difficulty_ordering(self):
        """Test difficulty ordering."""
        difficulties = [d.value for d in DifficultyLevel]
        assert difficulties == sorted(difficulties)


class TestScenarioClass:
    """Test scenario classification."""

    def test_scenario_classes(self):
        """Test scenario class values."""
        assert ScenarioClass.NOMINAL.value == "nominal"
        assert ScenarioClass.DEGRADED.value == "degraded"
        assert ScenarioClass.CRISIS.value == "crisis"
        assert ScenarioClass.CATASTROPHIC.value == "catastrophic"


class TestGeneratedScenario:
    """Test generated scenario dataclass."""

    def test_scenario_creation(self):
        """Test creating a generated scenario."""
        scenario = GeneratedScenario(
            scenario_id="scenario_1",
            class_=ScenarioClass.NOMINAL,
            difficulty=0.3,
            environment="warehouse",
            region="north_india",
            weather="clear",
            time_of_day="morning",
            day_of_week="weekday",
            season="summer",
            human_density=0.5,
            vehicle_density=0.1,
            sensor_degradation=0.05,
            active_violations=[],
            rare_events=[],
            infrastructure_failures=[],
            expectations_count=10,
            validation_checkpoints=["initial_position_valid", "goal_reachable"],
        )

        assert scenario.scenario_id == "scenario_1"
        assert scenario.class_ == ScenarioClass.NOMINAL
        assert scenario.difficulty == 0.3
        assert scenario.environment == "warehouse"
        assert scenario.region == "north_india"

    def test_scenario_with_violations(self):
        """Test scenario with violations."""
        scenario = GeneratedScenario(
            scenario_id="scenario_2",
            class_=ScenarioClass.DEGRADED,
            difficulty=0.45,
            environment="urban_road",
            region="new_york",
            weather="rain",
            time_of_day="evening",
            day_of_week="weekend",
            season="spring",
            human_density=2.0,
            vehicle_density=0.5,
            sensor_degradation=0.15,
            active_violations=["gps_unavailable", "communication_loss"],
            rare_events=["flooded_road"],
            infrastructure_failures=["traffic_lights"],
            expectations_count=15,
            validation_checkpoints=["recovery_attempted"],
        )

        assert len(scenario.active_violations) == 2
        assert "gps_unavailable" in scenario.active_violations
        assert len(scenario.rare_events) == 1


class TestAdvancedScenarioGenerator:
    """Test advanced scenario generator."""

    def test_generator_creation(self):
        """Test creating generator."""
        gen = AdvancedScenarioGenerator()

        assert gen.scenario_counter == 0
        assert len(gen.generated_scenarios) == 0
        assert len(gen.curriculum_lessons) == 0

    def test_create_curriculum_lesson(self):
        """Test creating curriculum lesson."""
        gen = AdvancedScenarioGenerator()

        lesson = gen.create_curriculum_lesson(
            lesson_id="lesson_1",
            name="Basic Navigation",
            description="Learn basic obstacle avoidance",
            difficulty_range=(0.1, 0.3),
            scenario_count=10,
            environment_weights={"warehouse": 0.7, "urban_road": 0.3},
            region_weights={"north_india": 1.0},
            violation_probability=0.05,
            rare_event_probability=0.01,
            learning_objectives=["avoid_obstacles", "reach_goal"],
        )

        assert lesson.lesson_id == "lesson_1"
        assert lesson.name == "Basic Navigation"
        assert lesson.difficulty_range == (0.1, 0.3)
        assert lesson.scenario_count == 10

    def test_curriculum_lesson_storage(self):
        """Test curriculum lesson storage."""
        gen = AdvancedScenarioGenerator()

        gen.create_curriculum_lesson(
            lesson_id="lesson_1",
            name="Lesson 1",
            description="Test",
            difficulty_range=(0.1, 0.3),
            scenario_count=5,
            environment_weights={"warehouse": 1.0},
            region_weights={"north_india": 1.0},
            violation_probability=0.05,
            rare_event_probability=0.01,
            learning_objectives=["test"],
        )

        assert "lesson_1" in gen.curriculum_lessons
        assert gen.curriculum_lessons["lesson_1"].name == "Lesson 1"

    def test_generate_scenarios_for_lesson(self):
        """Test generating scenarios for a lesson."""
        gen = AdvancedScenarioGenerator()

        gen.create_curriculum_lesson(
            lesson_id="lesson_1",
            name="Basic",
            description="Test",
            difficulty_range=(0.2, 0.4),
            scenario_count=20,
            environment_weights={"warehouse": 0.5, "urban_road": 0.5},
            region_weights={"north_india": 0.5, "new_york": 0.5},
            violation_probability=0.1,
            rare_event_probability=0.05,
            learning_objectives=["navigation"],
        )

        scenarios = gen.generate_scenarios_for_lesson("lesson_1")

        assert len(scenarios) == 20
        assert len(gen.generated_scenarios) == 20

        # Check scenario properties
        for scenario in scenarios:
            assert scenario.scenario_id is not None
            assert 0.2 <= scenario.difficulty <= 0.4
            assert scenario.class_ in [
                ScenarioClass.NOMINAL,
                ScenarioClass.DEGRADED,
            ]

    def test_generate_scenarios_for_nonexistent_lesson(self):
        """Test error handling for nonexistent lesson."""
        gen = AdvancedScenarioGenerator()

        with pytest.raises(ValueError):
            gen.generate_scenarios_for_lesson("nonexistent")

    def test_generate_scenario_batch(self):
        """Test generating batch of scenarios."""
        gen = AdvancedScenarioGenerator()

        scenarios = gen.generate_scenario_batch(count=50)

        assert len(scenarios) == 50
        assert len(gen.generated_scenarios) == 50

        # Check scenario variety
        environments = {s.environment for s in scenarios}
        regions = {s.region for s in scenarios}

        assert len(environments) > 1
        assert len(regions) > 1

    def test_generate_scenario_batch_with_custom_distribution(self):
        """Test batch generation with custom distributions."""
        gen = AdvancedScenarioGenerator()

        difficulty_dist = {DifficultyLevel.HARD: 0.7, DifficultyLevel.EXPERT: 0.3}
        env_dist = {"urban_road": 1.0}
        region_dist = {"new_york": 1.0}

        scenarios = gen.generate_scenario_batch(
            count=30,
            difficulty_distribution=difficulty_dist,
            environment_distribution=env_dist,
            region_distribution=region_dist,
        )

        assert len(scenarios) == 30

        # All should be urban_road
        assert all(s.environment == "urban_road" for s in scenarios)

        # All should be new_york
        assert all(s.region == "new_york" for s in scenarios)

    def test_scenario_difficulty_classification(self):
        """Test scenario classification by difficulty."""
        gen = AdvancedScenarioGenerator()

        # Generate scenarios across difficulty range
        scenarios = gen.generate_scenario_batch(count=100)

        # Check classification
        nominal = [s for s in scenarios if s.class_ == ScenarioClass.NOMINAL]
        degraded = [s for s in scenarios if s.class_ == ScenarioClass.DEGRADED]
        crisis = [s for s in scenarios if s.class_ == ScenarioClass.CRISIS]
        catastrophic = [
            s for s in scenarios if s.class_ == ScenarioClass.CATASTROPHIC
        ]

        # All classes should be represented
        assert len(nominal) > 0
        assert len(degraded) > 0
        assert len(crisis) > 0
        assert len(catastrophic) > 0

        # Check difficulty ranges for each class (must match the real
        # thresholds in AdvancedScenarioGenerator._generate_base_scenario).
        for s in nominal:
            assert s.difficulty < 0.35

        for s in degraded:
            assert 0.35 <= s.difficulty < 0.6

        for s in crisis:
            assert 0.6 <= s.difficulty < 0.8

        for s in catastrophic:
            assert s.difficulty >= 0.8

    def test_scenario_weather_selection(self):
        """Test weather selection by region."""
        gen = AdvancedScenarioGenerator()

        # Generate scenarios for specific regions
        scenarios = gen.generate_scenario_batch(
            count=100,
            environment_distribution={"warehouse": 1.0},
            region_distribution={"north_india": 1.0},
        )

        weathers = {s.weather for s in scenarios}

        # North India should have specific weather types
        north_india_weather = {"clear", "dust", "hot"}
        assert weathers.issubset(north_india_weather)

    def test_scenario_time_and_density(self):
        """Test time of day and density relationships."""
        gen = AdvancedScenarioGenerator()

        scenarios = gen.generate_scenario_batch(count=100)

        # Verify times of day are valid
        valid_times = {"morning", "afternoon", "evening", "night"}
        assert all(s.time_of_day in valid_times for s in scenarios)

        # Verify days of week are valid
        valid_days = {"weekday", "weekend"}
        assert all(s.day_of_week in valid_days for s in scenarios)

        # Verify seasons are valid
        valid_seasons = {"spring", "summer", "fall", "winter"}
        assert all(s.season in valid_seasons for s in scenarios)

        # Night should have lower human density (generally)
        night_scenarios = [s for s in scenarios if s.time_of_day == "night"]
        if night_scenarios:
            avg_night_density = sum(
                s.human_density for s in night_scenarios
            ) / len(night_scenarios)

            day_scenarios = [s for s in scenarios if s.time_of_day != "night"]
            avg_day_density = sum(s.human_density for s in day_scenarios) / len(
                day_scenarios
            )

            # On average night should have lower density
            assert avg_night_density < avg_day_density

    def test_scenario_violations_by_class(self):
        """Test violation generation by scenario class."""
        gen = AdvancedScenarioGenerator()

        # Generate nominal scenarios (should have few violations).
        # Bounded retry: with the default difficulty_distribution this
        # should converge in 1-2 batches (NOMINAL is roughly TRIVIAL+EASY
        # under the real classification thresholds). A previous version of
        # this loop had no iteration cap, and a since-fixed threshold bug
        # made NOMINAL unreachable under the default distribution at all --
        # that combination hung the whole suite indefinitely. The cap here
        # turns "unreachable" into a fast, clear test failure instead.
        nominal_scenarios = []
        for _ in range(50):
            if len(nominal_scenarios) >= 20:
                break
            gen.scenario_counter = 0
            gen.generated_scenarios = []
            batch = gen.generate_scenario_batch(count=100)
            nominal_scenarios.extend([s for s in batch if s.class_ == ScenarioClass.NOMINAL])
            nominal_scenarios = nominal_scenarios[:20]
        assert len(nominal_scenarios) >= 20, (
            "Failed to generate 20 NOMINAL scenarios in 50 batches of 100 -- "
            "NOMINAL may be unreachable under the default difficulty_distribution."
        )

        avg_nominal_violations = sum(
            len(s.active_violations) for s in nominal_scenarios
        ) / len(nominal_scenarios)

        # Generate catastrophic scenarios (should have more violations)
        gen.scenario_counter = 0
        gen.generated_scenarios = []
        difficulty_dist = {DifficultyLevel.EXTREME: 1.0}
        catastrophic_scenarios = gen.generate_scenario_batch(
            count=20, difficulty_distribution=difficulty_dist
        )
        catastrophic_scenarios = [
            s for s in catastrophic_scenarios if s.class_ == ScenarioClass.CATASTROPHIC
        ]

        if catastrophic_scenarios:
            avg_catastrophic_violations = sum(
                len(s.active_violations) for s in catastrophic_scenarios
            ) / len(catastrophic_scenarios)

            assert avg_catastrophic_violations > avg_nominal_violations

    def test_scenario_expectations_count(self):
        """Test expectations count calculation."""
        gen = AdvancedScenarioGenerator()

        scenarios = gen.generate_scenario_batch(count=50)

        for scenario in scenarios:
            # Expectations should scale with difficulty
            expected_min = 5
            expected_max = 5 + int(1.0 * 20)  # 25

            assert expected_min <= scenario.expectations_count <= expected_max

            # Higher difficulty = more expectations
            assert scenario.expectations_count >= expected_min

    def test_scenario_validation_checkpoints(self):
        """Test validation checkpoint generation."""
        gen = AdvancedScenarioGenerator()

        scenarios = gen.generate_scenario_batch(count=50)

        for scenario in scenarios:
            # All should have checkpoints
            assert len(scenario.validation_checkpoints) > 0

            # Basic checkpoints should be present for nominal
            if scenario.class_ == ScenarioClass.NOMINAL:
                assert "initial_position_valid" in scenario.validation_checkpoints
                assert "goal_reachable" in scenario.validation_checkpoints

    def test_get_scenario_statistics(self):
        """Test getting scenario statistics."""
        gen = AdvancedScenarioGenerator()

        gen.generate_scenario_batch(count=100)

        stats = gen.get_scenario_statistics()

        assert stats["total_scenarios"] == 100
        assert "class_distribution" in stats
        assert "average_difficulty" in stats
        assert "average_violations_per_scenario" in stats

        # Check class distribution sums to total
        class_total = sum(stats["class_distribution"].values())
        assert class_total == 100

    def test_multiple_lessons_scenario_generation(self):
        """Test generating multiple curriculum lessons."""
        gen = AdvancedScenarioGenerator()

        # Create multiple lessons
        for i in range(3):
            gen.create_curriculum_lesson(
                lesson_id=f"lesson_{i}",
                name=f"Lesson {i}",
                description=f"Test lesson {i}",
                difficulty_range=(0.1 * i, 0.3 + 0.2 * i),
                scenario_count=10,
                environment_weights={"warehouse": 1.0},
                region_weights={"north_india": 1.0},
                violation_probability=0.05 * (i + 1),
                rare_event_probability=0.01 * (i + 1),
                learning_objectives=[f"objective_{i}"],
            )

        # Generate scenarios for all lessons
        all_scenarios = []
        for i in range(3):
            scenarios = gen.generate_scenarios_for_lesson(f"lesson_{i}")
            all_scenarios.extend(scenarios)

        assert len(all_scenarios) == 30

        # Verify difficulty progression
        lesson_0_scenarios = all_scenarios[0:10]
        lesson_1_scenarios = all_scenarios[10:20]
        lesson_2_scenarios = all_scenarios[20:30]

        avg_diff_0 = sum(s.difficulty for s in lesson_0_scenarios) / len(lesson_0_scenarios)
        avg_diff_1 = sum(s.difficulty for s in lesson_1_scenarios) / len(lesson_1_scenarios)
        avg_diff_2 = sum(s.difficulty for s in lesson_2_scenarios) / len(lesson_2_scenarios)

        # Later lessons should be harder
        assert avg_diff_0 < avg_diff_1 < avg_diff_2

    def test_scenario_counter_increment(self):
        """Test scenario counter increments correctly."""
        gen = AdvancedScenarioGenerator()

        batch_1 = gen.generate_scenario_batch(count=10)
        batch_2 = gen.generate_scenario_batch(count=10)

        # Check IDs are unique and sequential
        ids_1 = [s.scenario_id for s in batch_1]
        ids_2 = [s.scenario_id for s in batch_2]

        assert ids_1 == [f"scenario_{i}" for i in range(1, 11)]
        assert ids_2 == [f"scenario_{i}" for i in range(11, 21)]

    def test_sensor_degradation(self):
        """Test sensor degradation calculation."""
        gen = AdvancedScenarioGenerator()

        # Easy scenarios should have less degradation
        easy_dist = {DifficultyLevel.EASY: 1.0}
        easy_scenarios = gen.generate_scenario_batch(
            count=20, difficulty_distribution=easy_dist
        )

        # Hard scenarios should have more degradation
        gen.scenario_counter = 0
        gen.generated_scenarios = []
        hard_dist = {DifficultyLevel.HARD: 1.0}
        hard_scenarios = gen.generate_scenario_batch(
            count=20, difficulty_distribution=hard_dist
        )

        avg_easy_degradation = sum(
            s.sensor_degradation for s in easy_scenarios
        ) / len(easy_scenarios)
        avg_hard_degradation = sum(
            s.sensor_degradation for s in hard_scenarios
        ) / len(hard_scenarios)

        assert avg_hard_degradation > avg_easy_degradation

    def test_empty_statistics(self):
        """Test statistics for empty generator."""
        gen = AdvancedScenarioGenerator()

        stats = gen.get_scenario_statistics()

        # Should return empty dict for no scenarios
        assert stats == {}

    def test_rare_events_distribution(self):
        """Test rare events distribution by scenario class."""
        gen = AdvancedScenarioGenerator()

        # Generate nominal scenarios
        nominal_scenarios = []
        while len(nominal_scenarios) < 50:
            batch = gen.generate_scenario_batch(count=100)
            nominal_scenarios.extend([s for s in batch if s.class_ == ScenarioClass.NOMINAL])
            nominal_scenarios = nominal_scenarios[:50]

        avg_nominal_events = sum(
            len(s.rare_events) for s in nominal_scenarios
        ) / len(nominal_scenarios)

        # Nominal should have few or no rare events
        assert avg_nominal_events < 0.5
