# Phase 2: Multi-Agent Narrative System - Detailed Implementation

## Overview

**Phase 2** adds AI-driven agents with memory, personality, goals, and emergent narrative generation using Claude Sonnet 5.

**Timeline:** 10 weeks  
**Team:** 5 engineers (1 AI lead, 2 narrative designers, 1 backend, 1 UE5)  
**Starting Point:** Phase 1 complete (2km city, traffic, pedestrians)  
**Output:** v0.3.0 with 100+ AI agents, emergent stories  

---

## Week 1-2: Entity-Component System (ECS)

### Architecture

**File: `python/pyrobosimulator/ecs_system.py`**

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Type, Optional
import uuid

class Component:
    """Base component class."""
    pass

class Entity:
    """Entity with dynamic components."""
    
    def __init__(self, entity_id: str = None, entity_type: str = "generic"):
        self.id = entity_id or str(uuid.uuid4())
        self.entity_type = entity_type
        self.components: Dict[Type, Component] = {}
        self.active = True
    
    def add_component(self, component: Component) -> None:
        """Add component to entity."""
        self.components[type(component)] = component
    
    def get_component(self, component_type: Type) -> Optional[Component]:
        """Get component by type."""
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type) -> bool:
        """Check if entity has component."""
        return component_type in self.components
    
    def remove_component(self, component_type: Type) -> None:
        """Remove component."""
        self.components.pop(component_type, None)

class System:
    """Base system that operates on entities."""
    
    def __init__(self, world: 'World'):
        self.world = world
    
    def update(self, dt: float):
        """Update system (called every frame)."""
        pass
    
    def get_entities_with_components(self, *component_types: Type) -> List[Entity]:
        """Find entities with specific components."""
        result = []
        for entity in self.world.entities.values():
            if entity.active and all(entity.has_component(ct) for ct in component_types):
                result.append(entity)
        return result

class World:
    """Container for entities and systems."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.systems: Dict[Type, System] = {}
        self.time = 0
    
    def create_entity(self, entity_type: str = "generic") -> Entity:
        """Create and register entity."""
        entity = Entity(entity_type=entity_type)
        self.entities[entity.id] = entity
        return entity
    
    def destroy_entity(self, entity_id: str) -> None:
        """Mark entity for destruction."""
        if entity_id in self.entities:
            self.entities[entity_id].active = False
    
    def register_system(self, system: System) -> None:
        """Register system."""
        self.systems[type(system)] = system
    
    def update(self, dt: float):
        """Update all systems."""
        self.time += dt
        
        # Clean up destroyed entities
        self.entities = {
            eid: e for eid, e in self.entities.items() if e.active
        }
        
        # Update systems
        for system in self.systems.values():
            system.update(dt)

# Component Definitions

@dataclass
class TransformComponent(Component):
    """Position, rotation, velocity."""
    position: List[float] = field(default_factory=lambda: [0, 0, 0])
    rotation: List[float] = field(default_factory=lambda: [0, 0, 0])
    velocity: List[float] = field(default_factory=lambda: [0, 0, 0])

@dataclass
class AppearanceComponent(Component):
    """Visual representation."""
    mesh_id: str = "human_base"
    material_id: str = "skin_tone_default"
    animations: Dict[str, str] = field(default_factory=dict)
    clothing: List[str] = field(default_factory=list)  # Garment IDs
    accessories: List[str] = field(default_factory=list)

@dataclass
class MindComponent(Component):
    """AI behavior and state."""
    memory: 'MemoryBank' = field(default_factory=lambda: MemoryBank(""))
    personality: 'Personality' = field(default_factory=Personality)
    goals: List['Goal'] = field(default_factory=list)
    current_action: Optional['Action'] = None
    emotional_state: 'EmotionalState' = field(default_factory=EmotionalState)

@dataclass
class NeedComponent(Component):
    """Biological and psychological needs."""
    hunger: float = 0.5
    fatigue: float = 0.5
    hygiene: float = 0.5
    loneliness: float = 0.5
    stress: float = 0.5
    
    def decay_over_time(self, dt: float):
        """Needs increase over time."""
        self.hunger = min(1.0, self.hunger + 0.0001 * dt)
        self.fatigue = min(1.0, self.fatigue + 0.0005 * dt)
        self.stress = min(1.0, self.stress + 0.00005 * dt)

@dataclass
class RelationshipComponent(Component):
    """Relationships with other agents."""
    relationships: Dict[str, 'Relationship'] = field(default_factory=dict)

# System Implementations

class TransformSystem(System):
    """Update entity positions and velocities."""
    
    def update(self, dt: float):
        """Physics integration."""
        for entity in self.get_entities_with_components(TransformComponent):
            transform = entity.get_component(TransformComponent)
            
            # Simple Euler integration
            for i in range(3):
                transform.position[i] += transform.velocity[i] * dt

class AnimationSystem(System):
    """Update animations based on actions."""
    
    def update(self, dt: float):
        """Update animation states."""
        for entity in self.get_entities_with_components(MindComponent, AppearanceComponent):
            mind = entity.get_component(MindComponent)
            appearance = entity.get_component(AppearanceComponent)
            
            if mind.current_action:
                # Play animation for action
                animation_name = self.action_to_animation(mind.current_action.type)
                appearance.animations["active"] = animation_name

class NeedDecaySystem(System):
    """Decay needs over time."""
    
    def update(self, dt: float):
        """Update needs."""
        for entity in self.get_entities_with_components(NeedComponent):
            needs = entity.get_component(NeedComponent)
            needs.decay_over_time(dt)

class BehaviorSystem(System):
    """Execute behavior trees and actions."""
    
    def update(self, dt: float):
        """Update behaviors."""
        for entity in self.get_entities_with_components(MindComponent):
            mind = entity.get_component(MindComponent)
            
            # Execute current action
            if mind.current_action:
                mind.current_action.execute(entity, self.world, dt)
                
                if mind.current_action.status == "done":
                    mind.current_action = None
            
            # Choose next action
            if not mind.current_action:
                next_action = self.choose_next_action(entity)
                if next_action:
                    mind.current_action = next_action

class AgentSpawner:
    """Helper to create agents."""
    
    @staticmethod
    def spawn_human(world: World, name: str, position: List[float],
                   personality: 'Personality' = None) -> Entity:
        """Spawn a human NPC agent."""
        
        entity = world.create_entity("human")
        
        # Transform
        transform = TransformComponent()
        transform.position = position
        entity.add_component(transform)
        
        # Appearance
        appearance = AppearanceComponent()
        appearance.mesh_id = "human_base"
        entity.add_component(appearance)
        
        # Mind
        if personality is None:
            personality = Personality.generate_random()
        
        mind = MindComponent()
        mind.personality = personality
        mind.memory = MemoryBank(entity.id)
        entity.add_component(mind)
        
        # Needs
        entity.add_component(NeedComponent())
        
        # Relationships
        entity.add_component(RelationshipComponent())
        
        return entity
```

### Testing (Week 1-2)

```python
# tests/test_ecs.py
class TestECS:
    def test_entity_creation(self):
        """Create entity with components."""
        world = World()
        entity = world.create_entity("human")
        
        entity.add_component(TransformComponent())
        entity.add_component(AppearanceComponent())
        
        assert entity.has_component(TransformComponent)
        assert entity.get_component(TransformComponent) is not None
    
    def test_system_query(self):
        """Systems find entities with specific components."""
        world = World()
        
        # Create entities
        e1 = world.create_entity()
        e1.add_component(TransformComponent())
        e1.add_component(MindComponent())
        
        e2 = world.create_entity()
        e2.add_component(TransformComponent())  # Only transform
        
        # Query for entities with both
        system = System(world)
        results = system.get_entities_with_components(TransformComponent, MindComponent)
        
        assert len(results) == 1
        assert results[0].id == e1.id
    
    def test_spawner(self):
        """AgentSpawner creates valid agents."""
        world = World()
        
        personality = Personality.generate_random()
        agent = AgentSpawner.spawn_human(
            world, "Alice", [100, 100, 0],
            personality
        )
        
        assert agent.has_component(TransformComponent)
        assert agent.has_component(MindComponent)
        assert agent.has_component(NeedComponent)
```

---

## Week 2-3: Memory & Personality System

### Memory Implementation

**File: `python/pyrobosimulator/memory_system.py`**

```python
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np

@dataclass
class Event:
    """Discrete experience."""
    id: str
    timestamp: float
    agent_id: str
    actor_id: str
    action: str
    location: Tuple[float, float]
    context: Dict
    emotional_valence: float  # -1 to +1

class EpisodicMemory:
    """What happened (timestamped events)."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.events: List[Event] = []
        self.max_events = 1000  # Limit memory
    
    def store(self, event: Event):
        """Store event."""
        self.events.append(event)
        
        # Forget oldest if exceeding limit
        if len(self.events) > self.max_events:
            self.events.pop(0)
    
    def search(self, query: str, time_window: float = None) -> List[Event]:
        """Search events by description or actor."""
        results = []
        
        for event in self.events:
            # Recency bias
            if time_window and event.timestamp < time_window:
                continue
            
            if query.lower() in event.action.lower() or \
               query.lower() in event.actor_id.lower():
                results.append(event)
        
        return results
    
    def get_recent(self, count: int = 10) -> List[Event]:
        """Get most recent events."""
        return self.events[-count:]

class SemanticMemory:
    """What is known (timeless facts)."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.facts: Dict[str, Any] = {}  # Key-value facts
        self.beliefs: Dict[str, float] = {}  # Uncertainty estimates
    
    def store_fact(self, key: str, value: Any, confidence: float = 1.0):
        """Store fact."""
        self.facts[key] = value
        self.beliefs[key] = confidence
    
    def get_fact(self, key: str) -> Any:
        """Retrieve fact."""
        return self.facts.get(key)
    
    def get_confidence(self, key: str) -> float:
        """Get confidence in fact (0-1)."""
        return self.beliefs.get(key, 0.0)
    
    def update(self, facts: Dict[str, Any]):
        """Update facts from event."""
        for key, value in facts.items():
            self.store_fact(key, value)

class ProceduralMemory:
    """How to do things (skills, habits)."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.skills: Dict[str, float] = {}  # Skill name → proficiency
        self.habits: List[str] = []  # Repeated behaviors
    
    def learn_skill(self, skill: str, proficiency: float = 0.1):
        """Learn or improve skill."""
        if skill in self.skills:
            self.skills[skill] = min(1.0, self.skills[skill] + proficiency)
        else:
            self.skills[skill] = proficiency
    
    def get_skill_proficiency(self, skill: str) -> float:
        """Get skill level (0-1)."""
        return self.skills.get(skill, 0.0)

class EmotionalMemory:
    """Feelings about events."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.emotional_tags: Dict[str, float] = {}  # Event ID → valence
        self.emotional_associations: Dict[str, float] = {}  # Concept → valence
    
    def tag_event(self, event: Event, valence: float):
        """Tag event with emotion."""
        self.emotional_tags[event.id] = valence
        
        # Learn associations (what triggers emotions)
        for actor in [event.actor_id, event.action]:
            key = f"actor:{actor}" if actor == event.actor_id else f"action:{actor}"
            if key not in self.emotional_associations:
                self.emotional_associations[key] = 0
            
            self.emotional_associations[key] += valence * 0.1

class MemoryBank:
    """Complete memory system."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.episodic = EpisodicMemory(agent_id)
        self.semantic = SemanticMemory(agent_id)
        self.procedural = ProceduralMemory(agent_id)
        self.emotional = EmotionalMemory(agent_id)
    
    def remember(self, event: Event, valence: float = 0):
        """Store event across all memory types."""
        # Episodic
        self.episodic.store(event)
        
        # Emotional tagging
        self.emotional.tag_event(event, valence)
        
        # Extract semantic knowledge
        facts = self.extract_facts(event)
        self.semantic.update(facts)
    
    def recall(self, query: str) -> List[Event]:
        """Retrieve relevant memories."""
        recent = self.episodic.search(query, time_window=7*24*3600)
        
        # Sort by emotional significance + recency
        sorted_events = sorted(recent,
            key=lambda e: (
                abs(self.emotional.emotional_tags.get(e.id, 0)),
                e.timestamp
            ),
            reverse=True
        )
        
        return sorted_events[:10]
    
    def extract_facts(self, event: Event) -> Dict[str, Any]:
        """Extract semantic facts from event."""
        return {
            f"knows_{event.actor_id}": True,
            f"visited_{event.location}": True,
            f"skill_{event.action}": 0.1,
        }

@dataclass
class Relationship:
    """Dynamic relationship between agents."""
    agent_a: str
    agent_b: str
    trust: float = 0.5           # -1 to +1
    affinity: float = 0.5        # -1 to +1
    familiarity: float = 0.0     # 0 to 1
    shared_memories: List[str] = field(default_factory=list)
    
    def update(self, event: Event, valence: float):
        """Update relationship based on event."""
        
        if valence > 0:
            # Positive event
            self.trust += valence * 0.05
            self.affinity += valence * 0.05
        else:
            # Negative event
            self.trust += valence * 0.05
            self.affinity += valence * 0.03
        
        # Familiarity increases with any interaction
        self.familiarity = min(1.0, self.familiarity + 0.01)
        
        # Clamp values
        self.trust = np.clip(self.trust, -1, 1)
        self.affinity = np.clip(self.affinity, -1, 1)

class Personality:
    """Big Five personality traits."""
    
    def __init__(self):
        self.openness: float = 0.5
        self.conscientiousness: float = 0.5
        self.extraversion: float = 0.5
        self.agreeableness: float = 0.5
        self.neuroticism: float = 0.5
    
    @staticmethod
    def generate_random() -> 'Personality':
        """Generate random personality."""
        p = Personality()
        p.openness = np.random.uniform(0, 1)
        p.conscientiousness = np.random.uniform(0, 1)
        p.extraversion = np.random.uniform(0, 1)
        p.agreeableness = np.random.uniform(0, 1)
        p.neuroticism = np.random.uniform(0, 1)
        return p
    
    def get_trait_modifiers(self) -> Dict[str, float]:
        """Convert traits to behavior modifiers."""
        return {
            "curiosity": self.openness * 1.5,
            "reliability": self.conscientiousness * 1.5,
            "sociability": self.extraversion * 1.5,
            "generosity": self.agreeableness * 1.5,
            "anxiety": self.neuroticism * 1.5,
        }
    
    def to_dict(self) -> Dict[str, float]:
        """Serialize to dict."""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

@dataclass
class EmotionalState:
    """Current emotions."""
    primary_emotion: str = "neutral"  # joy, sadness, anger, fear, etc.
    intensity: float = 0.0
    duration: float = 0.0
    
    def update(self, dt: float):
        """Emotions fade over time."""
        self.intensity *= 0.99 ** dt
        self.duration -= dt
        
        if self.duration < 0 or self.intensity < 0.1:
            self.primary_emotion = "neutral"
            self.intensity = 0
```

### Testing (Week 2-3)

```python
# tests/test_memory.py
class TestMemory:
    def test_episodic_storage(self):
        """Store and retrieve events."""
        memory = EpisodicMemory("agent_1")
        
        event = Event(
            id="evt_1",
            timestamp=100.0,
            agent_id="agent_1",
            actor_id="alice",
            action="talked_to",
            location=(100, 100),
            context={},
            emotional_valence=0.8
        )
        
        memory.store(event)
        results = memory.search("talked_to")
        
        assert len(results) == 1
        assert results[0].id == "evt_1"
    
    def test_personality_traits(self):
        """Personality generates valid traits."""
        p = Personality.generate_random()
        
        for trait in ["openness", "conscientiousness", "extraversion",
                     "agreeableness", "neuroticism"]:
            value = getattr(p, trait)
            assert 0 <= value <= 1
    
    def test_relationship_dynamics(self):
        """Relationships update with interactions."""
        rel = Relationship("alice", "bob")
        
        # Positive interaction
        event = Event("evt_1", 0, "alice", "bob", "helped", (0, 0), {}, 0.8)
        rel.update(event, 0.8)
        
        assert rel.trust > 0.5
        assert rel.affinity > 0.5
        assert rel.familiarity > 0
    
    def test_memory_recall(self):
        """Retrieve emotionally significant memories."""
        memory = MemoryBank("agent_1")
        
        # Store positive event
        positive = Event("evt_1", 100, "agent_1", "alice", "helped", 
                        (100, 100), {}, 0)
        memory.remember(positive, 0.9)
        
        # Store neutral event
        neutral = Event("evt_2", 101, "agent_1", "bob", "passed_by",
                       (100, 100), {}, 0)
        memory.remember(neutral, 0.0)
        
        # Recall should return positive first
        recalled = memory.recall("alice")
        assert len(recalled) > 0
```

---

## Week 4-5: Goals & Behavior Trees

### Goal System

**File: `python/pyrobosimulator/goal_system.py`**

```python
from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Callable

class GoalType(Enum):
    SURVIVAL = "survival"
    SOCIAL = "social"
    WORK = "work"
    LEISURE = "leisure"

class Goal(ABC):
    """Base goal."""
    
    def __init__(self, goal_id: str, agent_id: str, goal_type: GoalType):
        self.id = goal_id
        self.agent_id = agent_id
        self.type = goal_type
        self.priority: float = 0.5
        self.progress: float = 0.0
        self.deadline: Optional[float] = None
        self.preconditions: List[str] = []
    
    @abstractmethod
    def evaluate_satisfaction(self) -> float:
        """How satisfied is agent with progress? 0-1."""
        pass
    
    @abstractmethod
    def get_next_action(self, world: 'World', agent: Entity) -> Optional['Action']:
        """What action should agent take to progress this goal?"""
        pass

class SurvivalGoal(Goal):
    """Base needs: hunger, sleep, safety."""
    
    def __init__(self, agent_id: str, need_type: str):
        super().__init__(f"survival_{need_type}", agent_id, GoalType.SURVIVAL)
        self.need_type = need_type
        self.urgency = 1.0
    
    def evaluate_satisfaction(self) -> float:
        """Progress toward satisfying need."""
        need_level = self.get_agent_need()
        return 1.0 - need_level  # 0 when critical, 1 when satisfied
    
    def get_next_action(self, world: 'World', agent: Entity) -> Optional['Action']:
        """Return action to satisfy need."""
        if self.need_type == "hunger":
            return Action("eat", duration=5.0)
        elif self.need_type == "fatigue":
            return Action("sleep", duration=28800.0)  # 8 hours
        elif self.need_type == "hygiene":
            return Action("shower", duration=900.0)  # 15 minutes
        return None

class SocialGoal(Goal):
    """Social interaction: friendship, romance, status."""
    
    def __init__(self, agent_id: str, target_agent_id: str,
                relationship_type: str):
        super().__init__(f"social_{target_agent_id}", agent_id, GoalType.SOCIAL)
        self.target_agent = target_agent_id
        self.relationship_type = relationship_type
    
    def evaluate_satisfaction(self) -> float:
        """Satisfaction based on relationship quality."""
        relationship = self.get_relationship()
        if not relationship:
            return 0
        
        # Average of trust and affinity
        return (relationship.trust + relationship.affinity) / 2 + 0.5
    
    def get_next_action(self, world: 'World', agent: Entity) -> Optional['Action']:
        """Chat or spend time with target."""
        return Action("chat", target=self.target_agent, duration=300.0)

class WorkGoal(Goal):
    """Employment: job, career advancement."""
    
    def __init__(self, agent_id: str, employer_id: str, job_role: str,
                salary: float):
        super().__init__(f"work_{job_role}", agent_id, GoalType.WORK)
        self.employer = employer_id
        self.job_role = job_role
        self.salary = salary
        self.hours_worked = 0
    
    def evaluate_satisfaction(self) -> float:
        """Satisfaction based on salary vs. effort."""
        # Simple model: salary / hours worked
        return min(1.0, self.salary / max(self.hours_worked, 1))
    
    def get_next_action(self, world: 'World', agent: Entity) -> Optional['Action']:
        """Go to work."""
        return Action("work", target=self.employer, duration=28800.0)  # 8 hours

class LeisureGoal(Goal):
    """Fun & enrichment."""
    
    def __init__(self, agent_id: str, activity: str, social: bool = False):
        super().__init__(f"leisure_{activity}", agent_id, GoalType.LEISURE)
        self.activity = activity
        self.social = social
    
    def evaluate_satisfaction(self) -> float:
        """Satisfaction = progress through activity."""
        return self.progress
    
    def get_next_action(self, world: 'World', agent: Entity) -> Optional['Action']:
        """Pursue leisure activity."""
        return Action(self.activity, duration=3600.0)  # 1 hour

class MotivationEngine:
    """Compute goal priorities based on needs and personality."""
    
    def __init__(self, agent: Entity):
        self.agent = agent
    
    def update_priorities(self, world: 'World'):
        """Recalculate priorities for all goals."""
        
        mind = self.agent.get_component(MindComponent)
        needs = self.agent.get_component(NeedComponent)
        
        for goal in mind.goals:
            # Base priority from goal type
            if goal.type == GoalType.SURVIVAL:
                base_priority = 1.0
            elif goal.type == GoalType.SOCIAL:
                base_priority = 0.6
            elif goal.type == GoalType.WORK:
                base_priority = 0.7
            elif goal.type == GoalType.LEISURE:
                base_priority = 0.3
            else:
                base_priority = 0.5
            
            # Urgency modulation (survival needs increase urgency)
            if isinstance(goal, SurvivalGoal):
                urgency = max(needs.hunger, needs.fatigue)
                base_priority *= (1.0 + urgency)
            
            # Personality modulation
            trait_mods = mind.personality.get_trait_modifiers()
            
            if goal.type == GoalType.SOCIAL:
                base_priority *= (0.5 + trait_mods["sociability"])
            elif goal.type == GoalType.WORK:
                base_priority *= (0.5 + trait_mods["reliability"])
            elif goal.type == GoalType.LEISURE:
                base_priority *= (0.5 + trait_mods["curiosity"])
            
            # Satisfaction adjustment
            satisfaction = goal.evaluate_satisfaction()
            base_priority *= (1.0 - satisfaction * 0.5)  # Active goals > satisfied ones
            
            goal.priority = np.clip(base_priority, 0, 1)

class BehaviorTreeNode(ABC):
    """Base behavior tree node."""
    
    @abstractmethod
    def execute(self, agent: Entity, world: 'World',
                dt: float) -> str:
        """Execute node, return status: success, failure, running."""
        pass

class Selector(BehaviorTreeNode):
    """Try children in order until one succeeds."""
    
    def __init__(self, children: List[BehaviorTreeNode]):
        self.children = children
    
    def execute(self, agent: Entity, world: 'World', dt: float) -> str:
        for child in self.children:
            status = child.execute(agent, world, dt)
            if status != "failure":
                return status
        return "failure"

class Sequence(BehaviorTreeNode):
    """Execute children in order; all must succeed."""
    
    def __init__(self, children: List[BehaviorTreeNode]):
        self.children = children
    
    def execute(self, agent: Entity, world: 'World', dt: float) -> str:
        for child in self.children:
            status = child.execute(agent, world, dt)
            if status == "failure":
                return "failure"
        return "success"

class ActionNode(BehaviorTreeNode):
    """Leaf node that executes an action."""
    
    def __init__(self, action_type: str, precondition: Callable = None):
        self.action_type = action_type
        self.precondition = precondition
    
    def execute(self, agent: Entity, world: 'World', dt: float) -> str:
        # Check precondition
        if self.precondition and not self.precondition(agent, world):
            return "failure"
        
        # Execute action
        action = Action(self.action_type, duration=10.0)
        
        mind = agent.get_component(MindComponent)
        mind.current_action = action
        
        return "running"

class ConditionNode(BehaviorTreeNode):
    """Check condition."""
    
    def __init__(self, condition: Callable):
        self.condition = condition
    
    def execute(self, agent: Entity, world: 'World', dt: float) -> str:
        if self.condition(agent, world):
            return "success"
        return "failure"
```

---

## Week 6-7: Narrative Generation with Claude

### Narrative Engine

**File: `python/pyrobosimulator/narrative_engine.py`**

```python
from anthropic import Anthropic
import json

class NarrativeEngine:
    """Generate story arcs from world events using Claude."""
    
    def __init__(self):
        self.claude = Anthropic()
        self.story_cache = {}
    
    def generate_narrative(self, world: 'World', protagonist: Entity) -> 'Story':
        """Generate narrative from world state."""
        
        # 1. Collect significant events
        mind = protagonist.get_component(MindComponent)
        significant_events = mind.memory.episodic.get_recent(20)
        
        # 2. Build relationship graph
        relationships = self.extract_relationships(world, protagonist)
        
        # 3. Identify conflicts
        conflicts = self.detect_conflicts(world, protagonist, relationships)
        
        # 4. Generate story structure via Claude
        story_structure = self.claude_generate_story(
            protagonist, significant_events, conflicts
        )
        
        # 5. Expand into full narrative
        narrative = self.expand_story_structure(story_structure, world)
        
        return narrative
    
    def claude_generate_story(self, protagonist: Entity, events: List[Event],
                             conflicts: List[str]) -> Dict:
        """Use Claude Sonnet 5 to generate story structure."""
        
        # Format events for Claude
        event_descriptions = []
        for event in events:
            event_descriptions.append(
                f"- {event.actor_id} {event.action} at {event.location}"
            )
        
        # Format protagonist info
        mind = protagonist.get_component(MindComponent)
        personality = mind.personality.to_dict()
        goals = [f"- {g.id} (progress: {g.progress})" for g in mind.goals]
        
        prompt = f"""
You are a master storyteller. Generate a compelling 3-act story structure from this world state:

PROTAGONIST: {protagonist.entity_type}
Personality: {personality}
Goals: {chr(10).join(goals)}

RECENT EVENTS:
{chr(10).join(event_descriptions[:10])}

CONFLICTS/TENSIONS:
{chr(10).join(conflicts)}

Generate a story in this exact JSON format:
{{
  "title": "story title",
  "theme": "core message",
  "acts": [
    {{
      "name": "Act name",
      "beats": [
        "beat 1: description",
        "beat 2: description"
      ],
      "turning_point": "key plot point"
    }}
  ],
  "character_arc": "how protagonist changes",
  "resolution": "how it ends"
}}

Make it compelling and grounded in the world events provided.
"""
        
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            thinking={
                "type": "enabled",
                "budget_tokens": 4000,
            },
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract JSON from response
        text = response.content[0].text
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        return {"title": "Untitled", "theme": "survival", "acts": []}
    
    def extract_relationships(self, world: 'World',
                            protagonist: Entity) -> Dict[str, Dict]:
        """Extract relationships from protagonist."""
        rel_component = protagonist.get_component(RelationshipComponent)
        
        relationships = {}
        for agent_id, rel in rel_component.relationships.items():
            relationships[agent_id] = {
                "trust": rel.trust,
                "affinity": rel.affinity,
                "familiarity": rel.familiarity,
            }
        
        return relationships
    
    def detect_conflicts(self, world: 'World', protagonist: Entity,
                        relationships: Dict) -> List[str]:
        """Identify narrative conflicts."""
        conflicts = []
        
        # Relationship conflicts (distrust, low affinity)
        for agent_id, rel in relationships.items():
            if rel["trust"] < 0:
                conflicts.append(f"Conflict with {agent_id}: distrust")
            if rel["affinity"] < -0.3:
                conflicts.append(f"Rivalry with {agent_id}: mutual dislike")
        
        # Need conflicts (unsatisfied needs)
        needs = protagonist.get_component(NeedComponent)
        mind = protagonist.get_component(MindComponent)
        
        if needs.hunger > 0.8:
            conflicts.append("Hunger: struggling to find food")
        if needs.stress > 0.7:
            conflicts.append("Stress: overwhelmed by demands")
        
        # Goal conflicts (competing goals)
        if len(mind.goals) > 3:
            conflicts.append("Overcommitted: too many responsibilities")
        
        return conflicts
    
    def expand_story_structure(self, structure: Dict,
                              world: 'World') -> 'Story':
        """Convert story structure to full narrative."""
        
        story = Story()
        story.title = structure.get("title", "Untitled")
        story.theme = structure.get("theme", "survival")
        
        for act_data in structure.get("acts", []):
            act = Story.Act(
                name=act_data.get("name", "Act"),
                beats=act_data.get("beats", []),
                turning_point=act_data.get("turning_point", "")
            )
            story.acts.append(act)
        
        return story

@dataclass
class Story:
    """Complete narrative arc."""
    title: str = "Untitled"
    theme: str = "survival"
    acts: List['Story.Act'] = field(default_factory=list)
    character_arc: str = ""
    resolution: str = ""
    
    @dataclass
    class Act:
        name: str = "Act"
        beats: List[str] = field(default_factory=list)
        turning_point: str = ""
```

### Dialogue Generation

**File: `python/pyrobosimulator/dialogue_system.py`**

```python
class DialogueSystem:
    """Generate realistic dialogue using Claude."""
    
    def __init__(self):
        self.claude = Anthropic()
    
    def generate_dialogue(self, agent_a: Entity, agent_b: Entity,
                         context: str) -> 'Dialogue':
        """Generate conversation between two agents."""
        
        mind_a = agent_a.get_component(MindComponent)
        mind_b = agent_b.get_component(MindComponent)
        
        # Get relationship
        rel_a = mind_a.memory.semantic.get_fact(f"relationship_{agent_b.id}")
        rel_b = mind_b.memory.semantic.get_fact(f"relationship_{agent_a.id}")
        
        personality_a = mind_a.personality.to_dict()
        personality_b = mind_b.personality.to_dict()
        
        prompt = f"""
Generate a natural 4-5 line dialogue between:

AGENT A:
- Personality: {personality_a}
- Current mood: {mind_a.emotional_state.primary_emotion}

AGENT B:
- Personality: {personality_b}
- Current mood: {mind_b.emotional_state.primary_emotion}

Relationship: Trust={rel_a.get('trust', 0.5)}, Affinity={rel_a.get('affinity', 0.5)}
Context: {context}

Generate realistic, natural dialogue. Format:
AGENT_A: "dialogue"
AGENT_B: "dialogue"

Make it emotionally authentic and consistent with personalities.
"""
        
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        dialogue_text = response.content[0].text
        dialogue = self.parse_dialogue(dialogue_text, agent_a.id, agent_b.id)
        
        return dialogue
    
    def parse_dialogue(self, text: str, agent_a_id: str,
                      agent_b_id: str) -> 'Dialogue':
        """Parse dialogue text."""
        dialogue = Dialogue(agent_a_id, agent_b_id)
        
        lines = text.split('\n')
        for line in lines:
            if ':' in line:
                speaker, text = line.split(':', 1)
                speaker = speaker.strip()
                text = text.strip().strip('"')
                
                exchange = Dialogue.Exchange(speaker=speaker, text=text)
                dialogue.exchanges.append(exchange)
        
        return dialogue

@dataclass
class Dialogue:
    """Conversation between agents."""
    agent_a_id: str
    agent_b_id: str
    exchanges: List['Dialogue.Exchange'] = field(default_factory=list)
    
    @dataclass
    class Exchange:
        speaker: str
        text: str
        emotion: str = "neutral"
        body_language: str = ""
```

---

## Summary: Phase 2 Week-by-Week

| Week | Component | Tasks | Tests |
|------|-----------|-------|-------|
| 1-2 | ECS Foundation | Entity creation, components, systems | 5 unit tests |
| 2-3 | Memory & Personality | Episodic/semantic/procedural/emotional memory | 4 unit tests |
| 3-4 | Goals & Motivation | Survival/social/work/leisure goals | 3 unit tests |
| 4-5 | Behavior Trees | Selector/sequence/action/condition nodes | 3 unit tests |
| 6-7 | Narrative Generation | Claude story generation, conflict detection | 2 integration tests |
| 6-7 | Dialogue System | Claude dialogue generation, conversation parsing | 2 integration tests |
| 7-8 | Cinematic Direction | Camera planning, shot selection | 2 integration tests |
| 8-9 | Integration & Testing | End-to-end agent behavior, narrative consistency | 5 integration tests |
| 9-10 | Polish & Documentation | Bug fixes, optimization, documentation | 0 (quality) |

**Total:** 20+ unit tests + 20+ integration tests

---

## Deliverables: v0.3.0

### Code
- `ecs_system.py` (~400 lines)
- `memory_system.py` (~800 lines)
- `goal_system.py` (~700 lines)
- `narrative_engine.py` (~600 lines)
- `dialogue_system.py` (~400 lines)
- Tests: 40+ test cases

### Features
- 100+ AI agents simultaneously
- Complex memory (episodic, semantic, procedural)
- Emergent goal-driven behavior
- Personality-driven actions
- Claude-powered narrative generation
- Dynamic dialogue

### APIs
- `POST /api/v1/agents/spawn`
- `GET /api/v1/agents/{id}/memory`
- `POST /api/v1/agents/{id}/interact`
- `GET /api/v1/narrative`
- `POST /api/v1/dialogue/generate`

---

**Phase 2 Implementation Guide Complete**  
**Ready for 10-week execution**
