# Competitive intelligence in roadmap and upgrade work

**Policy date:** 2026-10-19

Competitive findings are an input to product decisions, not a one-off report.
Every pending roadmap item, new feature, and routine dependency upgrade should
check the repository's [`AUDIT_FINDINGS.md`](AUDIT_FINDINGS.md) before work
starts, and record the decision in the PR or changelog.

## Required check before building

1. **Read `AUDIT_FINDINGS.md`.** Find the relevant competitor row and the
   ranked next actions. If the finding is stale, update it with a dated source.
2. **Name the competitor and the user problem.** A feature is not justified by
   "competitor has it". State the workflow it unlocks, who needs it, and how
   often. Mark unverified demand as a hypothesis.
3. **Prefer reuse over new code.** Check whether an existing Mullassery repo
   already provides the capability (see `BUNDLES.md` in the profile repo and
   the bundle role file in this repo, when present). Typical reuse:
   - crawling/fetching/robots/SSRF → **MudFish**
   - architecture maps / PR diffs → **CodeAtlas**
   - data-quality contracts / validation → **StatGuardian**
   - token counting / cost tables → **PyTokenCalc**
   - dependency graph / advisories / SBOM → **PyDeepMesh**
   - segmentation / CLV / churn → **ClusterAudienceKit**
   - activation / lineage / PII → **PyReverseETL**
   - fleet state sync → **SyncFleet** (only after conflict resolution)
4. **Choose one disposition:** build, integrate, defer, or reject. Write it
   down. A rejection with a reason is a successful outcome.
5. **For routine upgrades**, check whether the upgrade closes a known
   competitor gap or breaks a differentiated capability. Run the tests that
   cover the affected path; do not merge a green build that silently changes a
   user-visible contract.

## PR / changelog checklist

- [ ] Competitor and source URL/date recorded (or "no direct competitor").
- [ ] User impact and frequency stated; unverified demand labelled.
- [ ] Reuse check done against sibling repos/bundles.
- [ ] Failure mode and rollback considered (especially auth, PII, cost).
- [ ] Docs/roadmap status updated honestly.
- [ ] Tests or a manual verification command included.

## Review cadence

- Refresh the competitor row when a release changes the capability.
- Re-check the full `AUDIT_FINDINGS.md` at least quarterly and before a major
  release.
- If a finding is wrong or stale, correct it in the same PR that relies on it.

## Non-goals

- Copying features for parity.
- Adding a dependency just because a competitor uses it.
- Treating star counts or download counts as proof of user need.

## OSS gap analysis — 2026-10-24

**What matters most here:** packaging and test health before fidelity. `pip install` excludes `SimulationEngine`, backend tests fail, and CI is missing; fix distribution and the suite before chasing Gazebo/Isaac-grade physics.

Scope: PyRoboSimulator 0.12.5 (Rust/PyO3 core + FastAPI backend, Apache-2.0). Implemented per README, ROADMAP_HONEST, AUDIT_FINDINGS, Cargo.toml and pyproject.toml: pip Rust core (`World`, `Agent`, `StorageEngine`) with gravity, forward-Euler integration, O(n²) pairwise collision detection and a RocksDB event log; FastAPI service with scenario generation, AABB collision, behavior trees, A*/RVO, multi-layer memory and messaging; procedural RGB/depth/LiDAR/thermal streams; real MuJoCo backend; seeded domain randomization; Gymnasium/PettingZoo adapters; REST/SSE with JWT. Not shipped/working: `SimulationEngine`/`ScenarioBuilder` in the wheel, Gazebo and Isaac Sim backends (fail-fast stubs), SANA-WM, photoreal rendering, GPU-parallel scaling, persistent Postgres/Redis, a reproducible benchmark. Alpha; backend suite has known failures.

### Comparable OSS projects
| Project | GitHub | License | Last activity | Why it is the comparison |
|---|---|---|---|---|
| Gazebo (gz-sim) | https://github.com/gazebosim/gz-sim | Apache-2.0 | Pushed 2026-10-23 | The reference open-source multi-robot simulator: mature physics plugins, ray-based sensors, world files and first-class ROS 2 integration. The default users compare a robot world simulator against. |
| Webots | https://github.com/cyberbotics/webots | Apache-2.0 | Pushed 2026-10-24 (develop) | Cross-platform robot simulator with cameras, lidars, range-finders, physics and ROS 2 support; the closest "batteries-included, sensor-rich, Python-controllable" alternative. |
| Isaac Lab | https://github.com/isaac-sim/IsaacLab | BSD-3-Clause | Pushed 2026-10-24 | GPU-parallel robot-learning simulator built on Isaac Sim/PhysX; the benchmark for thousands of parallel environments and RTX sensor simulation, which we do not offer. |

### Capability comparison
| Capability | Ours | Gazebo | Webots | Isaac Lab | Gap |
|---|---|---|---|---|---|
| Multi-robot / multi-agent worlds | Yes | Yes | Yes | Yes | Parity at the feature level |
| Physics fidelity (contacts, joints, friction) | Partial | Yes | Yes | Yes | Weaker: core is gravity + Euler + AABB; real dynamics only via MuJoCo |
| Sensor simulation (RGB/depth/LiDAR/thermal) | Partial | Yes | Yes | Partial | Weaker: streams are procedural/mock, not ray-traced |
| Synthetic thermal camera | Yes | No | No | No | Ahead: unique among the three |
| Photorealistic rendering | No | Partial | Partial | Yes | Absent: Isaac Lab/Isaac Sim owns RTX rendering |
| ROS 2 integration | Partial | Yes | Yes | Partial | Weaker/unverified: `ROS2Bridge` exists, no mature bridge evidence |
| Python-native pip core | Yes | No | Partial | Yes | Ahead of Gazebo/Webots on packaging ergonomics |
| REST/SSE service + JWT auth | Yes | No | No | No | Ahead: unique service surface |
| Procedural scenario generation | Yes | No | No | Partial | Ahead: built-in parking/warehouse/urban generators |
| RL adapters (Gymnasium/PettingZoo) | Yes | Partial | Partial | Yes | Parity |
| GPU-parallel environments | No | No | No | Yes | Absent: CPU-first; 100K claim unverified |
| Deterministic seeding / domain randomization | Partial | Partial | Partial | Yes | Weaker: seeded draws only; bit-exact not verified |
| Multi-agent behavior (BT/A*/RVO) | Yes | Partial | Partial | No | Ahead: built-in behavior/memory/messaging stack |
| Persistence (RocksDB / Postgres / Redis) | Partial | Partial | Partial | Partial | Mixed: RocksDB real; Postgres/Redis partially wired |
| Maturity / green test suite | No | Yes | Yes | Yes | Weaker: alpha, 5 known backend failures |

### Gaps that matter (ranked)
1. **Physics and sensor fidelity are weaker, not absent.** The pip core is gravity plus forward-Euler with AABB/O(n²) collision (README "Features"); real contacts/joints only appear through the MuJoCo backend, and RGB/depth/LiDAR/thermal streams are explicitly "procedural/mock, not photorealistic". Gazebo and Webots ship mature contact physics and ray sensors; Isaac Lab adds RTX sensors. This blocks sim-to-real perception work. Effort: L.
2. **Packaging and test health undermine trust.** `pip install pyrobosimulator` does not include `SimulationEngine`/`ScenarioBuilder` (README "Two pieces"), ROADMAP_HONEST reports 5 real backend test failures and no CI over the Rust core or frontend, and AUDIT_FINDINGS says to invest only after packaging/test health. Users cannot reproduce the advertised service from the package. Effort: M-L.
3. **No GPU-parallel scale or reproducible benchmark.** README calls the 100K-agent figure "unverified"; ROADMAP and AUDIT_FINDINGS both note the absent committed benchmark. Isaac Lab is the reference for thousands of parallel environments. Without numbers, the multi-agent scalability pitch is unsubstantiated. Effort: L.
4. **ROS 2 integration is thin and unverified.** A Rust `ROS2Bridge` is listed, but the README's integration evidence is adapter/scaffold language while Gazebo (`ros_gz`) and Webots have mature ROS 2 bridges. Teams already standardized on ROS 2 must treat this as partial. Effort: M.
5. **Gazebo and Isaac Sim backends are fail-fast stubs despite being headline-adjacent.** README "NVIDIA ecosystem" and AUDIT_FINDINGS confirm `initialize()` raises `EnvironmentError`; only MuJoCo works. The repo is honest about this, but the capability is absent and users expecting Unreal/Omniverse rendering must look elsewhere. Effort: L.
6. **Photorealistic perception data is absent.** Procedural sensors cannot train vision models for real deployment; Isaac Lab/Isaac Sim and, to a lesser degree, Gazebo/Webots provide rendered sensor data. Effort: L or integrate an external renderer.

### Where we are differentiated
- **Service-first simulation.** A REST/SSE API with JWT auth, simulation CRUD, status/results and streaming is unique among the comparables and suits parallel experiment orchestration from a laptop.
- **Synthetic thermal sensing.** RGB+thermal (plus depth and LiDAR) per-agent streams are not a first-class feature in Gazebo, Webots or Isaac Lab.
- **Scenario generation built in.** Parking-lot, warehouse and urban-street generators with seeds make large randomized experiment batches cheap, without authoring world files.
- **Multi-agent behavior stack.** Behavior trees, A*/NavMesh with RVO avoidance, multi-layer memory and messaging ship in the backend; engine-centric simulators leave this to plugins or user code.
- **Rust core with a durable event log.** RocksDB-backed append-only storage keyed by world id is an unusual, useful primitive for replay and audit.
- **Deterministic seeded randomization** across lighting, friction, mass and mock sensors with one seed is a clean reproducibility story, even if bit-exact MuJoCo is unverified.

### Disposition
- **Build:** ship `SimulationEngine`/`ScenarioBuilder` in the wheel; fix the 5 known failing tests and add CI for the Rust core; publish a reproducible multi-agent benchmark with hardware/method; finish Postgres/Redis persistence.
- **Integrate/reuse:** keep MuJoCo as the physics backend; use `ros_gz`/Gazebo or Webots adapters for ray-traced sensors and ROS 2 rather than reimplementing rendering; use Isaac Lab for GPU-parallel RL instead of building a GPU engine; reuse existing scenario/RL adapters.
- **Defer/reject:** Gazebo/Isaac Sim as near-term first-party backends (already rejected; adapter is the honest path); photoreal rendering and SANA-WM until user evidence; unverified 100K-agent and "production-grade" claims.

### Sources
- https://github.com/gazebosim/gz-sim (accessed 2026-10-24) — Apache-2.0, last commit 2026-10-23, multi-robot physics/sensors and ROS 2.
- https://github.com/cyberbotics/webots (accessed 2026-10-24) — Apache-2.0, develop branch last commit 2026-10-24, cameras/lidar/physics and ROS 2.
- https://github.com/isaac-sim/IsaacLab (accessed 2026-10-24) — BSD-3-Clause, last commit 2026-10-24, GPU-parallel RL and RTX sensors.
- Repo files inspected: `README.md`, `COMPETITIVE_INTELLIGENCE.md`, `AUDIT_FINDINGS.md`, `ROADMAP_HONEST.md`, `QUEUE_STATUS.md`, `backend/README.md`, `Cargo.toml`, `pyproject.toml`.
