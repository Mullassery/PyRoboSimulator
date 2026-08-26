"""Narrative Validator - Consistency and Feasibility Checking.

Validates narratives against sensor data, constraints, and execution feasibility.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.narratives.narrative_definitions import (
    Narrative,
    NarrativeConstraint,
    NarrativeEntity,
    NarrativeEvent,
    NarrativeGoal,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Narrative validation error."""
    error_id: str
    severity: str  # "critical" | "warning" | "info"
    message: str
    affected_component: str  # "entity" | "goal" | "event" | "constraint"
    component_id: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of narrative validation."""
    narrative_id: str
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    feasibility_score: float  # 0-1
    sensor_coverage_score: float  # 0-1
    constraint_satisfaction_score: float  # 0-1


class NarrativeValidator:
    """Validates narrative consistency, feasibility, and sensor coverage."""

    def __init__(self):
        """Initialize validator."""
        self._validation_rules: List[callable] = []
        self._register_default_rules()

    def validate(self, narrative: Narrative) -> ValidationResult:
        """Validate narrative completely.

        Args:
            narrative: Narrative to validate

        Returns:
            Validation result
        """
        logger.info(f"Validating narrative: {narrative.narrative_id}")

        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Run all validation rules
        for rule in self._validation_rules:
            rule_errors, rule_warnings = rule(narrative)
            errors.extend(rule_errors)
            warnings.extend(rule_warnings)

        # Compute scores
        feasibility_score = self._compute_feasibility_score(narrative, errors)
        sensor_coverage_score = self._compute_sensor_coverage_score(narrative)
        constraint_satisfaction_score = self._compute_constraint_satisfaction_score(narrative)

        is_valid = len(errors) == 0 and feasibility_score > 0.5

        result = ValidationResult(
            narrative_id=narrative.narrative_id,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            feasibility_score=feasibility_score,
            sensor_coverage_score=sensor_coverage_score,
            constraint_satisfaction_score=constraint_satisfaction_score,
        )

        logger.info(f"Validation complete: {len(errors)} errors, {len(warnings)} warnings")

        return result

    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        self._validation_rules = [
            self._validate_entities,
            self._validate_goals,
            self._validate_events,
            self._validate_constraints,
            self._validate_timeline,
            self._validate_entity_references,
        ]

    def _validate_entities(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate entities."""
        errors = []
        warnings = []

        if len(narrative.entities) == 0:
            errors.append(ValidationError(
                error_id="no_entities",
                severity="critical",
                message="Narrative must have at least one entity",
                affected_component="entity",
            ))

        for entity_id, entity in narrative.entities.items():
            # Validate entity properties
            if not entity.name or len(entity.name.strip()) == 0:
                errors.append(ValidationError(
                    error_id=f"empty_entity_name_{entity_id}",
                    severity="warning",
                    message=f"Entity {entity_id} has empty name",
                    affected_component="entity",
                    component_id=entity_id,
                ))

            if entity.entity_type not in ["robot", "human", "obstacle", "landmark", "object"]:
                warnings.append(ValidationError(
                    error_id=f"unknown_entity_type_{entity_id}",
                    severity="warning",
                    message=f"Unknown entity type: {entity.entity_type}",
                    affected_component="entity",
                    component_id=entity_id,
                ))

            # Check if robot entity has sensor suite
            if entity.entity_type == "robot" and not entity.sensor_suite:
                warnings.append(ValidationError(
                    error_id=f"no_sensor_suite_{entity_id}",
                    severity="warning",
                    message=f"Robot {entity_id} has no sensor suite configured",
                    affected_component="entity",
                    component_id=entity_id,
                ))

            # Validate position is reasonable
            pos = entity.initial_position
            if any(abs(p) > 1000 for p in pos):
                warnings.append(ValidationError(
                    error_id=f"extreme_position_{entity_id}",
                    severity="warning",
                    message=f"Entity {entity_id} position seems extreme: {pos}",
                    affected_component="entity",
                    component_id=entity_id,
                ))

        return errors, warnings

    def _validate_goals(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate goals."""
        errors = []
        warnings = []

        if len(narrative.goals) == 0:
            warnings.append(ValidationError(
                error_id="no_goals",
                severity="warning",
                message="Narrative has no explicit goals",
                affected_component="goal",
            ))

        for goal_id, goal in narrative.goals.items():
            # Validate goal type
            valid_types = [
                "reach_location", "pick_object", "avoid_obstacle",
                "follow_path", "inspect_area", "coordinate_agents",
            ]

            if goal.goal_type not in valid_types and goal.goal_type != "custom":
                warnings.append(ValidationError(
                    error_id=f"unknown_goal_type_{goal_id}",
                    severity="warning",
                    message=f"Unknown goal type: {goal.goal_type}",
                    affected_component="goal",
                    component_id=goal_id,
                ))

            # Validate goal has criteria
            if not goal.success_criteria or len(goal.success_criteria) == 0:
                warnings.append(ValidationError(
                    error_id=f"no_success_criteria_{goal_id}",
                    severity="warning",
                    message=f"Goal {goal_id} has no success criteria",
                    affected_component="goal",
                    component_id=goal_id,
                ))

            # Validate time limit if present
            if goal.time_limit_sec and goal.time_limit_sec < 0:
                errors.append(ValidationError(
                    error_id=f"negative_time_limit_{goal_id}",
                    severity="critical",
                    message=f"Goal {goal_id} has negative time limit",
                    affected_component="goal",
                    component_id=goal_id,
                ))

        return errors, warnings

    def _validate_events(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate events."""
        errors = []
        warnings = []

        total_events = sum(len(seq.events) for seq in narrative.sequences)

        if total_events == 0:
            warnings.append(ValidationError(
                error_id="no_events",
                severity="warning",
                message="Narrative has no events",
                affected_component="event",
            ))

        entity_ids = set(narrative.entities.keys())

        for sequence in narrative.sequences:
            for event in sequence.events:
                # Validate triggering entity
                if event.triggering_entity and event.triggering_entity not in entity_ids:
                    warnings.append(ValidationError(
                        error_id=f"unknown_triggering_entity_{event.event_id}",
                        severity="warning",
                        message=f"Event {event.event_id} references unknown entity {event.triggering_entity}",
                        affected_component="event",
                        component_id=event.event_id,
                    ))

                # Validate affected entities
                for affected_id in event.affected_entities:
                    if affected_id not in entity_ids:
                        warnings.append(ValidationError(
                            error_id=f"unknown_affected_entity_{event.event_id}",
                            severity="warning",
                            message=f"Event {event.event_id} references unknown entity {affected_id}",
                            affected_component="event",
                            component_id=event.event_id,
                        ))

                # Validate confidence
                if not (0.0 <= event.confidence <= 1.0):
                    errors.append(ValidationError(
                        error_id=f"invalid_confidence_{event.event_id}",
                        severity="critical",
                        message=f"Event {event.event_id} has invalid confidence: {event.confidence}",
                        affected_component="event",
                        component_id=event.event_id,
                    ))

        return errors, warnings

    def _validate_constraints(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate constraints."""
        errors = []
        warnings = []

        valid_types = ["safety", "efficiency", "realism", "challenge"]

        for constraint in narrative.constraints:
            if constraint.constraint_type not in valid_types:
                warnings.append(ValidationError(
                    error_id=f"unknown_constraint_type_{constraint.constraint_id}",
                    severity="warning",
                    message=f"Unknown constraint type: {constraint.constraint_type}",
                    affected_component="constraint",
                    component_id=constraint.constraint_id,
                ))

            if not (-1.0 <= constraint.violation_penalty <= 0.0):
                errors.append(ValidationError(
                    error_id=f"invalid_penalty_{constraint.constraint_id}",
                    severity="critical",
                    message=f"Constraint {constraint.constraint_id} has invalid penalty",
                    affected_component="constraint",
                    component_id=constraint.constraint_id,
                ))

        return errors, warnings

    def _validate_timeline(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate event timeline consistency."""
        errors = []
        warnings = []

        for sequence in narrative.sequences:
            prev_time = 0.0

            for event in sequence.events:
                if event.timestamp_sec < prev_time:
                    errors.append(ValidationError(
                        error_id=f"non_monotonic_time_{event.event_id}",
                        severity="critical",
                        message=f"Event {event.event_id} timestamp goes backward",
                        affected_component="event",
                        component_id=event.event_id,
                    ))

                prev_time = event.timestamp_sec

        return errors, warnings

    def _validate_entity_references(
        self, narrative: Narrative
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate all entity references are valid."""
        errors = []
        warnings = []

        entity_ids = set(narrative.entities.keys())
        goal_ids = set(narrative.goals.keys())

        for goal in narrative.goals.values():
            if goal.target and "target_entity_id" in goal.target:
                target_id = goal.target["target_entity_id"]

                if target_id not in entity_ids:
                    warnings.append(ValidationError(
                        error_id=f"invalid_goal_target_{goal.goal_id}",
                        severity="warning",
                        message=f"Goal {goal.goal_id} targets unknown entity {target_id}",
                        affected_component="goal",
                        component_id=goal.goal_id,
                    ))

        return errors, warnings

    def _compute_feasibility_score(
        self,
        narrative: Narrative,
        errors: List[ValidationError],
    ) -> float:
        """Compute feasibility score (0-1).

        Args:
            narrative: Narrative
            errors: Validation errors

        Returns:
            Feasibility score
        """
        score = 1.0

        # Reduce score for each critical error
        critical_errors = sum(1 for e in errors if e.severity == "critical")
        score -= critical_errors * 0.2

        # Reduce score if no goals
        if len(narrative.goals) == 0:
            score -= 0.1

        # Increase score if many entities
        entity_count = len(narrative.entities)
        if entity_count >= 3:
            score += 0.1
        elif entity_count == 0:
            score -= 0.3

        return max(0.0, min(score, 1.0))

    def _compute_sensor_coverage_score(self, narrative: Narrative) -> float:
        """Compute sensor coverage score (0-1).

        Measures what fraction of robots have sensor suites configured.

        Args:
            narrative: Narrative

        Returns:
            Coverage score
        """
        robots = [e for e in narrative.entities.values() if e.entity_type == "robot"]

        if not robots:
            return 0.5  # Neutral if no robots

        configured = sum(1 for r in robots if r.sensor_suite)
        return configured / len(robots)

    def _compute_constraint_satisfaction_score(self, narrative: Narrative) -> float:
        """Compute constraint satisfaction score (0-1).

        Measures how well-specified constraints are.

        Args:
            narrative: Narrative

        Returns:
            Satisfaction score
        """
        if len(narrative.constraints) == 0:
            return 0.5  # Neutral if no constraints

        valid_constraints = sum(
            1 for c in narrative.constraints
            if c.constraint_type in ["safety", "efficiency", "realism", "challenge"]
            and -1.0 <= c.violation_penalty <= 0.0
        )

        return valid_constraints / len(narrative.constraints)
