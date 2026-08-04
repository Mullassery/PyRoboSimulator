"""Difficulty Model - Quantify and scale scenario difficulty.

Analyzes trajectory metrics and generates scenarios at controlled difficulty levels.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """Difficulty levels for curriculum."""
    TRIVIAL = 0.1      # Very easy, perfect path available
    NOVICE = 0.25      # Suitable for learning basics
    BEGINNER = 0.4     # Some obstacles/complexity
    INTERMEDIATE = 0.55  # Moderate challenge
    ADVANCED = 0.7     # High complexity
    EXPERT = 0.85      # Very challenging
    IMPOSSIBLE = 1.0   # At or beyond capability limits


@dataclass
class DifficultyFactors:
    """Factors that contribute to scenario difficulty."""
    path_complexity: float = 0.0  # 0-1, based on turns, length
    obstacle_density: float = 0.0  # 0-1, number/proximity of obstacles
    time_pressure: float = 0.0    # 0-1, how tight the time limit
    sensor_constraints: float = 0.0  # 0-1, sensor degradation/limitations
    dynamic_elements: float = 0.0  # 0-1, moving obstacles, changing env
    precision_required: float = 0.0  # 0-1, accuracy demands
    multi_objective: float = 0.0  # 0-1, number of competing goals

    def overall_difficulty(self) -> float:
        """Compute overall difficulty.

        Returns:
            Weighted difficulty 0-1
        """
        factors = [
            (self.path_complexity, 0.20),
            (self.obstacle_density, 0.20),
            (self.time_pressure, 0.15),
            (self.sensor_constraints, 0.10),
            (self.dynamic_elements, 0.15),
            (self.precision_required, 0.10),
            (self.multi_objective, 0.10),
        ]

        weighted_sum = sum(f * w for f, w in factors)
        return min(max(weighted_sum, 0.0), 1.0)


@dataclass
class LearnerProfile:
    """Profile of learner (agent) performance."""
    learner_id: str
    scenarios_completed: int = 0
    success_rate: float = 0.0  # 0-1
    average_time_efficiency: float = 1.0  # 1.0 = optimal, <1 = slower
    average_path_efficiency: float = 1.0  # 1.0 = optimal, <1 = longer paths
    current_difficulty: float = 0.25  # Current level
    difficulty_ceiling: float = 0.5  # Max difficulty learner can handle
    last_5_success_rates: List[float] = field(default_factory=list)

    def get_recommended_difficulty(self) -> float:
        """Get recommended next difficulty level.

        Returns:
            Recommended difficulty 0-1
        """
        if len(self.last_5_success_rates) < 3:
            # Not enough data, return current
            return self.current_difficulty

        recent_avg = sum(self.last_5_success_rates[-3:]) / 3

        if recent_avg > 0.9:
            # Performing well, increase difficulty
            return min(self.current_difficulty + 0.1, self.difficulty_ceiling)
        elif recent_avg < 0.5:
            # Struggling, decrease difficulty
            return max(self.current_difficulty - 0.1, 0.1)
        else:
            # Acceptable performance, maintain
            return self.current_difficulty


@dataclass
class CurriculumLesson:
    """A single lesson in curriculum."""
    lesson_id: str
    order: int  # Position in curriculum
    difficulty: float  # Target difficulty 0-1
    target_success_rate: float = 0.8  # 80% success before advancing
    max_attempts: int = 5
    description: str = ""
    difficulty_factors: DifficultyFactors = field(default_factory=DifficultyFactors)
    scenarios: List[str] = field(default_factory=list)  # Scenario IDs


@dataclass
class CurriculumPlan:
    """Complete curriculum for learner progression."""
    plan_id: str
    learner_id: str
    start_difficulty: float = 0.1
    target_max_difficulty: float = 0.8
    num_lessons: int = 10
    lessons: List[CurriculumLesson] = field(default_factory=list)
    current_lesson_idx: int = 0
    completed_lessons: int = 0


class DifficultyModel:
    """Models and generates scenarios at different difficulty levels.

    Enables:
    - Analysis of scenario difficulty
    - Scaling difficulty up/down
    - Curriculum generation
    - Adaptive difficulty based on performance
    """

    def __init__(self):
        """Initialize difficulty model."""
        self._learner_profiles: Dict[str, LearnerProfile] = {}

    def analyze_trajectory_difficulty(
        self,
        trajectory_distance: float,
        trajectory_duration: float,
        path_smoothness: float,
        num_turns: int,
        obstacle_count: int,
    ) -> DifficultyFactors:
        """Analyze trajectory to determine difficulty factors.

        Args:
            trajectory_distance: Total distance traveled (m)
            trajectory_duration: Total time (s)
            path_smoothness: Smoothness 0-1 (1=smooth)
            num_turns: Number of direction changes
            obstacle_count: Number of obstacles

        Returns:
            DifficultyFactors
        """
        # Path complexity from distance and turns
        path_complexity = min((trajectory_distance / 100.0) + (num_turns / 20.0), 1.0)

        # Obstacle density
        obstacle_density = min(obstacle_count / 10.0, 1.0)

        # Time pressure (inverse of smoothness)
        time_pressure = 1.0 - path_smoothness

        # Path efficiency (less smooth = more difficult)
        precision_required = 1.0 - path_smoothness

        return DifficultyFactors(
            path_complexity=path_complexity,
            obstacle_density=obstacle_density,
            time_pressure=time_pressure,
            sensor_constraints=0.0,
            dynamic_elements=0.0,
            precision_required=precision_required,
            multi_objective=0.0,
        )

    def scale_difficulty(
        self,
        base_factors: DifficultyFactors,
        target_difficulty: float,
    ) -> DifficultyFactors:
        """Scale difficulty factors to target level.

        Args:
            base_factors: Original difficulty factors
            target_difficulty: Target difficulty 0-1

        Returns:
            Scaled difficulty factors
        """
        current = base_factors.overall_difficulty()
        scale_factor = target_difficulty / current if current > 0 else 1.0

        return DifficultyFactors(
            path_complexity=min(base_factors.path_complexity * scale_factor, 1.0),
            obstacle_density=min(base_factors.obstacle_density * scale_factor, 1.0),
            time_pressure=min(base_factors.time_pressure * scale_factor, 1.0),
            sensor_constraints=min(base_factors.sensor_constraints * scale_factor, 1.0),
            dynamic_elements=min(base_factors.dynamic_elements * scale_factor, 1.0),
            precision_required=min(base_factors.precision_required * scale_factor, 1.0),
            multi_objective=min(base_factors.multi_objective * scale_factor, 1.0),
        )

    def generate_curriculum(
        self,
        learner_id: str,
        start_difficulty: float = 0.1,
        target_difficulty: float = 0.8,
        num_lessons: int = 10,
    ) -> CurriculumPlan:
        """Generate adaptive curriculum for learner.

        Args:
            learner_id: Learner identifier
            start_difficulty: Starting difficulty 0-1
            target_difficulty: Target difficulty 0-1
            num_lessons: Number of lessons in curriculum

        Returns:
            CurriculumPlan
        """
        plan = CurriculumPlan(
            plan_id=f"curriculum_{learner_id}",
            learner_id=learner_id,
            start_difficulty=start_difficulty,
            target_max_difficulty=target_difficulty,
            num_lessons=num_lessons,
        )

        # Generate linearly spaced difficulty levels
        step = (target_difficulty - start_difficulty) / (num_lessons - 1)

        for i in range(num_lessons):
            difficulty = start_difficulty + (i * step)

            lesson = CurriculumLesson(
                lesson_id=f"lesson_{i}",
                order=i,
                difficulty=difficulty,
                description=f"Lesson {i+1}: Difficulty {difficulty:.1%}",
                difficulty_factors=DifficultyFactors(
                    path_complexity=difficulty,
                    obstacle_density=difficulty * 0.5,
                    time_pressure=difficulty * 0.3,
                ),
            )

            plan.lessons.append(lesson)

        # Create profile for learner
        profile = LearnerProfile(
            learner_id=learner_id,
            current_difficulty=start_difficulty,
            difficulty_ceiling=target_difficulty,
        )

        self._learner_profiles[learner_id] = profile

        logger.info(f"Generated curriculum for {learner_id}: {num_lessons} lessons")

        return plan

    def record_lesson_performance(
        self,
        learner_id: str,
        lesson_id: str,
        success_rate: float,
        time_efficiency: float,
        path_efficiency: float,
    ) -> None:
        """Record learner performance on lesson.

        Args:
            learner_id: Learner identifier
            lesson_id: Lesson identifier
            success_rate: Success rate 0-1
            time_efficiency: Time efficiency 0-1
            path_efficiency: Path efficiency 0-1
        """
        if learner_id not in self._learner_profiles:
            return

        profile = self._learner_profiles[learner_id]

        profile.scenarios_completed += 1
        profile.success_rate = success_rate
        profile.average_time_efficiency = time_efficiency
        profile.average_path_efficiency = path_efficiency

        # Track last 5 success rates
        profile.last_5_success_rates.append(success_rate)
        if len(profile.last_5_success_rates) > 5:
            profile.last_5_success_rates.pop(0)

        logger.info(
            f"{learner_id} completed {lesson_id}: "
            f"{success_rate:.0%} success, {time_efficiency:.0%} efficiency"
        )

    def get_next_difficulty(self, learner_id: str) -> float:
        """Get recommended next difficulty for learner.

        Args:
            learner_id: Learner identifier

        Returns:
            Recommended difficulty 0-1
        """
        if learner_id not in self._learner_profiles:
            return 0.25

        profile = self._learner_profiles[learner_id]
        return profile.get_recommended_difficulty()

    def get_learner_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        """Get learner profile.

        Args:
            learner_id: Learner identifier

        Returns:
            LearnerProfile or None
        """
        return self._learner_profiles.get(learner_id)

    def get_difficulty_level_name(self, difficulty: float) -> str:
        """Get human-readable difficulty level name.

        Args:
            difficulty: Difficulty value 0-1

        Returns:
            Level name
        """
        for level in DifficultyLevel:
            if abs(difficulty - level.value) < 0.1:
                return level.name

        return "CUSTOM"
