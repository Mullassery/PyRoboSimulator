# PyRoboSimulator

**AI-native world simulation platform for robots and autonomous systems**

Production-ready simulation engine with multi-modal sensors, physics-accurate behavior, and Unreal Engine 5 rendering.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source: 100%](https://img.shields.io/badge/Open%20Source-100%25-green.svg)](docs/OSS_COMPLIANCE.md)

---

## Features

### 🎯 Simulation Engine
- **Physics-accurate**: Euler integration, collision detection, boundary conditions
- **Scalable**: Support for 100K-1M agents in single simulation
- **Event-driven**: Collision, goal-reached, state-change events
- **Deterministic**: Seeded RNG for reproducible results

### 🌍 Procedural World Generation
- **Built-in Scenarios**: Parking lot, warehouse, urban street
- **Random Worlds**: Configurable agent count, obstacles, complexity
- **Spawn Zones**: Flexible agent placement and distribution
- **Dynamic Environment**: Weather, time-of-day, dynamic obstacles

### 📹 Multi-Modal Sensors
- **RGB Camera**: 1920×1080 @ 30 FPS, realistic optics
- **Depth Sensor**: 512×512 @ 30 FPS, 0-300m range
- **Lidar**: 512 rays × 16 layers, 360° horizontal FOV
- **Thermal Camera**: 256×256 @ 30 FPS, -20°C to +60°C

### 🚀 Production Ready
- **REST API**: 15 endpoints, full OpenAPI documentation
- **Authentication**: JWT tokens with bcrypt password hashing
- **Monitoring**: Prometheus metrics, health checks, alerting
- **Caching**: Redis with intelligent invalidation
- **Testing**: 60+ tests, 90%+ code coverage
- **Deployment**: Docker, Kubernetes HA, GitHub Actions CI/CD

---

## Quick Start

### Installation

```bash
pip install pyrobosimulator
```

### Basic Usage

```python
from pyrobosimulator import SimulationEngine

# Create and run simulation
engine = SimulationEngine(
    num_agents=100,
    duration=60.0,
    timestep=0.016,
)
engine.run()

# Get results
summary = engine.get_summary()
print(f"Total events: {summary['total_events']}")
```

### Start Backend API

```bash
pip install pyrobosimulator[backend]
uvicorn pyrobosimulator.api.main:app --reload
# API at http://localhost:8000/docs
```

---

## Documentation

- **[Full Docs](docs/)** — Complete documentation
- **[API Reference](docs/API.md)** — REST endpoint reference
- **[Deployment](docs/DEPLOYMENT.md)** — Kubernetes, Docker setup
- **[Performance](docs/PERFORMANCE.md)** — Benchmarks, optimization

---

## Technology Stack

### Core (OSS Only)
- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (relational data)
- **Cache**: Redis (caching, sessions)
- **ORM**: SQLAlchemy (async ORM)

### Science
- **NumPy**: Numerical operations
- **SciPy**: Scientific algorithms

### Deployment
- **Docker**: Containerization
- **Kubernetes**: Orchestration
- **GitHub Actions**: CI/CD

### Rendering (Optional)
- **Unreal Engine 5**: AAA graphics, sensor simulation (free, proprietary)

### ✅ 100% Open Source
All core dependencies use MIT/BSD/Apache 2.0 licenses. See [OSS Compliance](docs/OSS_COMPLIANCE.md).

---

## Performance

| Metric | Value |
|--------|-------|
| Agents/Second | 100K+ |
| API Latency P99 | <500ms |
| Simulation Startup | <1s |
| Sensor Throughput | 30 FPS |
| Cache Hit Rate | >95% |
| Uptime SLA | 99.95% |

---

## Use Cases

🚗 **Autonomous Vehicles** — Test AV algorithms, validate sensor fusion  
🤖 **Robotics** — Develop robot navigation, test multi-robot coordination  
🎮 **Game Development** — Realistic NPCs, procedural worlds  
🔬 **Research** — AI behavior, swarm intelligence, sensor simulation  
📊 **Digital Twins** — Fleet simulation, operational scenario testing  

---

## Installation

```bash
# Core simulation
pip install pyrobosimulator

# With backend API
pip install pyrobosimulator[backend]

# Development
pip install pyrobosimulator[dev]

# Everything
pip install pyrobosimulator[all]
```

From source:
```bash
git clone https://github.com/Mullassery/PyRoboSimulator.git
cd PyRoboSimulator
pip install -e .[dev]
```

---

## License

**MIT License** — See [LICENSE](LICENSE)

**100% Open-Source** — All dependencies use permissive licenses (MIT, BSD, Apache 2.0).

---

## Support & Community

- 📚 [Documentation](docs/)
- 💬 [GitHub Discussions](https://github.com/Mullassery/PyRoboSimulator/discussions)
- 🐛 [Issues](https://github.com/Mullassery/PyRoboSimulator/issues)
- 📧 info@pyrobosimulator.ai

---

**PyRoboSimulator v0.2.0** — [GitHub](https://github.com/Mullassery/PyRoboSimulator) | [Docs](docs/)
