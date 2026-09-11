# PyRoboSimulator Phase 0: Sprint Plan (Weeks 1–3)

## Sprint Goal
Prove end-to-end loop: NLP instruction → world spec → UE5 renders → sensors output → validation.

**Deliverable:** Parking lot scene in rain at sunset with RGB, depth, Lidar, thermal outputs.

---

## Week 1: Setup & World Spec Generator

### Day 1–2: Project Initialization

- [ ] **Repository Setup**
  - [ ] Create GitHub repo: `PyRoboSimulator`
  - [ ] Branch: `phase-0/poc`
  - [ ] Directory structure:
    ```
    PyRoboSimulator/
    ├── backend/              # Python FastAPI
    │   ├── world_spec/       # World spec generator
    │   ├── api/              # FastAPI endpoints
    │   └── requirements.txt
    ├── unreal/               # UE5 project
    │   ├── Content/          # Assets, blueprints, materials
    │   ├── Binaries/
    │   └── PyRoboSimulator.uproject
    ├── schemas/              # JSON schemas
    │   └── world_spec.json
    └── docs/
    ```

- [ ] **Team & Environment**
  - [ ] Assign: 1 UE5 engineer, 1 Python backend engineer
  - [ ] UE5 5.4+ installed (or latest)
  - [ ] Python 3.11+, pip/uv
  - [ ] GPU: NVIDIA RTX 3090+ (or RTX 4090 preferred)

### Day 3–5: World Spec Generator

- [ ] **JSON Schema Design**
  - [ ] File: `schemas/world_spec.json`
  - [ ] Define:
    ```json
    {
      "location": {
        "name": "Tokyo",
        "latitude": 35.6762,
        "longitude": 139.6503,
        "scene_type": "urban" | "rural" | "mars_colony" | "fictional"
      },
      "time": {
        "year": 2026,
        "month": 3,
        "day": 15,
        "hour": 17,
        "minute": 30
      },
      "season": "spring" | "summer" | "autumn" | "winter",
      "weather": {
        "type": "sunny" | "cloudy" | "rain" | "heavy_rain" | "snow" | "storm",
        "intensity": 0.0 - 1.0,
        "wind_speed": 0 - 20,
        "humidity": 0.0 - 1.0,
        "air_temperature": -50 to 50,
        "visibility_km": 0.1 - 100
      },
      "environment": {
        "vegetation_density": "sparse" | "moderate" | "dense",
        "architecture_style": "modern" | "historical" | "futuristic",
        "population_density": "low" | "medium" | "high",
        "traffic_level": "none" | "light" | "moderate" | "heavy"
      },
      "scene_scale": {
        "width_meters": 200,
        "height_meters": 200,
        "terrain_detail_level": 0 - 10
      }
    }
    ```

- [ ] **Claude API Integration**
  - [ ] File: `backend/world_spec/generator.py`
  - [ ] Install: `pip install anthropic`
  - [ ] Implement `generate_world_spec(natural_language_prompt: str) -> dict`
    - Input: `"Generate Tokyo after cherry blossom season at sunset after light rain."`
    - Use Claude Sonnet 5 (extended thinking, ~10K tokens for reasoning)
    - Output: Populated JSON schema
    - Example logic:
      ```python
      prompt = f"""
      Given this instruction: "{natural_language_prompt}"
      
      Generate a world specification JSON. Infer:
      - Location (city, coordinates if known)
      - Season (spring → cherry blossoms, moderate temp, higher humidity)
      - Time (sunset → hour ~18, golden light)
      - Weather (after rain → wet roads, lower humidity post-rain, remaining clouds)
      - Vegetation (spring → fresh greens, blooming trees)
      
      Return valid JSON only.
      """
      ```
  - [ ] Add caching for repeated prompts (avoid API calls)
  - [ ] Test: 5 prompts (Tokyo, Mumbai, Mars, fictional, seasonal)

- [ ] **FastAPI Backend**
  - [ ] File: `backend/api/main.py`
  - [ ] Endpoints:
    ```python
    POST /api/v1/generate-world
    {
      "prompt": "Tokyo after cherry blossom season at sunset after light rain",
      "rendering_quality": {
        "profile": "medium",  # or "low", "high", "ultra", "custom"
        "resolution_width": 1280,
        "resolution_height": 720,
        "fps": 30
      }
    }
    # Response: world_spec JSON
    
    POST /api/v1/load-world
    {
      "world_spec": { ... },
      "ue5_instance_id": "instance-001"
    }
    # Response: { "status": "loaded", "scene_ready": true }
    
    GET /api/v1/rendering-profiles
    # Response: Hardware-aware list of available profiles + estimates
    
    POST /api/v1/update-quality
    {
      "world_id": "world-12345",
      "profile": "high",  # Upgrade from medium to high
      "resolution_width": 1920,
      "resolution_height": 1080,
      "fps": 60
    }
    ```
  - [ ] Add logging, error handling, quality validation
  - [ ] Add `/api/v1/health` endpoint
  - [ ] Add GPU detection (`backend/gpu_detector.py`)

- [ ] **Testing**
  - [ ] Unit test: world spec generator
  - [ ] Integration test: prompt → world spec → JSON validation
  - [ ] Examples:
    ```
    ✓ "Tokyo at sunset" → location="Tokyo", hour=18, weather=varied
    ✓ "Mars dust storm" → location="Mars", weather=dust_storm, terrain=red_rocky
    ✓ "Mumbai monsoon flood" → location="Mumbai", weather=heavy_rain, water_level=high
    ```

---

## Week 2: Micro-Scene in UE5

### Day 1–3: Scene Setup

- [ ] **UE5 Project & Plugins**
  - [ ] Create new UE5 project (Blank, without starter content to minimize size)
  - [ ] Plugins to enable:
    - [ ] `Pixel Streaming` (for remote visualization)
    - [ ] `Niagara` (particles, rain, smoke)
    - [ ] `Chaos` (physics)
    - [ ] `OpenEXR` (HDR export)
  - [ ] Project Settings:
    - [ ] Enable Ray Tracing (for reflection accuracy)
    - [ ] Set RHI to Vulkan (or DX12 on Windows)
    - [ ] Enable DLSS (for quality scaling) if RTX GPU available

- [ ] **Micro-Scene Layout**
  - [ ] Create 200m × 200m flat terrain (ground plane)
  - [ ] Manually place 3–5 simple assets:
    - [ ] Parking lot (asphalt plane, 100m × 80m)
    - [ ] One small building (simple cube, ~20m tall)
    - [ ] 2–3 trees (imported SpeedTree or modeled)
    - [ ] Water puddle area (2m × 3m, for rain interaction)
  - [ ] Blueprint name: `BP_MicroScene_Parking`

### Day 4–5: Materials & Lighting

- [ ] **PBR Materials (High Fidelity)**
  - [ ] Create Material functions:
    - [ ] `M_Asphalt` (roughness 0.8, metallic 0.0, base color dark gray)
    - [ ] `M_AsphaltWet` (roughness 0.4, metallic 0.1, reflectivity 0.3) ← for rain
    - [ ] `M_Concrete` (roughness 0.9, metallic 0.0, light gray)
    - [ ] `M_Grass` (roughness 0.95, metallic 0.0, green)
    - [ ] `M_TreeBark` (roughness 0.8, metallic 0.0, brown with variation)
    - [ ] `M_TreeLeaves` (normal map for leaf detail, subsurface scattering for spring leaves)
    - [ ] `M_WaterPuddle` (metallic 1.0, roughness 0.3, base color = environment reflection)
    - [ ] `M_BuildingConcrete` (weathered, slight moss tint on edges)
  - [ ] Use Quixel assets where possible (free via UE5)

- [ ] **Dynamic Lighting**
  - [ ] Blueprint: `BP_SunLight`
    - [ ] Directional light (simulates sun)
    - [ ] Adjustable angle (for time of day)
    - [ ] Time of day input: 0–24 (hours) → sun angle, intensity, color
    - [ ] Sunset logic: hour 18 → warm color (orange/red tint), lower intensity, longer shadows
    - [ ] Cascade shadow map (4 levels, for sharp nearby + soft far shadows)
  - [ ] Blueprint: `BP_AmbientLight`
    - [ ] Skybox (dynamic, responds to weather)
    - [ ] Indirect lighting (Lumen for real-time GI)

- [ ] **Quality Manager Blueprint**
  - [ ] Blueprint: `BP_QualityManager`
    - [ ] Enum: `ERenderingProfile` (Low, Medium, High, Ultra, Cinematic, Custom)
    - [ ] Parameters:
      - [ ] `RenderingProfile` (selected profile)
      - [ ] `TargetResolution` (stored resolution)
      - [ ] `TargetFPS` (stored FPS cap)
      - [ ] `RayTracingQuality` (off, low, medium, high, ultra)
      - [ ] `ShadowQuality` (low, medium, high, ultra)
      - [ ] `AntiAliasingMethod` (none, FXAA, TAA, DLSS, FSR)
      - [ ] `TemporalSuperResolution` (bool)
    - [ ] Functions:
      - [ ] `SetQualityProfile(profile: ERenderingProfile)` → applies all settings
      - [ ] `UpdateCustomResolution(width, height)` → applies custom resolution
      - [ ] `GetGPUInfo()` → detects VRAM, model, recommends profile
      - [ ] `AutoSelectProfile()` → chooses best profile for detected GPU
    - [ ] Test: Manually change profiles and verify smooth transitions

- [ ] **Weather System (Blueprint)**
  - [ ] Blueprint: `BP_WeatherManager`
    - [ ] Parameters: `RainIntensity` (0–1), `CloudCover` (0–1), `FogDensity` (0–1)
    - [ ] Rain effect:
      - [ ] Niagara particle system (rain particles falling, wind-affected)
      - [ ] Material wetness overlay: lerp(M_Asphalt, M_AsphaltWet) by `RainIntensity`
      - [ ] Puddle spawner: spawn puddles on flat surfaces when rain > 0.3
      - [ ] Sound: rain ambient sound (lower volume, looped)
    - [ ] Cloud effect:
      - [ ] Volumetric fog (Exponential Height Fog)
      - [ ] Adjust fog density by `CloudCover`
      - [ ] Adjust sun visibility (darker sky as clouds increase)
    - [ ] Seasonal overlay:
      - [ ] `SeasonalColorCorrection` post-process (green tint for spring, etc.)

---

## Week 3: Sensor Output & API Integration

### Day 1–2: Sensor Capture Blueprint

- [ ] **Camera System Blueprint**
  - [ ] Create `BP_SensorRig` (attach all sensors to rigid body/skeletal mesh)
    - [ ] RGB camera (CineCam, 1080p @ 30Hz)
    - [ ] Depth camera (scene capture → depth texture)
    - [ ] Lidar sensor (ray-cast sweep, 16-channel)

- [ ] **RGB Output**
  - [ ] Scene Capture 2D component
  - [ ] Render target: 1920 × 1080, 8-bit RGBA
  - [ ] Output to file or via Pixel Streaming

- [ ] **Depth Output**
  - [ ] Scene Capture 2D (render target: depth-only)
  - [ ] Custom material: encode depth as grayscale (0 = near, 1 = far)
  - [ ] Post-process: depth discontinuity detection (for object edges)

- [ ] **Lidar Output**
  - [ ] Blueprint: `BP_LidarSensor`
    - [ ] Ray-cast sweep (16 rays vertically, 32 rays horizontally = 512 rays per frame)
    - [ ] Rotation speed: 10 Hz (one full sweep per 0.1s)
    - [ ] Output: point cloud (X, Y, Z, intensity)
    - [ ] Intensity = 1.0 - (1.0 / max_range) * distance (farther = darker)
    - [ ] Rain interaction: add random noise to point cloud when rain > 0.5 (simulate droplet scatter)
    ```cpp
    // Pseudocode
    for (int angle = 0; angle < 360; angle += 11.25) { // 32 rays
      for (int tilt = -45; tilt <= 45; tilt += 6) { // 16 rays
        FVector start = sensor.location;
        FVector direction = angle_to_direction(angle, tilt);
        FHitResult hit;
        GetWorld()->LineTraceSingleByChannel(hit, start, start + direction * 200m);
        if (rain_intensity > 0.5 && random() < rain_intensity) {
          // Add jitter to point
          hit.location += FVector::RandomUnitVector() * rain_intensity * 0.5f;
        }
        point_cloud.push(hit.location);
      }
    }
    ```

- [ ] **Thermal Output**
  - [ ] Material: `M_ThermalView`
    - [ ] Input: per-material emissivity lookup
      - [ ] Asphalt: 0.95 (high emissivity = dark in thermal)
      - [ ] Water: 0.98 (very dark)
      - [ ] Concrete: 0.90
      - [ ] Metal: 0.15 (low emissivity = bright in thermal)
      - [ ] Grass: 0.92
      - [ ] Leaves: 0.97
    - [ ] Base temperature: 20°C (can adjust by air_temperature)
    - [ ] Wet surfaces: slightly warmer emissivity response (water temp != air temp)
  - [ ] Scene Capture 2D with thermal material applied
  - [ ] Output: thermal_map.exr (single-channel, 0–1 = cold–hot)

### Day 3–4: API Bridge

- [ ] **UE5-to-Python Communication**
  - [ ] Option A: HTTP REST (UE5 HTTP module)
    - [ ] UE5 listens on `localhost:8000`
    - [ ] Python sends `/load-world` command
    - [ ] UE5 blueprint loads world spec, updates parameters
  - [ ] Option B: gRPC (recommended for performance)
    - [ ] Install: `gRPC C++ plugin for UE5`
    - [ ] Define `.proto` services:
      ```protobuf
      service WorldSimulation {
        rpc LoadWorld(WorldSpec) returns (LoadResponse);
        rpc UpdateWeather(WeatherParams) returns (UpdateResponse);
        rpc CaptureAllSensors(Empty) returns (SensorData);
      }
      message SensorData {
        bytes rgb_image = 1;
        bytes depth_map = 2;
        bytes point_cloud = 3;
        bytes thermal_map = 4;
      }
      ```

- [ ] **Python API Endpoints (Extended)**
  - [ ] `POST /api/v1/load-world` → calls UE5 gRPC LoadWorld
  - [ ] `GET /api/v1/sensors/rgb?quality=medium&format=png` → returns latest RGB frame
  - [ ] `GET /api/v1/sensors/depth?quality=medium` → returns depth map (EXR or NPY)
  - [ ] `GET /api/v1/sensors/lidar?quality=medium` → returns point cloud (PCD or NPY: Nx4 float32)
  - [ ] `GET /api/v1/sensors/thermal?quality=medium` → returns thermal map (NPY or EXR)
  - [ ] `GET /api/v1/rendering-profiles` → returns hardware-aware profiles + estimates
  - [ ] `POST /api/v1/update-quality` → change quality mid-simulation (requires reload)
  - [ ] `POST /api/v1/weather` → update weather parameters in UE5
  - [ ] `GET /api/v1/world-state` → returns current world spec + sensor timestamps + quality settings
  - [ ] **Quality parameter support:** All sensor endpoints accept optional `?quality=low|medium|high|ultra|custom`

- [ ] **Sensor Data Validation**
  - [ ] Test 1: Rain occlusion in Lidar
    - [ ] Load scene with rain_intensity=0.0 → capture lidar → save baseline
    - [ ] Load scene with rain_intensity=0.8 → capture lidar → expect ~30% point loss
    - [ ] Verify: point cloud density decreases
  - [ ] Test 2: Wet asphalt reflections
    - [ ] Capture RGB with weather=dry → asphalt matte
    - [ ] Capture RGB with weather=wet → asphalt shiny (specular highlights)
  - [ ] Test 3: Thermal emissivity
    - [ ] Capture thermal with asphalt surface
    - [ ] Verify: asphalt appears dark (high emissivity)
    - [ ] Verify: puddle (water) appears darker than asphalt
  - [ ] Test 4: Sunset lighting
    - [ ] Capture RGB at hour=18 → warm orange shadows, golden light on surfaces
    - [ ] Verify: shadow length > midday shadow length

### Day 5: Documentation & Demo

- [ ] **README.md** (backend)
  - [ ] Setup instructions (Python env, dependencies)
  - [ ] Running the API: `python -m uvicorn backend.api.main:app --reload`
  - [ ] Example curl commands:
    ```bash
    curl -X POST http://localhost:8000/api/v1/generate-world \
      -H "Content-Type: application/json" \
      -d '{"prompt": "Tokyo at sunset after rain"}'
    
    curl http://localhost:8000/api/v1/sensors/rgb -o output.png
    ```

- [ ] **Demo Script** (`demo/poc_demo.py`)
  - [ ] Sequence:
    1. Generate world spec from NLP
    2. Load world in UE5
    3. Capture all sensor modalities (10 frames each)
    4. Save outputs to `output/poc_demo/`
    5. Print validation results (rain occlusion, wet roads, etc.)

- [ ] **Validation Report** (`docs/phase0_validation.md`)
  - [ ] Checklist of all success criteria
  - [ ] Screenshots of RGB, depth, Lidar, thermal
  - [ ] Sensor accuracy measurements
  - [ ] API latency measurements
  - [ ] GPU memory usage
  - [ ] Recommendations for Phase 1

---

## Definition of Done (Phase 0)

### Deliverables
- [ ] GitHub repo with Phase 0 code
- [ ] UE5 project (micro-scene with all materials, weather, lighting)
- [ ] Python FastAPI backend (world spec generator + sensor API)
- [ ] gRPC or REST bridge (UE5 ↔ Python)
- [ ] Demo script (NLP → rendered → sensors)
- [ ] Validation report with sensor accuracy metrics

### Success Criteria
- [ ] `generate-world` API generates correct JSON for 10 diverse NLP prompts
- [ ] UE5 scene loads world spec and applies parameters
- [ ] RGB output: 1080p, 30 FPS, no artifacts
- [ ] Depth output: aligned with RGB, no NANs
- [ ] Lidar output: 512 points/frame, rain scatter detectable
- [ ] Thermal output: emissivity-correct per material
- [ ] API latency: <100ms per sensor query
- [ ] All sensor outputs saved successfully to disk
- [ ] Validation tests pass (rain occlusion, wet roads, thermal emissivity, sunset lighting)

---

## Estimated Schedule

- **Week 1:** 16 person-days (2 engineers @ 40h/week)
- **Week 2:** 16 person-days
- **Week 3:** 14 person-days (finishing integration + validation)

**Total Phase 0:** ~46 person-days = ~5.75 person-weeks

**Parallel Work:**
- UE5 engineer: scene, materials, lighting, sensor blueprints
- Python engineer: world spec generator, API, gRPC bridge, demo

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| UE5 Lidar ray-cast is slow | 10 FPS with ray-casting | Pre-compute collision geometry; use hardware ray-tracing (RTX) |
| World spec generator hallucinating | Wrong parameters | Constrain Claude output with JSON schema + enum validation |
| gRPC bridge complexity | Delays week 3 | Start with simple HTTP REST; migrate to gRPC in Phase 1 |
| GPU memory (Lidar + sensors) | OOM crashes | Profile early; use async sensor capture (don't capture all at once) |
| UE5 Pixel Streaming lag | Validation delays | Use local viewport instead for PoC; Pixel Streaming for Phase 1 review |

---

## Next Review Checkpoint

**End of Week 1 (Friday):**
- [ ] World spec generator working (5 test prompts pass)
- [ ] UE5 project with basic scene + materials
- [ ] FastAPI backend accessible

**End of Week 2 (Friday):**
- [ ] All materials implemented + lighting correct
- [ ] Sensor blueprints drafted (RGB, Depth, Lidar, Thermal)
- [ ] gRPC/REST bridge in progress

**End of Week 3 (Friday):**
- [ ] All sensors outputting valid data
- [ ] Demo script runs end-to-end
- [ ] Validation report complete

