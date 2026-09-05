# PyRoboSimulator: Product Vision

## Honest status (read this first)

This document previously described PyRoboSimulator as if the full "world operating
system" — persistent worlds, narrative-driven cinematics, movie-scale rendering,
native ROS 2 integration, natural-language world generation — already existed. It
did not, and much of it still does not. This rewrite separates **what's built and
verified** from **what's aspirational**, using the same evidence standard as the
README's "Known Issues" section and the v0.9–v0.11 "honesty pass" commits
(`5099677`, `433e511`, `59387ca`, `685b3a7`).

The long-term direction described further down is still the real direction of the
project. What changed is the claim about how much of it exists today.

---

## What's real and working today

- **A Rust-backed core package** (`pip install pyrobosimulator`) exposing `World`,
  `Agent`, `AgentType`, `Mission`, `NarrativeEngine`, `ROS2Bridge`, `StorageEngine`
  (`python/pyrobosimulator/__init__.py`). This is a real, importable package with a
  working `__init__.py` (a prior release shipped without one — fixed).
- **`StorageEngine`** is a real, RocksDB-backed event log
  (`pyrobosimulator-core/src/storage.rs`) — `world_id` → ordered event history on
  disk, not the in-memory no-op it was before.
- **`ROS2Bridge`** does exactly one real thing: `export_world_to_sdf()`
  (`pyrobosimulator-core/src/ros2.rs`) generates a real SDF document from actual
  `World`/`Agent` state. It does **not** export TF trees, launch files, or provide
  Nav2/MoveIt/Foxglove compatibility — those are aspirational (see below), not
  implemented anywhere in this repo.
- **A real MuJoCo physics backend** (`backend/src/simulators/mujoco_backend.py`)
  that loads actual MJCF/URDF models via `mujoco.MjSpec` and steps real dynamics
  with `mujoco.mj_step`, including contacts and camera/Lidar/IMU sensor extraction.
  Verified with kinematics-correctness tests (free-fall height matches
  `z0 - 1/2 g t^2`) in `backend/tests/test_mujoco_backend.py`.
- **A lightweight custom physics loop** (`backend/src/services/simulation_engine.py`)
  — Euler integration, AABB collision detection, boundary handling — that powers
  the multi-agent simulation used throughout the FastAPI backend examples.
- **A real sensor suite** (`backend/src/sensors/`) — RGB, depth, Lidar, thermal —
  each physically parameterized and configurable per agent.
- **A FastAPI backend** (`backend/`, run from source, not part of the pip package)
  with a REST API, JWT auth, and a real test suite: as of the last audited pass,
  925 test functions across 43 files in `backend/tests/`, 812 passing / 86 failing
  / 18 erroring / 6 skipped / 3 xfailed, 74% measured line coverage
  (`pytest --cov=src`). See README "Testing & Quality" for the current breakdown —
  failures are tracked, not hidden, and concentrated in speculative feature areas
  (`src/mission/`, `src/dashboards/`, `src/data/synthetic_data_generator.py`).
- **Narrative scenario generation via the Claude API** is real, but lives in the
  Python backend (`backend/src/narratives/narrative_converter.py`), not in the Rust
  core. The Rust core's `NarrativeEngine.generate_from_events` deliberately raises
  `NotImplementedError` (`pyrobosimulator-core/src/narrative.rs`) rather than faking
  an LLM call.

## What's partially built or scaffolding

- **"World Operating System" positioning** (the pitch that one world simultaneously
  serves robotics, cinema, game dev, and digital twins) describes the long-term
  goal, not a shipped capability. Individual pieces exist (physics, sensors, a
  narrative converter) but there is no working pipeline that takes a natural-language
  world description and produces a ROS 2-ready, cinematically-rendered, game-exportable
  environment.
- **"Movie-scale hyperrealistic rendering" / "Runway-quality video" / OptiX ray
  tracing / neural upsampling** — no rendering pipeline of this kind exists in the
  codebase. There is no OptiX, ray-tracing, or UE5 integration code anywhere in
  `backend/` or `python/pyrobosimulator/`; UE5 integration is explicitly listed as
  planned (README, "Phase 10+"). Any cinematic-rendering claim should be read as
  future direction, not current capability.
- **"ROS 2 native" positioning** overstates what exists. The real surface is
  `export_world_to_sdf()` — a static SDF document generator. There is no TF tree
  publishing, no launch-file generation, no live topic bridge, and no verified
  Nav2/MoveIt/Foxglove interoperation.
- **Gazebo and Isaac Sim physics backends** (`backend/src/simulators/gazebo_backend.py`,
  `isaac_sim_backend.py`) are unfinished sketches: `initialize()` raises
  `EnvironmentError` immediately by design (they need infrastructure — a full ROS 2
  install, or NVIDIA Omniverse + CUDA GPU — not available in a typical dev/CI
  environment), and the methods beneath them are unreachable in normal use.
- **PostgreSQL/Redis backend integration** is partially wired; simulations/users
  are still served from in-memory storage as of this pass (see README "Known
  Issues"). The Kubernetes/Docker manifests exist (`backend/k8s/`, `backend/Dockerfile`)
  but deploy a service whose persistence layer isn't fully load-bearing yet.
- **Performance numbers** in the README's benchmark table (100K+ agents/sec, <500ms
  P99 API latency, etc.) are not backed by a committed, reproducible benchmark
  script in this repo — they're marked "unverified" in the README itself. Treat
  them the same way here: unverified until a benchmark suite lands.
- **CI has been red across recent pushes to `main`**, including the commit that
  added the real `StorageEngine` — the "Code Quality" job's dependency-install step
  fails with `pip install: ResolutionImpossible` before the Tests/Build/Deploy jobs
  ever run. This is a dependency-pinning problem, not evidence the tests themselves
  fail (locally, pytest does run to the pass/fail counts cited above).
- **The multi-agent economy/social-dynamics/knowledge-graph "Agent Ecosystem" layer**
  described below (organizations, animals, relationships, alliances, resource
  pricing) exists only as a design sketch in this document — the shipped agent
  model is physics + behavior trees + multi-layer memory (episodic/semantic/
  procedural/emotional, `backend/src/services/agent_memory.py`), not an economic
  simulation.

## Realistic near-term roadmap

Given the actual pace of work (real MuJoCo backend, real StorageEngine, and a CI
honesty pass all landed within the last several commits), the next concrete steps
that build directly on what exists:

1. **Fix the CI dependency conflict** blocking the Tests/Build/Deploy jobs so the
   925-test suite actually runs in CI instead of only locally. This is a pinning
   fix, not new engineering — highest leverage per hour of work.
2. **Wire PostgreSQL/Redis in for real** so simulations and users persist beyond
   process memory, closing the gap between the Kubernetes manifests that exist and
   what they actually deploy.
3. **Reduce the 86 failing / 18 erroring backend tests**, prioritizing the
   near-zero-coverage modules already identified (`src/mission/`, `src/dashboards/`,
   `src/data/synthetic_data_generator.py`, `src/services/sensors.py`) over adding
   new feature surface.
4. **Extend `ROS2Bridge` incrementally** — TF tree export or a single real Nav2
   integration test — rather than continuing to describe "native ROS 2" as a
   finished capability. Each real increment here should get the same
   file-and-test citation treatment as the MuJoCo and StorageEngine work.

Anything beyond this (cinematic rendering, UE5, natural-language world generation,
game-engine export, cross-region cloud simulation) is long-term direction, not a
committed timeline — no phase/week estimate below should be read as a schedule
this project has demonstrated it can hit.

---

## Long-term direction (aspirational — not a status claim)

**PyRoboSimulator** aims to be an AI-native world simulation engine that generates
persistent fictional worlds usable simultaneously for robotics development,
cinematic production, autonomous agent research, and narrative storytelling —
world-centric rather than robotics-only or rendering-only.

The same fictional world would eventually serve as:
- A ROS 2-compatible robotics development environment
- A real-time physics simulation for agent behaviors
- A cinematic production platform
- A multi-agent research platform
- A narrative storytelling system with auto-generated missions
- A game-ready environment
- A digital twin for autonomous systems

### Core principle (goal, not shipped behavior)

> Generate worlds first. Everything else emerges from the world.

A creator would describe a world in natural language and get back a persistent
simulated universe, a ROS 2-ready robotics testing environment, cinematic
rendering, autonomous agents with memory and goals, and a game-ready export —
today, each of those exists (if at all) as a separate, partially-built piece, not
an integrated pipeline triggered by a natural-language prompt.

### What PyRoboSimulator intends to own (design intent, verify before relying on)

1. **World State & Persistence** — event log ✓ real (RocksDB, `storage.rs`);
   causality chains, versioned snapshots, time-indexed replay — not yet built.
2. **Agent Ecosystem** — ECS-style multi-agent types, behavior trees ✓ real
   (`backend/src/services/behavior_tree.py`), memory ✓ real
   (`backend/src/services/agent_memory.py`); social dynamics and economics — design
   sketch only.
3. **Mission System** — procedural mission framework exists
   (`backend/src/mission/mission_framework.py`) but is one of the near-zero-coverage
   modules noted above; constraint-based planning and failure injection are not
   verified working.
4. **Narrative Layer** — NL→scenario via Claude ✓ real (Python backend); story-arc
   generation from causality chains and cinematic camera/lighting planning — not
   built.
5. **Movie-scale rendering** — not built (see above).
6. **ROS 2 integration** — SDF export only ✓ real; everything else in this bullet
   is aspirational (see above).
7. **World generation from natural language** — the Claude-backed narrative
   converter is a real building block; a full NL→constraint-validated-world
   pipeline is not built.
8. **Simulation orchestration** — MuJoCo backend ✓ real; Gazebo/Isaac Sim backends
   are honest stubs (fail-fast, not fake); distributed/multi-GPU coordination not
   built.

### Dependencies on sibling repos (design intent, not verified code-level integration)

VISION previously listed PyTerrainMap, PyRoboReplay, PyRoboFrames, and PyRoboVision
as depended-upon foundation layers. Per the README's "Cross-repo compatibility"
section (verified by reading every `Cargo.toml`/`pyproject.toml` in the group): **none
of these repos have an actual Cargo or pip dependency on this repo, or on each
other.** The integration described below is architectural intent for a future
version, not a working interop today.

- **PyTerrainMap** — intended spatial/terrain foundation layer.
- **PyRoboReplay** — intended sensor-simulation/perception foundation layer.
- **PyRoboFrames** — intended data/training I/O layer (Parquet, LeRobot, HF Hub).
- **PyRoboVision** — intended vision/perception layer.

### Why this shape, long-term

The differentiation this project is aiming for — persistent (non-resetting) world
state, one world serving multiple fidelity levels (training/robotics/cinematic),
and narrative structure emerging from simulation events — is still a reasonable
bet relative to Gazebo/Isaac Sim/MuJoCo/Webots, none of which persist world state
across runs by default. The gap between that bet and the current codebase is
real and is documented above; closing it is the roadmap, not a marketing claim.
