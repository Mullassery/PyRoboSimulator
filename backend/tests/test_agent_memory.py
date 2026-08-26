"""Tests for Phase 2.3: Agent Memory & State."""

import time
import pytest

from src.services.agent_memory import (
    AgentMemory,
    Emotion,
    MemoryEntry,
    MemoryType,
    Relationship,
)


class TestMemoryEntry:
    """Test memory entry."""

    def test_entry_creation(self):
        """Test creating memory entry."""
        entry = MemoryEntry(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content={"event": "collision"},
            timestamp=time.time(),
            importance=0.8,
        )
        assert entry.id == "mem_1"
        assert entry.memory_type == MemoryType.EPISODIC

    def test_memory_strength(self):
        """Test memory strength calculation."""
        now = time.time()
        entry = MemoryEntry(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content={},
            timestamp=now,
            importance=0.8,
            decay_rate=0.0,  # No decay for test
        )

        strength = entry.get_strength()
        assert abs(strength - 0.8) < 0.01

    def test_memory_decay(self):
        """Test memory decay over time."""
        old_time = time.time() - 1000  # 1000 seconds ago
        entry = MemoryEntry(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content={},
            timestamp=old_time,
            importance=0.8,
            decay_rate=0.001,
        )

        strength = entry.get_strength()
        assert strength < 0.8  # Should have decayed

    def test_memory_accessible(self):
        """Test memory accessibility."""
        entry = MemoryEntry(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content={},
            timestamp=time.time(),
            importance=0.8,
        )

        assert entry.is_accessible(threshold=0.1)
        assert not entry.is_accessible(threshold=0.9)

    def test_memory_access_count(self):
        """Test memory access tracking."""
        entry = MemoryEntry(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content={},
            timestamp=time.time(),
        )

        assert entry.accessed_count == 0
        entry.access()
        assert entry.accessed_count == 1
        entry.access()
        assert entry.accessed_count == 2


class TestRelationship:
    """Test relationships."""

    def test_relationship_creation(self):
        """Test creating relationship."""
        rel = Relationship(
            entity_id="entity_1",
            relationship_type="friend",
            trust=0.8,
        )
        assert rel.entity_id == "entity_1"
        assert rel.relationship_type == "friend"

    def test_relationship_strength_friend(self):
        """Test relationship strength for friend."""
        rel = Relationship(
            entity_id="entity_1",
            relationship_type="friend",
            trust=0.8,
            familiarity=0.8,
        )

        strength = rel.get_relationship_strength()
        assert strength > 0.5

    def test_relationship_strength_enemy(self):
        """Test relationship strength for enemy."""
        rel = Relationship(
            entity_id="entity_1",
            relationship_type="enemy",
            trust=0.2,
            familiarity=0.8,
        )

        strength = rel.get_relationship_strength()
        assert strength < -0.5

    def test_relationship_neutral(self):
        """Test neutral relationship."""
        rel = Relationship(
            entity_id="entity_1",
            relationship_type="neutral",
            trust=0.5,
            familiarity=0.5,
        )

        strength = rel.get_relationship_strength()
        assert abs(strength) < 0.2


class TestAgentMemory:
    """Test agent memory system."""

    def test_memory_creation(self):
        """Test creating agent memory."""
        memory = AgentMemory("agent_1")
        assert memory.agent_id == "agent_1"
        assert memory.memory_capacity == 1000

    def test_add_episodic_memory(self):
        """Test adding episodic memory."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_episodic_memory(
            {"event": "collision", "damage": 10},
            importance=0.8,
        )

        assert mem_id in memory.episodic_memory
        assert memory.episodic_memory[mem_id].content["event"] == "collision"

    def test_add_semantic_memory(self):
        """Test adding semantic memory."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_semantic_memory(
            "The world is 1000x1000 meters",
            {"width": 1000, "height": 1000},
            importance=0.9,
        )

        assert mem_id in memory.semantic_memory
        assert memory.semantic_memory[mem_id].content["fact"] == "The world is 1000x1000 meters"

    def test_add_procedural_memory(self):
        """Test adding procedural memory."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_procedural_memory(
            "Navigate to goal",
            ["find_path", "follow_path", "reach_goal"],
            proficiency=0.7,
        )

        assert mem_id in memory.procedural_memory
        assert memory.procedural_memory[mem_id].content["skill"] == "Navigate to goal"

    def test_add_emotional_memory(self):
        """Test adding emotional memory."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_emotional_memory(
            "Successful mission",
            Emotion.HAPPY,
            intensity=0.8,
        )

        assert mem_id in memory.emotional_memory
        assert memory.emotional_memory[mem_id].emotional_valence > 0

    def test_recall_episodic(self):
        """Test recalling episodic memories."""
        memory = AgentMemory("agent_1")

        memory.add_episodic_memory({"event": "collision"}, importance=0.7)
        memory.add_episodic_memory({"event": "goal_reached"}, importance=0.9)

        recalled = memory.recall_memories(memory_type=MemoryType.EPISODIC)
        assert len(recalled) == 2

    def test_recall_by_tag(self):
        """Test recalling by tag."""
        memory = AgentMemory("agent_1")

        memory.add_episodic_memory(
            {"event": "collision"},
            tags={"danger", "physics"},
        )
        memory.add_episodic_memory(
            {"event": "goal_reached"},
            tags={"success"},
        )

        recalled = memory.recall_memories(tags={"danger"})
        assert len(recalled) == 1

    def test_recall_by_strength(self):
        """Test recalling by strength threshold."""
        memory = AgentMemory("agent_1")

        memory.add_episodic_memory(
            {"event": "event1"},
            importance=0.1,
        )
        memory.add_episodic_memory(
            {"event": "event2"},
            importance=0.9,
        )

        recalled = memory.recall_memories(
            memory_type=MemoryType.EPISODIC,
            min_strength=0.5,
        )
        assert len(recalled) == 1

    def test_recall_limit(self):
        """Test recalling with limit."""
        memory = AgentMemory("agent_1")

        for i in range(10):
            memory.add_episodic_memory({"event": f"event_{i}"})

        recalled = memory.recall_memories(limit=3)
        assert len(recalled) == 3

    def test_recall_increments_access_count(self):
        """Test that recall increments access count."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_episodic_memory({"event": "test"})
        assert memory.episodic_memory[mem_id].accessed_count == 0

        memory.recall_memories()
        assert memory.episodic_memory[mem_id].accessed_count == 1

    def test_relevant_memories(self):
        """Test getting relevant memories."""
        memory = AgentMemory("agent_1")

        memory.add_episodic_memory(
            {"description": "collision with wall"},
            tags={"collision", "wall"},
        )
        memory.add_semantic_memory(
            "Walls are obstacles",
            {"type": "obstacle"},
            tags={"wall"},
        )

        relevant = memory.get_relevant_memories("wall")
        assert len(relevant) == 2

    def test_add_relationship(self):
        """Test adding relationship."""
        memory = AgentMemory("agent_1")

        memory.add_relationship("agent_2", "friend", trust=0.8)

        rel = memory.get_relationship("agent_2")
        assert rel is not None
        assert rel.relationship_type == "friend"

    def test_update_relationship(self):
        """Test updating relationship."""
        memory = AgentMemory("agent_1")

        memory.add_relationship("agent_2", "neutral")
        memory.update_relationship("agent_2", trust_delta=0.2)

        rel = memory.get_relationship("agent_2")
        assert rel.trust == 0.7
        assert rel.interaction_count == 1

    def test_relationship_bounds(self):
        """Test relationship trust bounds."""
        memory = AgentMemory("agent_1")

        memory.add_relationship("agent_2", "neutral", trust=0.9)
        memory.update_relationship("agent_2", trust_delta=0.5)

        rel = memory.get_relationship("agent_2")
        assert rel.trust <= 1.0

    def test_get_overall_emotional_state(self):
        """Test getting emotional state."""
        memory = AgentMemory("agent_1")

        memory.add_emotional_memory("Success", Emotion.HAPPY, intensity=0.8)
        memory.add_emotional_memory("Failure", Emotion.SAD, intensity=0.4)

        state = memory.get_overall_emotional_state()
        assert isinstance(state, float)
        assert -1 <= state <= 1

    def test_memory_capacity(self):
        """Test memory capacity limit."""
        memory = AgentMemory("agent_1", memory_capacity=5)

        for i in range(10):
            memory.add_episodic_memory({"event": f"event_{i}"})

        total = len(memory.episodic_memory)
        assert total <= 5

    def test_forget_old_memories(self):
        """Test forgetting old memories."""
        memory = AgentMemory("agent_1")

        # Add old memory with high decay
        old_time = time.time() - 10000
        old_memory = MemoryEntry(
            id="old_mem",
            memory_type=MemoryType.EPISODIC,
            content={"event": "old"},
            timestamp=old_time,
            importance=0.5,
            decay_rate=0.01,  # High decay
        )
        memory.episodic_memory["old_mem"] = old_memory

        # Add recent memory
        memory.add_episodic_memory({"event": "new"})

        forgotten = memory.forget_old_memories(threshold=0.2)
        assert forgotten >= 1

    def test_memory_stats(self):
        """Test memory statistics."""
        memory = AgentMemory("agent_1")

        memory.add_episodic_memory({"event": "event1"})
        memory.add_semantic_memory("fact", {})
        memory.add_procedural_memory("skill", [])
        memory.add_emotional_memory("feeling", Emotion.HAPPY)
        memory.add_relationship("entity_1", "friend")

        stats = memory.get_memory_stats()
        assert stats["episodic_count"] == 1
        assert stats["semantic_count"] == 1
        assert stats["procedural_count"] == 1
        assert stats["emotional_count"] == 1
        assert stats["relationships_count"] == 1

    def test_memory_with_tags(self):
        """Test memory tagging."""
        memory = AgentMemory("agent_1")

        mem_id = memory.add_episodic_memory(
            {"event": "collision"},
            tags={"danger", "physics", "collision"},
        )

        recalled = memory.recall_memories(tags={"physics", "collision"})
        assert mem_id in [m.id for m in recalled]

    def test_multiple_memory_types(self):
        """Test combining multiple memory types."""
        memory = AgentMemory("agent_1")

        # Add different memory types for same event
        event_id = "collision_event"

        memory.add_episodic_memory(
            {"event": "collision", "id": event_id},
            tags={event_id},
        )
        memory.add_semantic_memory(
            "Collisions reduce health",
            {},
            tags={event_id},
        )
        memory.add_emotional_memory(
            f"Experienced {event_id}",
            Emotion.AFRAID,
            tags={event_id},
        )

        # Recall all memories about this event
        recalled = memory.recall_memories(tags={event_id})
        assert len(recalled) == 3

    def test_memory_decay_rates(self):
        """Test different decay rates."""
        now = time.time()

        # Episodic (fast decay)
        episodic = MemoryEntry(
            id="ep",
            memory_type=MemoryType.EPISODIC,
            content={},
            timestamp=now - 1000,
            importance=1.0,
            decay_rate=0.001,
        )

        # Semantic (slow decay)
        semantic = MemoryEntry(
            id="sem",
            memory_type=MemoryType.SEMANTIC,
            content={},
            timestamp=now - 1000,
            importance=1.0,
            decay_rate=0.0001,
        )

        episodic_strength = episodic.get_strength()
        semantic_strength = semantic.get_strength()

        # Semantic should be stronger than episodic
        assert semantic_strength > episodic_strength

    def test_relationship_familiarity(self):
        """Test relationship familiarity growth."""
        memory = AgentMemory("agent_1")
        memory.add_relationship("agent_2", "neutral")

        rel = memory.get_relationship("agent_2")
        assert rel.familiarity == 0.0

        for _ in range(5):
            memory.update_relationship("agent_2", trust_delta=0.1)

        rel = memory.get_relationship("agent_2")
        assert rel.familiarity == 0.5
        assert rel.interaction_count == 5
