# Contributing to PyRoboSimulator

Thank you for your interest in contributing to PyRoboSimulator! We welcome contributions of all kinds, from bug reports and documentation improvements to new features and performance optimizations.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please treat all community members with respect and courtesy.

## Ways to Contribute

### 1. Report Bugs

Found a bug? Open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Python version and OS
- Relevant code snippets

```bash
# Example: Run the failing code
python -c "from pyrobosimulator import SimulationEngine; ..."
```

### 2. Suggest Enhancements

Have an idea to improve PyRoboSimulator? Open an issue with:
- Clear description of the enhancement
- Use cases and benefits
- Possible implementation approach (optional)
- Relevant examples or links

### 3. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve API documentation
- Expand deployment guides

### 4. Submit Code Changes

We accept pull requests for:
- Bug fixes
- Performance improvements
- New features
- Test coverage improvements
- Code quality improvements

## Development Setup

### Prerequisites
- Python 3.10 or higher
- pip or uv
- PostgreSQL 12+ (for database tests)
- Redis (for caching tests)

### Local Environment

```bash
# Clone repository
git clone https://github.com/Mullassery/PyRoboSimulator.git
cd PyRoboSimulator

# Install in development mode
pip install -e .[dev]

# Run tests
pytest -v

# Run code quality checks
black src tests
isort src tests
flake8 src tests
mypy src
bandit -r src
```

### Docker Development

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run tests
pytest --cov=src

# Run API server
uvicorn backend.src.main:app --reload
```

## Coding Standards

### Style Guide

- **Python version**: 3.10+
- **Code formatter**: Black (line length 100)
- **Import sorting**: isort
- **Linting**: flake8
- **Type hints**: mypy (strict mode)
- **Security**: bandit

### Code Organization

```
backend/
├── src/
│   ├── config/         # Configuration
│   ├── models/         # Pydantic models
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   ├── db/             # Database layer
│   └── main.py         # FastAPI app
├── tests/
│   ├── conftest.py     # Pytest fixtures
│   └── test_*.py       # Test files
└── pyproject.toml      # Project config
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `SimulationEngine`)
- Functions/methods: `snake_case` (e.g., `get_simulation()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_AGENTS`)
- Private methods: `_leading_underscore` (e.g., `_internal_method()`)

### Type Hints

All functions must have type hints:

```python
from typing import Dict, List, Optional

def get_agents(
    simulation_id: int,
    filter_state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get agents for a simulation.
    
    Args:
        simulation_id: Simulation ID
        filter_state: Optional state filter (idle, moving, goal_reached)
    
    Returns:
        List of agent dictionaries
    """
    pass
```

### Comments

- Write docstrings for all public functions/classes
- Use docstring format: Google style
- Inline comments only for non-obvious logic
- No commented-out code

```python
def calculate_distance(pos1: Vector3, pos2: Vector3) -> float:
    """Calculate Euclidean distance between two positions.
    
    Args:
        pos1: First position
        pos2: Second position
    
    Returns:
        Euclidean distance in meters
    """
    delta = pos2.subtract(pos1)
    return delta.magnitude()
```

## Testing

### Writing Tests

All code changes should include tests. Test files follow naming convention `test_*.py`.

```python
import pytest
from pyrobosimulator.services.simulation_engine import SimulationEngine

class TestSimulationEngine:
    @pytest.fixture
    def engine(self):
        """Create engine instance for tests."""
        return SimulationEngine(num_agents=10, duration=10.0)
    
    def test_engine_initialization(self, engine):
        """Test engine initializes correctly."""
        assert engine.num_agents == 10
        assert engine.duration == 10.0
    
    def test_agent_movement(self, engine):
        """Test agents move during simulation."""
        initial_pos = engine.agents[0].position
        engine.run()
        final_pos = engine.agents[0].position
        assert initial_pos != final_pos
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_simulation_engine.py

# Run specific test
pytest tests/test_simulation_engine.py::TestSimulationEngine::test_engine_initialization

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance benchmarks
pytest tests/test_performance.py -v --benchmark-only
```

### Coverage Requirements

- Minimum 90% code coverage for new code
- No decrease in overall project coverage
- Check coverage: `pytest --cov=src --cov-report=term-missing`

## Pull Request Process

### Before Submitting

1. **Update with main**: `git pull origin main`
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** and commit with clear messages
4. **Run tests locally**: `pytest --cov=src`
5. **Check code quality**: `black`, `isort`, `flake8`, `mypy`, `bandit`
6. **Update documentation** if needed
7. **Rebase if needed**: `git rebase main`

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add distributed physics simulation support

- Implement multi-GPU agent scheduling
- Add worker pool for parallel physics updates
- Improve latency from 50ms to 10ms per frame

Closes #123
```

Format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test additions/changes
- `perf`: Performance improvements
- `refactor`: Code refactoring
- `chore`: Build, CI, dependencies

### Pull Request Description

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed:
- [ ] Unit tests added
- [ ] Integration tests passed
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Coverage >= 90%
- [ ] Documentation updated
- [ ] No new warnings/errors

## Related Issues
Closes #<issue-number>
```

## Performance Considerations

When contributing code:

- **Benchmarking**: Use `pytest-benchmark` for performance-sensitive code
- **Profiling**: Profile changes with `cProfile` before/after
- **Memory**: Monitor memory usage, especially for agent-heavy code
- **Database**: Minimize queries, use connection pooling
- **Async**: Maintain async/await patterns, don't block event loop

Example benchmark:

```python
def test_agent_update_performance(benchmark):
    """Benchmark agent update performance."""
    engine = SimulationEngine(num_agents=1000)
    
    def update():
        for agent in engine.agents:
            agent.update(0.016)
    
    result = benchmark(update)
    assert result.stats.mean < 0.001  # Should complete in <1ms
```

## Documentation

### Code Documentation

- All public APIs must have docstrings
- Use Google-style docstrings
- Include examples for complex functions

### User Documentation

- Add to appropriate docs file
- Include examples
- Update table of contents if applicable
- Keep consistent with existing documentation

## Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvement
- `performance`: Performance optimization
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information requested

## Review Process

1. **Automated checks**: CI/CD pipeline runs (tests, linting, security)
2. **Code review**: Maintainers review and provide feedback
3. **Changes requested**: Address feedback and push updates
4. **Approval**: Maintainer approves changes
5. **Merge**: Changes merged to main branch

Reviews typically take 2-5 business days.

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Mentioned on project page

## Questions?

- Open a discussion on GitHub
- Ask in an issue
- Email: info@pyrobosimulator.ai

---

Thank you for contributing to PyRoboSimulator! Together we're building better simulation tools for autonomous systems.
