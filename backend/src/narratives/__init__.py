"""Narrative Simulation Engine - Phase 6.

AI-native narrative-driven simulation with branching story logic.
"""

from src.narratives.agent_interpreter import (
    AgentBehaviorInterpreter,
    AgentBehaviorType,
    BehaviorPlan,
    BehaviorPrimitive,
)
from src.narratives.narrative_converter import NarrativeConverter
from src.narratives.narrative_definitions import (
    AgentRole,
    Narrative,
    NarrativeBranch,
    NarrativeBranchPoint,
    NarrativeConstraint,
    NarrativeEntity,
    NarrativeEvent,
    NarrativeEventType,
    NarrativeExecutionContext,
    NarrativeGoal,
    NarrativeSequence,
    NarrativeType,
)
from src.narratives.narrative_executor import NarrativeExecutor
from src.narratives.narrative_validator import NarrativeValidator, ValidationError, ValidationResult
from src.narratives.story_branching_engine import (
    BranchCondition,
    BranchingDecision,
    BranchPath,
    StoryBranchingEngine,
)

__all__ = [
    "Narrative",
    "NarrativeType",
    "NarrativeEntity",
    "NarrativeGoal",
    "NarrativeEvent",
    "NarrativeEventType",
    "NarrativeSequence",
    "NarrativeBranchPoint",
    "NarrativeConstraint",
    "NarrativeExecutionContext",
    "AgentRole",
    "NarrativeBranch",
    "NarrativeConverter",
    "NarrativeExecutor",
    "AgentBehaviorInterpreter",
    "BehaviorPrimitive",
    "BehaviorPlan",
    "AgentBehaviorType",
    "StoryBranchingEngine",
    "BranchCondition",
    "BranchPath",
    "BranchingDecision",
    "NarrativeValidator",
    "ValidationResult",
    "ValidationError",
]
