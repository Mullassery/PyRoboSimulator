# PyRoboSimulator Phase 2: Multi-Agent Narrative System

## Overview

**Goal:** Add AI-driven agents with memory, goals, relationships, and emergent narrative generation.

**Timeline:** 8-10 weeks  
**Team Size:** 5-6 engineers (1 AI lead, 2 narrative designers, 1 database, 1 UE5, 1 DevOps)  
**Target Release:** v0.3.0  
**Integration:** Claude 3.5 Sonnet + custom reasoning engine  

---

## Deliverables

### 1. Agent System (ECS Architecture) ✅ (Design)

#### Entity-Component System (ECS)

**Python Module: `agent_system.py`**

```python
class Agent:
    """Base entity with components."""
    id: str
    entity_type: str  # "human", "npc", "organization"
    components: Dict[str, Component]  # Dynamic component attachment
    
    def __init__(self, agent_id: str, agent_type: str):
        self.id = agent_id
        self.entity_type = agent_type
        self.components = {
            "transform": TransformComponent(),
            "appearance": AppearanceComponent(),
            "mind": MindComponent(),  # AI/behavior
        }

class Component:
    """Base component."""
    def update(self, dt: float):
        pass

class TransformComponent(Component):
    """Position, rotation, velocity."""
    position: (float, float, float)
    rotation: (float, float, float)
    velocity: (float, float, float)
    speed: float

class AppearanceComponent(Component):
    """Visual representation."""
    mesh_id: str
    material_id: str
    animations: Dict[str, Animation]
    clothing: List[Garment]
    accessories: List[Item]

class MindComponent(Component):
    """AI behavior + state machine."""
    state_machine: StateMachine
    goals: List[Goal]
    memory: MemoryBank
    personality: Personality
    current_action: Action
```

#### Agent Types

**Humans:**
- Single entities (player, NPCs)
- Complex behaviors, emotions
- Social interactions
- Memory + learning

**NPCs (Non-Player Characters):**
- Similar to humans but AI-controlled
- Pre-scripted routines (optional)
- Procedural behavior (default)
- Social groups

**Organizations:**
- Governments, corporations, groups
- Collective goals
- Resource management
- Political power

**Animals (Future):**
- Basic pathfinding
- Herd behavior
- Predator/prey dynamics

### 2. Agent Memory & Personality ✅ (Design)

#### Memory Bank (Multi-Layer)

**Python Module: `memory_system.py`**

```python
class MemoryBank:
    """Multi-layer memory system inspired by human cognition."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # Episodic: What happened (timestamped events)
        self.episodic = EpisodicMemory()
        # Semantic: Facts known (timeless knowledge)
        self.semantic = SemanticMemory()
        # Procedural: How to do things (skills, habits)
        self.procedural = ProceduralMemory()
        # Emotional: Feelings + valence
        self.emotional = EmotionalMemory()
    
    def remember(self, event: Event):
        """Store event in episodic memory."""
        self.episodic.store(event)
        
        # Emotional tagging
        valence = self.evaluate_event(event)  # -1 to +1
        self.emotional.tag_event(event, valence)
        
        # Extract semantic knowledge
        facts = self.extract_facts(event)
        self.semantic.update(facts)
    
    def recall(self, query: str) -> List[Event]:
        """Retrieve relevant memories."""
        # Search episodic memory (recency bias)
        recent = self.episodic.search(query, time_window=7*24*3600)
        
        # Sort by emotional significance + recency
        sorted_events = sorted(recent, 
            key=lambda e: (self.emotional.valence(e), e.timestamp),
            reverse=True)
        
        return sorted_events[:10]  # Top 10 most relevant

class Event:
    id: str
    timestamp: float
    agent_id: str  # Who experienced it
    actor_id: str  # Who did it
    action: str    # What happened
    location: (float, float)
    context: Dict  # Additional info
    emotional_response: float  # -1 to +1

class Relationship:
    """Agent-to-agent relationship."""
    agent_a: str
    agent_b: str
    trust: float        # -1 (distrust) to +1 (trust)
    affinity: float     # -1 (dislike) to +1 (like)
    familiarity: float  # 0 (stranger) to 1 (intimate)
    shared_memories: List[str]  # Event IDs
    
    def update(self, event: Event):
        """Update relationship based on event."""
        # Positive action: increase trust/affinity
        # Negative action: decrease trust
        # Repeated interaction: increase familiarity
        pass
```

#### Personality Model (Big Five)

**Traits (0-1 scale):**
- **Openness:** Curious, creative vs. conventional, practical
- **Conscientiousness:** Organized, disciplined vs. spontaneous, disorganized
- **Extraversion:** Outgoing, social vs. reserved, introverted
- **Agreeableness:** Cooperative, empathetic vs. competitive, critical
- **Neuroticism:** Anxious, sensitive vs. stable, resilient

**Implementation:**
```python
class Personality:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    
    def get_trait_modifiers(self) -> Dict[str, float]:
        """Convert traits to behavior modifiers."""
        return {
            "curiosity": self.openness * 1.5,
            "reliability": self.conscientiousness * 1.5,
            "sociability": self.extraversion * 1.5,
            "generosity": self.agreeableness * 1.5,
            "anxiety": self.neuroticism * 1.5,
        }
```

**Personality Distribution:**
- Generate using multivariate normal
- Cluster into archetypes (5-10 personality types)
- ~20% of agents are outliers (extreme traits)

#### Emotional State

**Current Emotions (0-1 intensity):**
- Joy
- Sadness
- Anger
- Fear
- Disgust
- Surprise
- Trust
- Anticipation

**State Machine:**
```python
class EmotionalState:
    primary_emotion: str
    intensity: float
    duration: float
    
    def decay(self, dt: float):
        """Emotions fade over time."""
        self.intensity *= 0.99 ** dt  # Exponential decay
        self.duration -= dt
```

**Emotional Contagion:**
- Nearby agents (within 50m) feel similar emotions
- Strong emotions spread faster
- Personalities modulate susceptibility

### 3. Goal & Motivation System ✅ (Design)

#### Goal Hierarchy

**Python Module: `goal_system.py`**

```python
class Goal:
    """Base goal."""
    id: str
    agent_id: str
    type: str        # "work", "social", "leisure", "survival"
    priority: float  # 0-1
    progress: float  # 0-1
    deadline: float  # Unix timestamp (optional)
    preconditions: List[str]  # Goals that must complete first
    
    def evaluate_satisfaction(self) -> float:
        """How satisfied is agent with this goal's progress?"""
        return self.progress - self.time_elapsed / self.deadline

class SurvivalGoal(Goal):
    """Base needs: hunger, sleep, hygiene, safety."""
    type = "survival"
    
    def __init__(self, need_type: str):
        self.need = need_type  # "hunger", "sleep", etc.
        self.urgency = self.calculate_urgency()

class SocialGoal(Goal):
    """Social interaction: friend, romantic, rival."""
    type = "social"
    target_agent: str
    relationship_type: str
    
    def update(self, relationship: Relationship):
        self.progress = 0.5 + (relationship.affinity + relationship.trust) / 4

class WorkGoal(Goal):
    """Employment: job, career advancement, wealth."""
    type = "work"
    employer: str
    job_role: str
    salary: float

class LeisureGoal(Goal):
    """Fun & enrichment: entertainment, education, hobbies."""
    type = "leisure"
    activity: str
    social: bool  # Solo vs. group activity
```

#### Motivation Engine

**Needs → Goals → Actions**

```python
class MotivationEngine:
    def calculate_goal_priority(self, agent: Agent):
        """Compute priority for all goals."""
        
        # Biological needs (Maslow)
        needs_priority = self.evaluate_needs(agent)  # 0-1
        
        # Social needs
        social_priority = self.evaluate_relationships(agent)
        
        # Self-actualization (growth, achievement)
        growth_priority = self.evaluate_growth(agent)
        
        # Environmental factors
        context_priority = self.evaluate_context(agent)
        
        # Personality modulation
        personality_mods = agent.personality.get_trait_modifiers()
        
        # Combine all factors
        for goal in agent.mind.goals:
            goal.priority = self.combine_priorities(
                goal, needs_priority, social_priority, 
                growth_priority, context_priority, personality_mods
            )
```

**Need Levels:**
```python
class Needs:
    hunger: float = 0.5        # 0 = full, 1 = starving
    fatigue: float = 0.5       # 0 = rested, 1 = exhausted
    hygiene: float = 0.5       # 0 = clean, 1 = filthy
    loneliness: float = 0.5    # 0 = connected, 1 = isolated
    stress: float = 0.5        # 0 = calm, 1 = anxious
    
    def decay_over_time(self, dt: float):
        """Needs increase over time."""
        self.hunger += 0.0001 * dt       # 10 hour cycle
        self.fatigue += 0.0005 * dt      # 8 hour cycle
        self.stress += 0.00005 * dt      # Long-term
```

### 4. Behavior & Action System ✅ (Design)

#### Behavior Tree Execution

**Python Module: `behavior_system.py`**

```python
class BehaviorTree:
    """Hierarchical behavior planning."""
    root: Node
    
    def execute(self, agent: Agent, dt: float) -> Action:
        """Evaluate tree and return next action."""
        return self.root.execute(agent, dt)

class Node:
    def execute(self, agent: Agent, dt: float) -> Action:
        pass

class SelectorNode(Node):
    """Try children in order until one succeeds."""
    children: List[Node]
    
    def execute(self, agent: Agent, dt: float) -> Action:
        for child in self.children:
            action = child.execute(agent, dt)
            if action.status != "failed":
                return action
        return Action(status="failed")

class SequenceNode(Node):
    """Execute children in order; all must succeed."""
    children: List[Node]
    
    def execute(self, agent: Agent, dt: float) -> Action:
        for i, child in enumerate(self.children):
            action = child.execute(agent, dt)
            if action.status == "failed":
                return action
        return Action(status="success")

class LeafNode(Node):
    """Actual action/condition."""
    condition_type: str  # "is_hungry", "is_near_friend", etc.
    action_type: str    # "eat", "sleep", "chat", etc.
    
    def execute(self, agent: Agent, dt: float) -> Action:
        if self.is_condition_met(agent):
            return Action(type=self.action_type, agent_id=agent.id)
        return Action(status="failed")
```

#### Action System

```python
class Action:
    """Atomic action (1-10 second duration)."""
    id: str
    agent_id: str
    type: str              # "walk", "eat", "talk", "work", "sleep"
    target: Optional[str]  # target agent/object
    location: Optional[(float, float)]
    start_time: float
    duration: float
    status: str            # "pending", "executing", "done", "failed"
    
    def execute(self, agent: Agent, world: World, dt: float):
        """Execute action for dt seconds."""
        self.start_time = world.time if not self.start_time else self.start_time
        elapsed = world.time - self.start_time
        
        if elapsed >= self.duration:
            self.complete(agent, world)
        else:
            self.update(agent, world, dt)
    
    def complete(self, agent: Agent, world: World):
        """Action finished; update agent state."""
        if self.type == "eat":
            agent.needs.hunger = 0
        elif self.type == "sleep":
            agent.needs.fatigue = 0
        elif self.type == "chat":
            # Strengthen relationship
            target_agent = world.get_agent(self.target)
            self.update_relationship(agent, target_agent)
        
        self.status = "done"
```

### 5. Narrative Generation Engine ✅ (Design)

#### Story Arc System

**Python Module: `narrative_engine.py`**

```python
class NarrativeEngine:
    """Generate story arcs from world events."""
    
    def __init__(self):
        self.claude = Anthropic()
        self.story_cache = {}
    
    def generate_narrative(self, world: World, 
                          protagonist: Agent = None) -> Story:
        """Generate narrative from world state."""
        
        # 1. Collect significant events
        significant_events = self.extract_events(world)
        
        # 2. Identify relationships & tensions
        relationship_graph = self.build_relationship_graph(world)
        conflicts = self.detect_conflicts(relationship_graph)
        
        # 3. Generate story structure
        story = self.claude_generate_story_structure(
            protagonist, significant_events, conflicts
        )
        
        # 4. Expand into narrative
        narrative = self.expand_story(story, world)
        
        # 5. Cache for consistency
        self.story_cache[world.time] = narrative
        
        return narrative
    
    def claude_generate_story_structure(self, protagonist, events, conflicts):
        """Use Claude to structure narrative."""
        
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            thinking={
                "type": "enabled",
                "budget_tokens": 8000,
            },
            messages=[{
                "role": "user",
                "content": f"""
                Generate a 3-act story structure from this world state:
                
                Protagonist: {protagonist.name}
                Personality: {protagonist.personality}
                Current Goal: {protagonist.mind.goals[0]}
                
                Recent Events:
                {format_events(events)}
                
                Conflicts/Tensions:
                {format_conflicts(conflicts)}
                
                Structure should include:
                1. Setup (exposition)
                2. Inciting Incident
                3. Rising Action (3 major beats)
                4. Climax
                5. Resolution
                
                Each beat should be 1-2 sentences, grounded in the world state.
                """
            }]
        )
        
        return parse_story_structure(response.content[0].text)

class Story:
    """Complete narrative arc."""
    protagonist: Agent
    acts: List[Act]
    turning_points: List[TurningPoint]
    themes: List[str]
    
    class Act:
        title: str
        beats: List[str]
        duration: float  # In-world hours
    
    class TurningPoint:
        name: str
        description: str
        trigger_condition: Callable
        emotional_impact: float  # -1 to +1
```

#### Cinematic Direction

**Python Module: `cinematic_system.py`**

```python
class CinematicDirector:
    """Plan camera shots for dramatic moments."""
    
    def generate_shot_plan(self, scene: Scene) -> ShotPlan:
        """Create cinematic shot sequence."""
        
        # 1. Analyze narrative importance
        importance = self.analyze_scene_importance(scene)
        
        # 2. Select shot types based on emotion
        shot_types = self.select_shot_types(importance, scene.emotion)
        
        # 3. Plan camera movements
        movements = self.plan_movements(scene, shot_types)
        
        # 4. Time to music/dialogue
        timed_shots = self.time_to_audio(movements, scene.audio)
        
        return ShotPlan(timed_shots)
    
    def select_shot_types(self, importance: float, emotion: str) -> List[str]:
        """Map emotion to visual language."""
        mapping = {
            "joy": ["wide_shot", "upward_angle", "bright_lighting"],
            "sadness": ["close_up", "downward_angle", "soft_lighting"],
            "anger": ["low_angle", "sharp_cuts", "red_color_cast"],
            "fear": ["narrow_fov", "tracking_shot", "shadows"],
        }
        return mapping.get(emotion, ["wide_shot"])
```

### 6. Agent-World Interaction ✅ (Design)

#### Dialogue System

**Python Module: `dialogue_system.py`**

```python
class DialogueSystem:
    def __init__(self):
        self.claude = Anthropic()
    
    def generate_dialogue(self, agent_a: Agent, agent_b: Agent,
                         context: Dict) -> Dialogue:
        """Generate realistic conversation."""
        
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            thinking={"type": "enabled", "budget_tokens": 4000},
            messages=[{
                "role": "user",
                "content": f"""
                Generate a short, realistic dialogue between:
                
                {agent_a.name} (Personality: {agent_a.personality})
                {agent_b.name} (Personality: {agent_b.personality})
                
                Relationship: {self.get_relationship(agent_a, agent_b)}
                Context: {context}
                
                Generate 3-5 exchanges. Each line should be:
                - Natural and conversational
                - Consistent with personality
                - Emotionally appropriate
                - 1-3 sentences max
                
                Format:
                AGENT_A: "..."
                AGENT_B: "..."
                """
            }]
        )
        
        return parse_dialogue(response.content[0].text)

class Dialogue:
    participant_a: str
    participant_b: str
    exchanges: List[Exchange]
    
    class Exchange:
        speaker: str
        text: str
        emotion: str
        body_language: str
```

#### Decision Points

**Python Module: `decision_system.py`**

```python
class DecisionPoint:
    """Critical moment where agent chooses path."""
    agent_id: str
    options: List[Option]
    context: Dict
    
    class Option:
        description: str
        action: Action
        consequences: List[Consequence]  # Future outcomes
        alignment_score: float  # Personality fit
    
    def resolve(self, agent: Agent) -> Action:
        """Agent chooses based on personality & goals."""
        
        # Score each option
        scores = {}
        for option in self.options:
            score = self.evaluate_option(agent, option)
            scores[option] = score
        
        # Add randomness (personality.neuroticism makes choices less certain)
        randomness = agent.personality.neuroticism * 0.3
        for option in scores:
            scores[option] += random.gauss(0, randomness)
        
        # Choose highest-scoring option
        chosen = max(scores, key=scores.get)
        return chosen.action
```

---

## Phase 2 Roadmap

### Week 1-2: Agent Foundation
- [ ] ECS architecture (Entity, Component, System)
- [ ] Agent spawning & initialization
- [ ] Basic movement & animation
- [ ] Component serialization

### Week 2-3: Memory & Personality
- [ ] Episodic memory system
- [ ] Semantic knowledge base
- [ ] Big Five personality model
- [ ] Emotional state machine
- [ ] Personality-driven behavior modification

### Week 3-4: Goals & Motivation
- [ ] Goal hierarchy (survival → social → growth)
- [ ] Need systems (hunger, sleep, stress)
- [ ] Motivation engine
- [ ] Goal planning & prioritization
- [ ] Goal completion & satisfaction

### Week 4-5: Behavior Trees & Actions
- [ ] Behavior tree framework
- [ ] Common action nodes (walk, eat, sleep, chat)
- [ ] Condition evaluation
- [ ] Action execution & completion
- [ ] Interruption handling

### Week 5-6: Dialogue & Relationships
- [ ] Dialogue generation (Claude)
- [ ] Conversation system
- [ ] Relationship tracking
- [ ] Social emotion contagion
- [ ] Group formation

### Week 6-7: Narrative Engine
- [ ] Event extraction & analysis
- [ ] Story arc generation (Claude)
- [ ] Turning point detection
- [ ] Narrative consistency checking
- [ ] Branching story paths

### Week 7-8: Cinematic System
- [ ] Shot planning
- [ ] Camera positioning
- [ ] Cut timing
- [ ] Dynamic camera following
- [ ] Emotional cinematography

### Week 8-9: Integration & Testing
- [ ] End-to-end agent behavior
- [ ] Narrative consistency
- [ ] Performance profiling (100+ agents)
- [ ] API integration
- [ ] Demo scenarios

### Week 9-10: Polish & Buffer
- [ ] Bug fixes & edge cases
- [ ] Performance optimization
- [ ] Documentation
- [ ] Validation against design

---

## Success Criteria (Phase 2)

| Metric | Target | Validation |
|--------|--------|-----------|
| Agent Count | 100+ simultaneous | Performance test |
| Memory System | Accurate recall | Memory accuracy test |
| Personality Variation | 10+ distinct archetypes | Behavioral clustering |
| Dialogue Quality | Natural, contextual | Human evaluation |
| Narrative Generation | Coherent story arcs | Story structure validation |
| Relationship Depth | Complex, dynamic | Relationship graph analysis |
| Cinematic Quality | Professional-looking shots | Visual inspection |
| Frame Rate | 30+ FPS with 100 agents | Benchmark |
| Scenario Playback | Consistent narratives | Replay test |

---

## API Additions (Phase 2)

### POST /api/v1/agents/spawn
```json
{
  "city_id": "uuid",
  "agent_type": "human",
  "name": "Alice",
  "personality": {
    "openness": 0.7,
    "conscientiousness": 0.6,
    "extraversion": 0.8,
    "agreeableness": 0.5,
    "neuroticism": 0.3
  },
  "starting_location": [100, 100]
}

Response: {"agent_id": "uuid", "status": "spawned"}
```

### GET /api/v1/agents/{agent_id}/memory
```
Response: List of recent memories with emotional tags
```

### POST /api/v1/agents/{agent_id}/interact
```json
{
  "action_type": "chat",
  "target_agent_id": "uuid"
}

Response: Generated dialogue
```

### GET /api/v1/narrative
```
Response: Current story arc for entire world
```

---

**Phase 2 Timeline:** 8-10 weeks  
**Target Release:** v0.3.0  
**Next:** Phase 3 (advanced physics, digital twins)
