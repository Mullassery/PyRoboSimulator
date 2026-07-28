# PyRoboSimulator Phase 0 Week 2: UE5 Micro-Scene & Materials

## Overview

**Goal:** Build a 200m × 200m parking lot scene in Unreal Engine 5 with AAA-quality rendering, dynamic lighting, and realistic materials.

**Timeline:** 1 week (3 days for scene/materials + 2 days for integration + 2 days buffer)  
**Team:** 1 UE5 engineer (C++ + Blueprints)  
**Engine Version:** UE 5.4+ (Nanite + Lumen enabled)  

---

## Phase 0 Week 2 Deliverables

### 1. UE5 Project Structure ✅ (Plan)

```
PyRoboSimulator-UE5/
├── Binaries/
├── Content/
│   ├── Maps/
│   │   └── ParkingLot/
│   │       └── ParkingLot_Main.umap        # 200m x 200m scene
│   │
│   ├── Materials/
│   │   ├── MI_Asphalt.uasset
│   │   ├── MI_WetAsphalt.uasset
│   │   ├── MI_Concrete.uasset
│   │   ├── MI_Grass.uasset
│   │   ├── MI_Bark.uasset
│   │   ├── MI_Leaves.uasset
│   │   ├── MI_Water.uasset
│   │   └── MasterMaterial_PBR.uasset
│   │
│   ├── Meshes/
│   │   ├── Roads/
│   │   ├── Buildings/
│   │   ├── Vegetation/
│   │   └── Props/
│   │
│   ├── Blueprints/
│   │   ├── BP_WorldLoader.cpp              # Loads world specs
│   │   ├── BP_SensorManager.cpp            # Manages captures
│   │   └── BP_WeatherSystem.cpp            # Dynamic weather
│   │
│   └── Plugins/
│       └── PyRoboSim/
│           ├── Binaries/
│           ├── Resources/
│           ├── Source/
│           │   └── PyRoboSim/
│           │       ├── Public/
│           │       │   ├── WorldLoaderComponent.h
│           │       │   ├── SensorCaptureComponent.h
│           │       │   └── WeatherSystemComponent.h
│           │       └── Private/
│           │           ├── WorldLoaderComponent.cpp
│           │           ├── SensorCaptureComponent.cpp
│           │           └── WeatherSystemComponent.cpp
│           └── .uplugin
│
├── Source/
│   ├── PyRoboSimulator/
│   │   ├── Public/
│   │   │   ├── PyRoboSimulator.h
│   │   │   ├── ParkingLotActor.h
│   │   │   ├── WorldSpecLoader.h
│   │   │   └── SensorSimulator.h
│   │   │
│   │   └── Private/
│   │       ├── PyRoboSimulator.cpp
│   │       ├── ParkingLotActor.cpp
│   │       ├── WorldSpecLoader.cpp
│   │       └── SensorSimulator.cpp
│   │
│   └── PyRoboSimulator.Target.cs
│
└── PyRoboSimulator.uproject
```

### 2. Parking Lot Scene Layout ✅ (Design)

**Scene Bounds:** 200m × 200m × 50m (XYZ)  
**Ground Level:** Z = 0m (sea level)  
**Sky Height:** Z = 50m  

#### Ground Layout:
```
                    North (Y+)
    +────────────────────────────────────+
    │  Parking Rows (Asphalt)            │
    │  [50 parking spaces]               │
    │                                    │  100m
    │  ┌─ Building (Concrete) ─┐        │
    │  │  [Parking Garage]      │        │
    │  │  30m x 60m x 15m high  │        │
    │  └────────────────────────┘        │
    │                                    │
    │  [Vegetation Areas]                │
    │                                    │
    +────────────────────────────────────+
    West (X-)           East (X+)
         100m
```

#### Key Elements:
1. **Asphalt Base** (180m × 180m)
   - Main parking surface
   - Worn texture + wet areas
   - Parking space lines (white)
   - Road markings (yellow)

2. **Parking Garage** (30m × 60m × 15m)
   - Concrete walls + pillars
   - Realistic shadows
   - Multifloor (3 floors, 5m each)

3. **Vegetation** (corners)
   - Grass areas (20m × 20m each corner)
   - 10-15 trees with bark + leaves
   - Bushes and shrubs

4. **Weather Elements**
   - Water puddles (simulated wet asphalt)
   - Puddles for rain capture validation

5. **Lighting Setup**
   - Directional light (sun)
   - 12 street light posts (poles 8m high)
   - Ambient light (realistic)

---

### 3. Material Definitions ✅ (Design)

#### Master Material (Physically Based)

**Name:** `MasterMaterial_PBR`  
**Domain:** Surface (Deferred)  

**Parameters:**
```
Vector3 BaseColor
Scalar Roughness (0-1)
Scalar Metallic (0-1)
Scalar Normal Strength (0-2)
Scalar Emissivity (0-1)
Texture2D BaseColorMap
Texture2D NormalMap
Texture2D RoughnessMap
Texture2D MetallicMap
Texture2D AmbientOcclusionMap
Bool UseDisplacement
```

#### Material Instances

**1. MI_Asphalt**
- BaseColor: (0.15, 0.15, 0.15)
- Roughness: 0.75
- Metallic: 0.0
- Normal: 1.0
- Emissivity: 0.95
- Texture: Asphalt with wear patterns
- Use Case: Main parking surface

**2. MI_WetAsphalt**
- BaseColor: (0.10, 0.10, 0.10)
- Roughness: 0.25 (glossy/reflective)
- Metallic: 0.0
- Normal: 1.5 (more reflections)
- Emissivity: 0.97
- Texture: Wet asphalt with puddles
- Use Case: Rain simulation validation
- **Special:** Use wet material blending on surface for rain

**3. MI_Concrete**
- BaseColor: (0.60, 0.60, 0.60)
- Roughness: 0.80
- Metallic: 0.0
- Normal: 1.0
- Emissivity: 0.90
- Texture: Concrete with weathering
- Use Case: Parking garage walls

**4. MI_Grass**
- BaseColor: (0.1, 0.35, 0.1)
- Roughness: 0.85
- Metallic: 0.0
- Normal: 1.2
- Emissivity: 0.98
- Texture: Grass with blade normal map
- Use Case: Corner vegetation areas

**5. MI_Bark**
- BaseColor: (0.35, 0.25, 0.15)
- Roughness: 0.80
- Metallic: 0.0
- Normal: 1.5
- Emissivity: 0.98
- Texture: Tree bark with natural variation
- Use Case: Tree trunks

**6. MI_Leaves**
- BaseColor: (0.1, 0.4, 0.1) → seasonal variation
- Roughness: 0.60
- Metallic: 0.0
- Normal: 1.3
- Emissivity: 0.97
- Texture: Foliage with subsurface scattering
- Use Case: Tree canopies
- **Special:** Seasonal color mapping:
  - Spring: Pale green (0.2, 0.45, 0.2)
  - Summer: Rich green (0.1, 0.40, 0.1)
  - Fall: Orange/red (0.5, 0.25, 0.1)
  - Winter: Muted (0.15, 0.2, 0.1)

**7. MI_Water**
- BaseColor: (0.05, 0.2, 0.3)
- Roughness: 0.10 (very glossy)
- Metallic: 0.0
- Normal: 2.0 (strong water ripples)
- Emissivity: 0.93
- Texture: Water with animated wave normal map
- Use Case: Puddles, water features

**8. MI_Metal**
- BaseColor: (0.5, 0.5, 0.5)
- Roughness: 0.20
- Metallic: 1.0
- Normal: 1.0
- Emissivity: 0.10
- Texture: Polished metal
- Use Case: Vehicle bodies, light poles

---

### 4. Dynamic Lighting System ✅ (Design)

#### Sun (Directional Light)
**Type:** Directional Light  
**Intensity:** 1.0-2.0 (based on time of day)  
**Rotation:** Controlled by time-of-day parameters  

**Time-of-Day Mapping:**
```python
# Elevation angle = f(hour)
# 6:00 AM:   -15° (just rising)
# 9:00 AM:   +20°
# 12:00 PM:  +45° (noon, highest)
# 3:00 PM:   +30°
# 6:00 PM:   -10° (sunset)
# 9:00 PM:   -45° (below horizon)

# Azimuth angle = 180° + (hour - 6) * 15°
# (assuming sun rises in east, sets in west)
```

**Color Temperature:**
```python
# 6:00 AM:   Orange (1.2, 0.7, 0.5)
# 12:00 PM:  White (1.0, 1.0, 0.9)
# 6:00 PM:   Orange-red (1.5, 0.6, 0.3)
```

**Shadow Settings:**
- Cascaded shadow maps (4 cascades)
- Dynamic shadows enabled
- Max shadow distance: 500m
- Shadow resolution: 1024×1024 per cascade

#### Street Lights (12 × Point Lights)

**Type:** Point Light  
**Intensity:** 500 lumens  
**Color:** Warm white (1.0, 0.9, 0.7)  
**Radius:** 30m  
**Positions:** Around perimeter at corners + edges  
**Casting:** Shadows on (but optimized)  

**Array Pattern:**
```
Grid: 4 lights on N edge, 4 on S, 2 on E, 2 on W
Spacing: ~25m apart
Height: 8m above ground
```

#### Ambient Light

**Type:** Skylight (no texture, solid color)  
**Intensity:** 0.3  
**Color:** Sky blue (0.8, 0.9, 1.0)  
**Specular Scale:** 1.0  

**Alternative (Phase 1):** Replace with actual sky dome from Quixel Megalibs

#### Post-Processing

**Exposure:** Auto (adaptive)  
**Contrast:** 1.1  
**Saturation:** 1.0  
**Bloom:** Enabled (threshold 0.5)  
**Motion Blur:** Disabled (Phase 0)  
**Depth of Field:** Disabled (Phase 0)  
**Ambient Occlusion:** Enabled (radius 50cm)  
**Screen Space Reflections:** Enabled (high quality)  

---

### 5. Weather System ✅ (Design)

#### Rain Simulation

**Type:** Cascading Post-Process Material  
**Parameters:**
- `RainIntensity` (0-1): Controls particle density + wet surface blending
- `PuddleHeight` (0-10cm): Wet surface level
- `SurfaceWetness` (0-1): Blend between dry + wet materials

**Implementation:**
1. Disable/enable directional light intensity (80% at heavy rain)
2. Blend asphalt materials: dry → wet (based on RainIntensity)
3. Add fake puddles using decals (transparent water material)
4. Darken sky color (overcast effect)
5. Add particle effect (falling raindrops)

**Cascade:**
```
RainIntensity = 0.0:  Clear day, dry asphalt, blue sky
RainIntensity = 0.3:  Light drizzle, slight wet spots
RainIntensity = 0.6:  Moderate rain, significant wet areas
RainIntensity = 1.0:  Heavy downpour, flooded puddles
```

#### Cloud Coverage

**Type:** Sky material + Directional Light adjustment  
**Parameters:**
- `CloudCoverage` (0-1): 0 = clear, 1 = fully overcast

**Implementation:**
1. Modulate directional light intensity: 1.0 → 0.6 (fully cloudy)
2. Increase ambient light intensity: 0.3 → 0.5 (cloudy skies are brighter ambient)
3. Desaturate sky color (from bright blue to gray)

**Cascade:**
```
CloudCoverage = 0.0:  Bright blue sky, 1.0 sun intensity
CloudCoverage = 0.5:  Partly cloudy, 0.8 sun intensity
CloudCoverage = 1.0:  Gray overcast, 0.6 sun intensity
```

#### Fog

**Type:** Exponential Height Fog  
**Parameters:**
- `FogDensity` (0-1)
- `FogHeightFalloff` (0.2)

**Settings (per density):**
```
FogDensity = 0.0:  No fog
FogDensity = 0.5:  Light haze, 500m visibility
FogDensity = 1.0:  Heavy fog, 100m visibility
```

#### Wind

**Type:** Wind Director (Blueprint)  
**Parameters:**
- `WindSpeed` (0-20 m/s)
- `WindDirection` (0-360°)

**Use Cases:**
- Particle direction (rain angle)
- Foliage animation (leaf sway)
- Tree branch sway (future phases)

---

### 6. Seasonal Color Correction ✅ (Design)

**Implementation:** Post-Process Volume with per-season settings

#### Color Grade LUT (Look-Up Table)

**Day of Year → Season Mapping:**
```
DOY 1-90:     Winter → Cool (blue shift, desaturation)
DOY 91-180:   Spring → Warm greens, higher saturation
DOY 181-270:  Summer → Bright, warm, high saturation
DOY 271-365:  Fall → Orange/red shift, warm desaturation
```

#### Material Color Adjustments

**Foliage (MI_Leaves):**
- Spring: (0.2, 0.45, 0.2) – Fresh greens
- Summer: (0.1, 0.40, 0.1) – Rich greens
- Fall: (0.5, 0.25, 0.1) – Oranges/reds
- Winter: (0.15, 0.2, 0.1) – Muted browns

**Grass (MI_Grass):**
- Spring: (0.15, 0.40, 0.1) – Bright greens
- Summer: (0.1, 0.35, 0.1) – Normal green
- Fall: (0.2, 0.3, 0.1) – Yellowed
- Winter: (0.1, 0.15, 0.05) – Brown-green

**Lighting Adjustments:**
- Winter: Cooler color temp (sun = 0.9, 0.9, 1.1)
- Summer: Warmer color temp (sun = 1.1, 1.0, 0.8)

---

### 7. Sensor Camera Setup ✅ (Design)

#### Main Camera (Stationary)
**Position:** (0, -80, 10)  
**Rotation:** Looking at (0, 0, 1) – parking lot center slightly elevated  
**FOV:** 90°  
**Aspect Ratio:** 16:9  

#### Scene Capture Cameras (C++)

**RGB Camera:**
- Scene Capture 2D Component
- Capture Source: Scene Color (ToneMapped)
- Resolution: 1920 × 1080
- Refresh Rate: 30 FPS
- Format: PNG

**Depth Camera:**
- Scene Capture 2D Component
- Capture Source: Scene Depth in R
- Resolution: 1920 × 1080
- Refresh Rate: 30 FPS
- Format: Raw depth (0-1 normalized)
- Post-Processing: Convert to NPY format in Python

**Lidar (Ray-Cast):**
- Custom C++ component
- Ray casting: 512 rays per frame (16 channels × 32 horizontal)
- Range: 100m max
- Frequency: 10 Hz (async queuing)
- Output: Point Cloud (X, Y, Z, intensity)
- Format: PCD file

**Thermal:**
- Scene Capture 2D Component
- Texture: Custom thermal material
- Resolution: 320 × 240 (typical thermal resolution)
- Frequency: 10 Hz
- Temperature lookup: Per-material emissivity
- Range: -20°C to 60°C → grayscale mapping

---

### 8. Python ↔ UE5 Bridge ✅ (Design)

#### REST API Integration (Python ← → UE5)

**Endpoint (Python):** `POST /api/v1/load-world`  
**Request:** WorldSpec JSON  
**UE5 Handler:**
1. Parse JSON in C++
2. Load assets by material type
3. Spawn objects at positions
4. Set lighting parameters
5. Configure weather
6. Return ready status

**Implementation:**
- HTTP library: libcurl in C++
- Endpoint: `http://localhost:8000/api/v1/load-world`
- Parse using rapidjson (or nlohmann/json)

#### Sensor Output Integration (UE5 → Python)

**Data Flow:**
```
UE5 Scene Capture → Memory Buffer → Write to disk
                  → HTTP POST to Python API (optional, Phase 1)
                  → Stored in /tmp/pyrobo_sensor_output/{world_id}/
```

**File Output Locations:**
```
/tmp/pyrobo_sensor_output/{world_id}/
├── rgb/
│   └── frame_0000.png
│   └── frame_0001.png
│   └── ...
├── depth/
│   └── frame_0000.npy
│   └── frame_0001.npy
│   └── ...
├── lidar/
│   └── frame_0000.pcd
│   └── frame_0001.pcd
│   └── ...
└── thermal/
    └── frame_0000.npy
    └── frame_0001.npy
    └── ...
```

---

## Week 2 Implementation Checklist

### Day 1-2: Scene Setup & Materials
- [ ] Create UE5 5.4+ project
- [ ] Set up folder structure (Maps, Materials, Meshes, Blueprints)
- [ ] Create 200m × 200m landscape/ground plane (Asphalt material)
- [ ] Build Master PBR material
- [ ] Create 8 material instances (Asphalt, WetAsphalt, Concrete, Grass, Bark, Leaves, Water, Metal)
- [ ] Import/create basic meshes:
  - [ ] Parking lot surface (landscape or large static mesh)
  - [ ] Parking garage building (simple modular concrete pieces)
  - [ ] 10-15 tree meshes (using Quixel Megalibs or free assets)
  - [ ] Light poles (simple cylinder + light component)
- [ ] Apply materials to meshes
- [ ] Layout scene (garage, parking spaces, vegetation areas)

### Day 2-3: Lighting & Weather
- [ ] Set up directional light (sun) with time-of-day rotation
- [ ] Place 12 point lights (street lamps) around perimeter
- [ ] Configure ambient lighting (skylight)
- [ ] Set up post-processing (exposure, bloom, AO, SSR)
- [ ] Create weather system blueprint:
  - [ ] Rain material blending (dry ↔ wet asphalt)
  - [ ] Cloud coverage (light intensity modulation)
  - [ ] Fog (exponential height fog)
  - [ ] Wind director
- [ ] Implement seasonal color correction:
  - [ ] Day-of-year → season mapping
  - [ ] Foliage color changes
  - [ ] Lighting temperature adjustments

### Day 3: Sensors & Validation
- [ ] Create Main Camera (stationary viewpoint)
- [ ] Create RGB Scene Capture 2D camera
- [ ] Create Depth Scene Capture 2D camera
- [ ] Implement Lidar ray-caster (C++)
  - [ ] 512 rays per frame (16 × 32 grid)
  - [ ] Async ray casting
  - [ ] Point cloud generation
- [ ] Implement Thermal camera (material-based lookup)
- [ ] Set up file output structure
- [ ] Create test captures:
  - [ ] Clear day (no rain)
  - [ ] Wet asphalt (rain_intensity = 0.8)
  - [ ] Sunset lighting (hour = 18)
  - [ ] Overcast (cloud_coverage = 1.0)

### Day 4-5: Integration & Testing
- [ ] Implement world loader component (C++)
  - [ ] Parse WorldSpec JSON
  - [ ] Load scene based on spec
  - [ ] Set parameters (lighting, weather, season)
- [ ] Set up HTTP bridge:
  - [ ] Listen for load-world requests
  - [ ] Validate spec parameters
  - [ ] Load and configure scene
- [ ] Create sensor manager:
  - [ ] Capture RGB, Depth, Lidar, Thermal on demand
  - [ ] Save to disk in correct formats
  - [ ] Return metadata
- [ ] Validation tests:
  - [ ] Load parking lot spec → render correctly
  - [ ] Rain + wet asphalt → verify material blending
  - [ ] Sunset lighting → check color temperature
  - [ ] Lidar rain scatter → validate point density drop
  - [ ] Thermal emissivity → verify material ordering

### Day 5+: Buffer
- [ ] Polish and optimization
- [ ] Performance profiling
- [ ] Bug fixes

---

## Success Criteria (Week 2)

| Metric | Target | How to Validate |
|--------|--------|-----|
| Scene Loads | Complete 200m × 200m scene | Visual inspection in viewport |
| Materials Quality | Realistic PBR | Compare to reference photos |
| Lighting | Correct for time-of-day | Screenshots at 6am, 12pm, 6pm |
| Rain Effect | ~30% point loss @ 80% rain | Capture Lidar baseline + with rain |
| Wet Asphalt | Visible specular highlights | Side-by-side dry vs. wet captures |
| Thermal Accuracy | Asphalt > water > metal | Verify thermal output ordering |
| Sunset Lighting | Warm orange, long shadows | Screenshot at hour=18 |
| Frame Rate | 30 FPS @ 1080p | Measure in viewport |
| API Integration | Load-world endpoint works | POST JSON → scene updates |

---

## Resources & References

### Unreal Engine 5 Documentation
- [Physically Based Materials](https://docs.unrealengine.com/5.0/en-US/material-instances-in-unreal-engine/)
- [Lighting in UE5](https://docs.unrealengine.com/5.0/en-US/lighting-in-unreal-engine/)
- [Nanite Virtualized Geometry](https://docs.unrealengine.com/5.0/en-US/nanite-virtualized-geometry-in-unreal-engine/)
- [Lumen Global Illumination](https://docs.unrealengine.com/5.0/en-US/lumen-global-illumination-and-reflections-in-unreal-engine/)
- [Scene Capture Component](https://docs.unrealengine.com/5.0/en-US/scene-capture-component-in-unreal-engine/)

### Asset Libraries
- [Quixel Megalibs](https://www.quixel.com/megalibs) – Free PBR materials + meshes (requires Epic account)
- [Unreal Marketplace](https://www.unrealmarketplace.com/) – Free vegetation, buildings, props

### Rendering Reference
- [PBR Theory](https://learnopengl.com/PBR/Theory) – Material properties explained
- [Thermal Imaging Guide](https://www.flir.com/) – Emissivity reference values

---

## Next: Week 3

**Goal:** Implement actual sensor capture and end-to-end validation

**Deliverables:**
- RGB capture (1080p @ 30 FPS, PNG)
- Depth capture (aligned with RGB, NPY)
- Lidar capture (16-channel, 10 Hz, PCD)
- Thermal capture (per-material emissivity, NPY)
- gRPC/REST bridge (UE5 ↔ Python)
- Demo script (end-to-end: NLP → render → sensors)
- Validation tests (rain occlusion, wet roads, thermal accuracy, sunset lighting)

---

**Status:** Week 2 Design Complete. Ready for UE5 Implementation.
