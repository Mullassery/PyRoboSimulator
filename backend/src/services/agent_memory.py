"""Multi-layer agent memory system.

Implements episodic, semantic, procedural, and emotional memory with
decay, tagging, and relationship tracking.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory."""

    EPISODIC = "episodic"  # Events (what happened)
    SEMANTIC = "semantic"  # Facts (what is known)
    PROCEDURAL = "procedural"  # Skills (how to do)
    EMOTIONAL = "emotional"  # Feelings (how it felt)


class Emotion(Enum):
    """Agent emotions."""

    NEUTRAL = 0.0
    HAPPY = 1.0
    SAD = -1.0
    ANGRY = -0.8
    AFRAID = -0.6
    EXCITED = 0.8
    CONTENT = 0.5


@dataclass
class MemoryEntry:
    """Single memory entry."""

    id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    timestamp: float
    importance: float = 0.5  # 0-1 scale
    emotional_valence: float = 0.0  # -1 to +1 (negative to positive)
    tags: Set[str] = field(default_factory=set)
    related_entries: Set[str] = field(default_factory=set)
    decay_rate: float = 0.001  # Per second
    accessed_count: int = 0

    def get_strength(self) -> float:
        """Get current memory strength.

        Returns:
            Strength 0-1, accounting for decay
        """
        age = time.time() - self.timestamp
        decay = 1.0 - (self.decay_rate * age)
        return max(0.0, min(1.0, decay * self.importance))

    def is_accessible(self, threshold: float = 0.1) -> bool:
        """Check if memory is accessible.

        Args:
            threshold: Minimum strength to be accessible

        Returns:
            Whether memory is accessible
        """
        return self.get_strength() > threshold

    def access(self) -> None:
        """Mark memory as accessed."""
        self.accessed_count += 1


@dataclass
class Relationship:
    """Relationship between agent and entity."""

    entity_id: str
    relationship_type: str  # "friend", "enemy", "ally", "unknown"
    trust: float = 0.5  # 0-1 scale
    familiarity: float = 0.0  # 0-1, increases with interaction
    last_interaction: float = field(default_factory=time.time)
    interaction_count: int = 0

    def get_relationship_strength(self) -> float:
        """Get overall relationship strength.

        Returns:
            Strength -1 (enemy) to +1 (friend)
        """
        base = 0.0
        if self.relationship_type == "friend":
            base = 0.8
        elif self.relationship_type == "ally":
            base = 0.5
        elif self.relationship_type == "enemy":
            base = -0.8
        elif self.relationship_type == "neutral":
            base = 0.0

        return base * (0.5 + 0.5 * self.trust) * (0.5 + 0.5 * self.familiarity)


class AgentMemory:
    """Complete multi-layer memory system for an agent."""

    def __init__(self, agent_id: str, memory_capacity: int = 1000):
        """Initialize agent memory.

        Args:
            agent_id: Agent identifier
            memory_capacity: Maximum number of memory entries
        """
        self.agent_id = agent_id
        self.memory_capacity = memory_capacity

        # Memory stores
        self.episodic_memory: Dict[str, MemoryEntry] = {}  # Events
        self.semantic_memory: Dict[str, MemoryEntry] = {}  # Facts
        self.procedural_memory: Dict[str, MemoryEntry] = {}  # Skills
        self.emotional_memory: Dict[str, MemoryEntry] = {}  # Feelings

        # Relationships
        self.relationships: Dict[str, Relationship] = {}

        # Meta
        self.total_memories = 0
        self.memory_index = 0

    def add_episodic_memory(
        self,
        content: Dict[str, Any],
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """Add episodic memory (event).

        Args:
            content: Event content
            importance: Importance (0-1)
            emotional_valence: Emotional valence (-1 to +1)
            tags: Optional tags

        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id("episodic")

        entry = MemoryEntry(
            id=memory_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            timestamp=time.time(),
            importance=importance,
            emotional_valence=emotional_valence,
            tags=tags or set(),
            decay_rate=0.001,  # Episodic decays over time
        )

        self.episodic_memory[memory_id] = entry
        self._prune_memory(self.episodic_memory)

        return memory_id

    def add_semantic_memory(
        self,
        fact: str,
        details: Dict[str, Any],
        importance: float = 0.7,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """Add semantic memory (fact).

        Args:
            fact: Fact statement
            details: Fact details
            importance: Importance (0-1)
            tags: Optional tags

        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id("semantic")

        content = {"fact": fact, "details": details}
        entry = MemoryEntry(
            id=memory_id,
            memory_type=MemoryType.SEMANTIC,
            content=content,
            timestamp=time.time(),
            importance=importance,
            tags=tags or set(),
            decay_rate=0.0001,  # Semantic barely decays
        )

        self.semantic_memory[memory_id] = entry
        self._prune_memory(self.semantic_memory)

        return memory_id

    def add_procedural_memory(
        self,
        skill: str,
        procedure: List[str],
        proficiency: float = 0.5,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """Add procedural memory (skill).

        Args:
            skill: Skill name
            procedure: Steps to perform skill
            proficiency: Proficiency level (0-1)
            tags: Optional tags

        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id("procedural")

        content = {"skill": skill, "procedure": procedure, "proficiency": proficiency}
        entry = MemoryEntry(
            id=memory_id,
            memory_type=MemoryType.PROCEDURAL,
            content=content,
            timestamp=time.time(),
            importance=proficiency,
            tags=tags or set(),
            decay_rate=0.00001,  # Procedural barely decays
        )

        self.procedural_memory[memory_id] = entry
        self._prune_memory(self.procedural_memory)

        return memory_id

    def add_emotional_memory(
        self,
        event_description: str,
        emotion: Emotion,
        intensity: float = 0.5,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """Add emotional memory (feeling).

        Args:
            event_description: What triggered emotion
            emotion: Emotion type
            intensity: Intensity (0-1)
            tags: Optional tags

        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id("emotional")

        content = {
            "event": event_description,
            "emotion": emotion.name,
            "intensity": intensity,
        }
        entry = MemoryEntry(
            id=memory_id,
            memory_type=MemoryType.EMOTIONAL,
            content=content,
            timestamp=time.time(),
            importance=intensity,
            emotional_valence=emotion.value * intensity,
            tags=tags or set(),
            decay_rate=0.002,  # Emotional decays moderate
        )

        self.emotional_memory[memory_id] = entry
        self._prune_memory(self.emotional_memory)

        return memory_id

    def recall_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[Set[str]] = None,
        min_strength: float = 0.0,
        limit: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """Recall memories matching criteria.

        Args:
            memory_type: Filter by type
            tags: Filter by tags (any match)
            min_strength: Minimum strength threshold
            limit: Maximum results

        Returns:
            List of memories
        """
        results = []

        # Select memory store(s)
        stores = []
        if memory_type == MemoryType.EPISODIC or memory_type is None:
            stores.append(self.episodic_memory)
        if memory_type == MemoryType.SEMANTIC or memory_type is None:
            stores.append(self.semantic_memory)
        if memory_type == MemoryType.PROCEDURAL or memory_type is None:
            stores.append(self.procedural_memory)
        if memory_type == MemoryType.EMOTIONAL or memory_type is None:
            stores.append(self.emotional_memory)

        # Collect and filter
        for store in stores:
            for memory in store.values():
                if not memory.is_accessible():
                    continue

                strength = memory.get_strength()
                if strength < min_strength:
                    continue

                if tags:
                    if not memory.tags.intersection(tags):
                        continue

                results.append(memory)
                memory.access()

        # Sort by strength descending
        results.sort(key=lambda m: m.get_strength(), reverse=True)

        if limit:
            results = results[:limit]

        return results

    def get_relevant_memories(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Get memories relevant to query.

        Args:
            query: Query string
            limit: Maximum results

        Returns:
            List of relevant memories
        """
        query_lower = query.lower()
        results = []

        # Search all memory stores
        for store in [
            self.episodic_memory,
            self.semantic_memory,
            self.procedural_memory,
            self.emotional_memory,
        ]:
            for memory in store.values():
                if not memory.is_accessible():
                    continue

                # Simple text matching on tags
                if any(query_lower in tag.lower() for tag in memory.tags):
                    results.append(memory)

                # Match in content keys
                for key, val in memory.content.items():
                    if isinstance(val, str) and query_lower in val.lower():
                        results.append(memory)
                        break

        # Sort by strength
        results.sort(key=lambda m: m.get_strength(), reverse=True)
        return results[:limit]

    def add_relationship(
        self,
        entity_id: str,
        relationship_type: str,
        trust: float = 0.5,
    ) -> None:
        """Add or update relationship.

        Args:
            entity_id: Entity ID
            relationship_type: Type of relationship
            trust: Initial trust level
        """
        if entity_id not in self.relationships:
            self.relationships[entity_id] = Relationship(
                entity_id=entity_id,
                relationship_type=relationship_type,
                trust=trust,
            )
        else:
            self.relationships[entity_id].relationship_type = relationship_type
            self.relationships[entity_id].trust = trust

    def update_relationship(self, entity_id: str, trust_delta: float = 0.0) -> None:
        """Update relationship based on interaction.

        Args:
            entity_id: Entity ID
            trust_delta: Change in trust
        """
        if entity_id not in self.relationships:
            self.relationships[entity_id] = Relationship(entity_id=entity_id)

        rel = self.relationships[entity_id]
        rel.trust = max(0.0, min(1.0, rel.trust + trust_delta))
        rel.familiarity = min(1.0, rel.familiarity + 0.1)
        rel.interaction_count += 1
        rel.last_interaction = time.time()

    def get_relationship(self, entity_id: str) -> Optional[Relationship]:
        """Get relationship info.

        Args:
            entity_id: Entity ID

        Returns:
            Relationship or None
        """
        return self.relationships.get(entity_id)

    def get_overall_emotional_state(self) -> float:
        """Get overall emotional state.

        Returns:
            Valence -1 (sad) to +1 (happy)
        """
        if not self.emotional_memory:
            return 0.0

        total_valence = 0.0
        total_weight = 0.0

        for memory in self.emotional_memory.values():
            if memory.is_accessible():
                weight = memory.get_strength()
                total_valence += memory.emotional_valence * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_valence / total_weight

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "episodic_count": len(self.episodic_memory),
            "semantic_count": len(self.semantic_memory),
            "procedural_count": len(self.procedural_memory),
            "emotional_count": len(self.emotional_memory),
            "relationships_count": len(self.relationships),
            "total_memories": self.total_memories,
            "emotional_state": self.get_overall_emotional_state(),
        }

    def forget_old_memories(self, threshold: float = 0.05) -> int:
        """Remove memories below strength threshold.

        Args:
            threshold: Strength threshold for removal

        Returns:
            Number of memories forgotten
        """
        forgotten = 0

        for store in [
            self.episodic_memory,
            self.semantic_memory,
            self.procedural_memory,
            self.emotional_memory,
        ]:
            to_remove = []
            for mem_id, memory in store.items():
                if memory.get_strength() < threshold:
                    to_remove.append(mem_id)

            for mem_id in to_remove:
                del store[mem_id]
                forgotten += 1

        return forgotten

    def _generate_memory_id(self, prefix: str) -> str:
        """Generate unique memory ID.

        Args:
            prefix: ID prefix

        Returns:
            Unique memory ID
        """
        self.memory_index += 1
        return f"{self.agent_id}_{prefix}_{self.memory_index}"

    def _prune_memory(self, store: Dict[str, MemoryEntry]) -> None:
        """Prune oldest memories if store exceeds capacity.

        Args:
            store: Memory store to prune
        """
        if len(store) > self.memory_capacity:
            # Remove least important accessible memories
            removable = [
                (mem_id, mem) for mem_id, mem in store.items() if mem.is_accessible()
            ]
            removable.sort(key=lambda x: x[1].get_strength())

            for mem_id, _ in removable[: len(store) - self.memory_capacity]:
                del store[mem_id]
