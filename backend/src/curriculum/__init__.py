"""Curriculum Learning Module - Phase 8.

Adaptive curriculum generation with progressive difficulty scaling.
"""

from src.curriculum.difficulty_model import (
    DifficultyLevel,
    DifficultyFactors,
    LearnerProfile,
    CurriculumLesson,
    CurriculumPlan,
    DifficultyModel,
)
from src.curriculum.curriculum_generator import CurriculumScenarioGenerator

__all__ = [
    "DifficultyLevel",
    "DifficultyFactors",
    "LearnerProfile",
    "CurriculumLesson",
    "CurriculumPlan",
    "DifficultyModel",
    "CurriculumScenarioGenerator",
]
