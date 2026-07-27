# PyRoboSimulator

AI-native world simulation engine combining storytelling, world-building, robotics simulation, digital twins, and autonomous agent ecosystems into a single platform.

## Vision

**Core Principle:** Generate worlds first. Everything else emerges from the world.

### One Platform for:
- Storytelling & cinematics
- Robot development (ROS 2)
- Autonomous agent testing
- Digital ecosystems
- Multi-agent research
- Narrative generation
- Game environments
- Research-grade simulation

## Architectural Philosophy

PyRoboSimulator is **world-centric**, not robot-centric. It orchestrates on top of proven foundation layers:

- **PyTerrainMap** — Spatial indexing, terrain generation, coordinates
- **PyRoboReplay** — Sensor simulation, multi-modal fusion
- **PyRoboFrames** — I/O pipelines, tensor operations, training integration
- **PyRoboVision** — Perception and vision tasks

PyRoboSimulator owns:
- Agent ecosystems (humans, NPCs, robots, organizations)
- Mission planning & procedural generation
- Narrative emergence from causality chains
- ROS 2 integration (native)
- Multi-fidelity rendering (cinematic-grade)
- Persistent world state with history

## Project Structure

```
pyrobosimulator/
├── pyrobosimulator-core/      # Rust core (PyO3 bindings)
│   └── src/
│       ├── lib.rs             # Main module
│       ├── world.rs           # World state engine
│       ├── agent.rs           # Agent system (ECS foundation)
│       ├── mission.rs         # Mission planning
│       ├── narrative.rs       # Narrative generation
│       ├── ros2.rs            # ROS 2 bridge
│       ├── world_gen.rs       # LLM → world pipeline
│       └── storage.rs         # Persistence (RocksDB, Redis)
├── python/pyrobosimulator/    # Python package (user-facing API)
│   └── __init__.py
├── Cargo.toml                 # Rust workspace
├── pyproject.toml             # Python package config (maturin)
├── ARCHITECTURE.md            # Technical design document
└── README.md
```

## Phase 1: Foundation (8-12 weeks)

- [ ] World State Engine (RocksDB + Redis + BVH)
- [ ] Agent System (ECS, multi-agent types)
- [ ] ROS 2 Bridge (native, auto-export)
- [ ] LLM → World Pipeline (NL to validated specs)

## Phase 2: Emergence (12-16 weeks)

- [ ] Narrative Engine (story arcs from causality)
- [ ] Multi-Fidelity Rendering (OpenUSD LOD system)
- [ ] Mission System (procedural, constraint-based)
- [ ] Integration (PyTerrainMap, PyRoboReplay, PyRoboFrames)

## Key Differentiators

| Feature | PyRoboSimulator | Traditional Simulators |
|---------|-----------------|----------------------|
| **Persistent World State** | RocksDB event log + causality | Episode reset after each run |
| **Multi-Fidelity Rendering** | Same world: RL→Robotics→Cinematic | Choose one: scientific OR cinematic |
| **Narrative Layer** | Auto-generate stories from events | Events have no semantic meaning |
| **NL → World** | "Create a mining colony" | Manual URDF/CAD required |
| **Agent Ecosystems** | Humans, NPCs, orgs, animals | Robots only |
| **Movie-Scale Rendering** | Runway-quality cinematics | Not a priority |

## Dependencies

- **Rust:** 1.70+
- **Python:** 3.10+
- **PyTerrainMap:** ≥1.0.0
- **PyRoboReplay:** ≥2.0.0
- **PyRoboFrames:** ≥1.2.0

## Status

**v0.1.0** — Foundation architecture (local, not published)

Initial commit: Architecture, Rust core scaffolding, Python package structure.
