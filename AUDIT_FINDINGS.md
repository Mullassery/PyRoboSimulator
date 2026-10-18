# Audit findings — 2026-10-19

This file records the repository-specific findings from the portfolio audit
conducted on 2026-10-19. It is documentation only; no code or release artifacts
were changed in this pass unless explicitly noted under "Implementation status".

Sources: the repository's own README/source/workflows, GitHub metadata and
Actions runs, PyPI metadata, and official competitor documentation. Claims are
marked as verified, inferred, or open questions. "Absent" means not found in the
inspected repository/docs, not proof that it cannot exist.

## What it is

Multi-agent world simulation engine for robotics/agents: Rust core, FastAPI service, realistic sensors, MuJoCo physics, and ROS 2 integration.

## Verified strengths

- Rust World/Agent/StorageEngine; gravity/integration/collision; RocksDB; MuJoCo backend; RGB/depth/LiDAR/thermal; scenarios; REST/JWT/SSE; behavior trees/A*/RVO; 54 test files; ~882 passing.
- Pip-installable core + REST + real MuJoCo is a usable combination.

## Verified gaps and user-facing risks

- `pip install pyrobosimulator` does not include `SimulationEngine`/`ScenarioBuilder`; those are backend-only.
- Gazebo/Isaac stubs; 33 failing + 1 erroring tests; in-memory DB/cache; no committed benchmark; macOS arm64 wheel.
- Alpha; no production evidence.

## Direct competitors

- Gazebo (16 years), Isaac Lab (GPU), MuJoCo, PyBullet/Webots.

## Ranked next actions

- P1: ship the core in the wheel + fix failing tests + publish a benchmark (L).
- P2: persist Postgres/Redis fully (M).

## Do not build

- Gazebo/Isaac integration; too costly and already covered.

## Evidence gaps / validation needed

- No reproducible benchmark; 33 failures may hide real defects.

## Recommended disposition

Invest only after packaging/test health; otherwise freeze.

## Implementation status

No code changes in this pass.
