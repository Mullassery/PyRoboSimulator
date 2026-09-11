# PyRoboSimulator Phase 4: Production Hardening & v1.0 Release

## Overview

**Goal:** Production-ready release with deployment infrastructure, scalability, security, and comprehensive documentation.

**Timeline:** 8-10 weeks  
**Team Size:** 4-5 engineers (1 DevOps lead, 1 backend, 1 QA, 1 security, 1 documentation)  
**Target Release:** v1.0.0 (stable, production-ready)  
**Focus:** Reliability, security, scalability, documentation  

---

## Deliverables

### 1. Production Infrastructure  [DESIGN]

#### Kubernetes Deployment

**Python Module: `k8s_deployment.py`**

```python
class KubernetesDeployment:
    """Deploy PyRoboSimulator to Kubernetes."""
    
    def __init__(self):
        self.client = kubernetes.client.CoreV1Api()
        self.apps_client = kubernetes.client.AppsV1Api()
    
    def deploy_backend(self, replicas: int = 3):
        """Deploy Python backend with auto-scaling."""
        
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "pyrobosim-backend"},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": "pyrobosim-backend"}},
                "template": {
                    "metadata": {"labels": {"app": "pyrobosim-backend"}},
                    "spec": {
                        "containers": [{
                            "name": "backend",
                            "image": "pyrobosimulator:latest",
                            "ports": [{"containerPort": 8000}],
                            "resources": {
                                "requests": {"cpu": "2", "memory": "4Gi"},
                                "limits": {"cpu": "4", "memory": "8Gi"},
                            },
                            "env": [
                                {"name": "WORKERS", "value": "4"},
                                {"name": "LOG_LEVEL", "value": "INFO"},
                            ],
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 8000},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10,
                            },
                        }],
                    },
                },
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxSurge": 1,
                        "maxUnavailable": 0,
                    },
                },
            },
        }
        
        self.apps_client.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )
    
    def deploy_database(self):
        """Deploy PostgreSQL with persistence."""
        
        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": "postgres-pvc"},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "100Gi"}},
            },
        }
        
        statefulset = {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {"name": "postgres"},
            "spec": {
                "serviceName": "postgres",
                "replicas": 1,
                "selector": {"matchLabels": {"app": "postgres"}},
                "template": {
                    "metadata": {"labels": {"app": "postgres"}},
                    "spec": {
                        "containers": [{
                            "name": "postgres",
                            "image": "postgres:16",
                            "ports": [{"containerPort": 5432}],
                            "env": [
                                {"name": "POSTGRES_PASSWORD", "valueFrom": {
                                    "secretKeyRef": {
                                        "name": "postgres-secret",
                                        "key": "password"
                                    }
                                }},
                            ],
                            "volumeMounts": [{
                                "name": "postgres-storage",
                                "mountPath": "/var/lib/postgresql/data",
                            }],
                        }],
                        "volumes": [{
                            "name": "postgres-storage",
                            "persistentVolumeClaim": {"claimName": "postgres-pvc"},
                        }],
                    },
                },
            },
        }
        
        self.client.create_namespaced_persistent_volume_claim(
            namespace="default", body=pvc
        )
        self.apps_client.create_namespaced_stateful_set(
            namespace="default", body=statefulset
        )
```

#### Docker Containerization

**Dockerfile for production**

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
COPY requirements-prod.txt .

# Build wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements-prod.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements-prod.txt .

# Install wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY python/pyrobosimulator /app/pyrobosimulator

# Create non-root user
RUN useradd -m -u 1000 pyrobo && chown -R pyrobo:pyrobo /app
USER pyrobo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "pyrobosimulator.api:create_app()", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### CI/CD Pipeline

**GitHub Actions / GitLab CI**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Lint
        run: |
          flake8 python/pyrobosimulator --max-line-length=100
          black --check python/pyrobosimulator
      
      - name: Type checking
        run: |
          mypy python/pyrobosimulator
      
      - name: Run tests
        run: |
          pytest python/pyrobosimulator/tests/ -v --cov
      
      - name: Security scanning
        run: |
          bandit -r python/pyrobosimulator/
          safety check

  build-and-push:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t pyrobosimulator:${{ github.ref_name }} .
      
      - name: Push to registry
        run: |
          docker tag pyrobosimulator:${{ github.ref_name }} \
                      gcr.io/myproject/pyrobosimulator:${{ github.ref_name }}
          docker push gcr.io/myproject/pyrobosimulator:${{ github.ref_name }}

  deploy:
    runs-on: ubuntu-latest
    needs: build-and-push
    steps:
      - name: Deploy to GKE
        run: |
          gcloud container clusters get-credentials production --zone us-central1-a
          kubectl set image deployment/pyrobosim-backend \
                  backend=gcr.io/myproject/pyrobosimulator:${{ github.ref_name }}
          kubectl rollout status deployment/pyrobosim-backend
```

### 2. Monitoring & Observability  [DESIGN]

#### Logging

**Python Module: `logging_config.py`**

```python
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging for production."""
    
    # JSON logger for machine parsing
    logHandler = logging.handlers.RotatingFileHandler(
        'logs/app.json',
        maxBytes=100000000,
        backupCount=10
    )
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger

# Log structured events
logger.info("World loaded", extra={
    "world_id": world_id,
    "building_count": 52000,
    "load_time_ms": 1234,
    "timestamp": time.time(),
})
```

#### Metrics (Prometheus)

**Python Module: `metrics.py`**

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Simulation metrics
active_simulations = Gauge(
    'active_simulations',
    'Number of active simulations'
)

simulated_time_total = Counter(
    'simulated_time_total_seconds',
    'Total simulated time',
    ['scenario_type']
)

# Resource metrics
simulation_memory_bytes = Gauge(
    'simulation_memory_bytes',
    'Memory used by simulation',
    ['simulation_id']
)

# Usage
@app.post("/api/v1/load-world")
async def load_world(request: LoadWorldRequest):
    with http_request_duration_seconds.labels(
        method='POST',
        endpoint='load_world'
    ).time():
        # Process request
        active_simulations.inc()
        # ...
        http_requests_total.labels(
            method='POST',
            endpoint='load_world',
            status=200
        ).inc()
        return response
```

#### Tracing (OpenTelemetry)

**Distributed request tracing**

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in code
@app.post("/api/v1/generate-world")
async def generate_world(request: GenerateWorldRequest):
    with tracer.start_as_current_span("generate_world"):
        with tracer.start_as_current_span("claude_api_call"):
            spec = world_gen.generate(request.prompt)
        
        with tracer.start_as_current_span("schema_validation"):
            validated_spec = WorldSpec(**spec.model_dump())
        
        return validated_spec
```

#### Alerting

**Prometheus alert rules**

```yaml
# alerts.yml
groups:
  - name: pyrobosimulator
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, http_request_duration_seconds) > 1.0
        for: 10m
        annotations:
          summary: "High request latency"

      - alert: LowDiskSpace
        expr: |
          node_filesystem_avail_bytes{mountpoint="/"} < 10737418240
        for: 5m
        annotations:
          summary: "Less than 10GB disk space remaining"
```

### 3. Security Hardening  [DESIGN]

#### Authentication & Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredential
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredential = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403)
    return user_id

@app.post("/api/v1/cities/generate")
async def generate_city(
    request: CityGenerationRequest,
    user_id: str = Depends(verify_token)
):
    """Authenticated endpoint."""
    # Only authenticated users can generate cities
    return await city_generator.generate(request)
```

#### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/generate-world")
@limiter.limit("10/minute")
async def generate_world(request: GenerateWorldRequest):
    """Rate limited to 10 requests per minute per IP."""
    return world_gen.generate(request.prompt)
```

#### Input Validation

```python
from pydantic import BaseModel, validator, constr

class CityGenerationRequest(BaseModel):
    seed: int = Field(..., ge=0, le=2**32-1)
    style: constr(regex="^(downtown|suburbs|mixed)$")
    size_km: float = Field(..., ge=1, le=10)
    
    @validator('seed')
    def validate_seed(cls, v):
        if not isinstance(v, int):
            raise ValueError('Seed must be integer')
        return v
```

#### SQL Injection Prevention

```python
# Safe: Uses parameterized queries (SQLAlchemy ORM)
from sqlalchemy.orm import Session

def get_world(session: Session, world_id: str):
    return session.query(World).filter(World.id == world_id).first()

# Never do this:
# query = f"SELECT * FROM worlds WHERE id = '{world_id}'"  # Vulnerable!
```

#### Secrets Management

```python
import os
from dotenv import load_dotenv

# Load from .env (never commit to git!)
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

# Or use environment variables directly
# export ANTHROPIC_API_KEY="sk-..."
```

### 4. Comprehensive Testing  [DESIGN]

#### Unit Tests

**Existing + expanded for Phase 4**

```python
# tests/test_world_spec.py
class TestWorldSpecValidation:
    def test_material_constraints(self):
        """Verify material properties within valid ranges."""
        mat = MaterialDefinition(
            type=MaterialType.ASPHALT,
            color_rgb=(0.15, 0.15, 0.15),
            roughness=0.75,
        )
        assert 0 <= mat.roughness <= 1
        assert 0 <= mat.metallic <= 1
        assert 0 <= mat.emissivity <= 1
```

#### Integration Tests

```python
# tests/integration/test_api_flow.py
class TestEndToEndFlow:
    async def test_generate_load_query_world(self):
        """Test complete workflow: generate → load → query."""
        
        # 1. Generate world
        gen_response = await client.post(
            "/api/v1/generate-world",
            json={"prompt": "A parking lot"}
        )
        assert gen_response.status_code == 200
        world_id = gen_response.json()["world_id"]
        
        # 2. Load world
        load_response = await client.post(
            "/api/v1/load-world",
            json={"spec": gen_response.json()["spec"], "world_id": world_id}
        )
        assert load_response.status_code == 200
        
        # 3. Query sensors
        sensor_response = await client.get(
            f"/api/v1/sensors/{world_id}/rgb"
        )
        assert sensor_response.status_code == 200
```

#### Performance Tests

```python
# tests/performance/test_load_capacity.py
class TestPerformanceUnderLoad:
    def test_concurrent_world_generation(self):
        """Test API under concurrent load."""
        
        import asyncio
        
        async def generate_world():
            return await client.post(
                "/api/v1/generate-world",
                json={"prompt": "Random city"}
            )
        
        # Generate 100 worlds concurrently
        start = time.time()
        tasks = [generate_world() for _ in range(100)]
        results = asyncio.run(asyncio.gather(*tasks))
        elapsed = time.time() - start
        
        # Verify all successful
        assert all(r.status_code == 200 for r in results)
        
        # Verify performance
        assert elapsed < 60  # Should complete in <1 minute
        print(f"Generated 100 worlds in {elapsed:.1f}s")
```

#### Chaos Testing

```python
# tests/chaos/test_resilience.py
class TestResilience:
    def test_database_failure_recovery(self):
        """Test graceful degradation on DB failure."""
        
        # Simulate DB disconnection
        with mock.patch('db.connection.execute') as mock_db:
            mock_db.side_effect = Exception("DB connection failed")
            
            # API should still respond
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            
            # But query should fail gracefully
            response = client.get("/api/v1/worlds/123")
            assert response.status_code == 503  # Service unavailable
            assert "database" in response.json()["detail"].lower()
```

### 5. Documentation  [DESIGN]

#### API Documentation (Auto-generated)

**Swagger/OpenAPI**

```
GET http://localhost:8000/docs  → Interactive API explorer
GET http://localhost:8000/openapi.json  → OpenAPI schema
```

#### Developer Guide

**File: `DEVELOPER_GUIDE.md`**

```markdown
# Developer Guide

## Setup

1. Clone repository
2. Create Python venv
3. Install: `pip install -e ".[dev]"`
4. Run tests: `pytest`
5. Start server: `python -m pyrobosimulator`

## Architecture

- `schemas.py`: Pydantic models (world spec, agents, etc.)
- `api.py`: FastAPI endpoints
- `world_gen.py`: Claude integration
- `city_generator.py`: Procedural generation
- `agent_system.py`: ECS + AI
- `physics_engine.py`: Physics simulation
- `ros2_bridge.py`: ROS 2 integration

## Adding a New Endpoint

1. Define request/response models in `schemas.py`
2. Implement handler in `api.py`
3. Write tests in `tests/`
4. Document in docstring

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api.py

# With coverage
pytest --cov=pyrobosimulator
```

## Performance Profiling

```python
from cProfile import Profile
from pstats import SortKey

profiler = Profile()
profiler.enable()
# Code to profile
profiler.disable()
profiler.print_stats(SortKey.CUMULATIVE)
```
```

#### User Guide

**File: `USER_GUIDE.md`**

```markdown
# PyRoboSimulator User Guide

## Quick Start

### 1. Generate a World

```bash
curl -X POST http://localhost:8000/api/v1/generate-world \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A downtown city with traffic and pedestrians"}'
```

### 2. Load World

```bash
curl -X POST http://localhost:8000/api/v1/load-world \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}, "world_id": "my_city"}'
```

### 3. Simulate

```bash
# Simulation runs automatically
# Query sensors
curl http://localhost:8000/api/v1/sensors/my_city/rgb?frame=0
```

## Scenarios

Pre-built scenarios for testing:

- `parking_lot_clear`: Empty parking lot
- `downtown_rush_hour`: Peak traffic scenario
- `highway_merging`: Highway on-ramp test
- `weather_extremes`: Rain, fog, snow

## Configuration

`config.yaml`:

```yaml
simulation:
  physics_engine: "bullet"
  max_agents: 1000
  target_fps: 30

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4

database:
  url: "postgresql://..."
  pool_size: 20
```
```

#### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PyRoboSimulator v1.0                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           FastAPI Backend (Load-balanced)            │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │                                                       │ │
│  │  POST /api/v1/generate-world      Claude Sonnet     │ │
│  │  POST /api/v1/load-world          World Loader      │ │
│  │  GET  /api/v1/worlds/{id}         State Manager     │ │
│  │  GET  /api/v1/sensors/{id}/{type} Sensor Capture    │ │
│  │  POST /api/v1/cities/generate     City Generator    │ │
│  │  POST /api/v1/agents/spawn        Agent Factory     │ │
│  │  POST /api/v1/simulation/physics   Physics Engine   │ │
│  │  POST /api/v1/ros2/launch         ROS 2 Bridge      │ │
│  │                                                       │ │
│  └───────────────────────────────────────────────────────┘ │
│         ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓                                    │
├─────────────────────────────────────────────────────────────┤
│                    Simulation Engine                        │
│  ┌─────────────┬──────────────┬──────────────┬───────────┐ │
│  │ World Gen   │ City Gen     │ Physics      │ Agent AI  │ │
│  │ L-Systems   │ Procedural   │ Multi-body   │ Memory    │ │
│  │ Voronoi     │ Traffic      │ Vehicles     │ Narrative │ │
│  │ Road Net    │ Pedestrians  │ Constraints  │ Behavior  │ │
│  └─────────────┴──────────────┴──────────────┴───────────┘ │
│         ↓ ↓ ↓ ↓                                             │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                             │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ PostgreSQL   │ S3/Object    │ Redis Cache  │            │
│  │ World State  │ Assets       │ Hot Data     │            │
│  │ Agents       │ Textures     │              │            │
│  │ Events       │ Meshes       │              │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                      Infrastructure                         │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Kubernetes   │ Docker       │ Monitoring   │            │
│  │ Orchestration│ Containers   │ (Prometheus  │            │
│  │ Scaling      │ CI/CD        │  + Jaeger)   │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 4 Roadmap

### Week 1-2: Infrastructure
- [ ] Kubernetes deployment specs
- [ ] Docker image optimization
- [ ] Database provisioning (PostgreSQL)
- [ ] S3 asset storage setup
- [ ] Network & load balancer config

### Week 2-3: CI/CD
- [ ] GitHub Actions workflow
- [ ] Automated testing in CI
- [ ] Docker image building & pushing
- [ ] Automated deployment
- [ ] Rollback procedures

### Week 3-4: Monitoring
- [ ] Prometheus metrics
- [ ] Jaeger tracing
- [ ] Logging (JSON + aggregation)
- [ ] Alert rules
- [ ] Grafana dashboards

### Week 4-5: Security
- [ ] JWT authentication
- [ ] Rate limiting
- [ ] Input validation
- [ ] Secrets management
- [ ] Security audit
- [ ] Penetration testing

### Week 5-6: Testing
- [ ] Unit test coverage >90%
- [ ] Integration tests
- [ ] Performance tests
- [ ] Chaos tests
- [ ] Load testing

### Week 6-7: Documentation
- [ ] API docs (Swagger)
- [ ] Developer guide
- [ ] User guide
- [ ] Troubleshooting
- [ ] Architecture docs

### Week 7-8: Optimization
- [ ] Performance profiling
- [ ] Database query optimization
- [ ] Caching strategy
- [ ] Asset compression
- [ ] Network optimization

### Week 8-9: Quality Assurance
- [ ] Bug fixes
- [ ] Edge case handling
- [ ] Cross-platform testing
- [ ] Browser compatibility (if web UI)
- [ ] Accessibility

### Week 9-10: Release Preparation
- [ ] Version numbering (v1.0.0)
- [ ] Changelog generation
- [ ] Release notes
- [ ] Migration guides
- [ ] Release testing

---

## Success Criteria (Phase 4)

| Metric | Target | Validation |
|--------|--------|-----------|
| Test Coverage | >90% code coverage | Coverage report |
| Uptime | 99.9% availability | Monitoring metrics |
| Latency | P95 <500ms, P99 <1000ms | Performance test |
| Throughput | 1,000+ req/s | Load test |
| Deployment Time | <5 minutes | CI/CD test |
| Security | Zero critical vulnerabilities | Security audit |
| Documentation | 100% API coverage | Doc completeness |
| Performance | <2% memory leak over 24h | Memory profile |

---

## Post-Release (v1.1+)

**Features for future releases:**

- Multi-instance simulation (millions of agents)
- Cloud-native scaling (Kubernetes autoscaling)
- Advanced visualization (web 3D viewer)
- Real-time collaboration
- Extended API (gRPC, WebSocket)
- Mobile app
- Plugin ecosystem

---

**Phase 4 Timeline:** 8-10 weeks  
**Target Release:** v1.0.0 (Production-ready)  
**Maintenance:** Ongoing support, bug fixes, minor features
