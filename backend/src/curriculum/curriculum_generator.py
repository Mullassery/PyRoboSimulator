"""Curriculum Generator - Create training scenarios at progressive difficulty levels.

Generates synthetic scenarios at different difficulty levels for curriculum-based training.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from random import Random

from src.narratives import (
    Narrative,
    NarrativeType,
    NarrativeEntity,
    NarrativeGoal,
    NarrativeConstraint,
    AgentRole,
)
from src.curriculum.difficulty_model import DifficultyFactors, DifficultyLevel

logger = logging.getLogger(__name__)


class CurriculumScenarioGenerator:
    """Generates training scenarios at progressive difficulty levels.

    Creates scenarios with:
    - Progressive path complexity
    - Obstacle placement and density
    - Time pressure variations
    - Sensor constraints
    - Multi-objective goals
    """

    def __init__(self, seed: int = 42):
        """Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        self._rng = Random(seed)
        self._scenario_cache: Dict[str, Narrative] = {}

    def generate_scenario(
        self,
        curriculum_name: str,
        lesson_idx: int,
        difficulty: float,
        scenario_type: str = "navigation",
    ) -> Narrative:
        """Generate scenario at specified difficulty.

        Args:
            curriculum_name: Name of curriculum
            lesson_idx: Lesson index in curriculum
            difficulty: Difficulty level 0-1
            scenario_type: Type of scenario (navigation, inspection, delivery)

        Returns:
            Generated Narrative
        """
        logger.info(
            f"Generating {scenario_type} scenario for {curriculum_name} "
            f"lesson {lesson_idx} (difficulty {difficulty:.0%})"
        )

        # Generate base scenario
        if scenario_type == "navigation":
            narrative = self._generate_navigation_scenario(curriculum_name, lesson_idx, difficulty)
        elif scenario_type == "inspection":
            narrative = self._generate_inspection_scenario(curriculum_name, lesson_idx, difficulty)
        elif scenario_type == "delivery":
            narrative = self._generate_delivery_scenario(curriculum_name, lesson_idx, difficulty)
        else:
            narrative = self._generate_navigation_scenario(curriculum_name, lesson_idx, difficulty)

        return narrative

    def _generate_navigation_scenario(
        self,
        curriculum_name: str,
        lesson_idx: int,
        difficulty: float,
    ) -> Narrative:
        """Generate navigation scenario with progressive complexity.

        Args:
            curriculum_name: Curriculum name
            lesson_idx: Lesson index
            difficulty: Difficulty 0-1

        Returns:
            Narrative
        """
        # Generate based on difficulty
        if difficulty < 0.2:
            # Trivial: short, straight path
            distance = 10.0
            num_obstacles = 0
            turns = 0
        elif difficulty < 0.4:
            # Novice: moderate distance, few obstacles
            distance = 20.0 + (self._rng.random() * 10)
            num_obstacles = 1
            turns = 1
        elif difficulty < 0.6:
            # Intermediate: longer, curved path
            distance = 30.0 + (self._rng.random() * 15)
            num_obstacles = 2 + int(self._rng.random() * 2)
            turns = 2 + int(self._rng.random() * 2)
        elif difficulty < 0.8:
            # Advanced: complex path, many obstacles
            distance = 50.0 + (self._rng.random() * 20)
            num_obstacles = 4 + int(self._rng.random() * 3)
            turns = 4 + int(self._rng.random() * 3)
        else:
            # Expert: very complex
            distance = 80.0 + (self._rng.random() * 30)
            num_obstacles = 7 + int(self._rng.random() * 4)
            turns = 6 + int(self._rng.random() * 4)

        narrative = Narrative(
            narrative_id=f"curriculum_{curriculum_name}_lesson_{lesson_idx}",
            title=f"Navigation Lesson {lesson_idx + 1}",
            description=f"Progressive navigation training at {difficulty:.0%} difficulty",
            narrative_type=NarrativeType.EXPLORATION,
            difficulty_level=difficulty,
            environment_type="training_arena",
        )

        # Add robot
        robot = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Training Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        narrative.add_entity(robot)

        # Add obstacles
        for i in range(num_obstacles):
            angle = (i / num_obstacles) * 6.28
            obs_x = 10.0 + (5.0 * (i % 2)) * ((difficulty + 0.5) ** 1.5)
            obs_y = 5.0 * (i % 3)

            obstacle = NarrativeEntity(
                entity_id=f"obstacle_{i}",
                entity_type="obstacle",
                name=f"Obstacle {i}",
                role=AgentRole.OBSTACLE,
                initial_position=(obs_x, obs_y, 0.0),
                initial_orientation=(0.0, 0.0, 0.0, 1.0),
            )

            narrative.add_entity(obstacle)

        # Add goal
        goal = NarrativeGoal(
            goal_id="goal_navigate",
            description=f"Navigate {distance:.1f}m to destination",
            goal_type="reach_location",
            target={"position": [distance, 0.0, 0.0], "tolerance": 1.0},
            priority=1.0,
            time_limit_sec=distance * (2.0 - difficulty),  # Tighter for harder
            success_criteria={"distance": distance},
        )

        narrative.add_goal(goal)

        # Add constraint
        constraint = NarrativeConstraint(
            constraint_id="efficiency",
            description="Path should be reasonably efficient",
            constraint_type="efficiency",
            rule=f"path_length <= {distance * (1.2 - difficulty * 0.2)}",
            violation_penalty=-0.3,
        )

        narrative.add_constraint(constraint)

        return narrative

    def _generate_inspection_scenario(
        self,
        curriculum_name: str,
        lesson_idx: int,
        difficulty: float,
    ) -> Narrative:
        """Generate inspection scenario.

        Args:
            curriculum_name: Curriculum name
            lesson_idx: Lesson index
            difficulty: Difficulty 0-1

        Returns:
            Narrative
        """
        # Similar progression but for inspection
        num_points = int(2 + (difficulty * 8))
        area_size = 20.0 + (difficulty * 40.0)

        narrative = Narrative(
            narrative_id=f"curriculum_{curriculum_name}_lesson_{lesson_idx}",
            title=f"Inspection Lesson {lesson_idx + 1}",
            description=f"Progressive inspection training at {difficulty:.0%} difficulty",
            narrative_type=NarrativeType.INSPECTION,
            difficulty_level=difficulty,
        )

        # Add robot
        robot = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Inspector Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        narrative.add_entity(robot)

        # Add inspection points
        for i in range(num_points):
            angle = (i / num_points) * 6.28
            point_x = (area_size / 2) * (0.5 + 0.5 * (i % 2))
            point_y = (area_size / 2) * (i % 3) - (area_size / 3)

            point = NarrativeEntity(
                entity_id=f"inspect_point_{i}",
                entity_type="landmark",
                name=f"Inspection Point {i}",
                role=AgentRole.OBSTACLE,
                initial_position=(point_x, point_y, 0.0),
                initial_orientation=(0.0, 0.0, 0.0, 1.0),
            )

            narrative.add_entity(point)

        # Add goal
        goal = NarrativeGoal(
            goal_id="goal_inspect",
            description=f"Inspect {num_points} points in area",
            goal_type="inspect_area",
            target={"area_size": area_size, "points": num_points},
            priority=1.0,
            time_limit_sec=area_size * num_points * (1.5 - difficulty * 0.5),
        )

        narrative.add_goal(goal)

        return narrative

    def _generate_delivery_scenario(
        self,
        curriculum_name: str,
        lesson_idx: int,
        difficulty: float,
    ) -> Narrative:
        """Generate delivery scenario.

        Args:
            curriculum_name: Curriculum name
            lesson_idx: Lesson index
            difficulty: Difficulty 0-1

        Returns:
            Narrative
        """
        num_deliveries = int(1 + (difficulty * 4))
        area_size = 15.0 + (difficulty * 35.0)

        narrative = Narrative(
            narrative_id=f"curriculum_{curriculum_name}_lesson_{lesson_idx}",
            title=f"Delivery Lesson {lesson_idx + 1}",
            description=f"Progressive delivery training at {difficulty:.0%} difficulty",
            narrative_type=NarrativeType.DELIVERY_MISSION,
            difficulty_level=difficulty,
        )

        # Add robot
        robot = NarrativeEntity(
            entity_id="robot_0",
            entity_type="robot",
            name="Delivery Robot",
            role=AgentRole.PROTAGONIST,
            initial_position=(0.0, 0.0, 0.0),
            initial_orientation=(0.0, 0.0, 0.0, 1.0),
            sensor_suite="mobile",
        )

        narrative.add_entity(robot)

        # Add delivery locations
        for i in range(num_deliveries):
            loc_x = (area_size / 2) * (1 - 2 * (i % 2))
            loc_y = (area_size / 2) * ((i // 2) % 2) - (area_size / 4)

            location = NarrativeEntity(
                entity_id=f"delivery_{i}",
                entity_type="landmark",
                name=f"Delivery Location {i}",
                role=AgentRole.OBSTACLE,
                initial_position=(loc_x, loc_y, 0.0),
                initial_orientation=(0.0, 0.0, 0.0, 1.0),
            )

            narrative.add_entity(location)

        # Add multi-objective goal
        goal = NarrativeGoal(
            goal_id="goal_deliver",
            description=f"Deliver to {num_deliveries} locations",
            goal_type="reach_location",
            target={"locations": num_deliveries, "area": area_size},
            priority=1.0,
            time_limit_sec=area_size * num_deliveries * (1.2 - difficulty * 0.3),
        )

        narrative.add_goal(goal)

        return narrative

    def generate_curriculum_scenarios(
        self,
        curriculum_name: str,
        num_lessons: int,
        scenario_type: str = "navigation",
        start_difficulty: float = 0.1,
        end_difficulty: float = 0.8,
    ) -> List[Narrative]:
        """Generate all scenarios for curriculum.

        Args:
            curriculum_name: Curriculum name
            num_lessons: Number of lessons
            scenario_type: Type of scenario
            start_difficulty: Starting difficulty
            end_difficulty: Ending difficulty

        Returns:
            List of narratives
        """
        scenarios = []
        step = (end_difficulty - start_difficulty) / (num_lessons - 1)

        for i in range(num_lessons):
            difficulty = start_difficulty + (i * step)

            scenario = self.generate_scenario(
                curriculum_name, i, difficulty, scenario_type
            )

            scenarios.append(scenario)

        logger.info(f"Generated {num_lessons} scenarios for {curriculum_name}")

        return scenarios
