# PyRoboSimulator Phase 1: City Expansion & Streaming API

## Overview

**Goal:** Expand from single parking lot to full 2km × 2km procedural city with streaming, traffic, and distributed rendering.

**Timeline:** 6-8 weeks  
**Team Size:** 4-5 engineers (1 UE5 lead, 1 Python lead, 2 procedural generation, 1 DevOps)  
**Target Release:** v0.2.0  

---

## Deliverables

### 1. Procedural City Generation ✅ (Design)

#### Scale
- **Map Size:** 2km × 2km (100x expansion from Phase 0)
- **Grid:** 100m × 100m blocks (20×20 grid = 400 blocks)
- **Population:** 50,000+ buildings (residential + commercial)
- **Density:** Realistic urban layout

#### Generation Pipeline

**Python Module: `city_generator.py`**

```python
class CityGenerator:
    def __init__(self):
        self.perlin_noise = PerlinNoise(scale=100)
        self.osm_importer = OSMImporter()  # Optional: OpenStreetMap data
    
    def generate_city(self, seed: int, style: str = "downtown") -> CitySpec:
        """Generate procedural city.
        
        Args:
            seed: Random seed for reproducibility
            style: "downtown", "suburbs", "mixed"
        
        Returns:
            CitySpec with all buildings, roads, vegetation
        """
        # 1. Road network (L-system)
        roads = self.generate_roads(seed, style)
        
        # 2. City blocks
        blocks = self.generate_blocks(roads)
        
        # 3. Building placement
        buildings = self.generate_buildings(blocks, style)
        
        # 4. Vegetation (parks, trees)
        vegetation = self.generate_vegetation(blocks)
        
        # 5. Points of interest (landmarks, water features)
        poi = self.generate_poi(blocks)
        
        return CitySpec(roads, blocks, buildings, vegetation, poi)
```

#### Road Generation (L-System)

**Algorithm:** Context-Free L-System  
**Production Rules:**
```
Start: F[+X][-X]F[-FX][+FX]FX
X: F-[[X]+X]+F[+FX]-X
F: F (move forward)
+: Turn right 45°
-: Turn left 45°
[: Push state
]: Pop state
```

**Parameters per style:**
- Downtown: Dense grid (90° intersections), 15m roads
- Suburbs: Sparse hierarchy (tree-like), 20m roads
- Mixed: Combination (downtown center → suburbs edge)

**Output:**
```python
class Road:
    id: str
    start: (float, float)
    end: (float, float)
    width: float  # 10-20m
    type: str  # "highway", "arterial", "local", "alley"
    traffic_lanes: int  # 1-4
```

#### Building Generation

**Algorithm:** Voronoi-based lot subdivision + constraint satisfaction  
**Per Block:**
1. Divide into lots (100-500 m² each)
2. Assign building height (zoning rules)
3. Place footprint (setback rules)
4. Generate façade (windows, doors, materials)

**Building Types:**
```python
class BuildingType(Enum):
    RESIDENTIAL_LOW = 2      # 1-3 stories
    RESIDENTIAL_MID = 5      # 4-8 stories
    RESIDENTIAL_HIGH = 20    # 9-40 stories
    COMMERCIAL = 10          # 2-20 stories
    INDUSTRIAL = 8           # 1-15 stories
    LANDMARK = 50            # Special (40+ stories)
    PARKING = 4              # 1-4 stories
```

**Distribution by Style:**
- Downtown: 20% residential, 50% commercial, 20% parking, 10% landmark
- Suburbs: 80% residential, 15% commercial, 5% industrial
- Mixed: 50% residential, 35% commercial, 10% industrial, 5% landmark

**Output:**
```python
class Building:
    id: str
    lot_id: str
    position: (float, float)
    height: float  # meters
    footprint: Polygon  # 2D shape
    type: BuildingType
    color_variance: float  # 0-1 for material variation
    windows_pattern: str   # "grid", "modern", "ornate"
    roof_type: str        # "flat", "pitched", "curved"
```

#### Vegetation Generation

**Parks & Green Spaces:**
- 1 major park per 500 blocks (4-10 hectares)
- Green corridors along waterways
- Rooftop gardens (5% of buildings)
- Street trees (every 10-20m on major roads)

**Tree Placement:**
```python
class Tree:
    id: str
    position: (float, float, float)  # XYZ
    species: str  # "oak", "maple", "pine", etc.
    height: float  # 5-25m
    crown_radius: float  # 3-10m
    age_factor: float  # 0-1 (mature → dense)
```

**Species by Climate Zone:**
- Temperate: Oak, Maple, Ash, Elm
- Mediterranean: Pine, Cedar, Olive
- Subtropical: Palm, Magnolia, Cypress

#### Points of Interest (POI)

**Landmarks:**
- 1-3 major (city-scale): Monument, tower, palace
- 10-20 medium (district-scale): Museum, theater, cathedral
- 50+ minor (neighborhood-scale): Fountain, pavilion, statue

**Water Features:**
- Rivers (1-2 major)
- Lakes/ponds (5-10)
- Canals (if applicable to style)

**Output:**
```python
class POI:
    id: str
    name: str
    position: (float, float, float)
    type: str  # "monument", "water", "park", etc.
    height: float
    importance: int  # 1-5
```

### 2. Traffic & Pedestrian AI ✅ (Design)

#### Vehicle Traffic System

**Python Module: `traffic_system.py`**

```python
class TrafficSimulator:
    def __init__(self, city_spec: CitySpec):
        self.roads = city_spec.roads
        self.intersections = self.build_intersection_graph()
        self.vehicles = []  # Active vehicles
    
    def update(self, dt: float):
        """Simulate traffic for dt seconds."""
        for vehicle in self.vehicles:
            # Pathfinding (A*)
            path = self.find_path(vehicle.pos, vehicle.destination)
            
            # Physics (acceleration, braking, collision)
            self.update_vehicle_physics(vehicle, path, dt)
            
            # Lane changing (rule-based)
            self.update_lane(vehicle)
            
            # Remove if arrived
            if vehicle.arrived:
                self.vehicles.remove(vehicle)
    
    def spawn_vehicle(self, start: (float, float), end: (float, float),
                      vehicle_type: str = "car"):
        """Spawn vehicle."""
        vehicle = Vehicle(start, end, vehicle_type)
        self.vehicles.append(vehicle)
```

**Vehicle Types:**
```python
class VehicleType(Enum):
    CAR = {"speed": 15, "length": 4.5, "color": "varied"}
    TRUCK = {"speed": 12, "length": 9, "color": "gray"}
    BUS = {"speed": 12, "length": 12, "color": "red"}
    TAXI = {"speed": 15, "length": 4.8, "color": "yellow"}
    MOTORCYCLE = {"speed": 18, "length": 2, "color": "varied"}
    BICYCLE = {"speed": 6, "length": 1.8, "color": "varied"}
```

**Traffic Rules:**
- Speed limits by road type (highway: 90 km/h, arterial: 60, local: 40)
- Lane discipline (stay right except to pass)
- Traffic lights (4-way intersections)
- Collision avoidance (keep-distance rule)

**Density Control:**
```python
def set_traffic_density(level: float):  # 0-1
    """0 = empty, 0.5 = moderate, 1.0 = rush hour"""
    # Adjust spawn rate based on level
    # rush_hour: 1 vehicle every 2 seconds
    # moderate: 1 vehicle every 5 seconds
    # light: 1 vehicle every 10 seconds
```

#### Pedestrian AI

**Python Module: `pedestrian_system.py`**

```python
class PedestrianSimulator:
    def __init__(self, city_spec: CitySpec):
        self.sidewalks = city_spec.sidewalks
        self.pois = city_spec.pois
        self.pedestrians = []
    
    def spawn_pedestrian(self, start: (float, float)):
        """Spawn pedestrian with random destination."""
        # Choose destination (POI or random building entrance)
        dest = self.choose_destination()
        
        # Plan path (A* on sidewalk network)
        path = self.plan_path(start, dest)
        
        pedestrian = Pedestrian(start, path)
        self.pedestrians.append(pedestrian)
    
    def update(self, dt: float):
        """Update pedestrian positions."""
        for ped in self.pedestrians:
            # Follow path (with local avoidance)
            self.update_pedestrian(ped, dt)
            
            # Social force model (avoid crowds)
            self.apply_social_forces(ped)
            
            # Animation (walking animation)
            self.update_animation(ped)
            
            # Remove if arrived
            if ped.arrived:
                self.pedestrians.remove(ped)
```

**Pedestrian Parameters:**
- Speed: 1.4 m/s (average adult)
- Variation: 0.5-2.0 m/s (children, elderly, hurried)
- Grouping: 60% solo, 30% pairs, 10% groups
- Behavior: 80% business, 20% leisure

**Population Density:**
- Downtown: 200-500 pedestrians visible at once
- Suburbs: 50-100
- Control via spawn rate

### 3. Extended Weather System v2 ✅ (Design)

#### Dynamic Weather Simulation

**Python Module: `weather_v2.py`**

```python
class WeatherSystem:
    def __init__(self):
        self.time = TimeOfDay()
        self.particles = ParticleSystem()
        self.visibility_manager = VisibilityManager()
    
    def update(self, dt: float):
        """Simulate weather changes."""
        # Update wind (Perlin noise)
        self.wind = self.generate_wind(self.time.hour)
        
        # Update clouds (procedural)
        self.clouds = self.generate_clouds(self.time.season)
        
        # Update precipitation (physics-based)
        if self.rain_intensity > 0:
            self.simulate_rain(dt)
        
        # Update visibility (fog, rain)
        self.update_visibility()
        
        # Update effects (puddles, wet surfaces)
        self.update_surface_effects()
```

**Weather States:**
```python
class WeatherState(Enum):
    CLEAR = {"rain": 0, "clouds": 0, "wind": 0}
    PARTLY_CLOUDY = {"rain": 0, "clouds": 0.5, "wind": 2}
    CLOUDY = {"rain": 0, "clouds": 1.0, "wind": 3}
    LIGHT_RAIN = {"rain": 0.3, "clouds": 1.0, "wind": 5}
    MODERATE_RAIN = {"rain": 0.6, "clouds": 1.0, "wind": 8}
    HEAVY_RAIN = {"rain": 1.0, "clouds": 1.0, "wind": 12}
    THUNDERSTORM = {"rain": 1.0, "clouds": 1.0, "wind": 18, "lightning": True}
    FOG = {"rain": 0, "clouds": 1.0, "visibility": 50}
    SNOW = {"rain": 1.0, "clouds": 1.0, "type": "snow"}
```

**Weather Transitions:**
- Smooth interpolation (5-30 minutes per transition)
- Seasonal bias (summer: more clear, winter: more rain)
- Time-of-day effects (morning: fog, afternoon: clear)

#### Physics-Based Particle Systems

**Rain:**
- 1000+ particles per second (intensity dependent)
- Collision with geometry (splashes)
- Accumulation (puddles, wet surfaces)
- Wind influence (rain angle)

**Wind:**
- Perlin noise-based (continuous variation)
- Affects particles, foliage, flags, signs
- Speed: 0-25 m/s (0-90 km/h)

**Lightning:**
- 30-second intervals (thunderstorm)
- Sky flash + brief illumination
- Sound delay (1 second per 300m)

**Snow:**
- Accumulation on surfaces (texture blend)
- Footprints/tire tracks (interactive)
- Wind-drifting effects

### 4. Seasonal System ✅ (Design)

#### Season Simulation

**Timeline:** Full year cycle (365 days) or compressed (30 days)

**Spring (Day 90-180):**
- Foliage: Pale green → rich green
- Trees: Bud → full leaf
- Flowers: Blossom on cue
- Temperature: 5°C → 15°C
- Lighting: Gradually warming

**Summer (Day 181-270):**
- Foliage: Peak green
- Lighting: Long days, warm color temp
- Weather: More clear days, occasional rain
- Temperature: 15°C → 25°C
- Vegetation: Grass green and dense

**Fall (Day 271-360):**
- Foliage: Green → yellow → orange → red
- Trees: Leaf drop (animated)
- Weather: Increased rain, shorter days
- Temperature: 25°C → 10°C
- Lighting: Warm orange bias

**Winter (Day 1-89):**
- Foliage: Bare trees
- Vegetation: Brown/dormant
- Weather: Snow, frost, fog
- Temperature: 10°C → 5°C
- Lighting: Cool blue, short days (long shadows)

**Material Color Mapping:**

```python
def get_seasonal_color(base_color: RGB, season: str, day: int) -> RGB:
    """Interpolate color based on season/day."""
    seasonal_shift = {
        "spring": 0.3,   # Green shift
        "summer": 0.0,   # Neutral
        "fall": 0.8,     # Orange shift
        "winter": -0.2,  # Blue shift
    }
    
    # Interpolate with day-of-season
    alpha = (day % 90) / 90.0
    return blend_color(base_color, seasonal_shift[season], alpha)
```

#### Dynamic Events

**Random Events (% per day):**
- Festival/celebration (markets, decorations): 5%
- Construction (cranes, barriers): 3%
- Sports event (crowds): 2%
- Accident (emergency vehicles): 1%
- Power outage (lights out, darkness): 0.5%

**Scripted Events:**
- Holiday decorations (Christmas, New Year)
- Seasonal plant changes (flowers, harvest)
- Schedule-based (rush hour, night shift)

### 5. Streaming & Chunking System ✅ (Design)

#### Spatial Chunking

**Grid:** 500m × 500m chunks (16 chunks for 2km × 2km city)  
**Hierarchy:**
- Level 0 (Loaded): 1-2 chunks around camera
- Level 1 (Streamed): 3-4 chunks (detailed assets)
- Level 2 (Cached): 5-9 chunks (LOD assets)
- Level 3 (Unloaded): Rest (metadata only)

**Python Module: `streaming.py`**

```python
class StreamingManager:
    def __init__(self, city_spec: CitySpec):
        self.chunks = self.partition_city(city_spec)  # 16 chunks
        self.loaded_chunks = set()
        self.streaming_queue = []
    
    def update_viewport(self, camera_pos: (float, float)):
        """Update loaded chunks based on camera position."""
        chunk_id = self.get_chunk_id(camera_pos)
        
        # Always load current chunk
        self.load_chunk(chunk_id)
        
        # Load adjacent chunks
        for neighbor in self.get_neighbors(chunk_id):
            self.stream_chunk(neighbor)
        
        # Unload far chunks
        for chunk in self.loaded_chunks:
            if self.distance(chunk, camera_pos) > 2000:
                self.unload_chunk(chunk)
    
    def load_chunk(self, chunk_id: int):
        """Synchronously load chunk (blocking)."""
        if chunk_id in self.loaded_chunks:
            return
        
        chunk = self.chunks[chunk_id]
        chunk.load_assets()  # Load buildings, trees, etc.
        self.loaded_chunks.add(chunk_id)
    
    def stream_chunk(self, chunk_id: int):
        """Asynchronously stream chunk (non-blocking)."""
        if chunk_id in self.loaded_chunks:
            return
        
        # Queue for async loading
        self.streaming_queue.append(chunk_id)
```

**Chunk Contents:**
```python
class Chunk:
    id: int
    bounds: AABB  # 500m × 500m
    buildings: List[Building]  # 50-200 per chunk
    trees: List[Tree]          # 100-500 per chunk
    roads: List[RoadSegment]   # 10-30 per chunk
    poi: List[POI]             # 0-5 per chunk
    metadata: Dict             # Lighting, weather region
```

#### Level-of-Detail (LOD) System

**Buildings:**
- LOD0: Full detail (all windows, doors, ornament)
- LOD1: Simplified (baked textures, fewer meshes)
- LOD2: Very low (single mesh, basic material)
- LOD3: Invisible (beyond 2km, represent as light only)

**Trees:**
- LOD0: Full geometry + leaves + bark
- LOD1: Simple cone + foliage billboard
- LOD2: Billboard only
- LOD3: Invisible (beyond 1km)

**Vehicles:**
- LOD0: Full detail, animated (within 200m)
- LOD1: Simplified mesh (200-500m)
- LOD2: Billboard (500m+)

### 6. Persistent Storage (Phase 1) ✅ (Design)

**Database Schema:**

```sql
-- Cities
CREATE TABLE cities (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    seed INT,
    style VARCHAR(50),  -- "downtown", "suburbs", "mixed"
    created_at TIMESTAMP,
    bounds GEOMETRY,    -- 2km × 2km
    metadata JSONB      -- Version, notes, etc.
);

-- Buildings
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    geom GEOMETRY,      -- 3D footprint
    height FLOAT,
    type VARCHAR(50),
    materials JSONB,    -- Color, roughness, etc.
    created_at TIMESTAMP,
    INDEX (city_id)
);

-- Vehicles (dynamic)
CREATE TABLE vehicle_traffic (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    vehicle_type VARCHAR(50),
    path GEOMETRY,      -- LineString
    speed FLOAT,
    spawned_at TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX (city_id)
);

-- Pedestrians (dynamic)
CREATE TABLE pedestrians (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    path GEOMETRY,
    spawned_at TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX (city_id)
);

-- Snapshots (for replay)
CREATE TABLE world_snapshots (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    timestamp TIMESTAMP,
    vehicle_positions GEOMETRY[],
    pedestrian_positions GEOMETRY[],
    weather_state JSONB,
    INDEX (city_id, timestamp)
);
```

**Storage Format:**
- PostgreSQL (relational + GIS)
- PostGIS (spatial indexing)
- S3 (asset storage: textures, meshes)

---

## Phase 1 Roadmap

### Week 1-2: Procedural Generation
- [ ] L-System road generation
- [ ] Voronoi lot subdivision
- [ ] Building height assignment
- [ ] Building façade generation
- [ ] Vegetation placement
- [ ] POI distribution
- [ ] City generation testing (reproducibility, quality)

### Week 3-4: Traffic & Pedestrians
- [ ] Intersection graph construction
- [ ] Vehicle pathfinding (A*)
- [ ] Vehicle physics (acceleration, braking)
- [ ] Lane changing logic
- [ ] Traffic light simulation
- [ ] Pedestrian pathfinding
- [ ] Social force model
- [ ] Pedestrian grouping & behavior

### Week 5: Weather v2 & Seasons
- [ ] Dynamic weather transitions
- [ ] Physics-based rain simulation
- [ ] Wind simulation (Perlin noise)
- [ ] Lightning + sound effects
- [ ] Seasonal color mappings
- [ ] Foliage animations (bud → leaf → drop)
- [ ] Lighting adjustments per season

### Week 6-7: Streaming & Storage
- [ ] Chunk-based loading
- [ ] LOD system (Buildings, trees, vehicles)
- [ ] Async chunk streaming
- [ ] PostgreSQL schema + migrations
- [ ] PostGIS integration
- [ ] S3 asset upload
- [ ] Snapshot system (for replay)

### Week 8: Integration & Testing
- [ ] End-to-end city generation
- [ ] Performance profiling (FPS at different scales)
- [ ] Memory optimization
- [ ] API updates (city generation endpoint)
- [ ] Validation (traffic flow, pedestrian density)
- [ ] Demo & documentation

---

## Success Criteria (Phase 1)

| Metric | Target | Validation |
|--------|--------|-----------|
| City Generation | 2km × 2km procedural | Visual inspection + metrics |
| Building Count | 50,000+ buildings | Database count |
| Road Network | Realistic connectivity | Graph analysis |
| Traffic Simulation | 1,000+ vehicles real-time | Performance test |
| Pedestrians | 500+ pedestrians real-time | Performance test |
| Chunk Streaming | <200ms load time | Timer + memory profile |
| Weather Transitions | 5-30 min per change | Smooth interpolation |
| Seasonal Changes | 4 seasons, all visual | Side-by-side comparison |
| Database | ACID compliance | Query performance test |
| Frame Rate | 30+ FPS @ 1080p | Benchmark on target hardware |

---

## API Additions (Phase 1)

### POST /api/v1/cities/generate
```json
{
  "seed": 12345,
  "style": "downtown",
  "size_km": 2,
  "building_density": 0.8,
  "vegetation_coverage": 0.15
}

Response:
{
  "city_id": "uuid",
  "bounds": [...],
  "building_count": 52000,
  "road_length_km": 450,
  "generated_at": "2026-08-15T...",
  "status": "ready"
}
```

### POST /api/v1/cities/{city_id}/traffic
```json
{
  "density": 0.7,
  "vehicle_types": ["car", "bus", "truck"],
  "simulation_length": 3600  // seconds
}

Response:
{
  "vehicle_count": 1200,
  "average_speed": 30,
  "congestion_ratio": 0.3
}
```

### GET /api/v1/cities/{city_id}/chunk/{chunk_id}
```
Response: Chunk assets (buildings, trees, roads in world_spec format)
```

---

**Phase 1 Timeline:** 6-8 weeks  
**Target Release:** v0.2.0  
**Next:** Phase 2 (multi-agent narrative system)
