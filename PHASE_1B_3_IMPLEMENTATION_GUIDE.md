# Phase 1B-3 Implementation Guide

Quick-start guide for implementing Phases 1B (Advanced Visualization), 1C (Sensor Integration & UE5), 2 (AI), and 3 (Physics).

## Current Status (v0.3.0)

✓ Phase 0: Complete (Backend API, physics engine, tests)
✓ Phase 1A: Complete (WebSocket streaming, basic 3D rendering)
→ Phase 1B: Ready to start (sensor visualization)

## Phase 1B: Advanced Visualization (Weeks 1-4)

### Start: RGB Camera Feed Display (1B.1)

**Files to modify:**
```
backend/src/services/
  ├── simulation_engine.py (add sensor capture)
  ├── frame_streaming.py (add RGB data)
  └── visualization_integration.py (capture RGB frames)

frontend/src/
  ├── components/SensorPanel.tsx (add RGB display)
  └── hooks/useWebSocket.ts (handle RGB data)
```

**Implementation Steps:**

1. **Enable RGB capture in SimulationEngine**
   ```python
   # Add to Agent class:
   self.rgb_sensor = RGBSensor(config)
   
   # Add to SimulationEngine:
   def capture_agent_sensor_data(self, agent_id):
       agent = self.agents[agent_id]
       return agent.rgb_sensor.capture_frame()  # bytes
   ```

2. **Modify frame_streaming to include RGB**
   ```python
   # In VisualizationStreamer._capture_sensors():
   sensors[agent.id] = SensorData(
       rgb=self.engine.capture_agent_sensor_data(agent.id),
       # ... depth, lidar, thermal
   )
   ```

3. **Update frontend SensorPanel**
   ```tsx
   // In SensorPanel.tsx:
   const [rgbData, setRgbData] = useState<string | null>(null);
   
   // Decode base64 RGB in useWebSocket
   if (frameData.sensors[agentId]?.rgb) {
       setRgbData('data:image/jpeg;base64,' + frameData.sensors[agentId].rgb);
   }
   
   // Display in component
   <img src={rgbData} alt="RGB Feed" />
   ```

4. **Tests (8+ tests)**
   - RGB capture returns valid JPEG
   - Base64 encoding works
   - Display renders image
   - Performance <100ms per frame
   - Handles missing sensors gracefully

**Success Criteria:**
- RGB camera displays at 30 FPS
- No lag or artifacting
- Clean 16:9 aspect ratio
- Agent selection updates feed immediately

**Time Estimate:** 5 days
**Complexity:** Medium
**Dependency:** Phase 1A (WebSocket)

---

### Next: Depth Heatmap (1B.2) → Lidar Point Cloud (1B.3) → Thermal (1B.4)

Each sensor visualization follows same pattern:
1. Add data capture in SimulationEngine
2. Encode in frame_streaming
3. Display in frontend component
4. Add tests

**Timeline:**
- 1B.1 RGB: Days 1-5
- 1B.2 Depth: Days 6-9
- 1B.3 Lidar: Days 10-15
- 1B.4 Thermal: Days 16-18

---

## Phase 1C: Sensor Integration & UE5 Bridge (Weeks 5-9)

### Prerequisites
- Complete Phase 1B sensor visualization
- Unreal Engine 5.3+ installed
- gRPC knowledge

### Key Tasks

**1C.1-1C.4: Sensor Accuracy Improvements**
- Implement noise and distortion
- Add realistic camera artifacts
- Model depth sensor limitations
- Thermal emissivity simulation

**1C.5-1C.6: gRPC & UE5 Plugin**
- Create .proto definitions
- Implement gRPC server in FastAPI
- Build UE5 plugin (C++)
- Connect Python↔UE5 communication

**1C.7-1C.8: Sensor Capture in UE5**
- Implement render target captures
- Raycast lidar from UE5
- Material-based thermal simulation
- Stream world geometry to UE5

**Timeline:** 4-5 weeks consecutive

---

## Phase 2: AI Agents & Behavior (Weeks 10-15)

### Start: Behavior Tree System (2.1)

**Architecture:**
```python
class BehaviorNode:
    def evaluate(self, agent, dt) -> bool:
        pass

class Sequence(BehaviorNode):
    # All children must succeed

class Selector(BehaviorNode):
    # First child to succeed wins

class Action(BehaviorNode):
    # Movement, state change, etc.
```

### Key Features

**2.1: Behavior Trees**
- Composite nodes (Sequence, Selector, Parallel)
- Decorators (Inverter, Repeater, Limiter)
- YAML configuration loading
- Visual debugger

**2.2: Pathfinding & Navigation**
- A* algorithm with caching
- Navmesh generation
- RVO collision avoidance
- 1000+ agent support

**2.3: Agent Memory**
- Observation tracking
- Goal persistence
- Memory decay
- Fact database

**2.4: Multi-Agent Communication**
- Message passing
- Leader election
- Broadcast messaging

**2.5-2.7: NLP & Goals**
- Claude API integration
- World generation from text
- Goal/mission generation
- Personality system

**Timeline:** 5-6 weeks

---

## Phase 3: Physics Optimization (Weeks 16-20)

### GPU Physics (3.1)

**CUDA Implementation:**
```cpp
__global__ void update_agents_kernel(
    Agent* agents,
    int num_agents,
    float dt
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < num_agents) {
        // Update physics on GPU
    }
}
```

**Target:** 10x speedup (100K agents in <16ms)

### Advanced Collisions (3.2)

- Spatial hashing for broad phase
- Swept collision detection
- Constraint solving
- 1M agent support

### Memory Optimization (3.7)

- Object pooling
- <1KB per agent
- No GC pauses
- Efficient memory layout

**Timeline:** 4-5 weeks

---

## Development Workflow

### Daily Standup Checklist

```
[ ] Run tests: pytest -v --cov=src
[ ] Check performance: pytest --benchmark-only
[ ] Verify WebSocket streaming: npm run dev (frontend)
[ ] Manual testing: Create simulation, watch browser
```

### Git Workflow

```bash
# Create feature branch
git checkout -b phase-1b-rgb-camera

# Commit after each task (1-2 hours)
git commit -m "feat: Add RGB camera feed to sensor panel

- Capture RGB from sensors
- Encode as base64 JPEG
- Display in frontend component
- Add 8+ tests for accuracy"

# Push when ready for review
git push origin phase-1b-rgb-camera

# Create PR on GitHub
gh pr create --title "Phase 1B.1: RGB Camera Feed" \
  --body "Displays live RGB feed in sensor panel at 30 FPS"
```

### Branch Names
- `phase-1b-*` for 1B tasks
- `phase-1c-*` for 1C tasks
- `phase-2-*` for 2.x tasks
- `phase-3-*` for 3.x tasks

### Commit Message Format
```
feat: Add feature name

- Bullet 1
- Bullet 2
- Bullet 3

Add X tests. Addresses PHASE_TASKS.md item Y.Z
```

---

## Testing Strategy

### Unit Tests
- Sensor data capture
- Data encoding/decoding
- Physics calculations
- Behavior tree evaluation

### Integration Tests
- End-to-end visualization
- WebSocket streaming
- Frame timing
- Agent physics updates

### Performance Tests
```python
def test_rgb_capture_performance():
    """RGB capture should complete in <33ms (30 FPS)."""
    start = time.time()
    rgb_data = sensor.capture_frame()
    elapsed = time.time() - start
    assert elapsed < 0.033  # 30ms budget
```

### Manual Testing
```bash
# Start backend
cd backend && python -m uvicorn src.main:app --reload

# Start frontend
cd frontend && npm run dev

# Create simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -d '{"scenario":"parking_lot","num_agents":50,"duration":60}'

# Open browser
http://localhost:5173/?id=1
# Watch visualization in real-time
```

---

## Key Metrics to Track

### Performance
- Frame rate: Target 60 FPS
- Latency: <50ms WebSocket propagation
- Memory: <1GB for 1M agents
- CPU: <5% per connected client

### Quality
- Code coverage: >90%
- Type safety: mypy --strict passing
- Security: bandit, safety clean
- Tests: All passing with no flakes

### User Experience
- Simulation startup: <1s
- First frame displayed: <2s
- Sensor data: 30 FPS
- Control responsiveness: <100ms

---

## Debugging Tips

### WebSocket Issues
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check connected clients
from routers.visualization import connected_clients
print(connected_clients)  # See active connections
```

### Performance Bottlenecks
```bash
# Profile backend
python -m cProfile -s cumtime backend/src/main.py

# Profile frontend
Chrome DevTools → Performance tab → Record
```

### Visual Debugging
```javascript
// In browser console
// Check frame data
window.frameData = lastFrameReceived;

// Check WebSocket state
console.log(ws.readyState);  // 1 = OPEN
```

---

## Success Criteria by Phase

### Phase 1B Complete
- [ ] All 4 sensor types displayed (RGB, Depth, Lidar, Thermal)
- [ ] 60 FPS rendering maintained
- [ ] Collision effects visible
- [ ] Trajectory drawing works
- [ ] All camera modes functional
- [ ] Statistics dashboard shows live data
- [ ] Agent filtering works
- [ ] 50+ tests passing
- [ ] Documentation complete

### Phase 1C Complete
- [ ] gRPC communication working
- [ ] UE5 plugin compiles
- [ ] Sensor capture in UE5
- [ ] World streaming works
- [ ] State synchronization <16ms
- [ ] 100+ tests passing
- [ ] Zero data loss
- [ ] Enterprise-ready

### Phase 2 Complete
- [ ] 100 agents with behavior trees
- [ ] A* pathfinding <1ms per call
- [ ] 1000+ agents navigate without deadlock
- [ ] Agent communication works
- [ ] NLP world generation 95%+ accurate
- [ ] Personality system observable
- [ ] 200+ tests passing

### Phase 3 Complete
- [ ] 10x physics speedup on GPU
- [ ] 1M agents simulated
- [ ] <16ms physics frame
- [ ] Advanced collisions working
- [ ] Memory <1KB per agent
- [ ] 150+ tests passing

---

## Resources & References

- Behavior Trees: https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_game_development)
- A* Pathfinding: https://en.wikipedia.org/wiki/A*_search_algorithm
- RVO Avoidance: http://gamma.cs.unc.edu/RVO2/
- gRPC Tutorial: https://grpc.io/docs/languages/python/
- UE5 Development: https://dev.epicgames.com/documentation/en-us/unreal-engine
- CUDA Programming: https://developer.nvidia.com/cuda-learning-paths

---

**Ready to implement. Start with Phase 1B.1: RGB Camera Feed Display.**
