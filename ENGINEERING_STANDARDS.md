# Engineering Standards & Best Practices

## Executive Summary

Company-wide engineering standards for code quality, testing, documentation, performance, and security. These standards ensure consistent, maintainable, scalable code across all teams.

**Coverage:**
- Python code style & conventions
- Testing standards (unit, integration, e2e)
- Documentation requirements
- Performance benchmarks & profiling
- Security checklist
- Code review process
- CI/CD best practices

---

## Part 1: Python Code Standards

### Style Guide

**Follow PEP 8 with these additional rules:**

```python
# 1. Line length: 100 characters (not 80)
this_is_a_long_function_name_with_many_parameters(
    param1, param2, param3, param4, param5
)

# 2. Type hints: Required on all functions
async def create_simulation(
    name: str,
    agents: int,
    duration: float,
) -> Simulation:
    """Create a new simulation."""
    pass

# 3. Docstrings: Google-style, concise
class Agent:
    """Represents a single agent in simulation.
    
    Attributes:
        id: Unique agent identifier
        position: (x, y, z) coordinate
        velocity: Movement vector
    """
    
    def move(self, direction: tuple[float, float, float]) -> None:
        """Move agent in direction.
        
        Args:
            direction: (dx, dy, dz) movement vector
        """
        pass

# 4. Naming conventions
GLOBAL_CONSTANT = 100  # UPPER_SNAKE_CASE
_private_var = 42      # _leading_underscore for internal
public_var = "ok"      # lowercase_snake_case

# 5. Imports: Organized in groups
# Standard library
import asyncio
import json
from typing import Optional

# Third-party
import numpy as np
from fastapi import FastAPI

# Local
from .models import Simulation
from .db import get_database

# 6. Class structure
class Simulation:
    """Main simulation class."""
    
    # Class variables
    MAX_AGENTS = 1_000_000
    
    def __init__(self, name: str):
        # Instance variables
        self.name = name
        self._agents = []
    
    def add_agent(self, agent: Agent) -> None:
        """Public method."""
        self._agents.append(agent)
    
    def _internal_helper(self) -> None:
        """Private method (leading underscore)."""
        pass
```

### Code Quality Tools

```yaml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 100

[tool.pylint]
max-line-length = 100
disable = ["too-many-arguments", "duplicate-code"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_unused_ignores = true

[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=html --cov-report=term"
testpaths = ["tests"]
```

**Pre-commit hooks:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

---

## Part 2: Testing Standards

### Test Coverage Requirements

```
Minimum coverage: 85% (target: 95%)

By tier:
- Core libraries: 95%+
- APIs: 90%+
- Business logic: 85%+
- Integrations: 80%+
- Utilities: 75%+
```

### Unit Testing

```python
import pytest
from unittest.mock import MagicMock, patch

class TestSimulation:
    """Unit tests for Simulation class."""
    
    @pytest.fixture
    def simulation(self):
        """Create test simulation."""
        return Simulation(name="test")
    
    def test_add_agent(self, simulation):
        """Test adding agent to simulation."""
        agent = Agent(id=1)
        simulation.add_agent(agent)
        
        assert len(simulation.agents) == 1
        assert simulation.agents[0].id == 1
    
    def test_add_agent_exceeds_limit(self, simulation):
        """Test max agent enforcement."""
        for i in range(Simulation.MAX_AGENTS + 1):
            with pytest.raises(SimulationFull):
                simulation.add_agent(Agent(id=i))
    
    @patch('src.db.get_agent')
    def test_load_agent_from_db(self, mock_get):
        """Test loading agent with mock DB."""
        mock_get.return_value = Agent(id=1)
        
        agent = load_agent_from_db(1)
        
        assert agent.id == 1
        mock_get.assert_called_once_with(1)
    
    @pytest.mark.parametrize("agents,expected", [
        (10, 10),
        (1000, 1000),
        (0, 0),
    ])
    def test_agent_count(self, simulation, agents, expected):
        """Parameterized test."""
        for i in range(agents):
            simulation.add_agent(Agent(id=i))
        
        assert len(simulation.agents) == expected
```

### Integration Testing

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

class TestDatabaseIntegration:
    """Integration tests with real database."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        session = Session(engine)
        yield session
        session.close()
    
    async def test_create_and_fetch_simulation(self, db_session):
        """Test creating and retrieving simulation."""
        # Create
        sim = Simulation(name="integration_test")
        db_session.add(sim)
        db_session.commit()
        
        # Fetch
        fetched = db_session.query(Simulation).filter_by(
            name="integration_test"
        ).first()
        
        assert fetched is not None
        assert fetched.name == "integration_test"
    
    async def test_concurrent_simulation_creation(self, db_session):
        """Test concurrent creates don't conflict."""
        # Create 100 simulations concurrently
        tasks = [
            create_simulation_async(f"sim_{i}")
            for i in range(100)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 100
        assert all(r.status == "created" for r in results)
```

### End-to-End Testing

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestSimulationAPI:
    """E2E tests for simulation API."""
    
    @pytest.fixture
    async def client(self):
        """Create async test client."""
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_create_simulation_e2e(self, client):
        """Test full simulation creation flow."""
        # 1. Create simulation
        response = await client.post("/simulations", json={
            "name": "test_scenario",
            "agents": 100,
            "duration": 60,
        })
        
        assert response.status_code == 201
        sim_id = response.json()["id"]
        
        # 2. Verify creation
        response = await client.get(f"/simulations/{sim_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "created"
        
        # 3. Start simulation
        response = await client.post(f"/simulations/{sim_id}/start")
        assert response.status_code == 202
        
        # 4. Poll for completion
        for _ in range(60):  # 60 second timeout
            response = await client.get(f"/simulations/{sim_id}")
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # 5. Fetch results
        response = await client.get(f"/simulations/{sim_id}/results")
        assert response.status_code == 200
        assert "events" in response.json()
```

### Performance Testing

```python
import pytest
import time

class TestSimulationPerformance:
    """Performance benchmarks for critical paths."""
    
    def test_agent_update_latency(self, benchmark):
        """Benchmark agent physics update (target: < 10µs per agent)."""
        agent = Agent(id=1)
        
        result = benchmark(agent.update_physics, dt=0.016)
        
        assert result is not None
        # Benchmark runs multiple times, tracks latency automatically
    
    @pytest.mark.benchmark(group="database")
    def test_query_simulation_list(self, benchmark, db_session):
        """Benchmark simulation list query (target: < 100ms)."""
        # Create 1000 simulations
        for i in range(1000):
            db_session.add(Simulation(name=f"sim_{i}"))
        db_session.commit()
        
        def query():
            return db_session.query(Simulation).limit(100).all()
        
        result = benchmark(query)
        
        assert len(result) == 100
    
    def test_large_simulation_throughput(self, benchmark):
        """Benchmark 100K agent simulation (target: 100K agents/sec)."""
        sim = Simulation(name="perf_test", agents=100_000)
        
        def run_step():
            return sim.step(dt=0.016)
        
        result = benchmark(run_step)
        
        # Assert throughput
        # benchmark provides .stats attribute with timing info
```

---

## Part 3: Documentation Standards

### Code Documentation

**Every public function/class needs:**
```python
def fetch_simulation(sim_id: int) -> Simulation:
    """Fetch simulation by ID.
    
    Retrieves simulation from database. Returns immediately if found in cache.
    
    Args:
        sim_id: Simulation identifier (must be positive)
    
    Returns:
        Simulation object with all populated fields
    
    Raises:
        SimulationNotFound: If sim_id doesn't exist
        DatabaseError: If database connection fails
    
    Example:
        >>> sim = fetch_simulation(123)
        >>> print(sim.name)
        'my_scenario'
    """
    pass
```

### API Documentation

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="PyRoboSimulator API",
    description="AI-native world simulation platform",
    version="0.1.0",
)

class SimulationRequest(BaseModel):
    """Create simulation request."""
    name: str  # Human-readable name
    agents: int  # Number of agents (1-1M)
    duration: float  # Duration in seconds

class SimulationResponse(BaseModel):
    """Simulation response."""
    id: int  # Unique ID
    name: str
    status: str  # "created", "running", "completed"
    created_at: str  # ISO8601 timestamp

@app.post(
    "/simulations",
    response_model=SimulationResponse,
    status_code=201,
    summary="Create simulation",
    tags=["Simulations"],
)
async def create_simulation(req: SimulationRequest) -> SimulationResponse:
    """Create a new simulation scenario.
    
    Parameters:
        - **name**: Human-readable scenario name
        - **agents**: Number of agents (1-1,000,000)
        - **duration**: Simulation length in seconds
    
    Returns:
        SimulationResponse with created simulation details
    
    Errors:
        - 400: Invalid request (negative agents, etc.)
        - 409: Duplicate name
    """
    pass
```

### Architecture Decision Records (ADRs)

```markdown
# ADR-001: Use PostgreSQL for Event Storage

## Decision
We use PostgreSQL with jsonb columns for storing simulation events.

## Context
- Need to store 100M+ events/day
- Events have variable structure (different event types)
- Need efficient querying by simulation/timestamp
- ACID compliance required for consistency

## Alternatives Considered
1. MongoDB: Better for flexible schema, but worse for ACID guarantees
2. ClickHouse: Excellent for time-series, but overkill for our queries
3. DuckDB: Good for analytics, but not designed for transactional workloads

## Consequences
- Positive: ACID compliance, great tooling, proven at scale
- Negative: Schema rigidity (mitigated by jsonb), operational overhead
- Migration path: jsonb → TimescaleDB for analytics later

## Status
Accepted (2024-01-15)
```

---

## Part 4: Performance Benchmarks

### Target Metrics

| Component | Metric | Target | P99 | Method |
|-----------|--------|--------|-----|--------|
| API | Latency | 100ms | 500ms | Load test 1K users |
| Database | Query | 10ms | 100ms | Query analyzer |
| Cache | Hit rate | 95% | - | Monthly review |
| Simulation | Agents/sec | 100K | - | Benchmark suite |
| GPU | Utilization | 80% | - | nvidia-smi |

### Continuous Benchmarking

```python
# benchmarks/suite.py
import pytest
import time

class BenchmarkSuite:
    """Continuous benchmarking."""
    
    @pytest.mark.benchmark(group="api")
    def test_list_simulations_p50(self, benchmark):
        """Median latency for listing simulations."""
        benchmark(self.api_client.list_simulations)
    
    @pytest.mark.benchmark(group="database")
    def test_query_agents_p99(self, benchmark):
        """P99 latency for fetching agents."""
        benchmark(lambda: self.db.fetch_agents(sim_id=1, limit=1000))

# Run: pytest benchmarks/ --benchmark-save=baseline
# Compare: pytest benchmarks/ --benchmark-compare=baseline --benchmark-compare-fail=mean:5%
```

---

## Part 5: Security Checklist

### Pre-Deployment Security Review

```yaml
Code:
  - [ ] No hardcoded secrets (API keys, passwords)
  - [ ] Input validation on all user inputs
  - [ ] SQL injection prevention (parameterized queries)
  - [ ] XSS prevention (HTML escaping)
  - [ ] CSRF tokens on state-changing operations
  - [ ] Rate limiting on sensitive endpoints

Dependencies:
  - [ ] Run `safety check` (no known vulnerabilities)
  - [ ] Run `pip-audit` (check all dependencies)
  - [ ] Review dependency licenses (no GPL in production)
  - [ ] Pin versions in requirements.txt

Database:
  - [ ] No SELECT * queries in production
  - [ ] Encrypted connections (TLS)
  - [ ] Connection pooling (no connection exhaustion)
  - [ ] Row-level security (RLS) for multi-tenant
  - [ ] Audit logging enabled

API:
  - [ ] Authentication on all protected endpoints
  - [ ] Authorization checks (verify user owns resource)
  - [ ] Rate limiting (prevent brute force)
  - [ ] CORS configuration (allowlist)
  - [ ] HTTPS enforced

Deployment:
  - [ ] Environment variables (no secrets in code)
  - [ ] Secrets in vault (AWS Secrets Manager, Vault)
  - [ ] Health checks configured
  - [ ] Monitoring & alerting enabled
  - [ ] Incident runbook created
```

### Security Scanning

```bash
# Dependency vulnerability scanning
safety check --json
pip-audit

# Code static analysis
bandit -r src/

# Secrets scanning
git-secrets --scan

# SAST (Static Application Security Testing)
semgrep --config=p/security-audit src/

# Container scanning
trivy image pyrobosim:latest
```

---

## Part 6: Code Review Process

### Review Checklist

**Before Submitting:**
- [ ] Code passes all tests locally
- [ ] Type hints on all functions
- [ ] Docstrings complete
- [ ] No debug prints (except logging)
- [ ] No hardcoded values (use config)

**Reviewer Checklist:**
- [ ] Does it solve the problem?
- [ ] Code style consistent?
- [ ] Tests adequate (new code tested)?
- [ ] Performance acceptable?
- [ ] Security reviewed?
- [ ] Documentation updated?

### Review Template

```markdown
## Summary
What does this PR do?

## Changes
- Item 1
- Item 2

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing done

## Performance Impact
- API latency: No change
- Database: +2% query time (acceptable)
- Memory: -5% (improved)

## Security Review
- [ ] No secrets in code
- [ ] Input validation added
- [ ] No SQL injection risk

## Breaking Changes
- None
```

---

## Part 7: CI/CD Standards

### GitHub Actions Pipeline

```yaml
# .github/workflows/main.yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Lint
        run: |
          black --check .
          isort --check .
          flake8 .
          pylint src/
      
      - name: Type check
        run: mypy src/
      
      - name: Test
        run: |
          pytest --cov=src --cov-report=xml
      
      - name: Security scan
        run: |
          bandit -r src/
          safety check
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t pyrobosim:latest .
      
      - name: Push to registry
        run: |
          docker tag pyrobosim:latest gcr.io/project/pyrobosim:${{ github.sha }}
          docker push gcr.io/project/pyrobosim:${{ github.sha }}
      
      - name: Deploy to staging
        run: kubectl set image deployment/pyrobosim -n staging pyrobosim=gcr.io/project/pyrobosim:${{ github.sha }}
```

---

## Part 8: Standards Compliance

### Monthly Audit

```python
class StandardsAudit:
    """Verify engineering standards compliance."""
    
    def audit_code_style(self):
        """Check PEP 8 compliance."""
        # Run black, isort, flake8
        return check_code_format("src/")
    
    def audit_test_coverage(self):
        """Ensure 85%+ coverage."""
        coverage = run_pytest_coverage()
        assert coverage >= 0.85, f"Coverage too low: {coverage}"
    
    def audit_documentation(self):
        """Verify all functions documented."""
        undocumented = find_undocumented_functions("src/")
        assert len(undocumented) == 0, f"Missing docs: {undocumented}"
    
    def audit_performance(self):
        """Run performance benchmarks."""
        results = run_benchmark_suite()
        for metric, value, target in results:
            assert value <= target * 1.1, f"{metric} degraded: {value} > {target}"
    
    async def generate_report(self):
        """Monthly compliance report."""
        return {
            'code_style': self.audit_code_style(),
            'test_coverage': self.audit_test_coverage(),
            'documentation': self.audit_documentation(),
            'performance': self.audit_performance(),
        }
```

---

**Engineering Standards Complete**  
**Consistent, Scalable, Production-Ready Code**
