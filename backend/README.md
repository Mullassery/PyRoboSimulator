# PyRoboSimulator Backend

AI-native world simulation platform for robots and autonomous systems.

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6.0+

### Local Development Setup

```bash
# 1. Clone and navigate to backend
cd backend

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Copy environment file
cp config/.env.example config/.env
# Edit config/.env with your local settings

# 5. Set up pre-commit hooks
pre-commit install

# 6. Start development database
docker-compose up -d postgres redis

# 7. Run migrations
alembic upgrade head

# 8. Start backend server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py      # Configuration & environment variables
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   ├── simulations.py   # Simulation endpoints (Task #7)
│   │   └── ...
│   ├── models/              # Pydantic data models (Task #6)
│   ├── db/                  # Database layer (Task #11)
│   └── services/            # Business logic
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_health.py
│   ├── test_simulations.py  # (Task #18)
│   └── ...
├── config/
│   ├── .env.example         # Environment template
│   └── .env                 # Local development (git-ignored)
├── pyproject.toml           # Dependencies & configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── docker-compose.yml       # Local dev environment
└── README.md
```

## Development Workflow

### Code Quality

All code must pass quality checks before committing:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/ tests/

# Type check
mypy src/

# Security scan
bandit -r src/
safety check
```

Pre-commit hooks will run these automatically on `git commit`.

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_health.py::test_health_check

# Run with verbose output
pytest -v

# Run benchmarks
pytest --benchmark-only
```

Coverage target: **85%+**

### Running Locally

```bash
# Development server with hot reload
python -m uvicorn src.main:app --reload

# Production server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Checks

- `GET /api/v1/health` - Application health status
- `GET /api/v1/ready` - Kubernetes readiness probe

### Simulations (Task #7)

- `POST /api/v1/simulations` - Create simulation
- `GET /api/v1/simulations` - List simulations (paginated)
- `GET /api/v1/simulations/{id}` - Get simulation details
- `PUT /api/v1/simulations/{id}` - Update simulation
- `DELETE /api/v1/simulations/{id}` - Delete simulation
- `POST /api/v1/simulations/{id}/start` - Start simulation
- `POST /api/v1/simulations/{id}/stop` - Stop simulation

### Results & Events (Task #8)

- `GET /api/v1/simulations/{id}/results` - Fetch events
- `GET /api/v1/simulations/{id}/stream` - Stream events (SSE)
- `GET /api/v1/simulations/{id}/summary` - Aggregate statistics

## Configuration

Environment variables are loaded from `config/.env`:

```
# FastAPI
ENVIRONMENT=development|staging|production
DEBUG=true|false
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_POOL_MIN_SIZE=5
DATABASE_POOL_MAX_SIZE=20

# Cache (Redis)
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Simulation limits
MAX_AGENTS=1000000
MAX_SIMULATION_DURATION=3600
```

## Database Migrations

Migrations are managed with Alembic:

```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Rollback one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Docker

```bash
# Build image
docker build -t pyrobosim:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  pyrobosim:latest

# Run with docker-compose (local dev)
docker-compose up -d
```

## Monitoring

Metrics available at `http://localhost:8001/metrics` (Prometheus format).

### Health Checks

- API latency (P50, P95, P99)
- Database query latency
- Cache hit rate
- Active connections
- Memory usage

## Troubleshooting

### Database connection fails
```bash
# Check PostgreSQL is running
docker-compose ps

# Verify connection string in config/.env
# Example: postgresql+asyncpg://postgres:postgres@localhost:5432/pyrobosim_dev
```

### Import errors
```bash
# Reinstall in development mode
pip install -e ".[dev]"

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Tests fail
```bash
# Check test database is clean
rm -rf tests/.db

# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/test_health.py::test_health_check -v
```

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and run quality checks: `pytest && black . && mypy .`
3. Commit with pre-commit: `git commit -m "Add my feature"`
4. Push and create PR
5. Ensure CI passes (GitHub Actions)

## Performance Targets

| Metric | Target | P99 |
|--------|--------|-----|
| API Latency | 100ms | 500ms |
| Database Query | 10ms | 100ms |
| Cache Hit Rate | 95% | - |
| Simulation Throughput | 100K agents/sec | - |

## Technology Stack

- **Framework:** FastAPI (async Python web framework)
- **Database:** PostgreSQL (ACID-compliant relational DB)
- **Cache:** Redis (in-memory data store)
- **ORM:** SQLAlchemy (async ORM)
- **Validation:** Pydantic (data validation)
- **Authentication:** JWT (JSON Web Tokens)
- **Testing:** pytest (testing framework)
- **Monitoring:** Prometheus (metrics collection)
- **Deployment:** Docker, Kubernetes

All dependencies are open-source (OSS-only stack).

## License

MIT License - See LICENSE file for details
