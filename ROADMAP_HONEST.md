# ROADMAP_HONEST

This is the blunt version of project status. It exists because README.md
and VISION.md necessarily focus on "what this is" — this file exists to
say, without hedging, what's actually done, what's half-done, and what's
broken. Last verified: 2026-09-20, by actually running the test suite,
linters, and security scanners locally (see "How this was verified" at the
bottom), not by reading old docs and trusting them.

## Done and verified

- **Rust-backed core (`pip install pyrobosimulator`)**: `World`, `Agent`,
  `AgentType`, `Mission`, `NarrativeEngine`, `ROS2Bridge`, `StorageEngine`
  are real and importable (`python/pyrobosimulator/__init__.py`).
  `StorageEngine` is a real RocksDB-backed event log
  (`pyrobosimulator-core/src/storage.rs`), not a stub.
  `NarrativeEngine.generate_from_events` honestly raises `NotImplementedError`
  — it isn't implemented, by design, not by accident.
- **MuJoCo physics backend** (`backend/src/simulators/mujoco_backend.py`):
  real `mujoco.MjSpec`/`mujoco.mj_step` integration, verified by
  kinematics-correctness tests (`backend/tests/test_mujoco_backend.py`).
- **Code formatting/linting**: `black --check src/ tests/`,
  `isort --check-only src/ tests/`, and `flake8 src/ tests/
  --max-line-length=100` all pass with 0 issues, re-run directly against the
  pinned tool versions in `backend/pyproject.toml` (2026-09-20). The
  previously-documented 72/134-file black/isort backlog and 27-issue flake8
  backlog are both gone.
- **`bandit -r src/ -ll`**: 0 issues (1 nosec-suppressed finding,
  justified: the app binds `0.0.0.0` inside a container by design).
- **`safety check --ignore 64396 --ignore 64459`**: 0 vulnerabilities
  reported (down from a previously-documented 50). The 2 ignored `ecdsa`
  findings have no patched release upstream.
- **License**: repo-root `LICENSE`, root `pyproject.toml`, and `Cargo.toml`
  all now consistently say Apache-2.0. `backend/pyproject.toml` and
  `backend/README.md` said MIT until this pass — fixed.

## Fixed this pass (2026-09-20)

- `backend/pyproject.toml`: pinned `pytest>=7.4.4,<8`. An unbounded floor
  let a fresh install resolve pytest 9.x (or 8.x), both of which break
  `pytest-asyncio==0.21.1`'s internals (`AttributeError: 'FixtureDef' object
  has no attribute 'unittest'`) — this was silently breaking 33 tests
  (all of `test_api_integration.py`, `test_simulations.py`,
  `test_health.py`, and part of `test_performance.py`) on any environment
  that resolved a recent pytest. Verified fix: 0 such errors with the pin.
- `backend/pyproject.toml` / `backend/README.md`: MIT → Apache-2.0 (see
  above).
- Root `pyproject.toml`: added `[tool.maturin] include = ["LICENSE"]` —
  without it, `maturin sdist` omits `LICENSE`, and PyPI rejects the upload
  with a 400. This is a recurring bug pattern across this maintainer's other
  maturin-based repos.
- `.gitignore`: `Cargo.lock` was ignored (never tracked, despite existing on
  disk with real content). Removed from `.gitignore` and committed. This is
  a published cdylib/binary artifact, not a library consumed by other
  crates, so pinning resolved dependency versions is the right call for
  build reproducibility.
- `.gitignore`: added `.coverage`, `htmlcov/`, `.pytest_cache/`,
  `.mypy_cache/`, `.benchmarks/`, `.deepeval/`. A stray `.coverage` binary
  file had been committed since the "Phase 6" commit; untracked via
  `git rm --cached`.
- `.github/workflows/ci-cd.yaml`: bumped 6 actions off versions GitHub
  Actions has stopped running on newer runner images (setup-python
  v4→v5, codecov-action v3→v4, docker/setup-buildx-action v2→v3,
  google-github-actions/auth v1→v2, google-github-actions/setup-gcloud
  v1→v2, docker/build-push-action v4→v6); quoted `$GITHUB_OUTPUT` per
  shellcheck; added a missing `id: docker_build` on the image-build step
  (the "Image digest" step referenced `steps.docker_build.outputs.digest`,
  which was always empty because no step had that id — a real, if cosmetic,
  bug). `actionlint` is clean after these fixes.
- Added `CODE_OF_CONDUCT.md`, `.github/dependabot.yml` (cargo + pip×2 +
  npm + github-actions ecosystems), this file.
- `SECURITY.md`: removed fabricated "Security Team" framing, committed
  24h/48h/7-day/30-day response SLAs, a version-support table for
  0.1.x/0.2.x (predating the actual 0.11.x release line by a wide margin),
  and "aims to support SOC 2/GDPR/HIPAA/PCI DSS" compliance language — none
  of that reflected a real process or audit. Replaced fake
  `security@pyrobosimulator.ai`/`info@pyrobosimulator.ai` addresses (an
  unowned/unmonitored domain) with GitHub Security Advisories and the
  maintainer's real email.
- README.md: removed "Production-grade" framing from the opening line
  (the honesty-pass content further down explicitly contradicts that
  framing — mypy/test/CI gaps below are not "production-grade"); updated
  every stale metric in Known Issues and Testing & Quality to numbers
  re-verified on 2026-09-20 (test pass/fail counts, coverage %, mypy error
  count, safety/bandit results, flake8 backlog).

## Documented, not fixed — needs a dedicated follow-up session

1. **mypy: 546 errors across 58 files** (`mypy src/`, strict mode). Not
   individually triaged. `continue-on-error: true` in CI
   (`.github/workflows/ci-cd.yaml`), so this doesn't block merges but also
   means the type-check gate has effectively never been enforced. Fixing
   this for real means either turning off `strict = true` in
   `backend/pyproject.toml`'s `[tool.mypy]` (honest, if that's the intent)
   or doing the actual multi-week cleanup — picking neither is the current
   state.
2. **33 failed / 1 error in `backend/tests/`** (re-verified 2026-09-20,
   down from a previously-reported 41 failed/1 error). Representative
   failures: `test_pathfinding.py::TestAStarPathfinder::test_simple_path`,
   `test_agent_memory.py::TestRelationship::test_relationship_strength_enemy`,
   `test_lidar_rain.py::TestLidarIntegration::test_engine_lidar_capture_all_agents`,
   `test_world_streaming.py::TestWorldStreamingService::test_1000_obstacles`.
   Not root-caused individually in this pass — that's real, scoped
   debugging work across sensor/pathfinding/memory/streaming subsystems,
   not a mechanical fix.
3. **`frontend/package.json`'s `lint` script is broken as written.**
   `"lint": "eslint src --ext ts,tsx"` — `eslint` is not in `dependencies`
   or `devDependencies` (only `typescript`/`vite`/`vitest` are), and there
   is no `.eslintrc*` or `eslint.config.*` anywhere under `frontend/`.
   `npm run lint` fails immediately after a clean `npm install`. Fixing
   this properly means picking an ESLint major version + React/TS config,
   which is a real setup decision, not a one-liner — deferred.
4. **`frontend/` has never been audited for JS/TS code quality**, test
   coverage, or correctness in any of the honesty passes to date (this one
   included, for the same reason as #3 — no working lint/build pipeline was
   verified). `frontend/package.json` claims a `test` script
   (`vitest run`) and a `type-check` script (`tsc --noEmit`); neither was
   run as part of this pass. Unverified: assume broken until checked.
5. **CI coverage gap by design, not oversight**:
   `.github/workflows/ci-cd.yaml`'s `on.push.paths`/`on.pull_request.paths`
   only match `backend/**` and the workflow file itself. The Rust workspace
   (`Cargo.toml`, `pyrobosimulator-core/`), the Python bindings
   (`python/pyrobosimulator/`), and all of `frontend/` have **zero** CI —
   no build, no test, no lint — regardless of what changes there. A change
   that breaks the Rust core or the pip-installable package would not be
   caught by this pipeline.
6. **The `build`/`scan`/`deploy-staging`/`smoke-test` jobs in
   `.github/workflows/ci-cd.yaml` are speculative and almost certainly
   non-functional as configured.** They require
   `secrets.WIF_PROVIDER`/`secrets.WIF_SERVICE_ACCOUNT`/`secrets.GCP_PROJECT`
   (Google Cloud Workload Identity) and `secrets.SLACK_WEBHOOK_URL`, which a
   solo-maintainer open-source repo is unlikely to have configured, and
   `smoke-test` curls a literal, never-replaced placeholder domain
   (`https://api-staging.example.com`). Net effect: any push to `main` that
   passes `quality`/`security-audit`/`test` will still fail at `build`,
   which can make the CI/CD status badge read red even when the parts that
   actually matter (lint, security scan, tests) are green. This needs a
   maintainer decision — either wire up real GCP/Slack credentials, or
   delete these four jobs and the GCR/Kubernetes staging-deploy narrative
   they imply — not a guess made on this pass. GitHub Actions `if:` at the
   job level cannot safely branch on whether a secret is set (secrets
   aren't available in that context), so this can't be "auto-detected" —
   it's a real either/or decision.
7. **Backend database/cache are still in-memory** for simulations/users.
   The PostgreSQL/Redis integration implied by the Architecture section of
   the README is partially wired, not fully load-bearing.
8. **Gazebo and Isaac Sim physics backends are unfinished sketches.**
   `initialize()` fails fast with `EnvironmentError` (honest), but nothing
   past that point calls real Gazebo/ROS 2 or Omniverse APIs.
9. **Performance benchmark numbers in README.md's "Performance Benchmarks"
   table are not backed by a committed, reproducible benchmark script** —
   treat every number there (100K+ agents/sec, <500ms P99, etc.) as
   unverified marketing copy until a real `pytest --benchmark-...` report
   is committed and linked.

## Technical debt inventory (file:line specific)

| Item | Location | Severity | Notes |
|---|---|---|---|
| Unbounded `pytest` floor broke 33 tests | `backend/pyproject.toml:77` (pre-fix) | Fixed this pass | See above |
| MIT/Apache license mismatch | `backend/pyproject.toml:11`, `backend/README.md:299` | Fixed this pass | See above |
| Missing sdist LICENSE include | `pyproject.toml` `[tool.maturin]` | Fixed this pass | See above |
| `Cargo.lock` untracked | `.gitignore:3` (pre-fix) | Fixed this pass | See above |
| mypy strict-mode backlog | `backend/` (58 files) | Real, unfixed | 546 errors, `continue-on-error: true` in CI |
| 33 failing backend tests | `backend/tests/*` | Real, unfixed | See failure list above |
| Broken frontend lint script | `frontend/package.json:11` | Real, unfixed | `eslint` not installed, no config |
| Unaudited frontend | `frontend/` (entire tree) | Real, unfixed | No CI, no verified test/build run |
| CI path-scoped to backend only | `.github/workflows/ci-cd.yaml` `on.push.paths`/`on.pull_request.paths` | Real, unfixed | Rust/Python-bindings/frontend uncovered |
| Speculative GCP/Slack deploy pipeline | `.github/workflows/ci-cd.yaml` `build`/`scan`/`deploy-staging`/`smoke-test` jobs | Real, unfixed | Needs maintainer decision, not a guess |
| Fake staging URL | `.github/workflows/ci-cd.yaml` (smoke-test step, `https://api-staging.example.com`) | Real, unfixed | Never replaced with a real value |
| Unbacked performance claims | `README.md` "Performance Benchmarks" table | Real, unfixed | No committed benchmark artifact |
| `NarrativeEngine.generate_from_events` unimplemented | `pyrobosimulator-core/src/` (Rust core) | Documented, by design | Use `backend/src/narratives/narrative_converter.py` instead |
| Gazebo/Isaac Sim backends are stubs past `initialize()` | `backend/src/simulators/gazebo_backend.py`, `isaac_sim_backend.py` | Documented, by design | Real integration blocked on infra access |

## Deliberately skipped in this pass, and why

- **Did not attempt a mass reformat or mass mypy fix.** Formatting is
  already clean (verified); mypy's 546 errors are a multi-week effort best
  done as its own dedicated session with test coverage as a safety net, not
  mixed into a documentation pass.
- **Did not touch `frontend/`'s dependency versions or add an ESLint
  config.** Picking a config is a real design decision (which ESLint major,
  which React/TS ruleset) that deserves its own review, not a
  drive-by default.
- **Did not modify the GCP/Slack deploy jobs beyond safe version bumps.**
  Deciding whether this repo should have a real staging deployment pipeline
  at all is a product/infrastructure decision for the maintainer, not
  something to guess at in a docs-and-hygiene pass.
- **Did not convert `.github/ISSUE_TEMPLATE/*.md` to YAML form.** Both
  `bug_report.md` and `feature_request.md` already exist and are
  functional; GitHub renders classic Markdown issue templates fine, so this
  would be pure churn with no functional benefit.
- **`safety scan`/newer network-dependent tooling**: this sandbox does have
  outbound network access to safety's vulnerability DB (the scan completed
  with a real timestamp), but no attempt was made to reach
  github.com/crates.io/PyPI directly for CI/registry verification — that's
  an environment constraint, not a new finding.

## How this was verified (2026-09-20)

- `black --check src/ tests/`, `isort --check-only src/ tests/`,
  `flake8 src/ tests/ --max-line-length=100` — run directly from `backend/`
  with the pinned tool versions.
- `mypy src/` — run to completion (89 files checked).
- `bandit -r src/ -ll` and `safety check --ignore 64396 --ignore 64459` —
  both run directly.
- `pytest --cov=src --cov-report=term-missing` — run against real
  `postgres:16-alpine` and `redis:7-alpine` Docker containers (matching the
  CI workflow's service containers), both before and after the pytest pin
  fix, to isolate the fixture-breakage bug from pre-existing failures.
- `actionlint .github/workflows/ci-cd.yaml` — clean after the version-bump
  and step-id fixes.
