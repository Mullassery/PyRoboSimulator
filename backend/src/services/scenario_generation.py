"""Advanced Scenario Generation Engine for Phase 3.1.

Generates millions of diverse, realistic scenarios by combining
environment profiles, geographic constraints, weather, and expectations.
Supports curriculum learning and difficulty scaling.
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Difficulty levels for scenario generation."""

    TRIVIAL = 0.1
    EASY = 0.3
    MEDIUM = 0.5
    HARD = 0.7
    EXPERT = 0.9
    EXTREME = 1.0


class ScenarioClass(Enum):
    """Classification of generated scenarios."""

    NOMINAL = "nominal"  # Expected conditions
    DEGRADED = "degraded"  # Some systems failing
    CRISIS = "crisis"  # Multiple failures
    CATASTROPHIC = "catastrophic"  # System breakdown


@dataclass
class CurriculumLesson:
    """Single lesson in curriculum learning progression."""

    lesson_id: str
    name: str
    description: str
    difficulty_range: Tuple[float, float]  # (min, max)
    scenario_count: int
    environment_weights: Dict[str, float]  # environment -> probability
    region_weights: Dict[str, float]  # region -> probability
    violation_probability: float  # 0-1
    rare_event_probability: float  # 0-1
    learning_objectives: List[str]


@dataclass
class GeneratedScenario:
    """A generated scenario with full specification."""

    scenario_id: str
    class_: ScenarioClass
    difficulty: float
    environment: str
    region: str
    weather: str
    time_of_day: str
    day_of_week: str
    season: str
    human_density: float
    vehicle_density: float
    sensor_degradation: float
    active_violations: List[str]
    rare_events: List[str]
    infrastructure_failures: List[str]
    expectations_count: int
    validation_checkpoints: List[str]


class AdvancedScenarioGenerator:
    """Advanced scenario generation with curriculum learning."""

    def __init__(self):
        """Initialize generator."""
        self.scenario_counter = 0
        self.generated_scenarios: List[GeneratedScenario] = []
        self.curriculum_lessons: Dict[str, CurriculumLesson] = {}
        self.difficulty_distribution: Dict[float, int] = {}

    def create_curriculum_lesson(
        self,
        lesson_id: str,
        name: str,
        description: str,
        difficulty_range: Tuple[float, float],
        scenario_count: int,
        environment_weights: Dict[str, float],
        region_weights: Dict[str, float],
        violation_probability: float,
        rare_event_probability: float,
        learning_objectives: List[str],
    ) -> CurriculumLesson:
        """Create curriculum lesson.

        Args:
            lesson_id: Unique lesson identifier
            name: Lesson name
            description: Lesson description
            difficulty_range: (min, max) difficulty
            scenario_count: Number of scenarios in lesson
            environment_weights: Environment probabilities
            region_weights: Region probabilities
            violation_probability: Violation injection rate
            rare_event_probability: Rare event rate
            learning_objectives: What agent should learn

        Returns:
            CurriculumLesson instance
        """
        lesson = CurriculumLesson(
            lesson_id=lesson_id,
            name=name,
            description=description,
            difficulty_range=difficulty_range,
            scenario_count=scenario_count,
            environment_weights=environment_weights,
            region_weights=region_weights,
            violation_probability=violation_probability,
            rare_event_probability=rare_event_probability,
            learning_objectives=learning_objectives,
        )

        self.curriculum_lessons[lesson_id] = lesson
        logger.info(f"Created curriculum lesson: {name}")
        return lesson

    def generate_scenarios_for_lesson(
        self, lesson_id: str, vary_parameters: bool = True
    ) -> List[GeneratedScenario]:
        """Generate scenarios for a curriculum lesson.

        Args:
            lesson_id: Lesson identifier
            vary_parameters: Whether to vary parameters

        Returns:
            List of generated scenarios
        """
        if lesson_id not in self.curriculum_lessons:
            raise ValueError(f"Unknown lesson: {lesson_id}")

        lesson = self.curriculum_lessons[lesson_id]
        scenarios = []

        for i in range(lesson.scenario_count):
            # Select difficulty within lesson range
            difficulty = random.uniform(lesson.difficulty_range[0], lesson.difficulty_range[1])

            # Select environment based on weights
            environment = random.choices(
                list(lesson.environment_weights.keys()),
                weights=list(lesson.environment_weights.values()),
            )[0]

            # Select region based on weights
            region = random.choices(
                list(lesson.region_weights.keys()),
                weights=list(lesson.region_weights.values()),
            )[0]

            # Generate scenario
            scenario = self._generate_base_scenario(
                environment,
                region,
                difficulty,
                lesson.violation_probability,
                lesson.rare_event_probability,
            )

            scenarios.append(scenario)
            self.generated_scenarios.append(scenario)

        logger.info(f"Generated {lesson.scenario_count} scenarios for lesson {lesson_id}")
        return scenarios

    def generate_scenario_batch(
        self,
        count: int = 1000,
        difficulty_distribution: Optional[Dict[DifficultyLevel, float]] = None,
        environment_distribution: Optional[Dict[str, float]] = None,
        region_distribution: Optional[Dict[str, float]] = None,
    ) -> List[GeneratedScenario]:
        """Generate batch of scenarios with specified distributions.

        Args:
            count: Number of scenarios to generate
            difficulty_distribution: Probability distribution over difficulties
            environment_distribution: Probability distribution over environments
            region_distribution: Probability distribution over regions

        Returns:
            List of generated scenarios
        """
        # Set defaults
        if difficulty_distribution is None:
            difficulty_distribution = {
                DifficultyLevel.EASY: 0.2,
                DifficultyLevel.MEDIUM: 0.4,
                DifficultyLevel.HARD: 0.3,
                DifficultyLevel.EXPERT: 0.1,
            }

        if environment_distribution is None:
            environment_distribution = {
                "warehouse": 0.25,
                "urban_road": 0.25,
                "hospital": 0.15,
                "factory": 0.15,
                "other": 0.2,
            }

        if region_distribution is None:
            region_distribution = {
                "north_india": 0.15,
                "new_york": 0.25,
                "tokyo": 0.2,
                "dubai": 0.15,
                "europe": 0.25,
            }

        scenarios = []

        for _ in range(count):
            # Select difficulty
            difficulty_level = random.choices(
                list(difficulty_distribution.keys()),
                weights=list(difficulty_distribution.values()),
            )[0]
            difficulty = difficulty_level.value

            # Select environment
            environment = random.choices(
                list(environment_distribution.keys()),
                weights=list(environment_distribution.values()),
            )[0]

            # Select region
            region = random.choices(
                list(region_distribution.keys()),
                weights=list(region_distribution.values()),
            )[0]

            # Generate scenario
            scenario = self._generate_base_scenario(
                environment, region, difficulty, violation_probability=0.1, rare_event_probability=0.05
            )

            scenarios.append(scenario)
            self.generated_scenarios.append(scenario)

            # Track difficulty distribution
            self.difficulty_distribution[difficulty] = (
                self.difficulty_distribution.get(difficulty, 0) + 1
            )

        logger.info(f"Generated {count} scenarios in batch")
        return scenarios

    def _generate_base_scenario(
        self,
        environment: str,
        region: str,
        difficulty: float,
        violation_probability: float = 0.1,
        rare_event_probability: float = 0.05,
    ) -> GeneratedScenario:
        """Generate base scenario.

        Args:
            environment: Environment type
            region: Geographic region
            difficulty: Difficulty level (0-1)
            violation_probability: Probability of violations
            rare_event_probability: Probability of rare events

        Returns:
            Generated scenario
        """
        self.scenario_counter += 1
        scenario_id = f"scenario_{self.scenario_counter}"

        # Determine scenario class based on difficulty
        if difficulty < 0.25:
            scenario_class = ScenarioClass.NOMINAL
        elif difficulty < 0.5:
            scenario_class = ScenarioClass.DEGRADED
        elif difficulty < 0.75:
            scenario_class = ScenarioClass.CRISIS
        else:
            scenario_class = ScenarioClass.CATASTROPHIC

        # Generate components
        weather = self._select_weather(region, difficulty)
        time_of_day = random.choice(["morning", "afternoon", "evening", "night"])
        day_of_week = random.choice(["weekday", "weekend"])
        season = random.choice(["spring", "summer", "fall", "winter"])

        # Density multipliers based on time/day
        time_mult = {"morning": 1.5, "afternoon": 0.8, "evening": 1.3, "night": 0.3}.get(
            time_of_day, 1.0
        )
        day_mult = {"weekday": 1.2, "weekend": 1.5}.get(day_of_week, 1.0)

        human_density = 0.5 * time_mult * day_mult * (0.5 + difficulty)
        vehicle_density = 0.1 * time_mult * day_mult * difficulty

        # Sensor degradation
        sensor_degradation = random.uniform(0, difficulty * 0.5)

        # Generate violations and failures
        active_violations = self._generate_violations(
            scenario_class, violation_probability
        )
        rare_events = self._generate_rare_events(scenario_class, rare_event_probability)
        infrastructure_failures = self._generate_infrastructure_failures(
            scenario_class, region
        )

        # Validation checkpoints
        validation_checkpoints = self._generate_validation_checkpoints(scenario_class)

        # Estimate expectations count
        expectations_count = 5 + int(difficulty * 20)

        return GeneratedScenario(
            scenario_id=scenario_id,
            class_=scenario_class,
            difficulty=difficulty,
            environment=environment,
            region=region,
            weather=weather,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            season=season,
            human_density=human_density,
            vehicle_density=vehicle_density,
            sensor_degradation=sensor_degradation,
            active_violations=active_violations,
            rare_events=rare_events,
            infrastructure_failures=infrastructure_failures,
            expectations_count=expectations_count,
            validation_checkpoints=validation_checkpoints,
        )

    def _select_weather(self, region: str, difficulty: float) -> str:
        """Select weather based on region and difficulty.

        Args:
            region: Geographic region
            difficulty: Difficulty level

        Returns:
            Weather condition
        """
        region_weather = {
            "north_india": ["clear", "dust", "hot"],
            "south_india": ["clear", "heavy_rain", "humid"],
            "new_york": ["clear", "snow", "rain", "cold"],
            "tokyo": ["clear", "humid", "rain", "typhoon"],
            "dubai": ["clear", "sandstorm", "hot"],
            "europe": ["clear", "rain", "snow", "fog"],
        }

        weather_options = region_weather.get(region, ["clear"])

        # Harder difficulties favor worse weather
        if difficulty > 0.7:
            # Prefer more challenging weather
            return random.choice(weather_options[1:] if len(weather_options) > 1 else weather_options)

        return random.choice(weather_options)

    def _generate_violations(
        self, scenario_class: ScenarioClass, violation_probability: float
    ) -> List[str]:
        """Generate expectation violations.

        Args:
            scenario_class: Scenario class
            violation_probability: Probability of violations

        Returns:
            List of violation types
        """
        violations = []

        violation_types = [
            "gps_unavailable",
            "communication_loss",
            "sensor_failure",
            "infrastructure_breakdown",
            "human_interference",
        ]

        # Higher scenario class = more violations
        class_multiplier = {
            ScenarioClass.NOMINAL: 0.1,
            ScenarioClass.DEGRADED: 0.3,
            ScenarioClass.CRISIS: 0.6,
            ScenarioClass.CATASTROPHIC: 0.9,
        }

        multiplier = class_multiplier[scenario_class]

        for violation_type in violation_types:
            if random.random() < violation_probability * multiplier:
                violations.append(violation_type)

        return violations

    def _generate_rare_events(
        self, scenario_class: ScenarioClass, rare_event_probability: float
    ) -> List[str]:
        """Generate rare events.

        Args:
            scenario_class: Scenario class
            rare_event_probability: Probability of rare events

        Returns:
            List of rare event types
        """
        events = []

        rare_event_types = [
            "fallen_tree",
            "flooded_road",
            "earthquake",
            "fire_alarm",
            "power_outage",
            "communication_blackout",
        ]

        class_multiplier = {
            ScenarioClass.NOMINAL: 0.0,
            ScenarioClass.DEGRADED: 0.1,
            ScenarioClass.CRISIS: 0.4,
            ScenarioClass.CATASTROPHIC: 0.8,
        }

        multiplier = class_multiplier[scenario_class]

        for event_type in rare_event_types:
            if random.random() < rare_event_probability * multiplier:
                events.append(event_type)

        return events

    def _generate_infrastructure_failures(
        self, scenario_class: ScenarioClass, region: str
    ) -> List[str]:
        """Generate infrastructure failures.

        Args:
            scenario_class: Scenario class
            region: Geographic region

        Returns:
            List of infrastructure failures
        """
        failures = []

        failure_types = ["gps", "cellular", "wifi", "power", "traffic_lights"]

        class_multiplier = {
            ScenarioClass.NOMINAL: 0.0,
            ScenarioClass.DEGRADED: 0.2,
            ScenarioClass.CRISIS: 0.5,
            ScenarioClass.CATASTROPHIC: 0.8,
        }

        multiplier = class_multiplier[scenario_class]

        # Regional variance
        region_reliability = {
            "north_india": 0.7,
            "south_india": 0.75,
            "new_york": 0.95,
            "tokyo": 0.98,
            "dubai": 0.9,
            "europe": 0.95,
        }

        base_reliability = region_reliability.get(region, 0.85)

        for failure_type in failure_types:
            if random.random() > base_reliability * (1 - multiplier):
                failures.append(failure_type)

        return failures

    def _generate_validation_checkpoints(self, scenario_class: ScenarioClass) -> List[str]:
        """Generate validation checkpoints based on scenario class.

        Args:
            scenario_class: Scenario class

        Returns:
            List of validation checkpoints
        """
        checkpoints = []

        base_checkpoints = [
            "initial_position_valid",
            "goal_reachable",
            "safety_maintained",
            "mission_completion",
        ]

        class_checkpoints = {
            ScenarioClass.NOMINAL: base_checkpoints,
            ScenarioClass.DEGRADED: base_checkpoints + ["recovery_attempted", "partial_mission"],
            ScenarioClass.CRISIS: base_checkpoints + ["emergency_response", "fallback_behavior"],
            ScenarioClass.CATASTROPHIC: base_checkpoints
            + ["survival_priority", "human_intervention"],
        }

        return class_checkpoints[scenario_class]

    def get_scenario_statistics(self) -> Dict[str, Any]:
        """Get statistics on generated scenarios.

        Returns:
            Statistics dictionary
        """
        if not self.generated_scenarios:
            return {}

        class_counts = {cls.value: 0 for cls in ScenarioClass}
        for scenario in self.generated_scenarios:
            class_counts[scenario.class_.value] += 1

        avg_difficulty = sum(s.difficulty for s in self.generated_scenarios) / len(
            self.generated_scenarios
        )
        avg_violations = sum(len(s.active_violations) for s in self.generated_scenarios) / len(
            self.generated_scenarios
        )

        return {
            "total_scenarios": len(self.generated_scenarios),
            "class_distribution": class_counts,
            "average_difficulty": avg_difficulty,
            "average_violations_per_scenario": avg_violations,
            "difficulty_distribution": self.difficulty_distribution,
        }
