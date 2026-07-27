# PyRoboSimulator Architecture

## Vision

AI-Native World Simulation Engine combining storytelling, world-building, robotics simulation, digital twins, and autonomous agent ecosystems into a single platform.

**Core Principle:** Generate worlds first. Everything else emerges from the world.

## Architectural Boundaries

### Dependencies (Do Not Rebuild)

| Component | Tool | Integration |
|-----------|------|-------------|
| Spatial indexing, terrain, coordinates | **PyTerrainMap** | Spatial foundation layer |
| Sensor simulation, multi-modal fusion | **PyRoboReplay** | Perception foundation layer |
| I/O pipelines, tensor ops, training | **PyRoboFrames** | Data/training integration layer |
| Computer vision tasks | **PyRoboVision** | Vision pipeline integration |

### PyRoboSimulator Owns

#### 1. World State & Persistence
- **RocksDB event log** — Immutable history of all world changes
- **Redis active state** — Fast access to current world positions/states
- **BVH spatial index** — Efficient entity queries by location
- **Versioned snapshots** — Save/load world states at any point in time
- **Causality chains** — Track cause→effect relationships

#### 2. Agent Ecosystem
- **ECS (Entity Component System)** — Scalable entity management
- **Agent Memory** — Knowledge graphs, past event recall
- **Behavior Trees** — Complex agent decision-making
- **Multi-Agent Types:**
  - Robots (with ROS 2 integration)
  - Humans (with goals, emotions, social dynamics)
  - NPCs (with schedules, relationships)
  - Organizations (corporations, governments)
  - Animals (with simple behaviors)

#### 3. Mission System
- **Procedural mission generation** from world state
- **Constraint-based planning** (resource scarcity, accessibility)
- **Task decomposition** (high-level goals → atomic actions)
- **Failure injection** (edge cases, anomalies)
- **Mission-to-narrative pipeline** (ROS 2 goals ↔ story beats)

#### 4. Narrative Layer
- **Cinematic intelligence** (camera planning, shot composition, lighting)
- **Story arc generation** from causality chains
- **Narrative event detection** (anomalies, conflicts, resolutions)
- **Cutscene planning** (temporal sequencing, pacing)
- **Multi-fidelity narratives** (mission briefing, cinematic, documentary)

#### 5. ROS 2 Integration
- **Native ROS 2 bridge** (not plugin or afterthought)
- **Auto-export to ROS 2 packages:**
  - TF trees (transform hierarchies)
  - Topic definitions (sensor, control, navigation)
  - URDF/SDFormat robot models
  - Nav2 maps and costmaps
  - MoveIt planning scenes
- **Launch file generation** (automatic Gazebo/Isaac setup)

#### 6. World Generation
- **Natural language → world spec** (LLM interpretation)
- **Constraint validation** (physically plausible, consistent)
- **Procedural generation** (terrain via PyTerrainMap, infrastructure, agents)
- **Multi-fidelity modes:**
  - Scientific mode (accurate physics, sensor simulation)
  - Robotics mode (navigation, manipulation, SLAM)
  - Cinematic mode (photorealistic rendering, story-driven)
- **World templating** (pre-built patterns + variation)

#### 7. Simulation Orchestration
- **Multi-physics backend support** (MuJoCo primary, plugins for ODE/Bullet/PhysX)
- **Rendering abstraction** (OpenUSD scene graph with LOD system)
- **Gazebo/Isaac Sim bridge** (coordinate simulation across platforms)
- **Real-time factor management** (speed up/slow down simulation)
- **Distributed simulation** (multi-machine, cloud coordination)

## Technology Stack

### Rust Core (pyrobosimulator-core)

**World State:**
- `rocksdb` — Event log (immutable history)
- `redis` — Active state cache
- `bvh` — Spatial indexing
- `serde` — Serialization (JSON, MessagePack)

**Agents & Simulation:**
- `bevy_ecs` — Entity Component System
- `tokio` — Async runtime
- `uuid` — Entity IDs

**Physics:**
- `mujoco-sys` — MuJoCo bindings (primary physics)
- Plugin interface for alternative engines

**Scene Graph & Rendering:**
- `openusd-sys` — OpenUSD bindings (scene representation)
- Multi-backend rendering (scientific/robotics/cinematic)

**ROS 2:**
- `rclrust` — ROS 2 client library (Rust native)
- Topic/service definitions auto-generated from world state

**Integration:**
- `tonic` — gRPC for distributed sim coordination
- `tokio-kafka` — Kafka event streams

### Python Layer

**User-Facing API:**
- PyO3 bindings (abi3, Python 3.10+)
- Async Python for LLM integration
- Narrative generation (LLM-driven)

**Dependencies:**
- PyTerrainMap (spatial foundation)
- PyRoboReplay (sensor simulation)
- PyRoboFrames (I/O, tensor ops)
- PyRoboVision (perception)

**Optional:**
- `rclpy` — ROS 2 Python client (if needed alongside Rust bridge)

## Data Model

### World State

```
World {
  id: UUID,
  name: String,
  creation_time: DateTime,
  active_agents: HashMap<UUID, Agent>,
  spatial_index: BVH,
  event_log: RocksDB,
  active_state: Redis,
  metadata: Metadata,
}

Agent {
  id: UUID,
  agent_type: AgentType,  // Robot | Human | NPC | Organization | Animal
  name: String,
  position: Vec3,
  velocity: Vec3,
  rotation: Quaternion,
  memory: KnowledgeGraph,
  goals: Vec<Goal>,
  relationships: HashMap<UUID, Relationship>,
  resources: HashMap<String, f64>,
  behavior_tree: BehaviorTree,
}

Event {
  id: UUID,
  timestamp: DateTime,
  agent_id: UUID,
  event_type: EventType,
  position: Vec3,
  data: Value,
  causality_chain: Vec<UUID>,  // Previous events this caused
}

Mission {
  id: UUID,
  world_id: UUID,
  name: String,
  objectives: Vec<Objective>,
  constraints: Vec<Constraint>,
  narrative_arc: Option<NarrativeArc>,
  ros2_goal: Option<Goal>,  // Bridges to Nav2/MoveIt
}

Scene {
  id: UUID,
  world_id: UUID,
  usd_representation: String,  // OpenUSD file
  fidelity_level: FidelityLevel,  // Scientific | Robotics | Cinematic
  lod_variants: HashMap<FidelityLevel, Scene>,
}
```

## Integration Points

### With PyTerrainMap
- Import terrain geometry
- Use coordinate systems (temporal normalization)
- Query traversability for mission planning
- Generate procedural landscapes

### With PyRoboReplay
- Simulate sensor streams (RGB, depth, thermal, Lidar)
- Multi-modal sensor fusion
- Temporal alignment of multi-rate sensors
- Replay recorded trajectories for training

### With PyRoboFrames
- Export simulation data as training datasets (Parquet)
- LeRobot write-back for robot learning
- Hugging Face Hub integration
- Cross-platform tensor operations

### With PyRoboVision
- Perception feedback loops
- Vision-based agent behaviors
- Semantic scene understanding

## Phase 1 Deliverables (8-12 weeks)

1. **World State Engine** — RocksDB + Redis + BVH spatial index
2. **Agent System (ECS)** — Entity Component System, multi-agent types
3. **ROS 2 Bridge** — Native robot integration, topic auto-export
4. **LLM→World Pipeline** — Natural language → validated world spec

## Phase 2 Deliverables (12-16 weeks)

5. **Narrative Engine** — Story arc generation, auto-mission creation
6. **Multi-Fidelity Rendering** — OpenUSD LOD system, 3-level quality switching
7. **Mission System** — Procedural challenges, edge-case injection, constraints
8. **Integration Tests** — PyTerrainMap, PyRoboReplay, PyRoboFrames workflows

## Success Metrics

- [ ] User can describe world in English → get playable ROS 2 environment
- [ ] Same world renders at 3+ fidelity levels without code changes
- [ ] Agent simulation with 100+ entities at real-time factor > 1.0
- [ ] Mission generation produces 10+ unique variants per world
- [ ] Story arcs automatically emerge from 5+ simultaneous agent interactions
- [ ] ROS 2 navigation/manipulation tasks executable within 5 min of world generation
