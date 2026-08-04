"""Fleet Learning - Collective knowledge extraction and learning.

Agents learn from each other's experiences to improve collective performance.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ExperienceRecord:
    """Single learning experience from an agent."""
    agent_id: str
    scenario_id: str
    action_type: str
    success: bool
    outcome_metrics: Dict[str, float]
    timestamp: float
    path: List[Tuple[float, float, float]] = field(default_factory=list)
    obstacles_encountered: List[Tuple[float, float, float]] = field(default_factory=list)


@dataclass
class LearningPattern:
    """Identified pattern from fleet experience."""
    pattern_id: str
    pattern_type: str  # "successful_path", "obstacle_avoidance", "efficiency_technique"
    description: str
    success_rate: float  # 0-1, how often pattern succeeds
    adoption_count: int  # Number of agents using this
    confidence: float  # 0-1, confidence in pattern
    metadata: Dict[str, Any] = field(default_factory=dict)


class FleetLearningEngine:
    """Manages collective learning across multiple agents.

    Features:
    - Experience sharing
    - Pattern identification
    - Knowledge transfer
    - Performance benchmarking
    - Anomaly detection
    """

    def __init__(self, team_id: str):
        """Initialize fleet learning engine.

        Args:
            team_id: Team identifier
        """
        self._team_id = team_id
        self._experience_log: List[ExperienceRecord] = []
        self._patterns: Dict[str, LearningPattern] = {}
        self._agent_performances: Dict[str, float] = defaultdict(float)
        self._knowledge_base: Dict[str, Any] = {}

    def record_experience(
        self,
        agent_id: str,
        scenario_id: str,
        action_type: str,
        success: bool,
        outcome_metrics: Dict[str, float],
        timestamp: float,
        path: Optional[List[Tuple[float, float, float]]] = None,
        obstacles: Optional[List[Tuple[float, float, float]]] = None,
    ) -> None:
        """Record agent experience for learning.

        Args:
            agent_id: Agent ID
            scenario_id: Scenario ID
            action_type: Type of action
            success: Whether action succeeded
            outcome_metrics: Metrics from outcome
            timestamp: Experience timestamp
            path: Path taken
            obstacles: Obstacles encountered
        """
        experience = ExperienceRecord(
            agent_id=agent_id,
            scenario_id=scenario_id,
            action_type=action_type,
            success=success,
            outcome_metrics=outcome_metrics,
            timestamp=timestamp,
            path=path or [],
            obstacles_encountered=obstacles or [],
        )

        self._experience_log.append(experience)

        # Update agent performance
        if agent_id not in self._agent_performances:
            self._agent_performances[agent_id] = 0.0

        self._agent_performances[agent_id] = (
            0.7 * self._agent_performances[agent_id] + 0.3 * (1.0 if success else 0.0)
        )

        logger.debug(f"Recorded experience: {agent_id} {action_type} {'success' if success else 'failed'}")

    def identify_patterns(self) -> List[LearningPattern]:
        """Identify successful patterns from experience log.

        Returns:
            List of identified patterns
        """
        if len(self._experience_log) < 5:
            return []

        patterns = []

        # Pattern 1: Successful paths for specific scenarios
        scenario_successes: Dict[str, List[ExperienceRecord]] = defaultdict(list)

        for exp in self._experience_log:
            if exp.success:
                scenario_successes[exp.scenario_id].append(exp)

        for scenario_id, successes in scenario_successes.items():
            if len(successes) >= 2:
                success_rate = len(successes) / max(
                    len([e for e in self._experience_log if e.scenario_id == scenario_id]), 1
                )

                if success_rate > 0.6:
                    pattern = LearningPattern(
                        pattern_id=f"path_{scenario_id}",
                        pattern_type="successful_path",
                        description=f"Successful path for {scenario_id}",
                        success_rate=success_rate,
                        adoption_count=len(set(s.agent_id for s in successes)),
                        confidence=0.7,
                        metadata={"scenario": scenario_id, "example_paths": len(successes)},
                    )

                    patterns.append(pattern)

        # Pattern 2: Obstacle avoidance techniques
        obstacle_avoidances: Dict[str, List[ExperienceRecord]] = defaultdict(list)

        for exp in self._experience_log:
            if exp.success and "obstacle_avoidance" in exp.action_type:
                key = exp.action_type
                obstacle_avoidances[key].append(exp)

        for technique, techniques in obstacle_avoidances.items():
            if len(techniques) >= 2:
                pattern = LearningPattern(
                    pattern_id=f"technique_{technique}",
                    pattern_type="obstacle_avoidance",
                    description=f"Obstacle avoidance: {technique}",
                    success_rate=len(techniques) / max(
                        len([e for e in self._experience_log if e.action_type == technique]), 1
                    ),
                    adoption_count=len(set(t.agent_id for t in techniques)),
                    confidence=0.75,
                    metadata={"technique": technique},
                )

                patterns.append(pattern)

        self._patterns = {p.pattern_id: p for p in patterns}

        logger.info(f"Identified {len(patterns)} patterns from {len(self._experience_log)} experiences")

        return patterns

    def transfer_knowledge_to_agent(self, agent_id: str) -> Dict[str, Any]:
        """Transfer learned knowledge to specific agent.

        Args:
            agent_id: Target agent ID

        Returns:
            Dictionary of transferred knowledge
        """
        transferred = {
            "successful_patterns": [],
            "best_practices": [],
            "scenarios_learned": [],
            "estimated_improvements": {},
        }

        # Get top patterns
        sorted_patterns = sorted(
            self._patterns.values(),
            key=lambda p: (p.adoption_count, p.success_rate),
            reverse=True,
        )[:5]

        transferred["successful_patterns"] = [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type,
                "success_rate": p.success_rate,
                "adoption": p.adoption_count,
            }
            for p in sorted_patterns
        ]

        # Get best practices
        if self._agent_performances:
            top_agents = sorted(
                self._agent_performances.items(), key=lambda x: x[1], reverse=True
            )[:3]

            for top_agent, perf in top_agents:
                transferred["best_practices"].append(
                    {"agent_id": top_agent, "performance": perf}
                )

        # Get learned scenarios
        learned_scenarios = set(e.scenario_id for e in self._experience_log if e.success)
        transferred["scenarios_learned"] = list(learned_scenarios)

        # Estimate improvements
        avg_performance = sum(self._agent_performances.values()) / max(
            len(self._agent_performances), 1
        )
        current_agent_perf = self._agent_performances.get(agent_id, 0.5)
        estimated_improvement = (avg_performance - current_agent_perf) * 0.3  # 30% of gap

        transferred["estimated_improvements"]["performance_gain"] = estimated_improvement

        logger.info(
            f"Transferred knowledge to {agent_id}: "
            f"{len(transferred['successful_patterns'])} patterns, "
            f"{len(transferred['best_practices'])} practices"
        )

        return transferred

    def get_team_performance(self) -> Dict[str, Any]:
        """Get overall team performance metrics.

        Returns:
            Performance metrics
        """
        if not self._agent_performances:
            return {"avg_performance": 0.0, "agents": {}}

        avg_perf = sum(self._agent_performances.values()) / len(self._agent_performances)
        best_agent = max(self._agent_performances.items(), key=lambda x: x[1])
        worst_agent = min(self._agent_performances.items(), key=lambda x: x[1])

        # Success rate
        successes = len([e for e in self._experience_log if e.success])
        total = len(self._experience_log)
        success_rate = successes / total if total > 0 else 0.0

        return {
            "team_id": self._team_id,
            "avg_performance": avg_perf,
            "best_agent": {"id": best_agent[0], "performance": best_agent[1]},
            "worst_agent": {"id": worst_agent[0], "performance": worst_agent[1]},
            "overall_success_rate": success_rate,
            "total_experiences": total,
            "patterns_identified": len(self._patterns),
            "unique_scenarios_solved": len(set(e.scenario_id for e in self._experience_log if e.success)),
        }

    def get_agent_recommendation(self, agent_id: str) -> Dict[str, Any]:
        """Get personalized recommendation for agent.

        Args:
            agent_id: Agent ID

        Returns:
            Recommendation dictionary
        """
        agent_exps = [e for e in self._experience_log if e.agent_id == agent_id]
        success_rate = len([e for e in agent_exps if e.success]) / max(len(agent_exps), 1)

        recommendation = {
            "agent_id": agent_id,
            "current_performance": self._agent_performances.get(agent_id, 0.0),
            "success_rate": success_rate,
            "recommended_actions": [],
        }

        if success_rate < 0.5:
            recommendation["recommended_actions"].append(
                "Focus on learning from successful agents in the team"
            )
            recommendation["recommended_actions"].append("Review failure patterns")

        elif success_rate < 0.75:
            recommendation["recommended_actions"].append("Apply learned patterns to improve")

        else:
            recommendation["recommended_actions"].append("Agent performing well, maintain current strategy")

        # Find most similar successful agent
        if agent_exps:
            best_agents = [
                (aid, perf)
                for aid, perf in self._agent_performances.items()
                if aid != agent_id and perf > self._agent_performances.get(agent_id, 0.0)
            ]

            if best_agents:
                mentor = max(best_agents, key=lambda x: x[1])
                recommendation["suggested_mentor"] = mentor[0]

        return recommendation

    def reset(self) -> None:
        """Reset learning state."""
        self._experience_log.clear()
        self._patterns.clear()
        self._agent_performances.clear()
        self._knowledge_base.clear()

        logger.info(f"Reset fleet learning for team {self._team_id}")
