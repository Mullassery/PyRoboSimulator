"""Narrative Executor - Runtime Simulation Tracking.

Tracks narrative state during simulation execution.
Manages event sequencing, goal progress, and constraint monitoring.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.narratives.narrative_definitions import (
    Narrative,
    NarrativeEvent,
    NarrativeExecutionContext,
    NarrativeGoal,
)

logger = logging.getLogger(__name__)


class NarrativeExecutor:
    """Executes narrative during simulation.

    Tracks:
    - Current sequence and event
    - Entity states and positions
    - Goal progress
    - Constraint violations
    - Decision points and agent decisions
    """

    def __init__(self, narrative: Narrative):
        """Initialize executor.

        Args:
            narrative: Narrative to execute
        """
        self._narrative = narrative
        self._context = NarrativeExecutionContext(narrative=narrative)
        self._callbacks: Dict[str, List[callable]] = {
            "event_triggered": [],
            "goal_progress": [],
            "constraint_violated": [],
            "sequence_completed": [],
        }

    def start_execution(self) -> NarrativeExecutionContext:
        """Start narrative execution.

        Returns:
            Execution context
        """
        self._context.execution_state = "running"
        self._narrative.execution_state = "running"

        # Initialize entity states
        for entity_id, entity in self._narrative.entities.items():
            self._context.update_entity_state(entity_id, {
                "position": entity.initial_position,
                "orientation": entity.initial_orientation,
                "status": "active",
            })

        # Initialize goal progress
        for goal_id in self._narrative.goals.keys():
            self._context.update_goal_progress(goal_id, 0.0)

        logger.info(f"Started narrative execution: {self._narrative.title}")
        return self._context

    def pause_execution(self) -> None:
        """Pause narrative execution."""
        self._context.execution_state = "paused"
        self._narrative.execution_state = "paused"
        logger.info("Narrative execution paused")

    def resume_execution(self) -> None:
        """Resume narrative execution."""
        self._context.execution_state = "running"
        self._narrative.execution_state = "running"
        logger.info("Narrative execution resumed")

    def update(self, elapsed_time_sec: float, simulation_state: Dict[str, Any]) -> None:
        """Update narrative execution.

        Args:
            elapsed_time_sec: Simulation elapsed time
            simulation_state: Current simulation state (positions, sensor data, etc.)
        """
        self._context.elapsed_time_sec = elapsed_time_sec

        # Process current sequence
        if self._context.current_sequence_idx < len(self._narrative.sequences):
            self._process_sequence(self._context.current_sequence_idx, simulation_state)

        # Update goal progress
        self._update_goal_progress(simulation_state)

        # Check constraints
        self._check_constraints(simulation_state)

    def _process_sequence(self, seq_idx: int, simulation_state: Dict[str, Any]) -> None:
        """Process events in current sequence."""
        if seq_idx >= len(self._narrative.sequences):
            return

        sequence = self._narrative.sequences[seq_idx]

        # Process events up to current time
        for evt_idx, event in enumerate(sequence.events):
            if evt_idx >= self._context.current_event_idx:
                if event.timestamp_sec <= self._context.elapsed_time_sec:
                    self._trigger_event(event, simulation_state)
                    self._context.current_event_idx += 1
                else:
                    break

        # Check if sequence is complete
        if self._context.current_event_idx >= len(sequence.events):
            self._on_sequence_completed(seq_idx)
            self._context.current_sequence_idx += 1
            self._context.current_event_idx = 0

    def _trigger_event(self, event: NarrativeEvent, simulation_state: Dict[str, Any]) -> None:
        """Trigger a narrative event."""
        logger.info(f"Triggering event: {event.event_id} - {event.description}")

        self._context.events_executed.append(event)

        # Notify callbacks
        for callback in self._callbacks.get("event_triggered", []):
            callback(event)

        # Execute event effects
        self._execute_event_effects(event, simulation_state)

    def _execute_event_effects(self, event: NarrativeEvent, simulation_state: Dict[str, Any]) -> None:
        """Execute effects of an event."""
        params = event.parameters

        if event.event_id.startswith("goal_"):
            # Goal milestone achieved
            for goal_id in self._narrative.goals.keys():
                if goal_id in params.get("related_goals", []):
                    progress = params.get("progress_increment", 0.25)
                    current = self._context.goal_progress.get(goal_id, 0.0)
                    self._context.update_goal_progress(goal_id, current + progress)

        # Update affected entity states
        for entity_id in event.affected_entities:
            if "position_delta" in params:
                current_pos = self._context.entity_states.get(entity_id, {}).get("position", [0, 0, 0])
                delta = params["position_delta"]
                new_pos = tuple(current_pos[i] + delta[i] for i in range(3))
                self._context.update_entity_state(entity_id, {"position": new_pos})

            if "status" in params:
                entity_state = self._context.entity_states.get(entity_id, {})
                entity_state["status"] = params["status"]
                self._context.update_entity_state(entity_id, entity_state)

    def _update_goal_progress(self, simulation_state: Dict[str, Any]) -> None:
        """Update progress toward goals based on simulation state."""
        for goal_id, goal in self._narrative.goals.items():
            progress = self._compute_goal_progress(goal, simulation_state)
            self._context.update_goal_progress(goal_id, progress)

            # Notify if significant progress
            if goal_id not in self._context.goal_progress:
                self._context.goal_progress[goal_id] = progress
            elif progress > self._context.goal_progress[goal_id]:
                for callback in self._callbacks.get("goal_progress", []):
                    callback(goal_id, progress)

    def _compute_goal_progress(self, goal: NarrativeGoal, simulation_state: Dict[str, Any]) -> float:
        """Compute progress toward a goal (0-1)."""
        goal_type = goal.goal_type

        if goal_type == "reach_location":
            # Compute distance to goal location
            target_pos = goal.target.get("position", [0, 0, 0])
            agent_pos = simulation_state.get("agent_position", [0, 0, 0])

            distance = sum((agent_pos[i] - target_pos[i])**2 for i in range(3))**0.5
            max_distance = goal.target.get("tolerance", 10.0)

            return max(0.0, 1.0 - (distance / max_distance))

        elif goal_type == "inspect_area":
            # Compute area coverage
            visited_area = simulation_state.get("visited_area", 0.0)
            total_area = goal.target.get("area_size", 100.0)

            return min(visited_area / total_area, 1.0)

        elif goal_type == "avoid_obstacle":
            # Compute minimum distance to obstacles
            min_distance = simulation_state.get("min_obstacle_distance", float('inf'))
            safety_distance = goal.target.get("min_distance", 2.0)

            return 1.0 if min_distance >= safety_distance else 0.0

        else:
            return self._context.goal_progress.get(goal.goal_id, 0.0)

    def _check_constraints(self, simulation_state: Dict[str, Any]) -> None:
        """Check narrative constraints."""
        for constraint in self._narrative.constraints:
            violated = self._evaluate_constraint(constraint, simulation_state)

            if violated:
                self._on_constraint_violated(constraint)

    def _evaluate_constraint(self, constraint: Any, simulation_state: Dict[str, Any]) -> bool:
        """Evaluate if a constraint is violated."""
        constraint_type = constraint.constraint_type

        if constraint_type == "safety":
            # Check collision/safety distances
            min_distance = simulation_state.get("min_obstacle_distance", float('inf'))
            return min_distance < 1.0  # Too close

        elif constraint_type == "efficiency":
            # Check if solution is efficient enough
            time_used = self._context.elapsed_time_sec
            time_limit = self._narrative.sequences[0].duration_sec * 1.5
            return time_used > time_limit

        else:
            return False

    def _on_constraint_violated(self, constraint: Any) -> None:
        """Handle constraint violation."""
        logger.warning(f"Constraint violated: {constraint.description}")
        self._context.record_violation(constraint.constraint_id, self._context.elapsed_time_sec)

        for callback in self._callbacks.get("constraint_violated", []):
            callback(constraint)

    def _on_sequence_completed(self, seq_idx: int) -> None:
        """Handle sequence completion."""
        sequence = self._narrative.sequences[seq_idx]
        logger.info(f"Sequence completed: {sequence.name}")

        for callback in self._callbacks.get("sequence_completed", []):
            callback(sequence)

    def register_callback(self, event_type: str, callback: callable) -> None:
        """Register callback for narrative event.

        Args:
            event_type: "event_triggered" | "goal_progress" | "constraint_violated" | "sequence_completed"
            callback: Callable to invoke
        """
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)

    def get_context(self) -> NarrativeExecutionContext:
        """Get current execution context.

        Returns:
            Execution context
        """
        return self._context

    def finish_execution(self, outcome: str = "completed") -> Dict[str, Any]:
        """Finish narrative execution.

        Args:
            outcome: "completed" | "failed" | "interrupted"

        Returns:
            Execution summary
        """
        self._context.execution_state = outcome
        self._narrative.execution_state = outcome

        # Compute execution summary
        total_goals = len(self._narrative.goals)
        completed_goals = sum(1 for p in self._context.goal_progress.values() if p >= 0.95)

        summary = {
            "narrative_id": self._narrative.narrative_id,
            "outcome": outcome,
            "total_time_sec": self._context.elapsed_time_sec,
            "goals_completed": completed_goals,
            "goals_total": total_goals,
            "success_rate": completed_goals / total_goals if total_goals > 0 else 0.0,
            "constraints_violated": len(self._context.constraint_violations),
            "events_triggered": len(self._context.events_executed),
            "decisions_made": len(self._context.decisions_made),
        }

        logger.info(f"Narrative execution finished: {outcome} " +
                   f"({completed_goals}/{total_goals} goals, " +
                   f"{len(self._context.constraint_violations)} violations)")

        return summary
