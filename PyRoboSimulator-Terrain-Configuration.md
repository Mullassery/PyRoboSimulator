# PyRoboSimulator: Terrain Detail & Complexity Configuration

**Purpose:** Allow users to independently control terrain mesh density, vegetation coverage, building complexity, and erosion simulation. Terrain detail is orthogonal to rendering quality—you can have low rendering quality with high terrain detail (or vice versa).

---

## Terrain Detail Levels (0–10 Scale)

### **Level 0: Flat Plane** ⚡ (Edge/Mobile)
```json
{
  "terrain": {
    "detail_level": 0,
    "mesh_density": 512,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 0,
    "building_complexity": 1
  }
}
```
**Use Case:**
- Mobile robots (Jetson Nano, edge devices)
- Minimal terrain variation (parking lots, indoor scenes)
- Real-time monitoring feeds
- Bandwidth-constrained environments

**Performance:** >120 FPS on mid-range GPUs (GTX 1050)  
**VRAM:** 1–2 GB  
**Description:** Literally a flat plane; no elevation variation

---

### **Level 1: Minimal Terrain** ⚡ (Embedded Systems)
```json
{
  "terrain": {
    "detail_level": 1,
    "mesh_density": 1024,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 1,
    "building_complexity": 2
  }
}
```
**Use Case:**
- Embedded robotics systems (Jetson Xavier)
- Very simple outdoor scenes (flat field with slight rolls)
- Lightweight simulation for quick iteration
- Data logging with minimal overhead

**Performance:** 60–90 FPS on mid-range GPUs  
**VRAM:** 2–3 GB

---

### **Level 2: Basic Heightmap** ⚡ (Low-End)
```json
{
  "terrain": {
    "detail_level": 2,
    "mesh_density": 2048,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 2,
    "building_complexity": 3
  }
}
```
**Use Case:**
- Low-end gaming GPUs (GTX 1080, RTX 2060)
- Simple outdoor terrain (hills, valleys)
- Early-stage robotics testing
- Procedural world generation (fast iteration)

**Performance:** 45–60 FPS on GTX 1080  
**VRAM:** 3–4 GB

---

### **Level 3: Moderate Terrain** 🟡 (Standard)
```json
{
  "terrain": {
    "detail_level": 3,
    "mesh_density": 2048,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 3,
    "building_complexity": 4
  }
}
```
**Use Case:**
- Small environments (100m × 100m parks, facilities)
- Natural-looking hills and water bodies
- Vegetation distribution (trees, grass patches)
- Early robotics validation

**Performance:** 30–45 FPS on RTX 3060  
**VRAM:** 4–5 GB

---

### **Level 4: Standard Terrain** 🟡 (Default for Small Scenes)
```json
{
  "terrain": {
    "detail_level": 4,
    "mesh_density": 4096,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 4,
    "building_complexity": 5
  }
}
```
**Use Case:**
- Typical outdoor environments (200m × 200m parking lots, gardens)
- Realistic rolling terrain
- Good vegetation distribution
- Mixed urban/natural scenes

**Performance:** 30–50 FPS on RTX 3070  
**VRAM:** 5–7 GB  
**Note:** Good balance between detail and performance

---

### **Level 5: Default Terrain Detail** ⭐ (Robotics Recommended)
```json
{
  "terrain": {
    "detail_level": 5,
    "mesh_density": 4096,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 5,
    "building_complexity": 5
  }
}
```
**Use Case:**
- **Primary recommendation for Phase 0 PoC** ⭐
- Medium-sized outdoor scenes (500m × 500m)
- Good fidelity for robotics simulation
- Balanced performance vs. visual quality
- Training data generation

**Performance:** 30–45 FPS on RTX 3070, RTX 3080  
**VRAM:** 6–8 GB  
**Description:** Natural-looking terrain with clear features (rocks, vegetation, water courses)

---

### **Level 6: Enhanced Terrain Detail** 🟠 (High-End GPUs)
```json
{
  "terrain": {
    "detail_level": 6,
    "mesh_density": 8192,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 6,
    "building_complexity": 6
  }
}
```
**Use Case:**
- Larger scenes (1km × 1km)
- High-fidelity terrain features
- Detailed vegetation distribution
- Research-grade robotics validation

**Performance:** 20–35 FPS on RTX 3080  
**VRAM:** 8–10 GB  
**Description:** Detailed terrain with micro-features (small rocks, bush clusters, eroded paths)

---

### **Level 7: High Terrain Detail** 🟠 (RTX 3080+)
```json
{
  "terrain": {
    "detail_level": 7,
    "mesh_density": 8192,
    "lod_enable": true,
    "erosion_simulation": false,
    "vegetation_density": 7,
    "building_complexity": 7
  }
}
```
**Use Case:**
- Large complex scenes (2km × 2km urban)
- Fine surface features (ruts, cracks, erosion channels)
- Rich vegetation with species variation
- Cinematic simulation sequences

**Performance:** 15–25 FPS on RTX 3080, RTX 4070  
**VRAM:** 10–12 GB  
**Description:** Highly detailed natural/urban terrain with distinct feature character

---

### **Level 8: Ultra Terrain Detail** 🔴 (RTX 4090)
```json
{
  "terrain": {
    "detail_level": 8,
    "mesh_density": 16384,
    "lod_enable": true,
    "erosion_simulation": true,
    "microvertex_displacement": true,
    "vegetation_density": 8,
    "vegetation_detail_level": 8,
    "building_complexity": 8
  }
}
```
**Use Case:**
- High-fidelity research simulations
- Photo-realistic environments
- Erosion simulation (water flow, wind effects)
- Micro-displacement mapping (fine surface detail)
- Advanced robotics validation

**Performance:** 10–20 FPS on RTX 4090  
**VRAM:** 15–18 GB  
**Description:** Near-photographic terrain detail with realistic weathering and erosion patterns

---

### **Level 9: Extreme Terrain Detail** 🔴 (RTX 4090 High-End)
```json
{
  "terrain": {
    "detail_level": 9,
    "mesh_density": 16384,
    "lod_enable": true,
    "erosion_simulation": true,
    "microvertex_displacement": true,
    "vegetation_density": 9,
    "vegetation_detail_level": 9,
    "building_complexity": 9
  }
}
```
**Use Case:**
- Offline rendering (baked sequences)
- Feature film VFX
- Ultra-high-fidelity research datasets
- Geological accuracy for earth simulation

**Performance:** 5–15 FPS on RTX 4090 (real-time)  
**VRAM:** 20–22 GB  
**Description:** Extreme geometric complexity with full erosion simulation and micro-displacements

---

### **Level 10: Maximum Detail** 🔴 (RTX 4090 + Offline)
```json
{
  "terrain": {
    "detail_level": 10,
    "mesh_density": 32768,
    "lod_enable": true,
    "erosion_simulation": true,
    "microvertex_displacement": true,
    "vegetation_density": 10,
    "vegetation_detail_level": 10,
    "building_complexity": 10
  }
}
```
**Use Case:**
- Offline rendering only (not real-time)
- Maximum fidelity datasets
- Photogrammetric accuracy
- Scientific visualization

**Performance:** <5 FPS (real-time), suitable for offline baking  
**VRAM:** 22–24 GB  
**Description:** Maximum possible geometric detail with full erosion simulation, weathering, and displacement mapping

---

## Quick Selection Guide

**Choose your terrain detail level based on:**

| Criterion | Choose Level |
|-----------|---|
| Running on Jetson Nano / Mobile GPU | 0–1 |
| Running on GTX 1080 / RTX 2060 | 2–3 |
| Running on RTX 3060 / 3070 | 4–5 ⭐ |
| Running on RTX 3080 / 3090 | 6–7 |
| Running on RTX 4090 (real-time) | 7–8 |
| Running on RTX 4090 (offline baking) | 9–10 |
| **Need robotics accuracy** | 5–6 ⭐ |
| **Need cinematic quality** | 7–8 |
| **Need photo-realistic** | 9–10 |
| **Need fast iteration** | 2–3 |

---

## Terrain Mesh Density Scaling

| Mesh Density | Scene Size | Vertex Count | Use Case |
|---|---|---|---|
| 512 | Any (flat) | ~250K | Mobile, embedded |
| 1024 | Small (100m) | ~1M | Embedded systems |
| 2048 | Small (500m) | ~4M | Quick testing |
| 4096 | Medium (1km) | ~16M | **Phase 0 default** ⭐ |
| 8192 | Large (2km) | ~67M | High-end GPUs |
| 16384 | Very large (4km) | ~268M | RTX 4090 only |
| 32768 | Ultra large (10km) | ~1B | Offline rendering |

---

## Vegetation Density Configuration

### **Vegetation Density Levels (0–10)**

| Level | Density | Placement | Use Case |
|-------|---------|-----------|----------|
| 0 | None | No vegetation | Paved areas, deserts |
| 1 | Sparse | Occasional trees/shrubs | Arid regions |
| 2 | Light | Scattered vegetation | Open fields |
| 3 | Moderate | Regular spacing | Meadows, grasslands |
| 4 | Dense | Close spacing | Forests edge |
| 5 | **Default** | Natural distribution | Most environments ⭐ |
| 6 | Very dense | Thick coverage | Dense forests |
| 7 | Thick | Heavy forest | Jungle/rainforest |
| 8 | Very thick | Impenetrable | Deep forest/canyon |
| 9 | Extreme | Wall-like coverage | Magical/fictional |
| 10 | Maximum | Procedural explosion | Ultra-dense (performance risk) |

### **Vegetation Detail Level (0–10)**

Independent of density; controls tree/plant complexity:

| Level | Tree Detail | Leaf Count | Branch Complexity |
|-------|---|---|---|
| 0 | Billboard | 0 | None (plane mesh) |
| 1 | Simple LOD0 | ~100 | 4 main branches |
| 2 | Basic LOD1 | ~200 | 8 branches |
| 3 | Moderate LOD2 | ~500 | 16 branches |
| 4 | Standard LOD3 | ~1000 | 32 branches |
| 5 | **Default** | ~2000 | Full procedural tree ⭐ |
| 6 | Detailed | ~4000 | Fine branch detail |
| 7 | High Detail | ~8000 | Individual leaf clusters |
| 8 | Ultra Detail | ~16000 | Per-leaf geometry |
| 9 | Extreme | ~32000 | Wind-deformed leaves |
| 10 | Maximum | ~64000+ | Full photogrammetry |

---

## Building Complexity Configuration

### **Building Complexity Levels (0–10)**

| Level | Architecture | Detail | Use Case |
|-------|---|---|---|
| 0 | Box | No detail | Placeholder geometry |
| 1 | Simple box | Flat walls | Low-end mobile |
| 2 | Simple with holes | Window/door cutouts | Basic scenes |
| 3 | Modular | Basic structure | Standard urban |
| 4 | Standard | Windows, doors, roof | Typical city ⭐ (Phase 0) |
| 5 | Detailed | Rooftop structures (HVAC) | **Default** ⭐ |
| 6 | Complex | Interior visibility, balconies | High-end urban |
| 7 | High Detail | Architectural style, weathering | Cinematic |
| 8 | Ultra Detail | Individual bricks/tiles visible | Photo-realistic |
| 9 | Extreme | Interior room geometry | Full building sim |
| 10 | Maximum | Full photogrammetry | Real building scan |

---

## API Endpoints for Terrain Configuration

### **1. Generate World with Terrain Detail**

```bash
POST /api/v1/generate-world
Content-Type: application/json

{
  "prompt": "Tokyo park with mountains",
  "terrain": {
    "detail_level": 5,
    "vegetation_density": 6,
    "vegetation_detail_level": 5,
    "building_complexity": 5
  },
  "rendering_quality": {
    "profile": "medium"
  }
}

Response:
{
  "world_id": "world-12345",
  "terrain_config": {
    "detail_level": 5,
    "estimated_vram_gb": 7,
    "estimated_fps": 35
  }
}
```

### **2. Update Terrain Detail (Mid-Simulation)**

```bash
POST /api/v1/worlds/{world_id}/update-terrain
Content-Type: application/json

{
  "detail_level": 7,
  "vegetation_density": 8,
  "erosion_simulation": true
}

Response:
{
  "status": "terrain_updated",
  "previous_detail_level": 5,
  "new_detail_level": 7,
  "scene_reload_required": true,
  "estimated_reload_time_seconds": 15
}
```

### **3. Get Terrain Configuration**

```bash
GET /api/v1/worlds/{world_id}/terrain-config

Response:
{
  "detail_level": 5,
  "mesh_density": 4096,
  "lod_enabled": true,
  "erosion_simulation": false,
  "microvertex_displacement": false,
  "vegetation_density": 5,
  "vegetation_detail_level": 5,
  "building_complexity": 5,
  "estimated_vram_gb": 7,
  "estimated_fps": 35
}
```

### **4. Get Terrain Detail Recommendations**

```bash
GET /api/v1/terrain-recommendations?gpu_model=RTX_4090&use_case=robotics

Response:
{
  "gpu_model": "RTX 4090",
  "recommended_detail_level": 8,
  "recommended_vegetation_density": 8,
  "recommended_building_complexity": 7,
  "rationale": "RTX 4090 can handle high terrain detail for research-grade robotics simulation"
}
```

---

## Terrain Detail vs. Rendering Quality

**These are INDEPENDENT:**

- **Terrain Detail:** Geometric complexity (mesh density, vegetation, buildings)
- **Rendering Quality:** Visual fidelity (resolution, ray-tracing, anti-aliasing)

### **Example 1: Low Rendering, High Terrain**
```json
{
  "rendering_quality": { "profile": "low", "resolution": "640x480", "fps": 15 },
  "terrain": { "detail_level": 7, "vegetation_density": 8 }
}
```
**Use Case:** Embedded robot with high-precision terrain navigation  
**Benefit:** Cheap pixels, expensive geometry (sensors prefer geometry)

### **Example 2: High Rendering, Low Terrain**
```json
{
  "rendering_quality": { "profile": "ultra", "resolution": "2560x1440", "fps": 60 },
  "terrain": { "detail_level": 2, "vegetation_density": 2 }
}
```
**Use Case:** VFX test on flat outdoor surface  
**Benefit:** Beautiful pixels, minimal geometry

### **Example 3: Balanced (Recommended)**
```json
{
  "rendering_quality": { "profile": "medium", "resolution": "1280x720", "fps": 30 },
  "terrain": { "detail_level": 5, "vegetation_density": 5 }
}
```
**Use Case:** Phase 0 robotics PoC  
**Benefit:** Good balance of both

---

## Performance Scaling Chart

```
Terrain Detail vs. FPS (RTX 3080)

FPS
 60 ├─────────────┐
    │           ╱  Rendering: Low
 50 │          ╱   (640x480)
    │       ╱
 40 │     ╱
    │   ╱
 30 │ ╱────────────┐
    │            ╱  Rendering: Medium
 20 │           ╱   (1280x720)
    │         ╱
 10 │       ╱──────┐
    │      ╱        Rendering: High
  0 └────╱─────────────────────────────
    0  2  4  6  8  10
       Terrain Detail Level
```

---

## Phase 0 Sprint: Terrain Configuration Tasks

### **Week 1: Schema & API**
- [ ] Update `world_spec_schema.json` with detailed terrain configuration (DONE ✅)
- [ ] Add terrain detail to FastAPI endpoints
- [ ] Implement GPU-aware terrain recommendations

### **Week 2: UE5 Blueprint**
- [ ] Create `BP_TerrainManager`
  - [ ] Enum: `ETerrainDetailLevel` (0–10)
  - [ ] Functions: `SetTerrainDetail()`, `GetTerrainInfo()`
  - [ ] Terrain mesh resolution scaling
  - [ ] Vegetation spawner with density control
  - [ ] LOD manager (stream detail based on camera distance)

- [ ] Implement erosion simulation (for levels 8+)
  - [ ] Water flow visualization
  - [ ] Erosion channels
  - [ ] Weathering effects

### **Week 3: Testing & Validation**
- [ ] Test all 11 detail levels (0–10)
- [ ] Measure FPS, VRAM, latency per level
- [ ] Validate terrain accuracy for robotics (Level 5)
- [ ] Create performance chart
- [ ] Document recommendations

---

## Default Recommendation for Phase 0

✅ **Terrain Detail Level 5** (default)  
✅ **Vegetation Density 5** (default)  
✅ **Vegetation Detail Level 5** (default)  
✅ **Building Complexity 5** (default)  
✅ **Rendering Quality Profile: Medium** (720p, 30 FPS)

This combination provides:
- Good terrain fidelity for robotics
- Reasonable performance (30–45 FPS on RTX 3070+)
- Balanced visual quality
- Scalable up/down for different GPUs

---

## Terrain Configuration Examples

### **Fast Iteration (Early Development)**
```json
{
  "terrain": {
    "detail_level": 2,
    "vegetation_density": 1,
    "building_complexity": 2
  }
}
```
→ Renders instantly, minimal quality, good for rapid testing

### **Robotics Validation (Phase 0 PoC)**
```json
{
  "terrain": {
    "detail_level": 5,
    "vegetation_density": 5,
    "vegetation_detail_level": 5,
    "building_complexity": 5
  }
}
```
→ Good fidelity, good performance, recommended baseline ⭐

### **High-Fidelity Research**
```json
{
  "terrain": {
    "detail_level": 7,
    "vegetation_density": 7,
    "vegetation_detail_level": 7,
    "building_complexity": 7
  }
}
```
→ Excellent visual quality, higher performance cost, RTX 3080+

### **Cinematic Rendering (Offline)**
```json
{
  "terrain": {
    "detail_level": 9,
    "vegetation_density": 9,
    "vegetation_detail_level": 9,
    "building_complexity": 9,
    "erosion_simulation": true,
    "microvertex_displacement": true
  }
}
```
→ Maximum quality, offline baking only, RTX 4090 required

