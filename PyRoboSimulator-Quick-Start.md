# PyRoboSimulator Visual Engine – Quick Start Guide

**For:** Team leads starting Phase 0 PoC  
**Duration:** 2–3 weeks  
**Team:** 2 engineers (1 UE5, 1 Python)

---

## What Are We Building?

A world-generation platform that:
1. Accepts natural language instructions: *"Generate Tokyo after cherry blossom season at sunset after light rain"*
2. Generates a structured world specification (JSON) with **user-configurable terrain detail & rendering quality**
3. Loads that world in Unreal Engine 5
4. Renders it with AAA-quality graphics (configurable: 480p → 4K)
5. Generates terrain at user-selected detail (flat plane → photorealistic)
6. Simulates multiple sensor outputs: RGB camera, Depth, Lidar, Thermal
7. Returns sensor data via REST/gRPC API

**Goal:** Prove the end-to-end loop works in 3 weeks with flexible quality scaling.

**Key Features:**
- ⚙️ **Configurable Rendering Quality:** Low (480p) → Ultra (4K)
- 🏔️ **Configurable Terrain Detail:** Level 0 (flat) → Level 10 (photorealistic)
- 🌳 **Independent Vegetation & Building Complexity** control
- 📊 **Hardware-Aware Recommendations** (GPU detection + auto-profile selection)
- 🎬 **Scalable Output:** Same world at multiple quality levels (720p + 4K)

---

## Key Configuration Parameters

Users can independently control **3 dimensions** when generating worlds:

### 1. **Rendering Quality** (Visual fidelity)
- Profiles: Low (480p) → Medium (720p) → High (1080p) → Ultra (2K) → Cinematic (4K)
- Configurable: resolution, FPS, ray-tracing, anti-aliasing
- **Default: 720p, 30 FPS**

### 2. **Terrain Detail** (Geometric complexity)
- Levels: 0 (flat plane) → 5 (default) → 10 (photorealistic with erosion)
- Configurable: mesh density, vegetation density, building complexity, erosion simulation
- **Default: Level 5 (balanced)**

### 3. **Sensors** (What to capture)
- RGB (1080p video)
- Depth (aligned with RGB)
- Lidar (16–64 channels, configurable)
- Thermal (per-material emissivity)
- Optional: Radar, IMU, GPS, Event Camera

**These are INDEPENDENT:** You can have low rendering quality with high terrain detail (robot edge device) or vice versa (VFX test).

---

## Technology Stack (Frozen)

| Layer | Technology | Why |
|-------|-----------|-----|
| Rendering | Unreal Engine 5 | Best AAA quality + Lumen (real-time GI) + Nanite (megageometry) |
| NLP → Spec | Claude Sonnet 5 (extended thinking) + JSON Schema | Accurate semantic understanding of natural language |
| Backend API | FastAPI (Python) | Simple, fast, plays well with sensor data (NumPy arrays) |
| IPC Bridge | gRPC or REST | UE5 ↔ Python communication |
| Materials | Quixel + Custom PBR | 20K+ photoscanned materials + weathering layers |
| Terrain Config | Procedural + DEM + Satellite imagery | Multi-level detail from flat plane to photorealistic |
| Physics | Unreal Chaos (optional Phase 1+) | Native to UE5; we focus on visuals first |

---

## Phase 0 Deliverables Checklist

### ✅ Week 1: Setup & World Spec Generator

**Python Engineer:**
- [ ] Create GitHub repo: `PyRoboSimulator` on `phase-0/poc` branch
  ```bash
  git init PyRoboSimulator
  git checkout -b phase-0/poc
  mkdir -p backend/{world_spec,api} schemas docs
  ```

- [ ] Install dependencies
  ```bash
  pip install anthropic fastapi uvicorn pydantic pydantic-json-schema
  ```

- [ ] Implement `backend/world_spec/generator.py`
  ```python
  from anthropic import Anthropic
  
  def generate_world_spec(prompt: str) -> dict:
      """Convert natural language prompt to world spec JSON."""
      client = Anthropic()
      response = client.messages.create(
          model="claude-sonnet-5",
          max_tokens=10000,
          thinking={
              "type": "enabled",
              "budget_tokens": 8000
          },
          messages=[{
              "role": "user",
              "content": f"""Given: "{prompt}"
              
  Generate a world specification JSON matching this schema:
  {WORLD_SPEC_SCHEMA}
  
  Return ONLY valid JSON, no explanation."""
          }]
      )
      return json.loads(response.content[0].text)
  ```

- [ ] Create `backend/api/main.py` (FastAPI server)
  ```python
  from fastapi import FastAPI
  from backend.world_spec.generator import generate_world_spec
  
  app = FastAPI()
  
  @app.post("/api/v1/generate-world")
  def generate_world(prompt: str) -> dict:
      return generate_world_spec(prompt)
  
  @app.post("/api/v1/load-world")
  def load_world(world_spec: dict) -> dict:
      # Call UE5 via gRPC/REST to load the world
      return {"status": "loaded"}
  
  @app.get("/api/v1/sensors/rgb")
  def get_rgb_frame() -> dict:
      # Return latest RGB frame from UE5
      return {"image": "base64_encoded_png"}
  ```

- [ ] Load and validate `schemas/world_spec.json` (provided separately)

- [ ] Write unit tests for world spec generator
  ```bash
  pytest backend/tests/test_world_spec_generator.py
  ```

- [ ] Test 5 sample prompts:
  - "Tokyo at sunset after rain"
  - "Mars dust storm colony"
  - "Mumbai monsoon flood"
  - "Fictional cyberpunk city"
  - "Snowy alpine village"

**UE5 Engineer:**
- [ ] Create new UE5 5.4+ project (Blank, minimal plugins)
- [ ] Enable plugins: Pixel Streaming, Niagara, Chaos
- [ ] Create base directory structure:
  ```
  Content/
  ├── Materials/
  ├── Blueprints/
  ├── Maps/
  └── Meshes/
  ```

---

### ✅ Week 2: Micro-Scene in UE5

**UE5 Engineer:**

- [ ] Create micro-scene map: `Maps/M_ParkingLot_Micro`
  - [ ] Ground plane (200m × 200m, flat terrain)
  - [ ] Parking lot (asphalt, 100m × 80m)
  - [ ] Simple building (cube, ~20m tall)
  - [ ] 2–3 trees (SpeedTree or modeled)
  - [ ] Puddle area (water plane, 2m × 3m)

- [ ] Implement PBR materials:
  - [ ] `M_Asphalt` (roughness=0.8, metallic=0.0, gray)
  - [ ] `M_AsphaltWet` (roughness=0.4, metallic=0.1, reflective)
  - [ ] `M_Concrete` (roughness=0.9, metallic=0.0, light gray)
  - [ ] `M_Grass` (roughness=0.95, metallic=0.0, green)
  - [ ] `M_TreeBark` (brown, normal-mapped)
  - [ ] `M_TreeLeaves` (green with SSS, seasonal tint)
  - [ ] `M_Water` (metallic=1.0, roughness=0.3)

- [ ] Create lighting blueprint: `BP_SunLight`
  - [ ] Directional light (simulates sun)
  - [ ] Time-of-day input (0–24 hours) → sun angle, color, intensity
  - [ ] Cascade shadow map (4 levels)
  - [ ] Example: hour=18 → orange tint, low intensity, long shadows

- [ ] Create weather blueprint: `BP_WeatherManager`
  - [ ] Exposed parameters: `RainIntensity`, `CloudCover`, `FogDensity`
  - [ ] Rain effect: Niagara particle system + material lerp (dry → wet)
  - [ ] Cloud effect: Volumetric fog, sky darkening
  - [ ] Test: rain_intensity=0.8 → roads look wet, visibility drops

- [ ] Create a simple test sequence:
  - Load scene
  - Transition time from 6:00 (sunrise) → 18:00 (sunset)
  - Toggle weather (clear → rainy)
  - Verify visual transitions look correct

---

### ✅ Week 3: Sensor Output & API Bridge

**UE5 Engineer:**

- [ ] Implement RGB camera capture
  - [ ] Scene Capture 2D component
  - [ ] Render target: 1920 × 1080, 8-bit RGBA
  - [ ] Export to texture file or via gRPC

- [ ] Implement Depth camera
  - [ ] Scene Capture 2D (depth-only render target)
  - [ ] Material: encode depth as grayscale
  - [ ] Discontinuity detection for edges

- [ ] Implement Lidar sensor blueprint: `BP_LidarSensor`
  - [ ] 16 rays vertically × 32 rays horizontally = 512 rays/frame
  - [ ] Ray-cast each frame
  - [ ] 10 Hz rotation (one sweep per 0.1s)
  - [ ] Output: point cloud (X, Y, Z, intensity)
  - [ ] Rain noise: if `rain_intensity > 0.5`, add random jitter to points

- [ ] Implement Thermal camera
  - [ ] Scene Capture 2D with custom thermal material
  - [ ] Material: per-pixel emissivity lookup
    - Asphalt: 0.95 (appears dark)
    - Water: 0.98 (very dark)
    - Metal: 0.15 (appears bright)
  - [ ] Output: thermal_map.exr (0–1 scale)

- [ ] Create gRPC bridge (or simple REST)
  - [ ] UE5 listens on localhost:8000
  - [ ] FastAPI sends `/load-world` command
  - [ ] UE5 applies world spec parameters

**Python Engineer:**

- [ ] Expand FastAPI with sensor endpoints:
  ```python
  @app.get("/api/v1/sensors/rgb")
  def get_rgb() -> FileResponse:
      # Return latest RGB PNG
  
  @app.get("/api/v1/sensors/depth")
  def get_depth() -> FileResponse:
      # Return depth as NPY or EXR
  
  @app.get("/api/v1/sensors/lidar")
  def get_lidar() -> dict:
      # Return point cloud as Nx4 array
      return {"points": points.tolist()}
  
  @app.get("/api/v1/sensors/thermal")
  def get_thermal() -> FileResponse:
      # Return thermal map
  ```

- [ ] Implement validation tests:
  ```python
  def test_rain_occlusion():
      """Lidar point density should decrease in rain."""
      spec_no_rain = {..., "weather": {"type": "clear"}}
      spec_rain = {..., "weather": {"type": "rain", "intensity": 0.8}}
      
      load_world(spec_no_rain)
      points_dry = capture_lidar()
      
      load_world(spec_rain)
      points_wet = capture_lidar()
      
      # Expect ~30% fewer points
      assert len(points_wet) < 0.7 * len(points_dry)
  ```

- [ ] Create demo script: `demo/poc_demo.py`
  ```bash
  python demo/poc_demo.py \
      --prompt "Tokyo at sunset after rain" \
      --output-dir output/poc_demo/
  # Output: RGB.png, depth.npy, lidar.pcd, thermal.exr
  ```

- [ ] Generate validation report: `docs/phase0_validation.md`
  - Screenshots of all sensor outputs
  - Metrics: latency, point cloud density, thermal accuracy
  - Pass/fail checklist

---

## Success Validation (Day 21)

Run the demo script and verify:

```bash
✓ NLP prompt → world spec JSON (semantic correctness)
✓ RGB output: 1080p, no artifacts, correct lighting
✓ Depth output: aligned with RGB, sharp edges
✓ Lidar output: 512 points/frame, rain scatter visible
✓ Thermal output: asphalt > water > metal (emissivity ordering)
✓ API latency: <100ms per sensor query
✓ Sunset lighting: orange tint, long shadows
✓ Wet asphalt: visible specular reflections
```

If ✓ all pass → proceed to Phase 1 (procedural cities, expanded weather, traffic)

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `world_spec_schema.json` | Complete schema for world specifications |
| `PyRoboSimulator-Visual-Engine-Architecture.md` | Full 4-phase roadmap (22 weeks) |
| `PyRoboSimulator-Phase0-Sprint.md` | Detailed week-by-week sprint breakdown |
| `backend/world_spec/generator.py` | Claude API world spec generation |
| `backend/api/main.py` | FastAPI server |
| `Content/Blueprints/BP_SunLight` | Time-of-day + lighting system |
| `Content/Blueprints/BP_WeatherManager` | Weather system (rain, fog, clouds) |
| `Content/Blueprints/BP_LidarSensor` | Lidar ray-cast + point cloud output |

---

## Team Sync Points

- **EOD Week 1 (Fri):** World spec generator working + UE5 scene started
- **EOD Week 2 (Fri):** All materials + lighting complete + sensors drafted
- **EOD Week 3 (Fri):** Demo runs end-to-end + validation report complete

---

## Common Issues & Fixes

### UE5 Ray-Cast is Slow (10 FPS)
- **Solution:** Use hardware ray-tracing (RTX); profile with GPU debugger
- **Fallback:** Pre-bake collision geometry; cache ray results

### Claude API Hallucinating World Spec
- **Solution:** Add strict JSON schema validation + enum constraints
- **Test:** Feed edge cases ("underwater city", "Saturn moon")

### Thermal Emissivity Inaccurate
- **Solution:** Validate against real thermal camera data
- **Reference:** FLIR Boson thermal imaging specs

### Wet Asphalt Not Reflective Enough
- **Solution:** Adjust material roughness (0.4 instead of 0.5)
- **Check:** Compare with Flight Simulator wet road materials

---

## Phase 1 Sneak Peek (Not This Sprint)

Once PoC validates, Phase 1 will add:
- Procedural city generation (2km × 2km)
- Traffic & pedestrians
- Real-time weather transitions
- Seasonal vegetation changes
- Extended sensors (Radar, IMU, Event Camera)
- Persistent world state (PostgreSQL)

**Estimated:** 6–8 weeks, 3–4 engineers

---

**Status:** Ready to kick off Week 1  
**Questions?** See `PyRoboSimulator-Phase0-Sprint.md` for detailed breakdown

