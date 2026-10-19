# PyRoboSimulator

AI-native world simulation engine for robotics, agents, and ROS 2 — a pip-installable Rust core for multi-agent state/physics plus a FastAPI simulation service with realistic sensors and a real MuJoCo physics backend.

[![CI](https://github.com/Mullassery/PyRoboSimulator/actions/workflows/ci-cd.yaml/badge.svg)](https://github.com/Mullassery/PyRoboSimulator/actions/workflows/ci-cd.yaml)
[![PyPI](https://img.shields.io/pypi/v/pyrobosimulator)](https://pypi.org/project/pyrobosimulator/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

## What it is

PyRoboSimulator is two separately-installed pieces under one name:

1. **A pip-installable Rust core** (`pip install pyrobosimulator`) exposing `World`, `Agent`, `AgentType`, `Mission`, `NarrativeEngine`, `ROS2Bridge`, and `StorageEngine`. It provides real multi-agent state, gravity, forward-Euler integration, and pairwise collision detection, plus a RocksDB-backed event log.
2. **A FastAPI backend service** run from source in `backend/`. It provides the simulation loop (`SimulationEngine`), procedural world generation (`ScenarioBuilder`), realistic RGB/Depth/Lidar/Thermal sensors, a REST API, and the pluggable physics backends (MuJoCo, Gazebo, Isaac Sim).

The two are not interchangeable — read **What it is not** before copying any example.

## Features

- **Multi-agent physics (pip core)** — `World.step(dt)` applies gravity to every agent and integrates; `Agent.apply_force()`, velocity clamping, `World.detect_collisions()` (O(n²) pairwise).
- **RocksDB event log (pip core)** — `StorageEngine` is a real on-disk append-only store keyed by `world_id`.
- **Simulation loop (backend)** — configurable timestep (default 16 ms @ 60 Hz), AABB collision, boundary conditions, deterministic seeding.
- **Sensors (backend)** — RGB camera, depth, Lidar point clouds, and thermal cameras with per-agent configuration.
- **Real MuJoCo backend** — loads real MJCF/URDF models, steps real dynamics, and extracts body/joint/contact/sensor state.
- **World generation** — built-in parking-lot, warehouse, and urban-street scenarios; procedural obstacle placement; reproducible seeds.
- **REST API** — simulation CRUD, status, results, and SSE streaming; JWT auth with bcrypt; OpenAPI docs at `/docs`.
- **Agent behavior (backend)** — behavior trees, A*/NavMesh pathfinding with RVO avoidance, multi-layer agent memory, and multi-agent messaging.
- **Narrative + learning (backend)** — Claude-backed NLP→scenario conversion, curriculum learning, and fleet learning.

## Who it's for / Use cases

- **Autonomous-vehicle algorithm testing** — scripted urban scenarios with many agents to exercise collision avoidance.
- **Multi-robot coordination** — warehouse fleets, formation control, and communication testing.
- **Sensor-fusion research** — synchronized RGB/depth/Lidar/thermal streams per agent.
- **RL / imitation-learning experiments** — procedural environments with deterministic seeds.
- **Service integration** — drive simulations over the REST API instead of embedding the engine.

## What it is not

- **`pip install pyrobosimulator` does not include `SimulationEngine` or `ScenarioBuilder`.** Those live only in the `backend/` service; install from source to use them.
- **`NarrativeEngine.generate_from_events` is not implemented in the Rust core** — it raises `NotImplementedError` by design. Use the Claude-backed path in `backend/src/narratives/narrative_converter.py`.
- **Gazebo and Isaac Sim backends are not real integrations.** `initialize()` raises `EnvironmentError` immediately; only MuJoCo is a working physics backend. Using either requires infrastructure (ROS 2 / Omniverse + NVIDIA GPU) not present in a typical dev or CI environment.
- **Backend database and cache are still in-memory** for simulations/users. The PostgreSQL/Redis integration is partially wired, not fully load-bearing.
- **The published performance benchmarks are not backed by a committed, reproducible benchmark suite** — treat them as unverified historical claims.
- **Not a certified or production-verified simulator.** Development status is Alpha.

## Project status

Alpha (Development Status 3), version **0.12.1**, matching the latest PyPI release. The Rust core (`World`/`Agent`/`StorageEngine`, real gravity, integration, collision detection, RocksDB storage) and the MuJoCo backend are implemented and unit-tested; Gazebo/Isaac Sim are stubs that fail fast. The backend suite runs ~882 passing / 33 failing / 1 erroring tests at ~75% measured line coverage; remaining failures are pre-existing and unrelated to the physics/simulator work. `mypy` (strict) still reports a large backlog that is not CI-gating, and the frontend has had a TypeScript error sweep but not a full quality audit. See [ROADMAP_HONEST.md](ROADMAP_HONEST.md).

## Installation

```bash
pip install pyrobosimulator
```

This installs only the Rust core (Python 3.10+).

The backend service is run from source:

```bash
git clone https://github.com/Mullassery/PyRoboSimulator.git
cd PyRoboSimulator/backend
pip install -e ".[dev]"
uvicorn src.main:app --reload
```

Add the optional MuJoCo physics backend with `pip install -e ".[physics]"`.

## Quick start

Rust core (from the pip package):

```python
from pyrobosimulator import World, Agent, AgentType

world = World("demo")
robot = Agent("robot-1", AgentType.Robot)
robot.set_position(0.0, 0.0, 10.0)
robot.set_mass(1.0)
world.add_agent(robot)

for _ in range(100):          # 1 simulated second at 10 ms
    world.step(0.01)

print(world.get_agent(robot.id()).position())
print("collisions:", world.detect_collisions())
```

Backend service (run from source — see Installation; `SimulationEngine` is not in the pip package):

```python
from pyrobosimulator import SimulationEngine

engine = SimulationEngine(num_agents=100, duration=60.0, timestep=0.016)
engine.run()
summary = engine.get_summary()
print(summary["collision_count"], summary["goal_reached_count"])
```

## Usage

```bash
# Start the API, then create a simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{"scenario": "parking_lot", "num_agents": 50, "duration": 30.0}'
```

Key backend endpoints: `POST/GET/PUT/DELETE /api/v1/simulations`, `.../{id}/start|stop|status|results|agents|summary|stream` (SSE), plus `GET /health`, `/ready`, `/metrics`. Full list in `backend/docs/`.

## Documentation

- [backend/README.md](backend/README.md) — backend service setup
- [VISION.md](VISION.md) — product vision
- [ROADMAP_HONEST.md](ROADMAP_HONEST.md) — implemented vs planned, honest caveats
- [backend/docs/DEPLOYMENT.md](backend/docs/DEPLOYMENT.md) — Docker / Kubernetes / local dev
- [backend/docs/SCHEMA.md](backend/docs/SCHEMA.md) — database schema
- [backend/docs/UE5_INTEGRATION.md](backend/docs/UE5_INTEGRATION.md) — rendering integration
- [backend/docs/OSS_COMPLIANCE.md](backend/docs/OSS_COMPLIANCE.md) — dependency license audit
- [examples/](examples/) — example scripts
- [CHANGELOG.md](CHANGELOG.md) — notable changes

## Queue status

Shipped, blocked/failed, and rejected work for this repository is documented in
[`QUEUE_STATUS.md`](QUEUE_STATUS.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature requests: [GitHub Issues](https://github.com/Mullassery/PyRoboSimulator/issues); questions: [GitHub Discussions](https://github.com/Mullassery/PyRoboSimulator/discussions).

## Part of the robotics & autonomy family

PyRoboSimulator is one of six complementary, composable tools in the Mullassery **robotics & autonomy** family. Together they form a single stack: **perceive → map → simulate → learn → debug → coordinate the fleet**.

| Tool | Role | What it does |
|---|---|---|
| [PyRoboVision](https://github.com/Mullassery/PyRoboVision) | Perception | Multi-object tracker (Kalman filter + Hungarian algorithm) and trajectory predictor for robot perception. |
| [PyTerrainMap](https://github.com/Mullassery/PyTerrainMap) | Mapping / SLAM | Fuses multi-robot terrain observations into a spatial-temporal store, with H3 spatial indexing and SLAM. |
| [PyRoboSimulator](https://github.com/Mullassery/PyRoboSimulator) | Simulation | **This project** — world simulator for autonomous systems, with a FastAPI backend. |
| [PyRoboFrames](https://github.com/Mullassery/PyRoboFrames) | Learning data | Rust-backed ML dataloader for robot-learning datasets (native LeRobot format, Apple Silicon hardware video decode). |
| [PyRoboReplay](https://github.com/Mullassery/PyRoboReplay) | Mission forensics | Forensic-debugging and causal-analysis engine for autonomous robot mission replay. |
| [SyncFleet](https://github.com/Mullassery/SyncFleet) | Fleet coordination | Rust + SQLite, peer-to-peer state sync for robotics fleets — mutual-TLS 1.3, version-vector replication, mDNS discovery; conflict resolution on the roadmap. |

Each works standalone, but they're complementary by design. [Browse all projects →](https://github.com/Mullassery?tab=repositories)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
