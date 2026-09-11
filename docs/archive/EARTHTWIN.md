# EarthTwin: Reality-to-Simulation Platform

## Vision

Transform PyRoboSimulator into the **Reality-to-Simulation Platform for Robotics**, enabling users to generate fully configured, geographically accurate digital twins of real-world locations without manual world creation.

**Core Value Proposition:**
- Input: City name, GPS coordinates, date, weather mode
- Output: Physics-ready, ROS 2-compatible, sensor-aware digital twin

**Competitive Advantage:** Closes a critical gap in existing simulators (Gazebo, Isaac Sim, Webots, CARLA) which require significant manual effort to create geographically realistic worlds.

---

## Module Scope

### What EarthTwin Owns
1. **Geographic Data Integration** — OSM, NASA, Sentinel, Google Maps, Weather APIs
2. **Real-World Terrain Generation** — Elevation, land cover, procedural infrastructure
3. **Season & Weather Engine** — Hemisphere-aware seasons, historical weather recreation
4. **Route-Aware World Generation** — Corridor mode for autonomous vehicle testing
5. **Traffic & Population Simulation** — Realistic agent density based on time/location/season
6. **World Evolution** — Time-based changes (construction, vegetation, traffic patterns)
7. **ROS 2 Asset Generation** — Costmaps, HD maps, occupancy grids, navigation waypoints

### Integrations (Do Not Rebuild)
- **PyTerrainMap** — 3D terrain indexing, coordinate systems, procedural landscapes
- **PyRoboReplay** — Sensor simulation (RGB, depth, thermal, Lidar) with weather/lighting effects
- **PyRoboFrames** — Export training datasets, tensor operations
- **PyRoboVision** — Perception feedback on generated scenes

---

## Roadmap

### Phase 0: Design & Scaffolding (1-2 weeks)
**Goal:** Define APIs and data structures before implementation.

#### Deliverables
1. **Python API Design**
   - `EarthTwin` class with fluent builder
   - `GeoLocation`, `GeoRegion`, `GeoRoute` types
   - Configuration objects for weather, season, time

2. **Rust Data Model**
   - `EarthTwinConfig` struct
   - `GeographicData` (unified representation of OSM, elevation, weather)
   - `DataSourceAdapter` trait for pluggable backends
   - Serialization formats (MessagePack for efficiency)

3. **Scaffolding**
   - New `earthtwin.rs` module in pyrobosimulator-core
   - Python package structure (`pyrobosimulator.earthtwin` submodule)
   - Test fixtures (sample OSM data, elevation datasets)
   - Documentation with examples

#### Success Criteria
- [ ] Python API is documented and exemplified
- [ ] Rust type system is type-safe and serializable
- [ ] All data structures can round-trip (serialize → deserialize)
- [ ] Test fixtures load and parse correctly

---

### Phase 1: Geographic Data Pipeline (2-3 weeks)
**Goal:** Fetch and normalize geographic data from authoritative sources.

#### Deliverables

##### 1. OSM Data Fetcher
- **Dependency:** `osm-xml` or `overpass-api-rs`
- **Capabilities:**
  - Query by bounding box (city, region)
  - Extract: buildings, roads, POIs, water bodies, parks, railways
  - Normalize tags (building type, road class, speed limits)
  - Store as `GeoFeature` objects
- **Output:** GeoJSON or custom binary format (MessagePack)
- **Caching:** Local disk cache (avoid repeated API calls)

##### 2. Elevation Data Integration
- **Primary:** SRTM (Shuttle Radar Topography Mission)
  - Global 30m resolution (~1 arc second)
  - Fallback: GEBCO for ocean/coastal areas
- **NASA DEM:**
  - Higher fidelity where available (~10m)
  - Specific regions (e.g., Mars terrain via PyTerrainMap)
- **Integration:**
  - Download tiles on-demand
  - Cache locally
  - Interpolate to PyTerrainMap format
  - Output: Heights grid for terrain mesh generation

##### 3. Land Cover Classification
- **Source:** Sentinel-1/Sentinel-2 or Copernicus DEM
- **Classification:**
  - Urban (buildings, roads)
  - Suburban (houses, gardens)
  - Vegetation (forest, grassland, crops)
  - Water (rivers, lakes)
  - Barren (rock, sand)
- **Integration:**
  - Semantic labels per grid cell
  - Used for procedural generation of appropriate features
  - Cached classification maps

##### 4. Historical Weather Recreation
- **Sources:**
  - **NOAA Global Forecast System (GFS)** — Historical weather (past 15+ years)
  - **ECMWF ERA5** — Reanalysis (best accuracy, past 40+ years)
  - **Open-Meteo API** — Free historical weather alternative
- **Data Points (per day):**
  - Temperature (min, max, avg)
  - Humidity
  - Precipitation (rain, snow)
  - Wind speed & direction
  - Cloud cover
  - Visibility
- **Integration:**
  - Query by (lat, lon, date)
  - Interpolate to hourly (if only daily available)
  - Inject into weather engine for sensor simulation

#### Technical Requirements
- [ ] HTTP client for API calls (tokio-based async)
- [ ] Caching layer (RocksDB for local storage)
- [ ] Error handling for network/unavailable data (graceful fallback)
- [ ] Rate limiting (respect API quotas)
- [ ] Data validation & QA

#### Success Criteria
- [ ] Fetch OSM data for a city (Bangalore) in <5 seconds
- [ ] Cache works; repeat queries hit disk, not network
- [ ] Elevation grid covers bounds with <100ms per query
- [ ] Historical weather for any date (past 10 years) within 2 seconds
- [ ] Geospatial queries (point-in-polygon, nearest feature) execute in <10ms

---

### Phase 2: Terrain & Infrastructure Generation (2-3 weeks)
**Goal:** Generate 3D worlds with realistic terrain and built infrastructure.

#### Deliverables

##### 1. Terrain Mesh Generation
- **Integration:** PyTerrainMap
- **Process:**
  - Receive elevation grid from Phase 1
  - Normalize to PyTerrainMap 3D coordinates + temporal dimension
  - Generate mesh (triangulate, LOD variants)
  - Output: USD representation (via OpenUSD) for rendering
- **Optimization:**
  - Streaming (generate only visible regions)
  - LOD hierarchy (far = low-poly, near = high-poly)

##### 2. Building Placement & Geometry
- **Input:** OSM building footprints, height estimates
- **Process:**
  - Snap buildings to terrain
  - Infer height from OSM tags or ML (building type → typical height)
  - Generate simple geometry (boxes, then detail)
  - Assign materials/colors (urban aesthetic)
- **Output:** Building entities in world, USD geometry

##### 3. Road Network
- **Input:** OSM ways (roads, pedestrian paths, railways)
- **Process:**
  - Extract road graph (nodes, edges, connectivity)
  - Classify by type (highway, residential, footway, etc.)
  - Assign traffic semantics (speed limits, one-way, bike lanes)
  - Snap to terrain elevation
  - Generate road mesh (simple quad strips)
- **Output:**
  - Road geometries in world
  - Topology graph for navigation planning
  - Traffic rules metadata (for simulation)

##### 4. Vegetation & Water Bodies
- **Vegetation:**
  - Parks (from OSM) → procedural tree placement
  - Land cover (from Phase 1) → grass, forest
  - Season-aware (winter = bare, summer = lush)
- **Water:**
  - Rivers, lakes (from OSM)
  - Simple plane geometry, water shader
  - Seasonal variation (dry vs. monsoon)

#### Integration with PyTerrainMap
- Terrain engine receives:
  - Bounding box (lat/lon)
  - Elevation grid (SRTM)
  - Land cover classification
- Returns:
  - Terrain mesh (3D coordinates)
  - Traversability map (for mission planning)
  - Temporal normalization (5D + clock + quality)

#### Success Criteria
- [ ] Generate Bangalore (1000 km²) in <30 seconds
- [ ] World is navigable by robots (no floating buildings, roads snap to terrain)
- [ ] Urban areas visually distinct from suburban/rural
- [ ] Buildings have appropriate heights (2-15 story range in cities)
- [ ] Road network is fully connected (no broken paths)
- [ ] Scene renders in 3 LOD modes (scientific/robotics/cinematic)

---

### Phase 3: Dynamic Systems (2-3 weeks)
**Goal:** Add realistic weather, traffic, population, and temporal dynamics.

#### Deliverables

##### 1. Season Engine
- **Input:** Month (or date)
- **Process:**
  - Detect hemisphere (from latitude)
  - Map month → season for hemisphere
  - Infer vegetation state:
    - **Summer (Northern):** Lush, green, full canopy
    - **Winter (Northern):** Bare trees, brown grass, possible snow
    - **Monsoon (Tropical):** Dense, wet, heavy vegetation
    - **Dry (Tropical):** Brown vegetation, dust
  - Adjust day length, sun angle
  - Set base weather patterns
- **Outputs:**
  - Vegetation visuals (shader variations)
  - Day/night cycle
  - Base temperature range
  - Precipitation likelihood

##### 2. Weather Simulation
- **Input:** Historical weather data (from Phase 1), current season
- **Simulation Loop:**
  - Interpolate historical data to simulation time
  - Add procedural variation (realistic fluctuations)
  - Compute effects:
    - **Rain:** Wet roads, reduced visibility, sensors affected
    - **Fog:** Reduced camera range, Lidar scatter
    - **Wind:** Dust particles, tree swaying, sensor noise
    - **Snow:** Road texture changes, sensor degradation
    - **Heat waves:** Shimmer effects, sensor thermal noise
- **Output:**
  - Weather state (temperature, humidity, wind, precipitation)
  - Environmental effects (visual + sensor impact)
  - Causality chain (why weather changed)

##### 3. Traffic & Agent Simulation
- **Input:**
  - Road network (from Phase 2)
  - Time of day (hour)
  - Day of week (weekday vs. weekend)
  - Season
  - City type (urban, suburban, rural)
- **Simulation:**
  - Estimate pedestrian density (OSM population data, time of day)
  - Estimate vehicle density (peak hours: 8-9am, 5-7pm)
  - Generate agent trajectories (realistic paths, speeds)
  - Collision avoidance (simple RVO)
  - Behavioral variety (some agents hurried, some leisurely)
- **Parametrization:**
  - Bangalore 8:30 AM Monday = high congestion, rush hour
  - Bangalore 2:00 PM Sunday = low traffic, leisure pedestrians
  - Tokyo winter = fewer cyclists, more cars
- **Output:**
  - Agent population (spawned in world)
  - Waypoint graphs for agent navigation
  - Traffic density heatmaps (for visualization)

##### 4. Population Density Estimation
- **Data Sources:**
  - OSM (administrative boundaries)
  - Sentinel (built area)
  - Historical census data (if available)
- **Method:**
  - Map grid cells to (buildings, area, land cover) → density estimate
  - Peak hours = 1.2x base density
  - Weekends = 0.8x weekday
  - Seasonal variation (tourism in monsoon vs. dry season)
- **Output:**
  - Population heatmap (visualization)
  - Agent spawn rates (used for traffic simulation)

#### Integration with PyRoboReplay
- Weather effects injected into sensor simulation:
  - Rain → reduced camera range, Lidar dropouts
  - Fog → specular noise on all sensors
  - Heat → thermal camera artifacts
  - Wind → IMU noise, GPS jitter

#### Success Criteria
- [ ] Season engine correctly identifies hemisphere & season
- [ ] Weather effects visible in rendered scene (rain particles, wet roads, fog)
- [ ] Traffic simulation produces realistic congestion patterns (rush hour peaks)
- [ ] Agents behave realistically (walk on sidewalks, vehicles on roads)
- [ ] Population density heatmap matches city demographics
- [ ] Time-based parametrization affects simulation (8am ≠ 2pm)

---

### Phase 4: Robotics Asset Export (1-2 weeks)
**Goal:** Generate ROS 2-ready assets for autonomous systems testing.

#### Deliverables

##### 1. Occupancy Grid & Costmap Generation
- **Input:** Building geometry, vegetation, water, road network
- **Process:**
  - Discretize world to grid (e.g., 0.1m cells)
  - Mark cells: free, occupied, unknown
  - Expand occupied by robot radius (inflation)
  - Generate costmap (gradient toward obstacles)
- **Output:**
  - ROS 2 OccupancyGrid message
  - Metadata (resolution, origin, bounds)
  - Cached binary format (fast loading)

##### 2. HD Map Generation
- **Output Format:** Lanelet2 (open standard)
- **Lane Graph:**
  - Extract lanes from roads (OSM)
  - Classify: driving lanes, bike lanes, parking, pedestrian
  - Define lane boundaries (polylines)
  - Mark traffic rules (speed limits, one-way, yield)
- **Integration:**
  - Lanelet2 → ROS 2 topic (for Nav2, autonomous vehicle stacks)
  - USD export (3D visualization)

##### 3. Semantic Map
- **Representation:** Grid with class labels
- **Classes:**
  - Road surface (asphalt, concrete, dirt)
  - Building
  - Vegetation (tree, grass, crop)
  - Water
  - Pedestrian crossing
  - Parking
  - Bike lane
- **Output:**
  - TensorFlow Lite model (real-time segmentation)
  - Label map (class ID → name)
  - Optional: Neural network trained on rendered images

##### 4. Navigation Waypoints
- **Generation:**
  - Sample points on roads (every 5m)
  - Mark intersections
  - Mark named locations (shops, parks, landmarks)
- **Integration:**
  - Exported as ROS 2 Waypoint list
  - Used by Nav2 for path planning
  - Queryable by name (e.g., "go to Bangalore Airport")

#### Success Criteria
- [ ] Occupancy grid is collision-free for all test routes
- [ ] HD map covers entire city with proper lane topology
- [ ] Semantic map accuracy >85% on validation set
- [ ] Nav2 can plan paths using generated maps
- [ ] Route following (A → B) succeeds in real-time sim

---

### Phase 5: World Evolution & Temporal Simulation (1-2 weeks)
**Goal:** Support long-duration robotics testing with realistic world changes.

#### Deliverables

##### 1. Construction Progress Simulation
- **Input:** OSM construction tags, timeline
- **Simulation:**
  - Buildings under construction → progressive visibility
  - Road closures → dynamic routing
  - Scaffolding placement
- **Output:**
  - Time-indexed world snapshots
  - Causality chain (what changed, why, when)

##### 2. Vegetation Growth & Seasonal Transitions
- **Simulation:**
  - Growth season: grass → plants → trees (procedural)
  - Leaf-out/leaf-fall (spring/fall transitions)
  - Seasonal color shifts
- **Output:**
  - Time-interpolated vegetation state
  - Seasonal landmark recognition (for visual SLAM)

##### 3. Traffic Pattern Evolution
- **Simulation:**
  - Time of day → density changes
  - Day of week → behavior changes
  - Seasonal events (holidays, festivals) → anomalies
- **Output:**
  - Dynamic agent spawning/despawning
  - Event history (logged for causality)

##### 4. Time-Indexed Snapshots
- **Storage:**
  - RocksDB key: (world_id, timestamp) → world state
  - Efficient queries: "give me world state at 2025-07-15 14:30"
- **Output:**
  - Replayable simulation (like video playback)
  - Training data generation (diverse conditions)

#### Integration with PyRoboSimulator World State Engine
- EarthTwin world persists in RocksDB with full causality
- Snapshot every simulation tick
- Query world at any point in time

#### Success Criteria
- [ ] Simulate 6 months of world evolution in <10 minutes
- [ ] Vegetation growth is visually plausible
- [ ] Traffic patterns evolve realistically
- [ ] Snapshots are queryable and reproducible
- [ ] Multi-scenario testing (same city, different dates) works

---

## Integration Points

### With PyTerrainMap
- **Receive:** 3D terrain mesh, coordinate systems, traversability
- **Send:** Bounding box, elevation grid, land cover

### With PyRoboReplay
- **Receive:** Sensor simulation (RGB, depth, thermal, Lidar, IMU, GPS)
- **Send:** Weather state, camera/sensor rig parameters, multi-view rendering

### With PyRoboFrames
- **Receive:** I/O pipelines, tensor operations, dataset exports
- **Send:** Training data (trajectories, sensor streams, action labels)

### With PyRoboVision
- **Receive:** Semantic segmentation, detection models
- **Send:** Rendered images for training

---

## Technical Requirements

### Dependencies (Rust)
- `osm-xml` or `osm2`: OSM parsing
- `geohash`: Geographic hashing (spatial queries)
- `gdal-sys`: DEM/raster data handling
- `reqwest`: Async HTTP client (data fetching)
- `geoutils`: Geospatial calculations (bearing, distance)
- `lanelet2-rs` (if available): HD map export
- `ndarray`: Grid/array operations (occupancy grids, weather)

### Dependencies (Python)
- `geopy`: Geocoding, distance calculations
- `overpy`: Overpass API client (OSM queries)
- `rasterio`: DEM/raster I/O
- `shapely`: Polygon operations (buildings, regions)
- `xarray`: N-dimensional grids (weather)

### Infrastructure
- Caching directory (~5GB for typical city: OSM, elevation, weather)
- API keys: Google Maps (optional), Open-Meteo (free)
- Storage: RocksDB for world state (PostgreSQL optional for scale)

---

## Success Metrics by Phase

### Phase 0
- [ ] API documentation complete with examples
- [ ] Type system is consistent and serializable
- [ ] All tests pass

### Phase 1
- [ ] Bangalore OSM fetched in <5s
- [ ] Elevation grid covers world with <100ms/query
- [ ] Historical weather for any date (past 10 years) available
- [ ] Data cache reduces network calls by 90%

### Phase 2
- [ ] 1000 km² world generated in <30s
- [ ] Buildings have correct heights (structural variety)
- [ ] Roads are connected and traversable
- [ ] 3 LOD modes render correctly

### Phase 3
- [ ] Season engine produces correct hemisphere/season
- [ ] Weather effects visible in rendering
- [ ] Traffic density peaks at 8-9am, 5-7pm
- [ ] Agents navigate realistically (no clipping)

### Phase 4
- [ ] Occupancy grid is collision-free
- [ ] HD map lane topology is correct
- [ ] Nav2 successfully plans and executes routes
- [ ] Semantic map accuracy >85%

### Phase 5
- [ ] 6-month evolution simulates in <10 minutes
- [ ] Snapshots are reproducible and queryable
- [ ] Multi-scenario testing produces diverse training data

---

## User-Facing API Preview

```python
from pyrobosimulator.earthtwin import EarthTwin

# Simple case: single city
world = EarthTwin(
    cities=["Bangalore, India"],
    month="July",
    weather_mode="historical_average",
    realism="high"
)
world.generate()

# Multi-city
world = EarthTwin(
    cities=[
        "Bangalore, India",
        "Tokyo, Japan",
        "New York, USA"
    ],
    date="2025-07-15",  # Specific date for historical weather
    weather_mode="historical",
    fidelity="robotics"  # scientific | robotics | cinematic
)
world.generate()

# Route-aware (corridor)
world = EarthTwin(
    route=[
        "Bangalore Airport",
        "Electronic City"
    ],
    corridor_width_m=500,  # 500m corridor around route
    fidelity="robotics"
)
world.generate()

# Access generated assets
occupancy_grid = world.get_occupancy_grid()
hd_map = world.get_hd_map()  # Lanelet2 format
semantic_map = world.get_semantic_map()
weather = world.get_weather()  # Current/historical
agents = world.get_agents()  # Traffic, pedestrians

# Time-based queries
world_at_t = world.get_snapshot(datetime(2025, 7, 15, 14, 30))
evolution = world.evolve(duration="6 months")

# ROS 2 integration (via PyRoboSimulator core)
world.export_ros2_package("./bangalore_world")
```

---

## Timeline

- **Phase 0:** Weeks 1-2
- **Phase 1:** Weeks 3-5
- **Phase 2:** Weeks 6-8
- **Phase 3:** Weeks 9-11
- **Phase 4:** Weeks 12-13
- **Phase 5:** Weeks 14-15

**Total:** ~15 weeks (from today, 2026-07-27 → ~2026-11-09)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Data quality** (OSM incomplete/incorrect) | Use multiple sources (OSM + Google Maps), validation layer, user override |
| **API rate limits** (weather, elevation services) | Local caching, fallback to open data, batch requests |
| **Geographic variability** (terrain, building styles, traffic) | Template-based parametrization, per-city tuning |
| **Performance** (1000+ agents, large terrain) | Streaming LOD, agent culling, parallel rendering |
| **Accuracy** (generated world ≠ real world) | Validation against satellite imagery, optional user CAD/point clouds |

---

## Non-Goals

1. **Exact photorealism** (Runway AI's domain) — We aim for cinematic plausibility, not pixel-perfect realism
2. **Real-time mapping** (Google Maps' domain) — We generate static worlds, not live city updates
3. **Real-world sim2real** (NVIDIA Isaac Lab's domain) — We focus on simulation; users handle real robot deployment
4. **Game-engine competition** (Unity/Unreal's domain) — We export to game engines; not build one

---

## Success Definition

**EarthTwin succeeds when:**
- User specifies: city + date + weather mode
- System generates: Physics-ready, ROS 2-ready, sensor-aware digital twin
- Robot/agent can: Navigate autonomously, interact with world, evolve over time
- All in: <2 minutes from API call to playable world

**Competitive positioning:** The standard choice for geographic world generation in robotics (what Gazebo/Isaac Sim can't do).
