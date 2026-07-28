# Real-Time Browser Visualization Architecture

## Overview

PyRoboSimulator's core value is showing agents moving through worlds with realistic sensors. This requires real-time visualization with:
- Live 3D world rendering
- Agent positions and states
- Sensor data streams (RGB, depth, lidar, thermal)
- Interactive controls (play, pause, speed)
- Multiple camera angles

## System Architecture

```
┌──────────────────────────────────────┐
│   Browser (React/Three.js)           │
│  - 3D world visualization            │
│  - Agent rendering                   │
│  - Sensor data display               │
│  - User interaction                  │
└──────────────────┬───────────────────┘
                   │
                   │ WebSocket (binary)
                   │
┌──────────────────▼───────────────────┐
│   FastAPI Backend                    │
│  - SimulationEngine (physics)        │
│  - Real-time frame streaming         │
│  - Camera/view management            │
│  - Sensor data serialization         │
└──────────────────┬───────────────────┘
                   │
                   ├─► PostgreSQL (persistent state)
                   ├─► Redis (frame cache)
                   └─► WebSocket broadcast
```

## Protocol: Binary WebSocket Frames

Send compact binary frames to minimize latency (target: <50ms per frame @ 60 FPS).

### Frame Format (MessagePack)

```
{
  "type": "frame",
  "frame_id": 123,
  "timestamp_ms": 1234567890,
  "agents": [
    {
      "id": 1,
      "pos": [100.5, 50.2, 0.0],
      "rot": [0.0, 0.0, 45.0],
      "vel": [5.0, 0.0, 0.0],
      "state": "moving"
    }
  ],
  "events": [
    {
      "id": 1,
      "type": "collision",
      "agent_id": 1,
      "other_id": 2,
      "pos": [100.5, 50.2, 0.0]
    }
  ],
  "sensors": {
    "1": {
      "rgb": "base64:...",
      "depth": "base64:...",
      "lidar": [[x,y,z], ...],
      "thermal": "base64:..."
    }
  }
}
```

## Components

### 1. Backend (FastAPI)

**New Endpoints:**
- `GET /api/v1/simulations/{id}/stream` — WebSocket streaming
- `GET /api/v1/simulations/{id}/camera` — Camera control
- `GET /api/v1/simulations/{id}/sensors` — Sensor configuration

**Real-Time Streaming:**
- Broadcast frames to all connected clients
- Queue mechanism (Redis) for buffering
- Frame rate control (configurable)

### 2. Frontend (React + Three.js)

**3D Visualization:**
- Three.js for 3D rendering
- Agent meshes with dynamic position updates
- World geometry (obstacles, boundaries)
- Particle effects for collisions/events

**Sensor Display:**
- RGB camera feed (side panel or overlay)
- Depth heatmap
- Lidar point cloud
- Thermal false-color image

**Controls:**
- Play/pause/resume
- Speed adjustment (0.5x, 1x, 2x, 4x)
- Camera angles (free, top-down, agent-follow)
- Filter agents by state/type
- Event timeline

**Performance:**
- Virtual scrolling for many agents
- LOD (level of detail) for distant objects
- Texture compression
- Request animation frame for smooth 60 FPS

## Implementation Phases

### Phase 1A: Backend WebSocket Streaming
1. Add WebSocket endpoint to FastAPI
2. Frame serialization (MessagePack)
3. Real-time frame broadcast
4. Client connection management

### Phase 1B: Basic 3D Visualization
1. React + Three.js scaffold
2. World grid/boundaries
3. Agent sphere rendering
4. Position updates via WebSocket

### Phase 1C: Sensor Visualization
1. RGB camera feed display
2. Depth map (grayscale or heatmap)
3. Lidar point cloud (WebGL)
4. Thermal false-color rendering

### Phase 1D: Interactive Controls
1. Play/pause/resume controls
2. Speed adjustment
3. Camera angle selection
4. Agent filtering

## Performance Targets

- WebSocket latency: <50ms frame propagation
- Browser frame rate: 60 FPS (16ms per frame)
- Network bandwidth: <10 Mbps for 100 agents
- Browser memory: <500MB for full scene
- Backend CPU: <5% per connected client

## Data Structure: World State

```python
@dataclass
class WorldFrame:
    """Real-time world state for visualization."""
    frame_id: int
    timestamp_ms: float
    agents: List[AgentFrame]
    events: List[EventFrame]
    
@dataclass
class AgentFrame:
    """Agent state for a single frame."""
    id: int
    position: Vector3
    rotation: Vector3  # Euler angles
    velocity: Vector3
    state: str  # "idle", "moving", "goal_reached", "collision"
    
@dataclass
class EventFrame:
    """Event that occurred this frame."""
    id: int
    type: str  # "collision", "goal_reached", etc
    agent_id: int
    position: Vector3
    data: Dict[str, Any]  # Event-specific data
```

## Browser Client Lifecycle

1. User opens simulation URL
2. Browser connects to WebSocket
3. Server starts sending frames at 60 FPS
4. Browser renders frames in real-time
5. User controls (speed, camera) update server
6. Server acknowledges and adjusts frame rate

## Deployment

### Production (Kubernetes)
- WebSocket service with sticky sessions
- Redis for frame queueing
- Load balancing via NGINX
- Browser caching for static assets

### Docker
- Single container with frontend + backend
- Development: hot-reload enabled
- Production: minified assets, gzip compression

## Security Considerations

- WebSocket over WSS (TLS)
- Authentication before streaming
- Rate limiting (frames per second)
- Input validation for camera/control commands
- No sensitive data in frame stream

## Browser Compatibility

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

**Expected Timeline:** 4-6 weeks for full implementation
**Next:** Backend WebSocket streaming
