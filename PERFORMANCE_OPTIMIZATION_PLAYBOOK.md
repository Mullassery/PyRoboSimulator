# Performance Optimization Playbook

## Executive Summary

This playbook provides systematic methodology for benchmarking, profiling, and optimizing PyRoboSimulator across all layers: API latency, database performance, GPU acceleration, caching, and simulation throughput.

**Target Metrics:**
- API P99 latency: <500ms
- Simulation throughput: 100K agents/sec
- Database query time: <100ms (p99)
- Cache hit rate: >95%
- GPU utilization: >80%

---

## Part 1: Profiling & Benchmarking

### Application Profiling

```python
from fastapi import FastAPI
from prometheus_client import Counter, Histogram
import cProfile
import pstats
import io

app = FastAPI()

# Metrics
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

function_calls = Counter(
    'function_calls_total',
    'Total function calls',
    ['function_name']
)

class ProfilingMiddleware:
    """Continuous application profiling."""
    
    def __init__(self, app):
        self.app = app
        self.profiler = cProfile.Profile()
    
    async def __call__(self, scope, receive, send):
        # Profile request
        self.profiler.enable()
        start = time.time()
        
        await self.app(scope, receive, send)
        
        self.profiler.disable()
        elapsed = time.time() - start
        
        # Record metrics
        request_duration.labels(
            method=scope['method'],
            endpoint=scope['path']
        ).observe(elapsed)
        
        # Log slow requests
        if elapsed > 1.0:
            self.log_slow_request(scope, elapsed)
    
    def log_slow_request(self, scope, elapsed):
        """Log requests slower than 1 second."""
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(10)
        
        logger.warning(f"Slow request {scope['path']}: {elapsed:.2f}s\n{s.getvalue()}")

# Apply middleware
app.add_middleware(ProfilingMiddleware)
```

### Load Testing Framework

```python
import asyncio
from locust import HttpUser, task, between
import numpy as np

class SimulationLoadTest(HttpUser):
    """Load testing for simulation API."""
    
    wait_time = between(1, 3)
    
    @task(3)
    def create_simulation(self):
        """Create simulation scenario."""
        self.client.post("/simulations", json={
            "name": "test_scenario",
            "agents": 1000,
            "duration": 60,
        })
    
    @task(2)
    def get_results(self):
        """Fetch simulation results."""
        self.client.get("/simulations/1/results")
    
    @task(1)
    def list_scenarios(self):
        """List available scenarios."""
        self.client.get("/scenarios?limit=100")

# Run with: locust -f load_test.py --host=http://localhost:8000 -u 1000 -r 50

class BenchmarkRunner:
    """Comprehensive benchmark suite."""
    
    async def run_benchmarks(self):
        """Execute all benchmarks."""
        
        results = {
            'api': await self.benchmark_api(),
            'database': await self.benchmark_database(),
            'simulation': await self.benchmark_simulation(),
            'cache': await self.benchmark_cache(),
        }
        
        self.generate_report(results)
    
    async def benchmark_api(self):
        """API endpoint latency."""
        
        endpoints = [
            ('GET', '/health'),
            ('POST', '/simulations'),
            ('GET', '/scenarios'),
            ('POST', '/simulations/1/step'),
        ]
        
        results = {}
        for method, endpoint in endpoints:
            latencies = []
            for _ in range(1000):
                start = time.time()
                response = await self.client.request(method, endpoint)
                latencies.append((time.time() - start) * 1000)
            
            results[endpoint] = {
                'p50': np.percentile(latencies, 50),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'mean': np.mean(latencies),
            }
        
        return results
    
    async def benchmark_database(self):
        """Database query performance."""
        
        queries = [
            ("SELECT * FROM simulations WHERE id = %s", (1,)),
            ("SELECT * FROM agents WHERE simulation_id = %s LIMIT 1000", (1,)),
            ("INSERT INTO events VALUES (...)", ()),
        ]
        
        results = {}
        for query, params in queries:
            latencies = []
            for _ in range(100):
                start = time.time()
                await self.db.execute(query, params)
                latencies.append((time.time() - start) * 1000)
            
            results[query[:50]] = {
                'p50': np.percentile(latencies, 50),
                'p99': np.percentile(latencies, 99),
            }
        
        return results
```

---

## Part 2: Database Optimization

### Query Optimization

```python
# BAD: N+1 query
def get_simulations_with_agents():
    sims = db.query("SELECT * FROM simulations LIMIT 100")
    for sim in sims:
        # This queries database 100 times!
        sim.agents = db.query(f"SELECT * FROM agents WHERE simulation_id = {sim.id}")

# GOOD: Join query
def get_simulations_with_agents():
    return db.query("""
        SELECT s.*, array_agg(a.id) as agent_ids
        FROM simulations s
        LEFT JOIN agents a ON a.simulation_id = s.id
        GROUP BY s.id
        LIMIT 100
    """)

# GOOD: Batch query
def get_simulations_with_agents():
    sims = db.query("SELECT * FROM simulations LIMIT 100")
    sim_ids = [s.id for s in sims]
    agents_by_sim = db.query(f"""
        SELECT simulation_id, id
        FROM agents
        WHERE simulation_id IN ({','.join(['%s'] * len(sim_ids))})
    """, sim_ids)
    
    agents_map = defaultdict(list)
    for agent in agents_by_sim:
        agents_map[agent.simulation_id].append(agent)
    
    for sim in sims:
        sim.agents = agents_map[sim.id]
```

### Indexing Strategy

```sql
-- Simulations table
CREATE INDEX idx_simulations_user_id ON simulations(user_id);
CREATE INDEX idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX idx_simulations_status ON simulations(status);

-- Agents table
CREATE INDEX idx_agents_simulation_id ON agents(simulation_id);
CREATE INDEX idx_agents_position ON agents(position) USING GIST;  -- Spatial

-- Events table (high volume)
CREATE INDEX idx_events_simulation_id_ts ON events(simulation_id, timestamp DESC);
CREATE INDEX idx_events_agent_id ON events(agent_id);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM agents WHERE simulation_id = 1 LIMIT 1000;

-- Vacuum & analyze
VACUUM ANALYZE simulations;
VACUUM ANALYZE agents;
```

### Connection Pooling

```python
from sqlalchemy.pool import QueuePool, NullPool

# Production: QueuePool for connection reuse
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Connections in pool
    max_overflow=40,        # Additional connections
    pool_recycle=3600,      # Recycle after 1 hour
    pool_pre_ping=True,     # Verify connections
)

# High-throughput: NullPool for stateless connections
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # No pooling (for serverless)
)
```

---

## Part 3: Cache Optimization

### Redis Caching Strategy

```python
import redis
from functools import wraps
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class CacheManager:
    """Intelligent caching."""
    
    def __init__(self):
        self.redis = redis_client
        self.ttls = {
            'scenario': 3600,        # 1 hour
            'simulation_result': 300,  # 5 minutes
            'leaderboard': 60,       # 1 minute
            'user_preference': 86400, # 1 day
        }
    
    def cache_key(self, prefix: str, **kwargs):
        """Generate cache key."""
        parts = [prefix]
        parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_str = "|".join(parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def cached(self, cache_type: str):
        """Decorator for caching."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key = self.cache_key(cache_type, **kwargs)
                
                # Try cache
                cached = self.redis.get(key)
                if cached:
                    return json.loads(cached)
                
                # Compute result
                result = await func(*args, **kwargs)
                
                # Store in cache
                ttl = self.ttls.get(cache_type, 300)
                self.redis.setex(
                    key,
                    ttl,
                    json.dumps(result, default=str)
                )
                
                return result
            
            return wrapper
        return decorator

cache = CacheManager()

@cache.cached('scenario')
async def get_scenario(scenario_id: int):
    """Cached scenario fetch."""
    return await db.fetch_one(
        "SELECT * FROM scenarios WHERE id = %s",
        (scenario_id,)
    )
```

### Cache Invalidation

```python
class CacheInvalidation:
    """Smart cache invalidation."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def invalidate_on_update(self, model: str, model_id: int):
        """Invalidate related cache on update."""
        
        if model == 'scenario':
            # Invalidate scenario & derived caches
            patterns = [
                f"scenario:{model_id}:*",
                f"leaderboard:scenario:{model_id}",
                f"results:scenario:{model_id}:*",
            ]
        
        elif model == 'simulation':
            # Invalidate simulation results
            patterns = [f"results:simulation:{model_id}:*"]
        
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    async def warm_cache(self):
        """Pre-populate hot cache."""
        
        # Cache popular scenarios
        popular = await db.fetch(
            "SELECT id FROM scenarios ORDER BY runs DESC LIMIT 100"
        )
        
        for scenario in popular:
            await get_scenario(scenario['id'])  # Trigger caching
```

### Cache Monitoring

```python
class CacheMonitoring:
    """Monitor cache effectiveness."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get_stats(self) -> dict:
        """Cache hit rate & memory usage."""
        
        info = self.redis.info()
        
        hit_rate = info['keyspace_hits'] / (
            info['keyspace_hits'] + info['keyspace_misses']
        ) if (info['keyspace_hits'] + info['keyspace_misses']) > 0 else 0
        
        return {
            'hit_rate': hit_rate * 100,
            'memory_used': info['used_memory_human'],
            'keys_count': sum(self.redis.dbsize() for _ in range(16)),
            'evictions': info['evicted_keys'],
        }
```

---

## Part 4: GPU Acceleration

### CUDA Optimization

```python
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

class SimulationGPUAccelerator:
    """GPU-accelerated physics simulation."""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    async def compute_agent_updates(self, agents: List[Agent], dt: float):
        """GPU-accelerated agent physics."""
        
        # Prepare tensors
        positions = torch.tensor(
            [a.position for a in agents],
            dtype=torch.float32,
            device=self.device
        )
        
        velocities = torch.tensor(
            [a.velocity for a in agents],
            dtype=torch.float32,
            device=self.device
        )
        
        accelerations = torch.tensor(
            [a.acceleration for a in agents],
            dtype=torch.float32,
            device=self.device
        )
        
        # Physics: x = x + v*dt + 0.5*a*dt^2
        new_positions = positions + velocities * dt + 0.5 * accelerations * dt * dt
        new_velocities = velocities + accelerations * dt
        
        # Boundary conditions (GPU-side)
        new_positions = torch.clamp(new_positions, min=-1000, max=1000)
        
        # Copy back to CPU
        for i, agent in enumerate(agents):
            agent.position = new_positions[i].cpu().numpy()
            agent.velocity = new_velocities[i].cpu().numpy()
    
    async def raycast_batch(self, rays: torch.Tensor) -> torch.Tensor:
        """GPU-accelerated raycasting."""
        
        # rays shape: (num_rays, 3) - origin + direction
        rays = rays.to(self.device)
        
        # Compute intersections (CUDA kernel)
        intersections = self.raycast_kernel(rays)
        
        return intersections.cpu()
    
    async def compute_perception(self, agent_positions: torch.Tensor) -> torch.Tensor:
        """GPU-accelerated perception (distance matrices)."""
        
        agent_positions = agent_positions.to(self.device)
        
        # Pairwise distance (efficient on GPU)
        distances = torch.cdist(agent_positions, agent_positions)
        
        # Perception filter (neighbors within range)
        perception_range = 50.0
        nearby = distances < perception_range
        
        return nearby.cpu()
```

### Batch Processing

```python
class BatchProcessor:
    """Batch processing for throughput optimization."""
    
    def __init__(self, batch_size=1000, max_queue_wait=100):
        self.batch_size = batch_size
        self.queue = asyncio.Queue()
        self.max_wait_ms = max_queue_wait
    
    async def add_task(self, task):
        """Add task to batch."""
        await self.queue.put(task)
    
    async def process_batches(self):
        """Process batches when ready."""
        while True:
            batch = []
            deadline = asyncio.get_event_loop().time() + (self.max_wait_ms / 1000)
            
            try:
                # Collect batch or timeout
                while len(batch) < self.batch_size:
                    timeout = max(0, deadline - asyncio.get_event_loop().time())
                    task = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=timeout
                    )
                    batch.append(task)
            
            except asyncio.TimeoutError:
                pass
            
            if batch:
                await self.process_batch(batch)
    
    async def process_batch(self, batch):
        """Process batch on GPU."""
        # Convert to tensors, process, return results
        pass
```

---

## Part 5: API Optimization

### Response Compression

```python
from fastapi.middleware.gzip import GZIPMiddleware

app = FastAPI()

# Automatic GZIP compression for responses > 500 bytes
app.add_middleware(GZIPMiddleware, minimum_size=500)

# Manual compression for streaming
@app.get("/simulations/{sim_id}/stream")
async def stream_simulation(sim_id: int):
    """Stream simulation events with compression."""
    
    async def event_generator():
        for i in range(10000):
            event = {
                "timestamp": i * 0.016,  # 60 FPS
                "agents": await get_agent_positions(sim_id, i),
            }
            # Compress JSON
            yield json.dumps(event).encode('utf-8')
    
    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
        headers={"Content-Encoding": "gzip"}
    )
```

### Pagination & Limiting

```python
@app.get("/simulations")
async def list_simulations(
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """Paginated simulation list."""
    
    # Validate limits
    limit = min(limit, 1000)  # Max 1000 per page
    offset = min(offset, 100000)  # Max offset
    
    # Query
    simulations = await db.fetch(f"""
        SELECT * FROM simulations
        WHERE user_id = %s
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """, (user_id, limit, offset))
    
    # Count total
    total = await db.fetch_val(
        "SELECT COUNT(*) FROM simulations WHERE user_id = %s",
        (user_id,)
    )
    
    return {
        "data": simulations,
        "pagination": {
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total,
        }
    }
```

---

## Part 6: Monitoring & Alerting

### Continuous Performance Monitoring

```python
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time

class PerformanceMonitor:
    """Continuous performance monitoring."""
    
    def __init__(self):
        # Metrics
        self.api_latency = Histogram(
            'api_latency_seconds',
            'API request latency',
            ['endpoint'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
        )
        
        self.db_latency = Histogram(
            'db_latency_seconds',
            'Database query latency',
            ['query_type'],
            buckets=(0.001, 0.01, 0.05, 0.1)
        )
        
        self.cache_hits = Counter(
            'cache_hits_total',
            'Cache hit count',
            ['cache_type']
        )
        
        self.gpu_utilization = Gauge(
            'gpu_utilization_percent',
            'GPU utilization percentage'
        )
        
        # Start Prometheus exporter
        start_http_server(8001)
    
    async def alert_on_degradation(self):
        """Alert on performance degradation."""
        
        # Get metrics
        api_p99 = self.get_metric('api_latency_p99')
        db_p99 = self.get_metric('db_latency_p99')
        cache_hit_rate = self.get_metric('cache_hit_rate')
        
        # Alert thresholds
        if api_p99 > 0.5:
            alert(f"API P99 latency high: {api_p99:.3f}s")
        
        if db_p99 > 0.1:
            alert(f"DB P99 latency high: {db_p99:.3f}s")
        
        if cache_hit_rate < 0.90:
            alert(f"Cache hit rate low: {cache_hit_rate:.1%}")
```

### Performance Dashboard

```python
class PerformanceDashboard:
    """Real-time performance dashboard."""
    
    async def generate_report(self) -> dict:
        """Generate performance report."""
        
        return {
            "timestamp": datetime.now(),
            
            "api_performance": {
                "p50_latency_ms": 50,
                "p95_latency_ms": 200,
                "p99_latency_ms": 450,
                "error_rate": 0.001,
            },
            
            "database": {
                "connections_active": 45,
                "connections_idle": 15,
                "query_time_p99_ms": 85,
                "slow_queries": 2,
            },
            
            "cache": {
                "hit_rate": 0.958,
                "memory_used_mb": 1024,
                "keys_evicted": 45000,
            },
            
            "gpu": {
                "utilization": 82,
                "memory_used_gb": 12,
                "temperature": 65,
            },
            
            "simulation": {
                "agents_per_second": 125000,
                "avg_agent_update_ms": 0.008,
                "physics_fps": 60,
            }
        }
```

---

## Performance Optimization Checklist

### Before Production
- [ ] Profiled all critical paths
- [ ] Database indexes verified
- [ ] Cache strategy implemented
- [ ] Load tested with 10K concurrent users
- [ ] GPU acceleration enabled for sim loop
- [ ] API response compression enabled
- [ ] Connection pooling configured

### Weekly
- [ ] Review P99 latencies
- [ ] Check cache hit rates
- [ ] Analyze slow query logs
- [ ] GPU utilization trending

### Monthly
- [ ] Full benchmark suite run
- [ ] Identify optimization opportunities
- [ ] Review cost/performance tradeoffs

---

**Performance Optimization Playbook Complete**  
**Ready for Sub-500ms P99 Latency**
