"""Agent Coordinator - Multi-agent orchestration and communication.

Coordinates multiple robots/agents in simulation with shared learning.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class AgentCommunicationType(Enum):
    """Types of inter-agent communication."""
    BROADCAST = "broadcast"  # One-to-all
    TARGETED = "targeted"    # One-to-one
    HIERARCHICAL = "hierarchical"  # Through leader
    CONSENSUS = "consensus"  # Vote-based decision


class FormationType(Enum):
    """Formation types for multi-agent coordination."""
    SWARM = "swarm"          # Distributed collective
    LINE = "line"            # Linear arrangement
    CIRCLE = "circle"        # Circular arrangement
    GRID = "grid"            # Grid pattern
    HIERARCHY = "hierarchy"  # Leader-follower
    SCOUT = "scout"          # Leader with scouts


@dataclass
class AgentState:
    """State of a single agent in multi-agent system."""
    agent_id: str
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    role: str  # "leader", "follower", "scout"
    status: str  # "active", "idle", "failed"
    local_observations: Dict[str, Any] = field(default_factory=dict)
    shared_knowledge: Dict[str, Any] = field(default_factory=dict)
    message_buffer: List[Dict[str, Any]] = field(default_factory=list)
    path_taken: List[Tuple[float, float, float]] = field(default_factory=list)


@dataclass
class AgentMessage:
    """Message between agents."""
    sender_id: str
    recipient_id: str
    message_type: str  # "goal", "observation", "request", "response"
    content: Dict[str, Any]
    timestamp: float


@dataclass
class CollectiveKnowledge:
    """Shared knowledge pool for fleet learning."""
    team_id: str
    visited_locations: Set[Tuple[float, float]] = field(default_factory=set)
    detected_obstacles: List[Tuple[float, float, float]] = field(default_factory=list)
    successful_paths: List[List[Tuple[float, float, float]]] = field(default_factory=list)
    failed_actions: List[Dict[str, Any]] = field(default_factory=list)
    environmental_features: Dict[str, Any] = field(default_factory=dict)


class AgentCoordinator:
    """Coordinates multiple agents with communication and learning.

    Features:
    - Multi-agent simulation
    - Inter-agent communication
    - Formation control
    - Collective learning
    - Leader-follower hierarchies
    """

    def __init__(self, team_id: str):
        """Initialize coordinator.

        Args:
            team_id: Team identifier
        """
        self._team_id = team_id
        self._agents: Dict[str, AgentState] = {}
        self._leader_id: Optional[str] = None
        self._formation: FormationType = FormationType.SWARM
        self._communication_type: AgentCommunicationType = AgentCommunicationType.BROADCAST
        self._collective_knowledge = CollectiveKnowledge(team_id=team_id)
        self._message_queue: List[AgentMessage] = []
        self._collaboration_score = 0.0

    def register_agent(
        self,
        agent_id: str,
        initial_position: Tuple[float, float, float],
        role: str = "follower",
    ) -> None:
        """Register agent with coordinator.

        Args:
            agent_id: Agent identifier
            initial_position: Starting position
            role: Agent role (leader, follower, scout)
        """
        agent = AgentState(
            agent_id=agent_id,
            position=initial_position,
            velocity=(0.0, 0.0, 0.0),
            role=role,
            status="active",
        )

        self._agents[agent_id] = agent

        if role == "leader":
            self._leader_id = agent_id

        logger.info(f"Registered agent {agent_id} with role {role}")

    def update_agent_state(
        self,
        agent_id: str,
        position: Tuple[float, float, float],
        velocity: Tuple[float, float, float],
        observations: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update agent state in coordinator.

        Args:
            agent_id: Agent identifier
            position: Current position
            velocity: Current velocity
            observations: Local observations
        """
        if agent_id not in self._agents:
            return

        agent = self._agents[agent_id]
        agent.position = position
        agent.velocity = velocity

        if observations:
            agent.local_observations = observations

            # Update collective knowledge
            if "location" in observations:
                loc = observations["location"]
                self._collective_knowledge.visited_locations.add((loc[0], loc[1]))

            if "obstacles" in observations:
                self._collective_knowledge.detected_obstacles.extend(
                    observations["obstacles"]
                )

        # Record path
        agent.path_taken.append(position)

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: str,
        content: Dict[str, Any],
        timestamp: float,
    ) -> None:
        """Send message from one agent to another.

        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID
            message_type: Type of message
            content: Message content
            timestamp: Message timestamp
        """
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            timestamp=timestamp,
        )

        self._message_queue.append(message)

        logger.debug(f"Message from {sender_id} to {recipient_id}: {message_type}")

    def broadcast_message(
        self,
        sender_id: str,
        message_type: str,
        content: Dict[str, Any],
        timestamp: float,
    ) -> None:
        """Broadcast message to all agents.

        Args:
            sender_id: Sender agent ID
            message_type: Type of message
            content: Message content
            timestamp: Message timestamp
        """
        for recipient_id in self._agents.keys():
            if recipient_id != sender_id:
                self.send_message(sender_id, recipient_id, message_type, content, timestamp)

    def process_messages(self) -> Dict[str, List[AgentMessage]]:
        """Process pending messages.

        Returns:
            Dictionary mapping recipient_id to list of messages
        """
        messages_by_recipient: Dict[str, List[AgentMessage]] = {}

        for message in self._message_queue:
            if message.recipient_id not in messages_by_recipient:
                messages_by_recipient[message.recipient_id] = []

            messages_by_recipient[message.recipient_id].append(message)

        self._message_queue.clear()

        return messages_by_recipient

    def set_formation(self, formation: FormationType) -> None:
        """Set formation type for team.

        Args:
            formation: Formation type
        """
        self._formation = formation
        logger.info(f"Set formation to {formation.value}")

    def compute_formation_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """Compute formation positions for all agents.

        Returns:
            Dictionary mapping agent_id to target position
        """
        if not self._leader_id:
            return {}

        leader = self._agents[self._leader_id]
        leader_pos = leader.position
        target_positions = {}

        agent_list = list(self._agents.keys())
        follower_positions = [a for a in agent_list if a != self._leader_id]

        if self._formation == FormationType.LINE:
            # Linear formation
            for i, agent_id in enumerate(follower_positions):
                offset_x = (i + 1) * 2.0
                target_positions[agent_id] = (
                    leader_pos[0] + offset_x,
                    leader_pos[1],
                    leader_pos[2],
                )

        elif self._formation == FormationType.CIRCLE:
            # Circular formation
            import math

            n = len(follower_positions)
            radius = 5.0

            for i, agent_id in enumerate(follower_positions):
                angle = (i / n) * 2 * math.pi
                x = leader_pos[0] + radius * math.cos(angle)
                y = leader_pos[1] + radius * math.sin(angle)
                target_positions[agent_id] = (x, y, leader_pos[2])

        elif self._formation == FormationType.GRID:
            # Grid formation
            cols = int(len(follower_positions) ** 0.5) + 1
            spacing = 2.0

            for i, agent_id in enumerate(follower_positions):
                row = i // cols
                col = i % cols
                x = leader_pos[0] + col * spacing
                y = leader_pos[1] + row * spacing
                target_positions[agent_id] = (x, y, leader_pos[2])

        else:
            # Swarm: maintain proximity
            for i, agent_id in enumerate(follower_positions):
                offset_x = (i % 2) * 3.0 - 1.5
                offset_y = (i // 2) * 3.0
                target_positions[agent_id] = (
                    leader_pos[0] + offset_x,
                    leader_pos[1] + offset_y,
                    leader_pos[2],
                )

        return target_positions

    def record_successful_path(self, agent_id: str) -> None:
        """Record successful path for fleet learning.

        Args:
            agent_id: Agent who found successful path
        """
        if agent_id not in self._agents:
            return

        agent = self._agents[agent_id]
        self._collective_knowledge.successful_paths.append(agent.path_taken.copy())

        logger.info(f"Recorded successful path from {agent_id}")

    def record_failed_action(self, agent_id: str, action: Dict[str, Any]) -> None:
        """Record failed action for learning.

        Args:
            agent_id: Agent that failed
            action: Action that failed
        """
        self._collective_knowledge.failed_actions.append(
            {"agent_id": agent_id, "action": action}
        )

    def get_collective_knowledge(self) -> CollectiveKnowledge:
        """Get collective knowledge pool.

        Returns:
            CollectiveKnowledge
        """
        return self._collective_knowledge

    def get_team_status(self) -> Dict[str, Any]:
        """Get overall team status.

        Returns:
            Status dictionary
        """
        active_count = sum(1 for a in self._agents.values() if a.status == "active")
        failed_count = sum(1 for a in self._agents.values() if a.status == "failed")

        # Compute team cohesion (how well agents maintain formation)
        if len(self._agents) > 1:
            positions = [a.position for a in self._agents.values()]
            avg_pos = (
                sum(p[0] for p in positions) / len(positions),
                sum(p[1] for p in positions) / len(positions),
                sum(p[2] for p in positions) / len(positions),
            )

            distances = [
                sum((p[i] - avg_pos[i]) ** 2 for i in range(3)) ** 0.5
                for p in positions
            ]
            max_dist = max(distances)
            cohesion = 1.0 / (1.0 + max_dist)
        else:
            cohesion = 1.0

        return {
            "team_id": self._team_id,
            "total_agents": len(self._agents),
            "active_agents": active_count,
            "failed_agents": failed_count,
            "formation": self._formation.value,
            "leader_id": self._leader_id,
            "team_cohesion": cohesion,
            "visited_locations": len(self._collective_knowledge.visited_locations),
            "detected_obstacles": len(self._collective_knowledge.detected_obstacles),
            "successful_paths": len(self._collective_knowledge.successful_paths),
            "failed_actions": len(self._collective_knowledge.failed_actions),
        }

    def get_agent_count(self) -> int:
        """Get number of agents in team.

        Returns:
            Agent count
        """
        return len(self._agents)

    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get state of specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentState or None
        """
        return self._agents.get(agent_id)

    def reset(self) -> None:
        """Reset team state."""
        self._agents.clear()
        self._message_queue.clear()
        self._collective_knowledge = CollectiveKnowledge(team_id=self._team_id)
        self._leader_id = None

        logger.info(f"Reset team {self._team_id}")
