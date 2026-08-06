# PyRoboSimulator: Visual Rendering & World Generation Engine
## Architecture & Phased Roadmap

**Vision:** AAA-quality, sensor-faithful, NLP-driven world simulation engine.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Instruction (NLP)                       │
│    "Tokyo after cherry blossom season at sunset, light rain"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│         World Spec Generation (Claude API + Reasoning)          │
│  Generates: terrain, weather, season, architecture, lighting,   │
│             traffic, population, environmental conditions       │
│                    → JSON World Specification                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
┌─────────▼────────┐ ┌──────▼──────────┐ ┌────▼─────────────┐
│  Terrain Layer   │ │  Asset Manager  │ │  Lighting Engine │
│  (PyTerrainMap)  │ │  (Procedural)   │ │  & Weather Sys   │
└──────────────────┘ └─────────────────┘ └──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Unreal Engine 5 World Orchestration                │
│  ✓ Load terrain, place assets, configure lighting              │
│  ✓ Run simulation, capture visuals                             │
│  ✓ Manage sensors (RGB, Lidar, Depth, Thermal, etc.)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼──────┐     ┌─────▼──────┐   ┌─────▼──────┐
    │  RGB Image │     │ Point Cloud│   │  Heatmap   │
    │  Sequences │     │  (Lidar)   │   │  (Thermal) │
    └────────────┘     └────────────┘   └────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│          API Layer (REST/gRPC) for PyRoboReplay                │
│  Exposes: world generation, simulation control, sensor access  │
└────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Rendering** | Unreal Engine 5 | Native Nanite (megageometry), Lumen (GI), Temporal Super Resolution, Metahuman |
| **Procedural Gen** | Houdini Engine (UE5 plugin) or Substance 3D Designer | Procedural cities, terrain, assets; Python API available |
| **World Spec** | Claude API (Sonnet 5) + JSON Schema | Natural language → structured simulation config |
| **Terrain** | PyTerrainMap (existing) + WorldCreator/GeoForge | Digital elevation, satellite imagery, LiDAR integration |
| **Materials** | Quixel Megalibs + custom PBR authoring | 20K+ photoscanned materials; weather/wear procedurally added |
| **Vegetation** | SpeedTree (UE5 integration) + procedural generation | Species-aware, seasonal variation, physics-interactive |
| **Weather/Sky** | Volumetric Clouds (Lumen) + Unreal's weather systems | Real-time volumetric fog, God rays, dynamic cloud formation |
| **Traffic/Crowds** | Unreal's Replicant AI (NPC system) + custom behavior trees | Realistic pedestrians, vehicles; sensor-responsive behavior |
| **Lighting** | Lumen (real-time GI) + Unreal's Sunlight + Volumetric Lighting | Photorealistic dynamic lighting; weather-responsive |
| **Sensor Simulation** | PyRoboReplay (existing) + UE5 capture pipeline | RGB, Lidar point cloud, thermal, depth, event camera |
| **API Bridge** | FastAPI + gRPC (Python) + UE5 Pixel Streaming or custom socket | Communicate with PyRoboSimulator backend |
| **Data Persistence** | PostgreSQL + S3 (world snapshots, event logs) | Versioned worlds, event causality chains, reproducibility |

---

## Phase Breakdown

### **Phase 0: PoC Validation (2–3 weeks)**

**Goal:** Prove the end-to-end loop: NLP → world spec → rendered visuals → sensor outputs.

**Deliverables:**
1. **World Spec Generator**
   - Claude API integration (Sonnet 5 with extended thinking)
   - Input: natural language instruction
   - Output: JSON schema (terrain, weather, lighting, assets, time-of-day)
   - Example: `"Tokyo after cherry blossom season at sunset"` → JSON with seasonal params, cherry tree spawns, sunset time, cloud cover, humidity

2. **Single Micro-Scene in UE5**
   - Manually curated 200m × 200m outdoor scene (parking lot + trees + building)
   - PBR materials (concrete, asphalt, wet asphalt, grass, leaves)
   - Dynamic lighting (sun arc, shadow cascades)
   - Basic weather (rain, clouds, fog)
   - Manually place trees, adjust seasonal colors

3. **Sensor Output Capture**
   - RGB camera feed (1080p @ 30Hz)
   - Depth map (aligned with RGB)
   - Lidar point cloud (16-channel sim, 10 Hz)
   - Verify: rain occlusion in Lidar, reflections in RGB, wet-road material response
   - Thermal output (camera sees different emissivity on wet vs. dry)

4. **API Bridge (FastAPI)**
   - `POST /generate-world` (natural language → world spec)
   - `POST /load-world` (world spec → UE5 instance)
   - `GET /sensor/rgb`, `/sensor/lidar`, `/sensor/depth`
   - `POST /weather` (update weather parameters in real-time)

**Success Criteria:**
- [ ] NLP → world spec generation works reliably
- [ ] UE5 scene loads spec and updates visuals
- [ ] Lidar correctly occludes in rain; RGB shows reflections
- [ ] Thermal output shows emissivity differences
- [ ] API response latency < 100ms for sensor queries

**Effort:** 1 engineer, 2–3 weeks

---

### **Phase 1: Core Platform (6–8 weeks)**

**Goal:** Extend PoC to procedurally generated urban scenes with traffic, realistic weather, and seasonal variation.

**Deliverables:**

1. **Procedural City Generator**
   - Input: city location (lat/lon), region (Tokyo, Mumbai, Mars colony), season, weather, time-of-day
   - Output: 2km × 2km procedurally placed buildings, roads, parks
   - Streets follow OSM data (if real city) or procedural grid (if fictional)
   - Building height/style based on zoning (residential, commercial, industrial)
   - Rooftop detail (HVAC, solar, antennas, helipads for drones)
   - Street furniture (lights, benches, traffic signs, billboards)

2. **Traffic & Pedestrian System**
   - Procedural vehicle spawning along roads
   - Traffic lights, lane following, collision avoidance
   - Regional driving behavior (Japan: orderly; India: chaotic)
   - Pedestrian crowds: sidewalk navigation, group dynamics
   - Weather-aware: slower traffic in rain, fewer pedestrians in heavy weather

3. **Weather System v2**
   - Real-time weather transitions (sunny → cloudy → rain)
   - Impact on materials: wet roads, puddle formation, tire marks
   - Impact on lighting: reduced sunlight intensity, darkened sky
   - Impact on sensors: rain occlusion in Lidar (simulate droplet scatter), reduced RGB contrast, thermal sees warm rain
   - Seasonal shifts: vegetation color, snow accumulation, water freezing

4. **Seasonal System**
   - Spring: cherry blossoms (Japan), fresh greens
   - Summer: dense foliage, dry terrain, blue sky
   - Autumn: leaf color transition, leaf fall particles
   - Winter: snow accumulation (roads/roofs), frozen water, bare trees
   - Auto-transition based on latitude/date

5. **Vegetation Layer**
   - Tree/bush placement respecting climate (tropical, temperate, desert)
   - Species variation per region (cherry trees in Japan, palm trees in Mumbai)
   - Seasonal color/foliage changes
   - Wind interaction (leaves sway, branches bend)
   - Occlusion interaction with Lidar (leaves scatter rays)

6. **Water Simulation**
   - Rivers and lakes with realistic flow
   - Rain pooling and runoff (procedural puddle placement)
   - Wave simulation on larger water bodies
   - Reflections/refraction in RGB
   - Water color based on pollution/sediment
   - Robot locomotion physics affected by water depth

7. **Lighting v2**
   - Real sun arc (latitude/longitude/date-dependent)
   - Time-of-day: sunrise, golden hour, blue hour, noon, night
   - Realistic sky (Rayleigh scattering, Mie scattering)
   - Cloud shadows cast in real-time
   - Street lights, vehicle headlights, building lights
   - Atmospheric haze (pollution, humidity)

8. **Extended Sensor Suite**
   - RGB + Stereo depth
   - Lidar (rotating 16/32/64-channel simulation)
   - Radar (doppler, range)
   - Thermal IR (emissivity maps per material)
   - Event camera (DVS sim, asynchronous pixel changes)
   - IMU output (gravity vector, acceleration from world motion)
   - GPS/GNSS (with optional jitter/multipath)

9. **Expanded API**
   - `/generate-world` improved with region/season/weather inference
   - `/simulation/start`, `/simulation/pause`, `/simulation/step`
   - `/world/query` (entity positions, semantic labels, causality)
   - `/sensor/all` (batch capture all sensor modalities)
   - `/export/scene` (save world snapshot, replay events)

**Success Criteria:**
- [ ] Generate Tokyo, Mumbai, and a fictional Mars colony
- [ ] Procedural city layout matches reference imagery
- [ ] Traffic behavior region-appropriate (Japan vs. India)
- [ ] Seasonal color changes work across all asset types
- [ ] All sensor modalities respond correctly to weather
- [ ] Lidar point cloud density decreases in rain (realistic)
- [ ] Thermal imagery shows correct emissivity
- [ ] API handles 10 concurrent worlds

**Effort:** 3–4 engineers, 6–8 weeks

---

### **Phase 2: Photorealism & Advanced Rendering (8–10 weeks)**

**Goal:** AAA-game visual quality + scientifically accurate sensor modeling.

**Deliverables:**

1. **Advanced PBR Material System**
   - 100+ unique materials with weathering
   - Puddle-water layering on roads
   - Mud, dirt accumulation
   - Moss/algae growth on surfaces
   - Paint fading, rust, oxidation
   - Glass reflections + interior visibility
   - Cloth deformation (clothing on pedestrians)

2. **Cinematic Rendering Features**
   - Depth of field (simulation of camera focus)
   - Motion blur (moving vehicles, pedestrians)
   - Bloom/glare (bright headlights, sun reflections)
   - HDR tone mapping (exposure adaptation)
   - Temporal anti-aliasing (reduce flicker)
   - Lens artifacts (chromatic aberration, vignetting)
   - Cinematic camera modes (drone, vehicle, robot POV, satellite)

3. **Advanced Atmospheric Effects**
   - Multi-layer volumetric clouds (Lumen-based)
   - Dust storms (Mars, desert scenes)
   - Fog, mist, haze (density per altitude, time-of-day)
   - Light scattering (God rays, crepuscular rays)
   - Aurora effects (high-latitude worlds)
   - Pollution haze (urban environments)

4. **Photogrammetry & Scan Data Integration**
   - Import real-world scans (buildings, streets from photogrammetry)
   - Automatic material extraction
   - Blend procedural and scanned assets

5. **Physics-Accurate Sensor Simulation**
   - Lidar: simulate angular resolution, range cutoff, rain scatter (simulate droplet probability)
   - Thermal: per-pixel emissivity lookup, atmospheric transmission loss
   - Radar: Doppler shift for moving targets, multipath detection
   - RGB: global illumination correct (Lumen provides this), chromatic aberration, lens flare
   - Event camera: asynchronous pixel-level changes, temporal contrast threshold

6. **Advanced Weather Physics**
   - Rain accumulation simulation (water depth per surface)
   - Mud formation on unpaved roads
   - Flooding simulation (water level rise)
   - Snow accumulation (build-up on surfaces, gravity settling)
   - Wind effects (particle drift, object interaction)
   - Hail damage (dents on cars, pitting on materials)

7. **Advanced Traffic & Crowd Simulation**
   - Accidents (vehicle collision, debris)
   - Road works (equipment, warnings, traffic diversion)
   - Delivery robots (autonomous small vehicles)
   - Bicycle traffic (with physics)
   - Crowd emotions (panic in rain, gathering in sunny areas)
   - Accessibility features (wheelchairs, visual aids)

8. **Real-Time Global Illumination**
   - Lumen (UE5 native) for dynamic GI
   - Light bounces off rain, wet surfaces
   - Shadow cascades from complex geometry

**Success Criteria:**
- [ ] Visual quality passes "AAA game" inspection (comparison screenshots)
- [ ] Lidar rain scatter is physically plausible (compared to real-world data)
- [ ] Thermal output matches emissivity lookup tables
- [ ] Puddles and mud form realistically after rain
- [ ] Cinematic mode produces publication-quality renders

**Effort:** 4–5 engineers, 8–10 weeks

---

### **Phase 3: Planetary Scale & Country-Scale Worlds (10–12 weeks)**

**Goal:** Support entire cities, countries, planets without performance degradation.

**Deliverables:**

1. **Hierarchical LOD (Level of Detail) System**
   - Satellite view (1000km × 1000km, 10km/pixel)
   - Regional view (100km × 100km, 1km/pixel)
   - City view (10km × 10km, 100m/pixel)
   - Street view (1km × 1km, 10m/pixel)
   - Detail view (100m × 100m, pixel-accurate)
   - Seamless LOD transitions

2. **Terrain Generation at Scale**
   - Integration with global DEMs (SRTM, AW3D)
   - Satellite imagery mapping (RGB base)
   - Procedural detail overlay at close range
   - Real-time streaming (only load visible chunks)

3. **City Generation at Country Scale**
   - Procedural placement of 1000+ cities
   - OSM data for real-world roads/buildings
   - Fictional cities for non-real worlds
   - Regional style variation (architecture, vegetation, traffic)

4. **Distributed Simulation**
   - Multi-instance UE5 (separate processes for different regions)
   - Coordinate via broker (shared world state)
   - Agents/robots can traverse region boundaries
   - Asynchronous region loading/unloading

5. **Persistent World State**
   - PostgreSQL: entity positions, events, causality
   - S3: scene snapshots, sensor data
   - Time-travel query: "show world state at T=2h ago"
   - Event logs: "all collisions in region X in last hour"

**Success Criteria:**
- [ ] Load 100km × 100km region without stuttering
- [ ] Seamless camera pan from satellite view to street view
- [ ] Multiple regions load in parallel
- [ ] World persists state across simulation restarts

**Effort:** 3–4 engineers, 10–12 weeks

---

### **Phase 4: Advanced Mission & Narrative Systems (8–10 weeks)**

**Goal:** Procedurally generate missions, narratives, and cinematic sequences from world state.

**Deliverables:**

1. **Mission Generator**
   - Input: world state (entities, environment, constraints)
   - Output: structured missions (delivery, search, navigation, coordination)
   - Failure injection (obstacles, delays, sensor degradation)
   - Export to ROS 2 goals, Nav2 paths, MoveIt plans

2. **Narrative Layer**
   - Story arcs emerging from agent behavior (PyRoboReplay events)
   - Dialogue generation (LLM-based, context-aware)
   - Cinematic cutscene planning (camera paths, lighting cues)
   - Emotional tone inference (sunny day → cheerful narrative)

3. **Human-Robot Interaction**
   - Pedestrians react to robots (avoid, stare, help)
   - Communication (gestures, messages)
   - Collaboration (humans guide robot, robot assists human)

**Effort:** 2–3 engineers, 8–10 weeks

---

## Integration with Existing PyRobo* Stack

| Component | Current | PyRoboSimulator Integration |
|-----------|---------|-----|
| **PyTerrainMap** | Spatial indexing, 3D terrain | Import terrain as base layer; query traversability → material response in UE5 |
| **PyRoboReplay** | Sensor simulation | Call PyRoboSimulator for RGB/Depth; feed into replay engine; fuse sensor modalities |
| **PyRoboFrames** | I/O pipelines, training data | Export sensor outputs (Parquet); feed to training pipeline |
| **PyRoboVision** | Perception models | Run inference on RGB captures; feed bounding boxes back to world state |
| **PyAutoLLM** | Ecosystem integration | Use for mission/narrative generation prompts |

---

## First Sprint: Weeks 1–3 (Phase 0 PoC)

1. **Week 1: Setup & World Spec Generator**
   - [ ] UE5 project bootstrap, Pixel Streaming setup
   - [ ] Claude API integration (Sonnet 5), JSON schema design
   - [ ] FastAPI backend for world spec generation
   - [ ] Test: "Generate Tokyo at sunset" → JSON output

2. **Week 2: Micro-Scene in UE5**
   - [ ] Manual 200m × 200m scene (parking lot, trees, building)
   - [ ] PBR material setup (concrete, asphalt, grass, leaves, water)
   - [ ] Dynamic lighting (sun arc, shadows, rain darkening)
   - [ ] Weather blueprint (rain, cloud cover, fog)
   - [ ] Basic seasonal color override (deciduous leaf color)

3. **Week 3: Sensor Output & API**
   - [ ] RGB camera capture (1080p @ 30Hz)
   - [ ] Depth map generation (matched to RGB)
   - [ ] Lidar sim (16-channel, rotating, 10 Hz, ray-casting)
   - [ ] Thermal output (emissivity lookup)
   - [ ] FastAPI endpoints: `/generate-world`, `/load-world`, `/sensor/*`
   - [ ] Validation: rain occlusion, wet-road reflections, thermal emissivity

---

## Success Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| **Visual Fidelity** | 8/10 (AAA quality by end of Phase 2) | Side-by-side comparison with reference (Flight Simulator, Cyberpunk 2077) |
| **Sensor Accuracy** | 95%+ match to real-world sensor behavior | Lidar rain scatter, thermal emissivity, depth discontinuities |
| **NLP Robustness** | 90%+ successful world generation from natural language | Test 100 diverse prompts; measure Jaccard similarity of generated ↔ intended parameters |
| **Performance** | 60+ FPS @ 1080p on RTX 4090 | Profile GPU utilization, memory |
| **API Latency** | <100ms per sensor query | P95 latency under load (10 concurrent worlds) |
| **Scale** | 100km × 100km without stuttering (Phase 3) | Measure memory usage, frame time variance |

---

## Open Questions & Decisions

1. **Lidar Simulation Accuracy**
   - Should we ray-cast in UE5 or import PyTerrainMap's collision geometry?
   - Trade-off: ray-cast is slow; geometry import requires sync

2. **Real-World Data Integration**
   - Should Phase 1+ support importing real OSM, satellite imagery, DEMs?
   - Scope risk: high data processing overhead

3. **Physics Engine**
   - Use UE5's Chaos? Or MuJoCo (PyTerrainMap already uses it)?
   - If MuJoCo: needs UE5 bridge (gRPC physics updates)

4. **Rendering Quality vs. Speed**
   - Lumen + Nanite is slow on some GPUs. Fallback to pre-baked GI?
   - Accept lower quality on commodity GPUs?

5. **Fictional Worlds**
   - Mars colony: terrain generation ∝ Earth procedural gen?
   - Sci-fi cities: architectural styles + materials from LLM descriptions?

---

## Next Steps

1. **Week 0 (Now)**
   - [ ] Allocate team (1 lead architect, 1 UE5 engineer, 1 Python/API engineer)
   - [ ] Set up UE5 project, GitHub repo
   - [ ] Define Claude API world spec JSON schema
   - [ ] Create Trello/Linear board for Phase 0 tasks

2. **Week 1**
   - [ ] Begin world spec generator
   - [ ] Create UE5 micro-scene
   - [ ] Bootstrap FastAPI

3. **Week 2–3**
   - [ ] Integrate sensors, validate PoC

4. **Post-PoC**
   - [ ] Review results; finalize Phase 1 scope
   - [ ] Green-light Phase 1 (procedural cities, weather, traffic)

---

**Estimated Total Effort to Phase 3 (Core Platform):**
- 10–12 engineers
- 18–22 weeks
- ~3,000–5,000 commits
- $500K–$1.5M (if using proprietary tools; ~$200K if OSS-only)

