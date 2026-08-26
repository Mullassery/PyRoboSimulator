"""Narrative Simulation Engine - Phase 6.

AI-native narrative-driven simulation with branching story logic.
"""

from src.narratives.narrative_definitions import (
    Narrative,
    NarrativeType,
    NarrativeEntity,
    NarrativeGoal,
    NarrativeEvent,
    NarrativeEventType,
    NarrativeSequence,
    NarrativeBranchPoint,
    NarrativeConstraint,
    NarrativeExecutionContext,
    AgentRole,
    NarrativeBranch,
)
from src.narratives.narrative_converter import NarrativeConverter
from src.narratives.narrative_executor import NarrativeExecutor
from src.narratives.agent_interpreter import (
    AgentBehaviorInterpreter,
    BehaviorPrimitive,
    BehaviorPlan,
    AgentBehaviorType,
)
from src.narratives.story_branching_engine import (
    StoryBranchingEngine,
    BranchCondition,
    BranchPath,
    BranchingDecision,
)
from src.narratives.narrative_validator import (
    NarrativeValidator,
    ValidationResult,
    ValidationError,
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
