"""Narrative Simulation Engine - Phase 6.

Core definitions for narrative-driven simulation.
Enables conversion of story descriptions into executable scenarios.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class NarrativeType(Enum):
    """Types of narratives."""
    RESCUE_OPERATION = "rescue_operation"
    DELIVERY_MISSION = "delivery_mission"
    EXPLORATION = "exploration"
    INSPECTION = "inspection"
    MULTI_AGENT_COORDINATION = "multi_agent_coordination"
    ADVERSARIAL_SCENARIO = "adversarial_scenario"
    TRAINING_CURRICULUM = "training_curriculum"
    CUSTOM = "custom"


class AgentRole(Enum):
    """Agent roles in narrative."""
    PROTAGONIST = "protagonist"
    ASSISTANT = "assistant"
    ANTAGONIST = "antagonist"
    OBSTACLE = "obstacle"
    OBSERVER = "observer"


class NarrativeEventType(Enum):
    """Types of events that can occur."""
    AGENT_ACTION = "agent_action"
    ENVIRONMENT_CHANGE = "environment_change"
    SENSOR_EVENT = "sensor_event"
    GOAL_MILESTONE = "goal_milestone"
    CONSTRAINT_VIOLATION = "constraint_violation"
    DECISION_POINT = "decision_point"
    OUTCOME = "outcome"


class NarrativeBranch(Enum):
    """Branch types for narrative branching."""
    LINEAR = "linear"
    CONDITIONAL = "conditional"
    PROBABILISTIC = "probabilistic"
    AGENT_DRIVEN = "agent_driven"


@dataclass
class NarrativeEntity:
    """Entity (agent or object) in a narrative."""
    entity_id: str
    entity_type: str  # "robot", "human", "obstacle", "landmark"
    name: str
    role: AgentRole
    initial_position: Tuple[float, float, float]
    initial_orientation: Tuple[float, float, float, float]  # quaternion
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    sensor_suite: Optional[str] = None  # reference to sensor config


@dataclass
class NarrativeGoal:
    """Goal or objective in narrative."""
    goal_id: str
    description: str
    goal_type: str  # "reach_location", "pick_object", "avoid_obstacle", etc.
    target: Optional[Dict[str, Any]] = None
    priority: float = 1.0
    time_limit_sec: Optional[float] = None
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    failure_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeEvent:
    """Event in narrative timeline."""
    event_id: str
    event_type: NarrativeEventType
    timestamp_sec: float
    description: str
    triggering_entity: Optional[str] = None
    affected_entities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    outcome: Optional[str] = None
    confidence: float = 1.0


@dataclass
class NarrativeBranchPoint:
    """Decision point where narrative can branch."""
    branch_id: str
    trigger_condition: str  # NL description or code condition
    branches: Dict[str, "NarrativeSequence"] = field(default_factory=dict)
    branch_type: NarrativeBranch = NarrativeBranch.CONDITIONAL
    probabilities: Dict[str, float] = field(default_factory=dict)
    decision_maker: Optional[str] = None  # which agent decides


@dataclass
class NarrativeConstraint:
    """Constraint or rule in narrative."""
    constraint_id: str
    description: str
    constraint_type: str  # "safety", "efficiency", "realism", "challenge"
    rule: str  # NL or code representation
    violation_penalty: float = -1.0


@dataclass
class NarrativeSequence:
    """Sequence of events forming part of narrative."""
    sequence_id: str
    name: str
    description: str
    events: List[NarrativeEvent] = field(default_factory=list)
    branches: List[NarrativeBranchPoint] = field(default_factory=list)
    constraints: List[NarrativeConstraint] = field(default_factory=list)
    duration_sec: float = 0.0

    def add_event(self, event: NarrativeEvent) -> None:
        """Add event to sequence."""
        self.events.append(event)
        if event.timestamp_sec > self.duration_sec:
            self.duration_sec = event.timestamp_sec

    def add_branch(self, branch: NarrativeBranchPoint) -> None:
        """Add branch point to sequence."""
        self.branches.append(branch)

    def add_constraint(self, constraint: NarrativeConstraint) -> None:
        """Add constraint to sequence."""
        self.constraints.append(constraint)


@dataclass
class Narrative:
    """Complete narrative scenario definition."""
    narrative_id: str
    title: str
    description: str
    narrative_type: NarrativeType

    # Core elements
    entities: Dict[str, NarrativeEntity] = field(default_factory=dict)
    goals: Dict[str, NarrativeGoal] = field(default_factory=dict)
    sequences: List[NarrativeSequence] = field(default_factory=list)
    constraints: List[NarrativeConstraint] = field(default_factory=list)

    # Metadata
    creation_timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    estimated_duration_sec: float = 0.0
    difficulty_level: float = 0.5  # 0-1
    success_criteria: Dict[str, Any] = field(default_factory=dict)

    # Environment
    environment_type: str = "urban"  # urban, industrial, outdoor, indoor
    weather_conditions: Dict[str, Any] = field(default_factory=dict)
    time_of_day: str = "noon"  # dawn, morning, noon, afternoon, dusk, night

    # Execution
    execution_state: str = "not_started"  # not_started, running, paused, completed
    execution_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_entity(self, entity: NarrativeEntity) -> None:
        """Add entity to narrative."""
        self.entities[entity.entity_id] = entity

    def add_goal(self, goal: NarrativeGoal) -> None:
        """Add goal to narrative."""
        self.goals[goal.goal_id] = goal

    def add_sequence(self, sequence: NarrativeSequence) -> None:
        """Add sequence to narrative."""
        self.sequences.append(sequence)
        self.estimated_duration_sec += sequence.duration_sec

    def add_constraint(self, constraint: NarrativeConstraint) -> None:
        """Add global constraint to narrative."""
        self.constraints.append(constraint)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "narrative_id": self.narrative_id,
            "title": self.title,
            "description": self.description,
            "narrative_type": self.narrative_type.value,
            "entity_count": len(self.entities),
            "goal_count": len(self.goals),
            "sequence_count": len(self.sequences),
            "estimated_duration_sec": self.estimated_duration_sec,
            "difficulty_level": self.difficulty_level,
            "execution_state": self.execution_state,
        }


@dataclass
class NarrativeExecutionContext:
    """Runtime context for narrative execution."""
    narrative: Narrative
    current_sequence_idx: int = 0
    current_event_idx: int = 0
    elapsed_time_sec: float = 0.0
    entity_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    goal_progress: Dict[str, float] = field(default_factory=dict)
    constraint_violations: List[Tuple[str, float]] = field(default_factory=list)
    events_executed: List[NarrativeEvent] = field(default_factory=list)
    decisions_made: List[Dict[str, Any]] = field(default_factory=list)

    def update_entity_state(self, entity_id: str, state: Dict[str, Any]) -> None:
        """Update entity state."""
        self.entity_states[entity_id] = state

    def update_goal_progress(self, goal_id: str, progress: float) -> None:
        """Update goal progress (0-1)."""
        self.goal_progress[goal_id] = min(max(progress, 0.0), 1.0)

    def record_violation(self, constraint_id: str, timestamp_sec: float) -> None:
        """Record constraint violation."""
        self.constraint_violations.append((constraint_id, timestamp_sec))

    def record_decision(self, decision: Dict[str, Any]) -> None:
        """Record agent decision."""
        self.decisions_made.append(decision)
