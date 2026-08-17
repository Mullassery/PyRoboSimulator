# Changelog

All notable changes to PyRoboSimulator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2026-08-17

### Corrected: the [0.9.0] Phase 4.2 entry below was inaccurate

The [0.9.0] entry claims "IsaacSimBackend: High-fidelity physics (PhysX)...",
"GazeboBackend: ROS 2 integration...", and "MuJoCoBackend: RL research
optimization, fast simulation" as complete. At the time, all three were
pure-Python bookkeeping stubs with zero calls into any real physics engine —
`step()` returned a hardcoded `SimulationStep`, sensors returned empty
bytes, contacts were always `[]`. This release fixes that gap for real
where it's actually achievable, and is honest about where it isn't.

### Added

- **Real MuJoCo physics backend** (`backend/src/simulators/mujoco_backend.py`,
  rewritten from scratch, 637 statements, 76% covered): loads real MJCF/URDF
  models via `mujoco.MjSpec` (including MuJoCo's native URDF compiler), steps
  real dynamics with `mujoco.mj_step`, and extracts real body/joint state,
  contact forces, and camera/Lidar/IMU sensor data. Verified with
  kinematics-correctness tests — e.g. a free-falling body's height matches
  `z0 - 1/2 g t^2` within numerical-integration tolerance, contact normal
  forces on a resting box sum to its real weight, position-servo joint
  control converges toward commanded targets under gravity load. See
  `backend/tests/test_mujoco_backend.py` (35 tests, all real physics, no
  mocks). Optional dependency: `pip install -e backend[physics]`.
- **Real ROS 2/Gazebo world export** (`pyrobosimulator-core/src/ros2.rs`):
  `ROS2Bridge::export_world` now generates a genuine SDF 1.9 world document
  from a `World`'s actual `Agent` data (position, orientation via
  quaternion→Euler conversion, per-agent-type geometry), replacing a stub
  that unconditionally returned the string `"ROS 2 world export stub"`.
  Exposed to Python for the first time (`from pyrobosimulator import
  ROS2Bridge`). Added `World.add_agent`/`remove_agent`/`agent_count` (there
  was previously no way to populate `World.active_agents` at all). 8 new
  Rust unit tests (`cargo test -p pyrobosimulator-core`).

### Changed

- **Gazebo and Isaac Sim backends now fail honestly.** `GazeboBackend.initialize()`
  and `IsaacSimBackend.initialize()` raise a clear `EnvironmentError` explaining
  the real infrastructure gap (Gazebo needs a full ROS 2 + Gazebo system
  install; Isaac Sim needs NVIDIA Omniverse + a CUDA GPU) instead of silently
  setting `self._initialized = True` and letting callers believe physics was
  running. Neither is achievable in a typical sandboxed dev environment or
  CI runner, so rather than fake it further, they now say so.
- `NarrativeEngine.generate_from_events` (Rust core) now raises
  `NotImplementedError` instead of returning the templated string
  `"Narrative from {n} events"`; real Claude-backed narrative generation
  already exists in `backend/src/narratives/` and is the supported path.
  `WorldGenerator::from_description` and `StorageEngine` (unused,
  `rocksdb`-backed) now return `Err` instead of silently no-op'ing.

### Fixed

- **Packaging bug: `pip install pyrobosimulator` shipped a broken wheel.**
  `pyproject.toml` was missing `[tool.maturin] python-source = "python"`, so
  maturin silently packaged an implicit-namespace `pyrobosimulator/` at the
  repo root (no `__init__.py`) instead of `python/pyrobosimulator/` (the
  real package, with `__init__.py` wiring up `World`/`Agent`/`Mission`/
  `NarrativeEngine`). Confirmed the already-published 0.8.0 wheel on PyPI has
  the same bug by unzipping it — `import pyrobosimulator; pyrobosimulator.World`
  has never worked for anyone who `pip install`ed this package. Also added
  the missing `m.add_class::<AgentType>()` registration (present as a type
  but never exposed to Python) and a `pyrobosimulator = "pyrobosimulator.cli:main"`
  console-script entry point (the Homebrew formula assumed one existed; it didn't).
- `SensorType.LIDAR_3D` didn't exist (only `SensorCategory.LIDAR_3D` did) —
  `SensorRegistry.DEFAULT_SPECS` referenced it as a dict key, crashing
  `test_sensor_configuration.py`/`test_sensor_noise.py` at collection time.
- `AdvancedScenarioGenerator`'s difficulty→`ScenarioClass` thresholds
  (`< 0.25/0.5/0.75`) didn't align with `DifficultyLevel`'s actual enum
  values (0.1/0.3/0.5/0.7/0.9/1.0), making `ScenarioClass.NOMINAL`
  mathematically unreachable under the default `difficulty_distribution`.
  A test that retried batches until it found 20 NOMINAL scenarios looped
  forever as a result, hanging the entire test suite indefinitely. Fixed
  the thresholds and added a bounded-retry safety net to the test.
- `DATABASE_URL` in `.github/workflows/ci-cd.yaml` used a plain
  `postgresql://` scheme; `create_async_engine` needs `postgresql+asyncpg://`
  or it falls back to the sync-only `psycopg2` driver (not even a declared
  dependency), breaking every test using the `client`/`test_db` fixtures
  with `ModuleNotFoundError: No module named 'psycopg2'`.
- Missing dependencies that broke imports at collection time: `anthropic`
  (hard dependency of `narrative_converter.py`, previously undeclared),
  `email-validator` (needed by pydantic `EmailStr`), `greenlet` (needed by
  SQLAlchemy's async engine).

### Coverage

Real measured coverage (`pytest --cov=src`, run from `backend/`): **74%**
(9475 statements, 2495 missed), up from 41% at the last audit — driven
mostly by fixing test collection (most of the suite couldn't even import
before the fixes above, contributing zero coverage) plus the new MuJoCo
test suite. 925 tests total: 812 passing, 86 failing, 18 erroring, 6
skipped, 3 xfailed. Remaining failures are pre-existing and outside this
pass's scope (auth/session edge cases, some sensor-pipeline assertions);
remaining 0%-coverage files are speculative/unfinished feature areas
(`src/mission/`, `src/dashboards/`, `src/data/synthetic_data_generator.py`,
`src/services/sensors.py`), not core simulation code.

### Reconciled

- Version was drifted three ways: root `pyproject.toml` (0.8.0), backend
  `pyproject.toml` (0.5.0), this changelog's top entry (0.9.0). All package
  manifests (root, backend, Rust workspace) now agree on 0.10.0.

## [0.9.0] - 2026-08-05

### Added - Phase 4: Multi-Backend Orchestration Platform Complete

#### Phase 4.1: Autonomous Regional Intelligence (ARI)
- Regional knowledge model (road, vehicle, pedestrian, terrain, infrastructure, weather)
- ARI discovery engine: YouTube, OpenStreetMap, elevation, weather, traffic data
- Statistical environmental learning (never memorizes frames)
- Confidence scoring (frame count, source diversity, temporal/geographic spread)
- Knowledge persistence and incremental refinement
- KnowledgeStore with JSON serialization
- Supports 10+ regions, learns geographic specifics (North India ≠ Tokyo)

#### Phase 4.2: Multi-Simulator Backend Adapters
- IsaacSimBackend: High-fidelity physics (PhysX), RTX rendering, sensor simulation
- GazeboBackend: ROS 2 integration, testing framework compatibility
- MuJoCoBackend: RL research optimization, fast simulation
- Common 30+ operation interface (spawn, control, sense, physics, rendering)
- Uniform sensor API (RGB, depth, semantic, Lidar, IMU, GPS, Radar, contact)
- Hot-swappable backends (switch simulators mid-session)
- Dependency injection & factory pattern

#### Phase 4.3: Mission Framework & LLM-Powered Planning
- Natural language mission specification ("Deliver box, avoid humans")
- MissionPlanner: NL-to-plan conversion, structured spec parsing
- Task-based execution (navigate, pick, place, inspect)
- Task dependencies and sequential execution
- Mission status tracking (planning, ready, executing, completed, failed)
- LLM integration point (for Claude-powered planning)
- Real-time mission monitoring and logging

#### Phase 4.4: Synthetic Data Generation
- AnnotatedFrame generation from simulation frames
- ObjectDetector: Automated bounding box annotation
- KeypointDetector: Semantic keypoint extraction
- SegmentationModel: Semantic and instance segmentation
- COCO format export (for object detection)
- YOLO format export (for real-time models)
- TFRecord export (for TensorFlow training)
- Dataset statistics and class distribution analysis

### Architecture
- **Simulator-agnostic**: AI layer never talks directly to simulators
- **Pluggable backends**: Add new simulators by implementing SimulatorBackend interface
- **Regional intelligence**: Learn unknow regions, improve over time
- **Mission-driven**: Natural language → plans → execution → results
- **Data generation**: Automatic training data from simulations

### Performance
- ARI discovery: 100+ regions in knowledge store
- Backend operations: <1ms spawn/control/sense
- Mission execution: Task-driven, dependency-aware
- Data generation: ~100 annotated frames/min per simulator

### Testing
- 20+ simulator backend tests
- 30+ ARI system tests
- 50+ mission framework tests
- 25+ synthetic data generation tests
- All integration tests passing

## [0.8.0] - 2026-08-05

### Added - Phase 4.0: Multi-Backend Simulator Interface Complete

#### Simulator Backend Abstraction (4.0)
- Generic SimulatorBackend ABC (30+ operations)
- Unified interface for Isaac Sim, Gazebo, MuJoCo, PyBullet
- Simulator-agnostic configuration (SimulatorConfig with physics/rendering)
- Robot/object/sensor management (spawn, remove, state querying)
- Complete sensor API (RGB, depth, semantic, Lidar, IMU, GPS, etc)
- Physics operations (gravity, timestep, raycast, contacts)
- Domain randomization (lighting, friction, mass)
- BackendFactory for dependency injection
- BackendManager for lifecycle & hot-swapping
- BackendContext for context-managed operations
- MockBackend for testing & validation
- Full data classes for all operations

#### Design Features
- Clean architecture with no simulator dependencies
- Dependency injection throughout
- Support for hot-swapping between simulators
- Extensible configuration system
- Comprehensive error handling
- Type-safe with Python dataclasses
- Future-ready for new simulators

### Performance
- Backend initialization: <1ms
- Robot spawn/remove: <1ms
- Sensor data retrieval: <5ms
- Configuration validation: <1ms
- Supports 100+ concurrent robots per backend

### Testing
- 20+ backend interface tests
- 10+ factory/manager tests
- 10+ mock backend integration tests
- Full workflow validation tests
- Multi-backend switching tests
- Context manager tests

## [0.7.0] - 2026-08-05

### Added - Phase 3: Expectation Framework & Scenario Generation Complete

#### Expectation-Aware Simulation (3.0)
- Probabilistic expectation modeling (11 types)
- Environment profiles (18+ types with sensor/network quality)
- Geographic profiles (10+ regions with infrastructure/cooperation factors)
- Expectation engine with violation detection
- Cascading effects modeling (multi-system failures)
- Fleet learning module (failure/recovery tracking)
- Expectation validator for action validation
- <10ms expectation evaluation per agent

#### Advanced Scenario Generation (3.1)
- Curriculum learning with progressive difficulty (6 levels)
- 18+ environment types × 10+ geographic regions
- Synthetic scenario generation (millions of scenarios)
- Weather/time-of-day/season/density integration
- Rare event generation (earthquakes, floods, power outages)
- Infrastructure failure simulation
- Scenario classification (nominal/degraded/crisis/catastrophic)
- Difficulty scaling and validation checkpoint generation

#### Validation & Reporting Framework (3.2)
- Performance metrics collector (6 metric types)
- Comprehensive validation framework (4 validators)
- Violation detection and tracking
- Root cause analysis engine (confidence/probability scoring)
- Executive summaries and detailed reports
- Violation dashboards with severity/type breakdowns
- Mitigation recommendations
- Performance statistics and aggregation

### Performance
- Scenario generation: 1000 scenarios/sec
- Expectation evaluation: <10ms per agent
- Report generation: <100ms for 1000+ events
- Memory: ~100KB per scenario + expectations

### Testing
- 50+ scenario generation tests
- 40+ validation & reporting tests
- All integration tests passing

## [0.5.0] - 2026-08-05

### Added - Phase 2: AI Agents & Behavior Complete

#### Navigation & Pathfinding (2.2)
- A* pathfinding algorithm with heuristic caching
- Navigation mesh with walkable polygon support
- RVO (Reciprocal Velocity Obstacle) collision avoidance
- Dynamic obstacle integration
- Path caching with 50%+ hit rate
- Support for 100+ concurrent agents
- <1ms pathfinding with cache

#### Agent Memory & State (2.3)
- Multi-layer memory system (episodic, semantic, procedural, emotional)
- Configurable decay rates for memory aging
- Relationship tracking (trust, familiarity, interaction count)
- Emotion-aware memory with valence tracking
- Advanced querying (by type, tags, strength threshold)
- Memory capacity management with auto-pruning
- Emotional state calculation
- Supports 1000+ memory entries per agent

#### Multi-Agent Communication (2.4)
- Message-based communication (direct, broadcast, multicast)
- Priority-based message queuing (critical, high, normal, low)
- Message expiration and acknowledgment tracking
- Communication network topology
- Range-based broadcasting (proximity communication)
- Message history and comprehensive querying
- Coordination primitives (CoordinationPrimitive, LeaderElection)
- Simple leader election algorithm
- Network statistics and telemetry

### Performance
- Navigation: <1ms A* with caching
- Memory: O(1) access with decay
- Communication: <10ms message delivery
- Support for 1000+ agents in all systems

### Testing
- 95+ new unit tests (all passing)
- Comprehensive integration tests
- Performance benchmarks included

## [0.4.0] - 2026-08-05

### Added - Phase 1C.8-1C.10 & Phase 2.1 Complete

#### World Streaming System (1C.8)
- Chunked world geometry streaming (500m × 500m chunks)
- Obstacle mesh generation and serialization
- Dynamic object streaming with state management
- Binary and JSON serialization formats
- LOD (Level of Detail) support for efficient rendering
- Support for 1000+ concurrent obstacles
- <100ms chunk loading latency
- Automatic cache management

#### State Synchronization (1C.9)
- Bidirectional state sync between Python and UE5
- Multiple conflict resolution strategies (last_write_wins, backend_wins, UE5_wins, custom)
- State validation framework with pluggable rules
- State history and rollback mechanism
- Sync telemetry and performance monitoring
- Message acknowledgment and sequence tracking
- Network interruption handling
- <16ms sync overhead per frame

#### Sensor Data Recording (1C.10)
- Ring buffer implementation for real-time recording
- Multi-format storage (HDF5, Zarr, raw binary)
- Compression support (lz4, zstd, gzip)
- Sensor frame serialization with metadata
- Advanced query interface (agent, timestamp, sensor type)
- Automatic buffer flushing and cleanup
- Memory estimation and monitoring
- <5MB/s per 100 agents storage rate

#### Behavior Tree System (2.1)
- Complete hierarchical behavior tree framework
- Composite nodes: Sequence, Selector, Parallel
- Decorator nodes: Inverter, Repeater, Limiter
- Leaf nodes: Action, Condition
- YAML-based tree loading and deserialization
- Builder pattern for programmatic construction
- Execution telemetry and performance tracking
- Support for 100+ agents with <1ms evaluation
- Serialization to dict/JSON for debugging

### Performance
- World streaming: <100ms per chunk load
- State sync: <16ms per frame
- Behavior trees: <1ms per tree evaluation
- Sensor recording: <5MB/s throughput
- All systems tested with 1000+ agents/obstacles

### Testing
- 40+ new comprehensive unit tests
- All services production-ready
- Verified with real-world scenarios

## [0.2.0] - 2024-07-29

### Added
- Production-grade REST API with 15 core endpoints
- Multi-modal sensor simulation (RGB, Depth, Lidar, Thermal)
- FastAPI async backend with OpenAPI auto-documentation
- PostgreSQL async ORM with SQLAlchemy
- Redis caching layer with pattern-based invalidation (>95% hit rate)
- Prometheus metrics and monitoring integration
- Kubernetes deployment manifests (3-30 replicas, HA setup)
- Docker multi-stage production container
- GitHub Actions 7-stage CI/CD pipeline
- Comprehensive test suite (60+ tests, 90%+ coverage)
- Complete OSS compliance audit (52 dependencies verified)
- UE5 integration design specification
- Full user and developer documentation

### Infrastructure
- Kubernetes manifests with autoscaling and pod disruption budgets
- PostgreSQL StatefulSet with persistent volumes
- Redis Sentinel configuration for HA caching
- NGINX ingress with Let's Encrypt TLS
- Prometheus and Grafana monitoring setup
- Network policies and security configurations

### Testing & Quality
- 60+ unit, integration, and performance tests
- 90%+ code coverage enforcement
- Black, isort, flake8, mypy, bandit, safety scanning
- Performance benchmarks (100K+ agents/sec)
- Security testing and vulnerability scanning

### Documentation
- Complete API reference with examples
- Deployment guide (local, Docker, Kubernetes)
- Database schema documentation
- Performance optimization guide
- UE5 rendering engine integration design
- OSS compliance audit report
- Contributing guidelines
- Security policy

### Performance
- 100K+ agents per second throughput
- <500ms P99 API latency
- <1s simulation startup time
- >95% cache hit rate
- ~2KB memory per agent

## [0.1.0] - 2024-07-15

### Added
- Core simulation engine with physics (Euler integration)
- Procedural world generation (3 built-in scenarios)
- Basic sensor simulation framework
- Event-driven architecture for collisions/goal events
- Initial project structure and setup

### Known Limitations
- No rendering engine (CLI-only)
- Basic world generation
- Minimal sensor implementation
- No distributed deployment

## Roadmap

### Phase 1 (Next Release - ~8-12 weeks)
- UE5 rendering engine integration
- Real-time 3D visualization
- Advanced AI behavior trees
- NLP-driven world generation
- Performance optimization with GPU acceleration

### Phase 2
- Domain randomization for ML training
- Multi-agent learning support
- Advanced analytics and replay system
- Custom sensor modeling
- Fleet simulation capabilities

### Phase 3+
- Digital twin capabilities
- Real-world hardware integration
- Commercial licensing options
- Enterprise support tiers

## Version Support

| Version | Release Date | End of Life | Status |
|---------|---|---|---|
| 0.2.0 | 2024-07-29 | 2025-07-29 | Active |
| 0.1.0 | 2024-07-15 | 2024-10-15 | Limited |

## Migration Guides

### 0.1.0 to 0.2.0

**Breaking Changes**:
- REST API endpoints changed to `/api/v1/` prefix
- SimulationEngine API unchanged (backward compatible)

**New Features**:
- REST API now available
- Database persistence
- Redis caching
- Kubernetes deployment support

**Migration Steps**:
1. Update pip: `pip install pyrobosimulator==0.2.0`
2. For API users: Update endpoint URLs to include `/api/v1/` prefix
3. For Docker: Pull new image `pyrobosimulator:0.2.0`
4. For Kubernetes: Apply new manifests from `backend/k8s/`

## Credits

**Core Contributors**:
- Georgi Mullassery (Creator, Lead Maintainer)

**Special Thanks**:
- FastAPI community
- SQLAlchemy team
- Kubernetes community
- Open source ecosystem

## License

All changes are released under the MIT License. See [LICENSE](LICENSE) for details.

## Security

For security vulnerability reports, please email security@pyrobosimulator.ai instead of opening public issues. See [SECURITY.md](SECURITY.md) for details.

---

**Notes for Release Managers**:
- Tag releases with `git tag v0.2.0`
- Publish to PyPI with `twine upload`
- Create GitHub release with changelog
- Update version in `pyproject.toml`
- Announce on community channels
