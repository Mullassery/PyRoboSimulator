# Audit findings — 2026-10-26

This file records the current portfolio-audit findings for pyrobosimulator. It
is documentation only; no code or release artifacts were changed. The fuller
evidence report is kept in the portfolio workspace at
`.audit/reports/pyrobosimulator/audit.md`.

## What it is

An alpha multi-agent robotics simulator split into a pip-installable Rust/PyO3
core (`World`, `Agent`, `StorageEngine`, ROS 2 bridge) and a larger FastAPI
simulation service with procedural scenarios, synthetic sensors, REST/SSE, and
pluggable physics.

## Verified strengths

- Rust core has real gravity, forward-Euler stepping, collision detection, and
  a RocksDB append-only event log.
- Backend has a real MuJoCo path, procedural scenario builder, synthetic
  RGB/depth/LiDAR/thermal sensors, REST/SSE/WebSocket surfaces, JWT auth,
  ownership-scoped simulations, and Prometheus health/metrics.
- `SECRET_KEY` rejects known weak defaults at startup.
- Gazebo/Isaac Sim fail fast instead of pretending to work.
- Backend suite: 47 test files and 952 static test definitions.

## Verified gaps and user-facing risks

- **Packaging mismatch:** the pip wheel ships the small Rust core only.
  `SimulationEngine`, `ScenarioBuilder`, sensors, MuJoCo, and the REST service
  are backend-only.
- **In-memory state:** `simulations_db` and `users_db` are module-level
  dictionaries with TODO markers. Restart loses data; multiple workers are not
  consistent.
- **CI scope:** the workflow only covers `backend/**`; Rust core, Python
  package, and frontend regressions can merge untested.
- **Test health is contradictory:** README cites 33 failures; the roadmap cites
  5. Neither is reconciled with a current full-suite run.
- **Quality debt:** 546 strict mypy errors are non-gating; frontend has no
  working lint pipeline.
- **Version drift:** package `0.12.5`; FastAPI app reports `0.1.0`.
- **Unbacked performance claims:** no committed reproducible benchmark.
- **Determinism:** unseeded synthetic LiDAR randomness breaks deterministic-mode
  tests.
- **Deploy pipeline:** GCP/Slack secrets and placeholder URLs imply a deployment
  path that is not verified.
- **Platform:** PyPI wheel is macOS arm64 only.

## Direct positioning

Against Gazebo, Isaac Lab, MuJoCo, PyBullet, and Webots. The usable combination
is Rust-core plus REST service plus real MuJoCo, but only if the backend ships
and test health is restored.

## Ranked next actions

1. P0: make persistence real (Postgres/Redis) or explicitly label the service
   as ephemeral and single-worker.
2. P0: run and reconcile the full test suite; publish one current result.
3. P0: expand CI to Rust, Python package, backend, and frontend.
4. P1: ship the simulation engine in the wheel, or clearly split the pip
   package from the backend product.
5. P1: burn down mypy errors and restore frontend lint/build.
6. P1: publish a reproducible benchmark and remove unverified performance
   claims.
7. P2: remove or disable the speculative deploy pipeline until it works.
8. P2: align version numbers across package and API.

## Do not build

- Gazebo/Isaac Sim parity, photorealistic rendering, or a production fleet
  controller. Integrate existing stacks rather than reimplementing them.

## Evidence gaps / validation needed

- No reproducible benchmark.
- No multi-worker or restart-recovery test.
- No end-to-end frontend build validation.
- No production deployment evidence.

## Recommended disposition

Invest only after packaging and test health are fixed. Until then, treat the
Rust core as the reliable artifact and the backend as an alpha service.
