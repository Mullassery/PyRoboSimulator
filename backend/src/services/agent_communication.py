"""Multi-agent communication system.

Implements message passing, broadcasting, and coordination primitives.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages."""

    DIRECT = "direct"  # Point-to-point
    BROADCAST = "broadcast"  # All agents
    MULTICAST = "multicast"  # Subset of agents
    QUERY = "query"  # Request information
    RESPONSE = "response"  # Answer to query


class MessagePriority(Enum):
    """Message priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """Single message between agents."""

    sender_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: float
    message_id: str
    priority: MessagePriority = MessagePriority.NORMAL
    recipients: List[str] = field(default_factory=list)  # For direct/multicast
    expiration_time: float = 300.0  # Seconds until expiration
    delivered: bool = False
    delivered_time: Optional[float] = None
    acknowledgments: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Check if message has expired.

        Returns:
            Whether message is expired
        """
        age = time.time() - self.timestamp
        return age > self.expiration_time

    def acknowledge(self, recipient_id: str) -> None:
        """Record acknowledgment from recipient.

        Args:
            recipient_id: Recipient ID
        """
        self.acknowledgments.add(recipient_id)

        if len(self.acknowledgments) == len(self.recipients):
            self.delivered = True
            self.delivered_time = time.time()


class MessageQueue:
    """Queue of messages for an agent."""

    def __init__(self, agent_id: str, max_queue_size: int = 1000):
        """Initialize message queue.

        Args:
            agent_id: Agent identifier
            max_queue_size: Maximum messages to queue
        """
        self.agent_id = agent_id
        self.max_queue_size = max_queue_size
        self.messages: List[Message] = []
        self.message_index: Dict[str, Message] = {}
        self.processed_count = 0

    def enqueue(self, message: Message) -> bool:
        """Add message to queue.

        Args:
            message: Message to add

        Returns:
            Whether message was added
        """
        if len(self.messages) >= self.max_queue_size:
            logger.warning(f"Message queue full for {self.agent_id}")
            return False

        self.messages.append(message)
        self.message_index[message.message_id] = message

        # Sort by priority (highest first)
        self.messages.sort(key=lambda m: m.priority.value, reverse=True)

        return True

    def dequeue(self) -> Optional[Message]:
        """Get next message from queue.

        Returns:
            Message or None
        """
        # Remove expired messages
        self.messages = [m for m in self.messages if not m.is_expired()]

        if not self.messages:
            return None

        message = self.messages.pop(0)
        self.processed_count += 1
        return message

    def peek(self, count: int = 1) -> List[Message]:
        """Look at messages without removing.

        Args:
            count: Number of messages to peek

        Returns:
            List of messages
        """
        # Remove expired
        self.messages = [m for m in self.messages if not m.is_expired()]

        return self.messages[:count]

    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID.

        Args:
            message_id: Message ID

        Returns:
            Message or None
        """
        return self.message_index.get(message_id)

    def size(self) -> int:
        """Get queue size.

        Returns:
            Number of messages
        """
        return len(self.messages)

    def clear_expired(self) -> int:
        """Remove expired messages.

        Returns:
            Number of messages removed
        """
        before = len(self.messages)
        self.messages = [m for m in self.messages if not m.is_expired()]
        return before - len(self.messages)

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "queue_size": len(self.messages),
            "processed_count": self.processed_count,
            "expired_count": sum(1 for m in self.messages if m.is_expired()),
        }


class CommunicationNetwork:
    """Network connecting agents for communication."""

    def __init__(self):
        """Initialize communication network."""
        self.agents: Set[str] = set()
        self.queues: Dict[str, MessageQueue] = {}
        self.message_history: List[Message] = []
        self.max_history_size = 10000
        self.total_messages = 0
        self.message_counter = 0

    def register_agent(self, agent_id: str) -> None:
        """Register agent on network.

        Args:
            agent_id: Agent ID to register
        """
        if agent_id not in self.agents:
            self.agents.add(agent_id)
            self.queues[agent_id] = MessageQueue(agent_id)
            logger.debug(f"Agent {agent_id} registered on network")

    def unregister_agent(self, agent_id: str) -> None:
        """Unregister agent from network.

        Args:
            agent_id: Agent ID to unregister
        """
        if agent_id in self.agents:
            self.agents.remove(agent_id)
            del self.queues[agent_id]

    def send_message(
        self,
        sender_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        recipients: Optional[List[str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        expiration_time: float = 300.0,
    ) -> Optional[str]:
        """Send message to recipient(s).

        Args:
            sender_id: Sender agent ID
            message_type: Type of message
            content: Message content
            recipients: List of recipient IDs (None for broadcast)
            priority: Message priority
            expiration_time: Time until expiration

        Returns:
            Message ID or None if failed
        """
        # Ensure sender is registered
        if sender_id not in self.agents:
            logger.warning(f"Sender {sender_id} not registered")
            return None

        self.message_counter += 1
        message_id = f"msg_{self.message_counter}"

        # Determine recipients
        if message_type == MessageType.BROADCAST:
            recipients = list(self.agents - {sender_id})
        elif recipients is None:
            logger.warning("No recipients specified for direct message")
            return None

        # Create message
        message = Message(
            sender_id=sender_id,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            message_id=message_id,
            priority=priority,
            recipients=recipients,
            expiration_time=expiration_time,
        )

        # Enqueue to recipients
        success_count = 0
        for recipient_id in recipients:
            if recipient_id in self.queues:
                if self.queues[recipient_id].enqueue(message):
                    success_count += 1

        if success_count > 0:
            self.total_messages += 1
            self._record_history(message)
            return message_id

        return None

    def receive_message(self, agent_id: str) -> Optional[Message]:
        """Receive next message for agent.

        Args:
            agent_id: Agent ID

        Returns:
            Message or None
        """
        if agent_id not in self.queues:
            return None

        return self.queues[agent_id].dequeue()

    def receive_all_messages(self, agent_id: str) -> List[Message]:
        """Receive all queued messages for agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of messages
        """
        if agent_id not in self.queues:
            return []

        messages = []
        while True:
            msg = self.queues[agent_id].dequeue()
            if msg is None:
                break
            messages.append(msg)

        return messages

    def acknowledge_message(self, message_id: str, recipient_id: str) -> bool:
        """Send acknowledgment for message.

        Args:
            message_id: Message ID
            recipient_id: Recipient acknowledging

        Returns:
            Whether acknowledgment was recorded
        """
        for message in self.message_history:
            if message.message_id == message_id:
                message.acknowledge(recipient_id)
                return True

        return False

    def query_messages(
        self,
        agent_id: str,
        sender_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        min_age_s: float = 0,
        max_age_s: float = 300,
    ) -> List[Message]:
        """Query message history for an agent.

        Args:
            agent_id: Agent to query for
            sender_id: Filter by sender
            message_type: Filter by type
            min_age_s: Minimum age in seconds
            max_age_s: Maximum age in seconds

        Returns:
            List of matching messages
        """
        results = []
        now = time.time()

        for message in self.message_history:
            if agent_id not in message.recipients:
                continue

            age = now - message.timestamp
            if not (min_age_s <= age <= max_age_s):
                continue

            if sender_id and message.sender_id != sender_id:
                continue

            if message_type and message.message_type != message_type:
                continue

            results.append(message)

        return results

    def get_queue_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of agent's message queue.

        Args:
            agent_id: Agent ID

        Returns:
            Queue statistics or None
        """
        if agent_id not in self.queues:
            return None

        return self.queues[agent_id].get_statistics()

    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network statistics.

        Returns:
            Dictionary with stats
        """
        total_queued = sum(q.size() for q in self.queues.values())

        return {
            "total_agents": len(self.agents),
            "total_messages_sent": self.total_messages,
            "total_queued_messages": total_queued,
            "history_size": len(self.message_history),
        }

    def broadcast_to_nearby(
        self,
        sender_id: str,
        content: Dict[str, Any],
        range_m: float,
        agent_positions: Dict[str, tuple],
    ) -> str:
        """Broadcast to agents within range.

        Args:
            sender_id: Sender ID
            content: Message content
            range_m: Communication range in meters
            agent_positions: Dictionary of agent positions (x, y)

        Returns:
            Message ID
        """
        if sender_id not in agent_positions:
            return None

        sender_pos = agent_positions[sender_id]

        # Find nearby agents
        nearby = []
        for agent_id, pos in agent_positions.items():
            if agent_id == sender_id:
                continue

            dx = pos[0] - sender_pos[0]
            dy = pos[1] - sender_pos[1]
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist <= range_m:
                nearby.append(agent_id)

        if not nearby:
            return None

        return self.send_message(
            sender_id,
            MessageType.MULTICAST,
            content,
            recipients=nearby,
        )

    def _record_history(self, message: Message) -> None:
        """Record message in history.

        Args:
            message: Message to record
        """
        self.message_history.append(message)

        # Trim history if too large
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size :]


class CoordinationPrimitive:
    """Base class for coordination primitives."""

    def __init__(self, name: str, network: CommunicationNetwork):
        """Initialize coordination primitive.

        Args:
            name: Primitive name
            network: Communication network
        """
        self.name = name
        self.network = network
        self.participants: Set[str] = set()

    def join(self, agent_id: str) -> None:
        """Agent joins coordination group.

        Args:
            agent_id: Agent ID
        """
        self.participants.add(agent_id)

    def leave(self, agent_id: str) -> None:
        """Agent leaves coordination group.

        Args:
            agent_id: Agent ID
        """
        self.participants.discard(agent_id)

    def broadcast(
        self,
        sender_id: str,
        content: Dict[str, Any],
    ) -> Optional[str]:
        """Broadcast to group.

        Args:
            sender_id: Sender ID
            content: Message content

        Returns:
            Message ID
        """
        return self.network.send_message(
            sender_id,
            MessageType.BROADCAST,
            content,
            recipients=list(self.participants - {sender_id}),
        )


class LeaderElection(CoordinationPrimitive):
    """Leader election coordination primitive."""

    def __init__(self, network: CommunicationNetwork):
        """Initialize leader election.

        Args:
            network: Communication network
        """
        super().__init__("leader_election", network)
        self.leader_id: Optional[str] = None
        self.term = 0

    def run_election(self) -> Optional[str]:
        """Run leader election.

        Returns:
            Elected leader ID or None
        """
        if not self.participants:
            return None

        # Select highest ID as leader (simple strategy)
        self.leader_id = max(self.participants)
        self.term += 1

        # Broadcast election result
        self.broadcast(
            self.leader_id,
            {"type": "leader_elected", "leader": self.leader_id, "term": self.term},
        )

        return self.leader_id

    def get_leader(self) -> Optional[str]:
        """Get current leader.

        Returns:
            Leader ID or None
        """
        return self.leader_id
