"""Curriculum Learning Module - Phase 8.

Adaptive curriculum generation with progressive difficulty scaling.
"""

from src.curriculum.curriculum_generator import CurriculumScenarioGenerator
from src.curriculum.difficulty_model import (
    CurriculumLesson,
    CurriculumPlan,
    DifficultyFactors,
    DifficultyLevel,
    DifficultyModel,
    LearnerProfile,
)

__all__ = [
    "DifficultyLevel",
    "DifficultyFactors",
    "LearnerProfile",
    "CurriculumLesson",
    "CurriculumPlan",
    "DifficultyModel",
    "CurriculumScenarioGenerator",
]
