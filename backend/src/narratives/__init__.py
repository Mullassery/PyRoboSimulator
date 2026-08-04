"""Narrative Simulation Engine - Phase 6.

AI-native narrative-driven simulation with branching story logic.
"""

from backend.src.narratives.narrative_definitions import (
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
from backend.src.narratives.narrative_converter import NarrativeConverter
from backend.src.narratives.narrative_executor import NarrativeExecutor
from backend.src.narratives.agent_interpreter import (
    AgentBehaviorInterpreter,
    BehaviorPrimitive,
    BehaviorPlan,
    AgentBehaviorType,
)
from backend.src.narratives.story_branching_engine import (
    StoryBranchingEngine,
    BranchCondition,
    BranchPath,
    BranchingDecision,
)
from backend.src.narratives.narrative_validator import (
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
