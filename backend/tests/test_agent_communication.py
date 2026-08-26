"""Tests for Phase 2.4: Multi-Agent Communication."""

import time
import pytest

from src.services.agent_communication import (
    CommunicationNetwork,
    CoordinationPrimitive,
    LeaderElection,
    Message,
    MessagePriority,
    MessageQueue,
    MessageType,
)


class TestMessage:
    """Test message."""

    def test_message_creation(self):
        """Test creating message."""
        msg = Message(
            sender_id="agent_1",
            message_type=MessageType.DIRECT,
            content={"text": "hello"},
            timestamp=time.time(),
            message_id="msg_1",
        )
        assert msg.sender_id == "agent_1"
        assert msg.message_type == MessageType.DIRECT

    def test_message_expiration(self):
        """Test message expiration."""
        old_time = time.time() - 400
        msg = Message(
            sender_id="agent_1",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=old_time,
            message_id="msg_1",
            expiration_time=300.0,
        )

        assert msg.is_expired()

    def test_message_not_expired(self):
        """Test message not expired."""
        msg = Message(
            sender_id="agent_1",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="msg_1",
            expiration_time=300.0,
        )

        assert not msg.is_expired()

    def test_message_acknowledgment(self):
        """Test message acknowledgment."""
        msg = Message(
            sender_id="agent_1",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="msg_1",
            recipients=["agent_2", "agent_3"],
        )

        assert not msg.delivered
        msg.acknowledge("agent_2")
        assert "agent_2" in msg.acknowledgments
        assert not msg.delivered

        msg.acknowledge("agent_3")
        assert msg.delivered


class TestMessageQueue:
    """Test message queue."""

    def test_queue_creation(self):
        """Test creating queue."""
        queue = MessageQueue("agent_1")
        assert queue.agent_id == "agent_1"
        assert queue.size() == 0

    def test_enqueue(self):
        """Test enqueuing message."""
        queue = MessageQueue("agent_1")
        msg = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="msg_1",
        )

        result = queue.enqueue(msg)
        assert result
        assert queue.size() == 1

    def test_dequeue(self):
        """Test dequeuing message."""
        queue = MessageQueue("agent_1")
        msg = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={"text": "hello"},
            timestamp=time.time(),
            message_id="msg_1",
        )

        queue.enqueue(msg)
        dequeued = queue.dequeue()

        assert dequeued is not None
        assert dequeued.message_id == "msg_1"
        assert queue.size() == 0

    def test_priority_ordering(self):
        """Test message priority ordering."""
        queue = MessageQueue("agent_1")

        # Add messages in reverse priority order
        msg_low = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="msg_low",
            priority=MessagePriority.LOW,
        )
        msg_high = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="msg_high",
            priority=MessagePriority.HIGH,
        )

        queue.enqueue(msg_low)
        queue.enqueue(msg_high)

        # Should dequeue high priority first
        first = queue.dequeue()
        assert first.message_id == "msg_high"

    def test_peek(self):
        """Test peeking at messages."""
        queue = MessageQueue("agent_1")

        for i in range(5):
            msg = Message(
                sender_id="agent_2",
                message_type=MessageType.DIRECT,
                content={},
                timestamp=time.time(),
                message_id=f"msg_{i}",
            )
            queue.enqueue(msg)

        peeked = queue.peek(3)
        assert len(peeked) == 3
        assert queue.size() == 5  # Not removed

    def test_get_message_by_id(self):
        """Test getting message by ID."""
        queue = MessageQueue("agent_1")
        msg = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={"data": "test"},
            timestamp=time.time(),
            message_id="msg_1",
        )

        queue.enqueue(msg)
        retrieved = queue.get_message("msg_1")

        assert retrieved is not None
        assert retrieved.content["data"] == "test"

    def test_clear_expired(self):
        """Test clearing expired messages."""
        queue = MessageQueue("agent_1")

        # Add old expired message
        old_msg = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time() - 400,
            message_id="old_msg",
            expiration_time=300.0,
        )

        # Add fresh message
        new_msg = Message(
            sender_id="agent_2",
            message_type=MessageType.DIRECT,
            content={},
            timestamp=time.time(),
            message_id="new_msg",
        )

        queue.enqueue(old_msg)
        queue.enqueue(new_msg)

        cleared = queue.clear_expired()
        assert cleared == 1
        assert queue.size() == 1

    def test_queue_capacity(self):
        """Test queue capacity limit."""
        queue = MessageQueue("agent_1", max_queue_size=5)

        for i in range(10):
            msg = Message(
                sender_id="agent_2",
                message_type=MessageType.DIRECT,
                content={},
                timestamp=time.time(),
                message_id=f"msg_{i}",
            )
            result = queue.enqueue(msg)
            if i >= 5:
                assert not result

        assert queue.size() <= 5


class TestCommunicationNetwork:
    """Test communication network."""

    def test_network_creation(self):
        """Test creating network."""
        network = CommunicationNetwork()
        assert len(network.agents) == 0

    def test_register_agent(self):
        """Test registering agent."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")

        assert "agent_1" in network.agents
        assert "agent_1" in network.queues

    def test_unregister_agent(self):
        """Test unregistering agent."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.unregister_agent("agent_1")

        assert "agent_1" not in network.agents

    def test_send_direct_message(self):
        """Test sending direct message."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        msg_id = network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"text": "hello"},
            recipients=["agent_2"],
        )

        assert msg_id is not None
        assert network.total_messages == 1

    def test_receive_message(self):
        """Test receiving message."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"text": "hello"},
            recipients=["agent_2"],
        )

        received = network.receive_message("agent_2")
        assert received is not None
        assert received.content["text"] == "hello"

    def test_broadcast_message(self):
        """Test broadcasting message."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")

        msg_id = network.send_message(
            "agent_1",
            MessageType.BROADCAST,
            {"text": "broadcast"},
        )

        assert msg_id is not None

        # Both agent_2 and agent_3 should receive
        msg2 = network.receive_message("agent_2")
        msg3 = network.receive_message("agent_3")

        assert msg2 is not None
        assert msg3 is not None

    def test_receive_all_messages(self):
        """Test receiving all messages."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        for i in range(5):
            network.send_message(
                "agent_1",
                MessageType.DIRECT,
                {"index": i},
                recipients=["agent_2"],
            )

        messages = network.receive_all_messages("agent_2")
        assert len(messages) == 5

    def test_acknowledge_message(self):
        """Test acknowledging message."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        msg_id = network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {},
            recipients=["agent_2"],
        )

        result = network.acknowledge_message(msg_id, "agent_2")
        assert result

    def test_query_messages(self):
        """Test querying message history."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")

        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"type": "greeting"},
            recipients=["agent_2", "agent_3"],
        )

        # Query messages for agent_2 from agent_1
        messages = network.query_messages(
            "agent_2",
            sender_id="agent_1",
        )

        assert len(messages) > 0

    def test_queue_status(self):
        """Test getting queue status."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {},
            recipients=["agent_2"],
        )

        status = network.get_queue_status("agent_2")
        assert status is not None
        assert status["queue_size"] == 1

    def test_network_statistics(self):
        """Test network statistics."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {},
            recipients=["agent_2"],
        )

        stats = network.get_network_statistics()
        assert stats["total_agents"] == 2
        assert stats["total_messages_sent"] == 1

    def test_broadcast_to_nearby(self):
        """Test broadcasting to nearby agents."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")
        network.register_agent("agent_4")

        positions = {
            "agent_1": (0, 0),
            "agent_2": (5, 0),  # 5m away
            "agent_3": (15, 0),  # 15m away
            "agent_4": (20, 0),  # 20m away
        }

        msg_id = network.broadcast_to_nearby(
            "agent_1",
            {"text": "nearby"},
            range_m=10,
            agent_positions=positions,
        )

        assert msg_id is not None

        # agent_2 should receive
        msg = network.receive_message("agent_2")
        assert msg is not None

    def test_message_loss_on_unregistered(self):
        """Test message not sent to unregistered agent."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")

        # agent_2 not registered
        msg_id = network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {},
            recipients=["agent_2"],
        )

        # Should fail or have low success
        assert msg_id is None or network.total_messages == 0


class TestCoordinationPrimitive:
    """Test coordination primitives."""

    def test_coordination_creation(self):
        """Test creating coordination primitive."""
        network = CommunicationNetwork()
        prim = CoordinationPrimitive("test", network)

        assert prim.name == "test"
        assert len(prim.participants) == 0

    def test_join_leave(self):
        """Test joining and leaving."""
        network = CommunicationNetwork()
        prim = CoordinationPrimitive("test", network)

        prim.join("agent_1")
        assert "agent_1" in prim.participants

        prim.leave("agent_1")
        assert "agent_1" not in prim.participants

    def test_broadcast_to_group(self):
        """Test broadcasting to group."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")

        prim = CoordinationPrimitive("group", network)
        prim.join("agent_1")
        prim.join("agent_2")
        prim.join("agent_3")

        msg_id = prim.broadcast("agent_1", {"text": "group message"})
        assert msg_id is not None


class TestLeaderElection:
    """Test leader election."""

    def test_election_creation(self):
        """Test creating election."""
        network = CommunicationNetwork()
        election = LeaderElection(network)

        assert election.leader_id is None

    def test_run_election(self):
        """Test running election."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")

        election = LeaderElection(network)
        election.join("agent_1")
        election.join("agent_2")
        election.join("agent_3")

        leader = election.run_election()
        assert leader is not None
        assert leader in ["agent_1", "agent_2", "agent_3"]

    def test_get_leader(self):
        """Test getting leader."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        election = LeaderElection(network)
        election.join("agent_1")
        election.join("agent_2")

        assert election.get_leader() is None

        election.run_election()
        leader = election.get_leader()
        assert leader is not None

    def test_election_term_increment(self):
        """Test election term tracking."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        election = LeaderElection(network)
        election.join("agent_1")
        election.join("agent_2")

        assert election.term == 0

        election.run_election()
        assert election.term == 1

        election.run_election()
        assert election.term == 2


class TestCommunicationIntegration:
    """Integration tests for communication."""

    def test_multi_agent_conversation(self):
        """Test multi-agent communication."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")
        network.register_agent("agent_3")

        # agent_1 sends message
        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"text": "hello", "to": "agent_2"},
            recipients=["agent_2"],
        )

        # agent_2 receives and broadcasts response
        msg = network.receive_message("agent_2")
        assert msg is not None

        network.send_message(
            "agent_2",
            MessageType.BROADCAST,
            {"text": "received message"},
        )

        # Both agent_1 and agent_3 receive broadcast
        msg1 = network.receive_message("agent_1")
        msg3 = network.receive_message("agent_3")

        assert msg1 is not None
        assert msg3 is not None

    def test_message_priority_delivery(self):
        """Test priority-based message delivery."""
        network = CommunicationNetwork()
        network.register_agent("agent_1")
        network.register_agent("agent_2")

        # Send messages in different order than priority
        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"seq": 1},
            recipients=["agent_2"],
            priority=MessagePriority.LOW,
        )
        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"seq": 2},
            recipients=["agent_2"],
            priority=MessagePriority.CRITICAL,
        )
        network.send_message(
            "agent_1",
            MessageType.DIRECT,
            {"seq": 3},
            recipients=["agent_2"],
            priority=MessagePriority.NORMAL,
        )

        # Should receive in priority order
        msg1 = network.receive_message("agent_2")
        assert msg1.content["seq"] == 2  # CRITICAL

        msg2 = network.receive_message("agent_2")
        assert msg2.content["seq"] == 3  # NORMAL

        msg3 = network.receive_message("agent_2")
        assert msg3.content["seq"] == 1  # LOW
