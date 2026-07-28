# PyRoboSimulator Database Schema

Production PostgreSQL schema for PyRoboSimulator backend.

## Overview

The schema is designed for:
- **Performance:** Simulations with 100K+ agents and millions of events/day
- **Scalability:** Horizontal partitioning ready (by simulation or time)
- **Integrity:** Foreign keys, constraints, audit columns
- **Observability:** Comprehensive indexing for analytics

## Tables

### users

Stores user accounts and authentication.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes:**
- `idx_users_email` - For login lookups

**Use Cases:**
- User registration & login
- Permission checks
- Audit trails

---

### scenarios

Reusable simulation scenarios (templates).

```sql
CREATE TABLE scenarios (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    world_config JSON NOT NULL,
    published BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Schema Example:**
```json
{
    "bounds": {"x_min": 0, "x_max": 1000, "y_min": 0, "y_max": 1000},
    "grid_size": 50,
    "spawn_zones": [{"x": 100, "y": 100, "radius": 50, "count": 100}],
    "obstacles": [{"x": 500, "y": 500, "radius": 100}],
    "weather": "sunny",
    "time_of_day": "noon"
}
```

**Indexes:**
- `idx_scenarios_published` - List published scenarios
- `idx_scenarios_created_at` - Sort by recency

**Use Cases:**
- Scenario browsing & filtering
- Simulation creation (clone scenario)
- Analytics on popular scenarios

---

### simulations

Individual simulation runs (instances).

```sql
CREATE TABLE simulations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scenario_id INTEGER,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'created',
    num_agents INTEGER NOT NULL,
    duration FLOAT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
);
```

**Status Values:**
- `created` - Initial state
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Execution error
- `cancelled` - User stopped

**Indexes:**
- `idx_simulations_user_id` - List user's simulations
- `idx_simulations_status` - Filter by status
- `idx_simulations_created_at, id` - Sort & paginate
- `idx_simulations_scenario_id` - Scenario analytics

**Use Cases:**
- List user's simulations
- Filter by status (show running sims)
- Pagination & sorting
- Simulation history

---

### agents

Individual agents within a simulation (100K-1M per simulation).

```sql
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    simulation_id INTEGER NOT NULL,
    agent_type VARCHAR(50) DEFAULT 'vehicle',
    position_x FLOAT NOT NULL,
    position_y FLOAT NOT NULL,
    position_z FLOAT DEFAULT 0.0,
    velocity_x FLOAT DEFAULT 0.0,
    velocity_y FLOAT DEFAULT 0.0,
    velocity_z FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
);
```

**Agent Types:**
- `vehicle` - Autonomous vehicle
- `pedestrian` - Walking agent
- `robot` - Mobile robot
- `obstacle` - Static obstacle

**Indexes:**
- `idx_agents_simulation_id` - Query all agents in simulation
- `idx_agents_position_x`, `idx_agents_position_y` - Spatial queries

**Performance Notes:**
- Agents table can grow to 100M+ rows
- Partitioning recommended by simulation_id or time
- Sensor queries use position indexes heavily

**Use Cases:**
- Query agents within simulation
- Spatial queries (agents near point)
- Collision detection
- Results generation

---

### events

Timestamped events during simulation (millions per simulation).

```sql
CREATE TABLE events (
    id BIGINT PRIMARY KEY,
    simulation_id INTEGER NOT NULL,
    agent_id INTEGER,
    timestamp FLOAT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    data JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);
```

**Event Types:**
- `step_complete` - Simulation step finished
- `collision` - Agents collided
- `goal_reached` - Agent reached destination
- `sensor_reading` - Sensor data captured
- `state_change` - Agent state change
- `error` - Runtime error

**Data Example (collision event):**
```json
{
    "agents": [1, 2],
    "position": {"x": 100.5, "y": 200.3},
    "impact_force": 2.5
}
```

**Indexes:**
- `idx_events_simulation_timestamp` - Most critical for queries
- `idx_events_agent_id` - Filter by agent
- `idx_events_event_type` - Filter by type

**Partitioning Strategy:**
- Partition by `simulation_id` (1000+ partitions)
- Each simulation gets dedicated partition
- Automatic cleanup after 90 days
- Archival to cold storage for long-term retention

**Use Cases:**
- Fetch all events for simulation (most common query)
- Collision analysis
- Agent trajectory reconstruction
- Performance monitoring
- Compliance auditing

---

## Query Patterns

### List User's Simulations (paginated)

```sql
SELECT id, name, status, num_agents, created_at
FROM simulations
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

**Index:** `idx_simulations_created_at`

---

### Fetch Simulation Results

```sql
SELECT * FROM events
WHERE simulation_id = $1
ORDER BY timestamp
LIMIT 10000;
```

**Index:** `idx_events_simulation_timestamp`

---

### Get Agent Trajectory

```sql
SELECT timestamp, position_x, position_y, position_z
FROM events
WHERE simulation_id = $1 AND agent_id = $2
ORDER BY timestamp;
```

**Index:** `idx_events_simulation_timestamp, idx_events_agent_id`

---

### Collision Analysis

```sql
SELECT * FROM events
WHERE simulation_id = $1
AND event_type = 'collision'
ORDER BY timestamp;
```

**Index:** `idx_events_simulation_timestamp`

---

## Performance Targets

| Operation | Target | Tool |
|-----------|--------|------|
| List simulations | <50ms | Index: idx_simulations_created_at |
| Fetch 10K events | <100ms | Index: idx_events_simulation_timestamp |
| Agent trajectory | <200ms | Indexes: simulation_id, agent_id, timestamp |
| Collision search | <500ms | Index: event_type, simulation_id |

## Scaling Strategy

### Current (Phase 0)
- Single PostgreSQL instance
- All tables in public schema
- No partitioning

### Phase 1 (1M events/day)
- Partition events by simulation_id
- Separate read replicas for analytics
- Connection pooling (PgBouncer)

### Phase 2+ (100M+ events/day)
- Sharding by simulation_id
- Time-series database for metrics
- Separate cold storage for archives
- Analytics warehouse (ClickHouse)

## Backup & Recovery

**Backup Schedule:**
- Hourly: Last 24 hours
- Daily: Last 30 days
- Weekly: Last 52 weeks
- Monthly: 7 years

**Recovery Time Objective (RTO):** <1 hour

**Recovery Point Objective (RPO):** <5 minutes

## Maintenance

### Routine Tasks
```bash
# Vacuum & analyze (weekly)
VACUUM ANALYZE;

# Update statistics
ANALYZE;

# Monitor index bloat
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;  -- Unused indexes
```

### Monitoring Queries

```sql
-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index effectiveness
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Active connections
SELECT datname, count(*) as connections
FROM pg_stat_activity
GROUP BY datname;
```

---

## Data Dictionary

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | INTEGER | No | Auto-increment | Primary key |
| created_at | TIMESTAMP | No | NOW() | Row creation time |
| updated_at | TIMESTAMP | No | NOW() | Last modification |
| position_x | FLOAT | No | | X coordinate |
| position_y | FLOAT | No | | Y coordinate |
| position_z | FLOAT | Yes | 0.0 | Z coordinate (elevation) |
| velocity_* | FLOAT | Yes | 0.0 | Movement vector |
| status | VARCHAR(50) | No | | Enum-like field |
| data | JSON | Yes | | Flexible event payload |

---

## Security

- **Row-Level Security:** Enabled for multi-tenant isolation (Phase 2+)
- **Encryption:** AES-256 at rest, TLS 1.3 in transit
- **Access Control:** Database role per application (no superuser)
- **Audit Logging:** All DDL changes logged to audit_log table

---

**Schema Version:** 001  
**Last Updated:** 2024-07-29  
**Maintenance:** Alembic migrations system
