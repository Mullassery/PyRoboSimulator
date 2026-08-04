"""Story Branching Engine - Dynamic Narrative Paths.

Enables conditional and probabilistic branching in narratives
based on simulation outcomes and agent decisions.
"""

import logging
import random
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from backend.src.narratives.narrative_definitions import (
    Narrative,
    NarrativeBranch,
    NarrativeBranchPoint,
    NarrativeSequence,
)

logger = logging.getLogger(__name__)


class BranchCondition:
    """Condition for narrative branching."""

    def __init__(
        self,
        condition_id: str,
        description: str,
        evaluator: Callable[[Dict[str, Any]], bool],
    ):
        """Initialize condition.

        Args:
            condition_id: Unique identifier
            description: Human-readable description
            evaluator: Function that evaluates condition
        """
        self.condition_id = condition_id
        self.description = description
        self.evaluator = evaluator

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition.

        Args:
            context: Simulation context (states, metrics, etc.)

        Returns:
            True if condition met
        """
        try:
            return self.evaluator(context)
        except Exception as e:
            logger.warning(f"Error evaluating condition {self.condition_id}: {e}")
            return False


class BranchPath:
    """A possible path through a narrative branch."""

    def __init__(
        self,
        path_id: str,
        description: str,
        sequence: NarrativeSequence,
        probability: float = 1.0,
    ):
        """Initialize branch path.

        Args:
            path_id: Unique identifier
            description: Path description
            sequence: Sequence to execute on this path
            probability: Probability of this path (for probabilistic branches)
        """
        self.path_id = path_id
        self.description = description
        self.sequence = sequence
        self.probability = probability
        self.taken_count = 0


class BranchingDecision:
    """A decision made at a branch point."""

    def __init__(
        self,
        branch_id: str,
        selected_path_id: str,
        timestamp_sec: float,
        context: Dict[str, Any],
        decision_maker: str = "system",
    ):
        """Initialize branching decision.

        Args:
            branch_id: Branch point ID
            selected_path_id: Selected path ID
            timestamp_sec: When decision was made
            context: Context that influenced decision
            decision_maker: Who/what made the decision
        """
        self.branch_id = branch_id
        self.selected_path_id = selected_path_id
        self.timestamp_sec = timestamp_sec
        self.context = context
        self.decision_maker = decision_maker

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "branch_id": self.branch_id,
            "selected_path_id": self.selected_path_id,
            "timestamp_sec": self.timestamp_sec,
            "decision_maker": self.decision_maker,
        }


class StoryBranchingEngine:
    """Manages dynamic branching in narratives.

    Supports:
    - Conditional branching (if-then paths)
    - Probabilistic branching (weighted random selection)
    - Agent-driven branching (based on agent decisions)
    - Multi-path exploration (parallel story threads)
    """

    def __init__(self):
        """Initialize branching engine."""
        self._conditions: Dict[str, BranchCondition] = {}
        self._branch_points: Dict[str, Dict[str, List[BranchPath]]] = {}
        self._decisions_made: List[BranchingDecision] = []
        self._active_paths: Set[str] = set()

    def register_condition(self, condition: BranchCondition) -> None:
        """Register a branch condition.

        Args:
            condition: Condition to register
        """
        self._conditions[condition.condition_id] = condition
        logger.info(f"Registered condition: {condition.description}")

    def add_branch_point(
        self,
        narrative_id: str,
        branch_point: NarrativeBranchPoint,
        paths: List[BranchPath],
    ) -> None:
        """Add branch point to narrative.

        Args:
            narrative_id: Narrative ID
            branch_point: Branch point definition
            paths: Possible paths from this branch
        """
        key = f"{narrative_id}_{branch_point.branch_id}"
        self._branch_points[key] = {
            "branch_point": branch_point,
            "paths": paths,
        }
        logger.info(f"Added branch point {branch_point.branch_id} with {len(paths)} paths")

    def evaluate_branch(
        self,
        narrative_id: str,
        branch_id: str,
        context: Dict[str, Any],
        elapsed_time_sec: float,
    ) -> Optional[BranchPath]:
        """Evaluate which path to take at a branch point.

        Args:
            narrative_id: Narrative ID
            branch_id: Branch point ID
            context: Simulation context
            elapsed_time_sec: Current time

        Returns:
            Selected branch path or None
        """
        key = f"{narrative_id}_{branch_id}"

        if key not in self._branch_points:
            logger.warning(f"Branch point not found: {key}")
            return None

        branch_data = self._branch_points[key]
        branch_point = branch_data["branch_point"]
        paths = branch_data["paths"]

        # Select path based on branch type
        selected_path = None

        if branch_point.branch_type == NarrativeBranch.LINEAR:
            # Linear: always take first path
            selected_path = paths[0] if paths else None

        elif branch_point.branch_type == NarrativeBranch.CONDITIONAL:
            # Conditional: evaluate conditions for each path
            selected_path = self._evaluate_conditional_branch(paths, context)

        elif branch_point.branch_type == NarrativeBranch.PROBABILISTIC:
            # Probabilistic: random selection weighted by probability
            selected_path = self._evaluate_probabilistic_branch(paths)

        elif branch_point.branch_type == NarrativeBranch.AGENT_DRIVEN:
            # Agent-driven: depends on agent decision (query agent policy)
            selected_path = self._evaluate_agent_driven_branch(paths, context)

        if selected_path:
            # Record decision
            decision = BranchingDecision(
                branch_id=branch_id,
                selected_path_id=selected_path.path_id,
                timestamp_sec=elapsed_time_sec,
                context=context,
                decision_maker=branch_point.decision_maker or "system",
            )
            self._decisions_made.append(decision)

            logger.info(f"Branch {branch_id}: selected {selected_path.path_id}")
            selected_path.taken_count += 1

        return selected_path

    def _evaluate_conditional_branch(
        self,
        paths: List[BranchPath],
        context: Dict[str, Any],
    ) -> Optional[BranchPath]:
        """Evaluate conditional branch."""
        for path in paths:
            # Path description may contain condition reference
            # e.g., "path_success" where "success" condition exists
            for cond_id, condition in self._conditions.items():
                if cond_id in path.description.lower():
                    if condition.evaluate(context):
                        return path

        # If no condition matched, return first path
        return paths[0] if paths else None

    def _evaluate_probabilistic_branch(self, paths: List[BranchPath]) -> Optional[BranchPath]:
        """Evaluate probabilistic branch using weighted random selection."""
        if not paths:
            return None

        # Normalize probabilities
        total_prob = sum(p.probability for p in paths)

        if total_prob <= 0:
            return paths[0]

        # Select using weighted random
        rand_val = random.uniform(0, total_prob)
        cumulative = 0.0

        for path in paths:
            cumulative += path.probability

            if rand_val <= cumulative:
                return path

        return paths[-1]

    def _evaluate_agent_driven_branch(
        self,
        paths: List[BranchPath],
        context: Dict[str, Any],
    ) -> Optional[BranchPath]:
        """Evaluate agent-driven branch.

        In a real system, this would query the agent's policy network.
        For now, use heuristic based on context.
        """
        if not paths:
            return None

        # Heuristic: prefer paths with higher success probability
        # or paths matching agent capabilities
        agent_capabilities = context.get("agent_capabilities", set())

        best_path = paths[0]
        best_score = 0.0

        for path in paths:
            score = path.probability

            # Boost score if path matches capabilities
            if agent_capabilities:
                path_reqs = set(path.description.lower().split())
                capability_overlap = len(path_reqs & agent_capabilities)
                score += capability_overlap * 0.1

            if score > best_score:
                best_score = score
                best_path = path

        return best_path

    def create_conditional_paths(
        self,
        condition_descriptions: Dict[str, str],
        sequences: Dict[str, NarrativeSequence],
    ) -> List[BranchPath]:
        """Create paths based on condition-sequence mapping.

        Args:
            condition_descriptions: Mapping of condition -> description
            sequences: Mapping of sequence_id -> NarrativeSequence

        Returns:
            List of branch paths
        """
        paths = []

        for seq_id, condition_desc in condition_descriptions.items():
            if seq_id in sequences:
                path = BranchPath(
                    path_id=f"path_{seq_id}",
                    description=condition_desc,
                    sequence=sequences[seq_id],
                    probability=1.0,
                )
                paths.append(path)

        return paths

    def create_probabilistic_paths(
        self,
        sequence_probabilities: Dict[str, Tuple[NarrativeSequence, float]],
    ) -> List[BranchPath]:
        """Create probabilistic paths.

        Args:
            sequence_probabilities: Mapping of path_id -> (sequence, probability)

        Returns:
            List of branch paths
        """
        paths = []

        for path_id, (sequence, probability) in sequence_probabilities.items():
            path = BranchPath(
                path_id=path_id,
                description=f"Probabilistic path {path_id}",
                sequence=sequence,
                probability=probability,
            )
            paths.append(path)

        return paths

    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get history of branching decisions.

        Returns:
            List of decisions made
        """
        return [d.to_dict() for d in self._decisions_made]

    def get_branch_statistics(self) -> Dict[str, Any]:
        """Get statistics about branching.

        Returns:
            Statistics dictionary
        """
        total_decisions = len(self._decisions_made)
        decision_makers = set(d.decision_maker for d in self._decisions_made)
        branch_usage = {}

        for decision in self._decisions_made:
            branch_id = decision.branch_id
            if branch_id not in branch_usage:
                branch_usage[branch_id] = {}

            path_id = decision.selected_path_id
            branch_usage[branch_id][path_id] = branch_usage[branch_id].get(path_id, 0) + 1

        return {
            "total_branch_points": len(self._branch_points),
            "total_decisions": total_decisions,
            "unique_decision_makers": len(decision_makers),
            "branch_usage": branch_usage,
        }

    def reset_decisions(self) -> None:
        """Reset decision history."""
        self._decisions_made.clear()
        for paths_dict in self._branch_points.values():
            for path in paths_dict.get("paths", []):
                path.taken_count = 0

        logger.info("Reset branching decisions")
