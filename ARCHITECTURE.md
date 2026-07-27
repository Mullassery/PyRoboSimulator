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

#### 7. Movie-Scale Hyperrealistic Rendering Pipeline
- **Real-time Rendering Engine** (OpenUSD + NVIDIA RTX)
  - Physically-based rendering (PBR)
  - Ray tracing for photorealism
  - Real-time 30–120 fps at 1080p+
  - DXR/OptiX acceleration
- **Multi-Fidelity LOD System** (same world, 3 quality levels)
  - Level 0: Scientific (boxes/primitives, accurate physics only)
  - Level 1: Robotics (medium-poly geometry, realistic materials)
  - Level 2: Cinematic (high-poly, photorealistic assets, advanced lighting)
  - Seamless runtime switching (no re-simulation)
- **Neural Enhancement Layer** (Runway-quality upsampling)
  - Optional video diffusion models (real-time inference)
  - Super-resolution (4K from 1080p)
  - Style transfer (narrative-driven cinematics)
  - Temporal coherence across frames
- **Cinematic Intelligence**
  - Automated camera planning (shot composition, depth of field, motion)
  - Dynamic lighting (volumetric, shadow mapping, GI)
  - Depth-of-field and motion blur (cinematography)
  - Color grading and post-processing (mood/narrative)
- **Output Formats**
  - Real-time video streams (H.264/H.265 encoding)
  - High-quality offline rendering (ProRes, DNxHD for post-production)
  - Image sequences (EXR with passes for compositing)
  - RGB + depth maps (for PyRoboReplay sensor simulation)
- **Integration with PyRoboReplay**
  - Render RGB + depth + thermal + segmentation in parallel
  - Sensor-specific distortion/noise injection
  - Multi-view rendering (omnidirectional, panoramic, drone perspectives)

#### 8. Simulation Orchestration
- **Multi-physics backend support** (MuJoCo primary, plugins for ODE/Bullet/PhysX)
- **Gazebo/Isaac Sim bridge** (coordinate simulation across platforms)
- **Real-time factor management** (speed up/slow down simulation)
- **Distributed simulation** (multi-machine, cloud coordination)
- **Rendering & Physics Decoupling** (separate threads/GPUs for rendering and physics)

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
- `openusd-rs` — OpenUSD Rust bindings for LOD management
- `nvapi-rs` — NVIDIA RTX DXR/OptiX acceleration
- Multi-fidelity LOD system (scientific/robotics/cinematic modes)

**Real-Time Rendering:**
- NVIDIA OptiX (ray tracing, photorealism)
- OpenGL/Vulkan fallback
- Multi-threaded rendering pipeline (decoupled from physics)
- Video encoding: `ffmpeg-sys-next` (H.264/H.265, ProRes, DNxHD)
- Image I/O: `image` crate (PNG, EXR, OpenEXR for compositing)

**Neural Enhancement (Optional, Phase 2+):**
- ONNX Runtime for real-time inference
- Video diffusion model integration (Runway-style upsampling)
- Model quantization for edge deployment

**ROS 2:**
- `rclrust` — ROS 2 client library (Rust native)
- Topic/service definitions auto-generated from world state

**Integration:**
- `tonic` — gRPC for distributed sim coordination
- `tokio-kafka` — Kafka event streams
- `serde_usd` — Custom serde for OpenUSD serialization

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

## Rendering Pipeline Architecture

### Multi-Fidelity System (Core Differentiator)

The same world generates three rendering variants **without re-simulation**:

```
World State (Physics Simulation)
    ↓
    ├─→ LOD-0 (Scientific Mode)
    │   ├─ Box primitives
    │   ├─ Physics-only visualization
    │   └─ Use: RL training, rapid iteration
    │       Output: Real-time streams to PyRoboReplay
    │
    ├─→ LOD-1 (Robotics Mode)
    │   ├─ Medium-poly geometry
    │   ├─ Realistic materials/textures
    │   ├─ Camera simulation (RGB, depth, Lidar)
    │   └─ Use: Nav2, MoveIt, SLAM testing
    │       Output: Sensor feeds to ROS 2 topics
    │
    └─→ LOD-2 (Cinematic Mode)
        ├─ High-poly/hero assets
        ├─ Photorealistic rendering (RTX)
        ├─ Advanced lighting (volumetric, GI)
        ├─ Cinematic camera control
        ├─ Optional: Neural upsampling (Runway-quality)
        └─ Use: Films, marketing, documentaries
            Output: H.265 video (UHD), EXR sequences
```

**Key Property:** Physics simulation runs once; rendering runs at 3 quality levels in parallel.

### Rendering Data Flow

```
Physics Engine (MuJoCo)
    ↓ Transform Updates (TF trees)
    ↓
OpenUSD Scene Graph
    ├─ Spatial hierarchy
    ├─ Material properties
    ├─ LOD variants (same geometry at 3 poly counts)
    └─ Shaders (PBR for robotics/cinematic)
    ↓
Multi-Backend Renderer
    ├─ Backend 1: OpenGL (fallback, fast)
    ├─ Backend 2: Vulkan (portable, high-performance)
    └─ Backend 3: OptiX (NVIDIA GPUs, photorealistic)
    ↓
Rendering Passes (Parallel)
    ├─ Geometry pass (LOD selection)
    ├─ Lighting pass (shadows, GI)
    ├─ Post-processing (DoF, motion blur, color grade)
    └─ Composition (multiple layers for editing)
    ↓
Output Encoders (Simultaneous)
    ├─ Real-time streams (H.264, network optimized)
    ├─ Offline rendering (ProRes, archival quality)
    ├─ Sensor simulation (RGB/depth for PyRoboReplay)
    └─ Analysis passes (segmentation, normals, etc.)
```

### Cinematic Intelligence Module

Runs in parallel with simulation, generates:

```
Causality Chain (from world events)
    ↓
Narrative Analyzer
    ├─ Identify key moments (conflicts, resolutions, discoveries)
    ├─ Extract emotional beats (tension, relief, climax)
    └─ Classify scene type (action, dialogue, exploration, mystery)
    ↓
Camera Planner
    ├─ Shot composition (rule-of-thirds, leading lines)
    ├─ Camera movement (push-in, pan, orbital)
    ├─ Depth-of-field targets (focus on protagonist)
    └─ Timing & pacing (frame rate, shot duration)
    ↓
Lighting Designer
    ├─ Key/fill/back light ratios
    ├─ Color temperature (warm/cool by mood)
    ├─ Shadow direction (narrative relevance)
    └─ Volumetric effects (fog, dust, atmosphere)
    ↓
Cuts & Transitions
    ├─ Scene boundaries (when to cut)
    ├─ Transition types (cut, fade, dissolve)
    └─ Music sync points (beat matching)
    ↓
Output
    ├─ Camera rig (automated trajectory)
    ├─ Lighting rig (dynamic light parameters)
    ├─ Post-processing stack (color grade, effects)
    └─ Editing decisions (cuts, pacing)
```

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

### Core Functionality
- [ ] User can describe world in English → get playable ROS 2 environment
- [ ] Same world renders at 3+ fidelity levels without code changes
- [ ] Agent simulation with 100+ entities at real-time factor > 1.0
- [ ] Mission generation produces 10+ unique variants per world
- [ ] Story arcs automatically emerge from 5+ simultaneous agent interactions
- [ ] ROS 2 navigation/manipulation tasks executable within 5 min of world generation

### Rendering & Cinematics (Phase 2+)
- [ ] Cinematic mode outputs 1080p at 30fps+ with photorealistic quality
- [ ] Same scene renders as: scientific (boxes) → robotics (medium) → cinematic (hero)
- [ ] Automated camera planning (shot composition, motion, pacing)
- [ ] Lighting design (key/fill/back, volumetric effects, color grading)
- [ ] Video output: H.265 UHD + ProRes offline + EXR for compositing
- [ ] Neural enhancement (optional): Runway-quality upsampling from 1080p
- [ ] Cinematic output quality competitive with production-grade tools (Runway, Synthesia)
- [ ] Multi-modal rendering: RGB + depth + thermal + segmentation in parallel
- [ ] Render farm coordination for distributed cinematic rendering

### Integration
- [ ] PyTerrainMap: Procedural terrain → world LOD variants
- [ ] PyRoboReplay: Sensor feeds from cinematic rendering
- [ ] PyRoboFrames: Export training datasets (RGB, depth, trajectories)
- [ ] PyRoboVision: Perception feedback loops in cinematic mode
