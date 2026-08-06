# PyRoboSimulator: Configurable Rendering Profiles & Output Scaling

**Purpose:** Enable flexible video quality settings from lightweight 720p streams to 4K cinematic renders, with automatic hardware detection and performance optimization.

---

## Rendering Profiles

### **Quick Reference**

| Profile | Resolution | FPS | Ray Tracing | Use Case | GPU Target | Approx Latency |
|---------|-----------|-----|-------------|----------|-----------|---|
| **Low** | 640×480 | 15 | Off | Embedded/edge robots, real-time monitoring | Mobile GPU, Jetson | <50ms |
| **Medium** ⭐ | **1280×720** | **30** | Medium | **Default sensor output, robotics sim** | **RTX 3060** | **<100ms** |
| **High** | 1920×1080 | 60 | High | HD video, cinematic output | RTX 3080 | <150ms |
| **Ultra** | 2560×1440 | 60 | Ultra | 2K cinematic, synthetic dataset generation | RTX 4090 | <200ms |
| **Cinematic** | 3840×2160 | 30 | Ultra | 4K rendering, film-grade output | RTX 4090 + | <300ms |
| **Custom** | Any | Any | Configurable | User-defined balance | Varies | Varies |

---

## Profile Specifications

### 🟢 **Low Profile**
```json
{
  "profile": "low",
  "resolution_width": 640,
  "resolution_height": 480,
  "fps": 15,
  "ray_tracing_enabled": false,
  "ray_tracing_quality": "off",
  "global_illumination_method": "baked",
  "shadow_quality": "low",
  "anti_aliasing": "fxaa",
  "temporal_super_resolution": false,
  "motion_blur_enabled": false,
  "depth_of_field_enabled": false,
  "bloom_enabled": false
}
```
**When to Use:**
- Real-time robot telemetry feeds (low bandwidth)
- Embedded systems (Jetson Nano, mobile devices)
- Rapid iteration during development
- Multiple concurrent simulations
- Data logging (store lightweight video)

**Performance:** ~60–120 FPS on mid-range GPUs (GTX 1080, RTX 3060)

---

### 🟡 **Medium Profile** (Default)
```json
{
  "profile": "medium",
  "resolution_width": 1280,
  "resolution_height": 720,
  "fps": 30,
  "ray_tracing_enabled": true,
  "ray_tracing_quality": "medium",
  "global_illumination_method": "lumen",
  "shadow_quality": "medium",
  "anti_aliasing": "taa",
  "temporal_super_resolution": true,
  "motion_blur_enabled": false,
  "depth_of_field_enabled": false,
  "bloom_enabled": true
}
```
**When to Use:**
- Default for all robotics simulations ⭐
- Sensor output capture (RGB, Depth, Lidar)
- Real-time monitoring dashboards
- Training data generation
- Interactive testing

**Performance:** ~30–60 FPS on consumer GPUs (RTX 3060, RTX 3070)  
**Recommended for Phase 0 PoC**

---

### 🟠 **High Profile**
```json
{
  "profile": "high",
  "resolution_width": 1920,
  "resolution_height": 1080,
  "fps": 60,
  "ray_tracing_enabled": true,
  "ray_tracing_quality": "high",
  "global_illumination_method": "lumen",
  "shadow_quality": "high",
  "anti_aliasing": "taa",
  "temporal_super_resolution": true,
  "motion_blur_enabled": true,
  "depth_of_field_enabled": false,
  "bloom_enabled": true
}
```
**When to Use:**
- HD video output (YouTube, reports)
- Cinematic sequences
- High-fidelity sensor simulation (research)
- Detailed performance analysis

**Performance:** ~30–60 FPS on high-end GPUs (RTX 3080, RTX 4070)

---

### 🔴 **Ultra Profile**
```json
{
  "profile": "ultra",
  "resolution_width": 2560,
  "resolution_height": 1440,
  "fps": 60,
  "ray_tracing_enabled": true,
  "ray_tracing_quality": "ultra",
  "global_illumination_method": "lumen",
  "shadow_quality": "ultra",
  "anti_aliasing": "taa",
  "temporal_super_resolution": true,
  "motion_blur_enabled": true,
  "depth_of_field_enabled": true,
  "bloom_enabled": true
}
```
**When to Use:**
- 2K cinematic renders
- Film production assets
- High-fidelity synthetic datasets
- Graphics benchmarking

**Performance:** ~30–60 FPS on very high-end GPUs (RTX 4090)

---

### 🎬 **Cinematic Profile**
```json
{
  "profile": "cinematic",
  "resolution_width": 3840,
  "resolution_height": 2160,
  "fps": 30,
  "ray_tracing_enabled": true,
  "ray_tracing_quality": "ultra",
  "global_illumination_method": "lumen",
  "shadow_quality": "ultra",
  "anti_aliasing": "taa",
  "temporal_super_resolution": true,
  "motion_blur_enabled": true,
  "depth_of_field_enabled": true,
  "bloom_enabled": true
}
```
**When to Use:**
- 4K feature film output
- Publication-grade imagery
- VFX showcase materials
- Premium synthetic data

**Performance:** ~20–30 FPS on RTX 4090  
**Note:** Output may be baked/offline; not real-time

---

## Custom Profile

For users who need specific combinations:

```json
{
  "profile": "custom",
  "resolution_width": 1600,
  "resolution_height": 900,
  "fps": 45,
  "ray_tracing_enabled": true,
  "ray_tracing_quality": "medium",
  "global_illumination_method": "hybrid",
  "shadow_quality": "high",
  "anti_aliasing": "dlss",
  "temporal_super_resolution": true,
  "motion_blur_enabled": false,
  "depth_of_field_enabled": false,
  "bloom_enabled": true
}
```

**Min/Max Bounds:**
- Resolution: 320×240 → 7680×4320
- FPS: 15 → 120
- Ray Tracing: off → ultra

---

## API Endpoints for Quality Control

### 1. **Generate World with Custom Quality**

```bash
POST /api/v1/generate-world-with-quality
Content-Type: application/json

{
  "prompt": "Tokyo at sunset after rain",
  "rendering_quality": {
    "profile": "high",
    "resolution_width": 1920,
    "resolution_height": 1080,
    "fps": 60
  }
}

Response:
{
  "world_id": "world-12345",
  "world_spec": { ... },
  "rendering_config": { ... }
}
```

### 2. **Update Output Quality (Mid-Simulation)**

```bash
POST /api/v1/worlds/{world_id}/update-quality
Content-Type: application/json

{
  "profile": "ultra",
  "resolution_width": 2560,
  "resolution_height": 1440,
  "fps": 30
}

Response:
{
  "status": "quality_updated",
  "previous_profile": "medium",
  "new_profile": "ultra",
  "restart_required": true  // Need to reload scene
}
```

### 3. **Get Current Quality Settings**

```bash
GET /api/v1/worlds/{world_id}/quality

Response:
{
  "profile": "medium",
  "resolution": "1280x720",
  "fps": 30,
  "estimated_bandwidth_mbps": 25,
  "estimated_gpu_vram_gb": 6,
  "estimated_fps_achievable": 35
}
```

### 4. **List Available Profiles (Hardware-Aware)**

```bash
GET /api/v1/rendering-profiles

Response:
{
  "gpu_model": "NVIDIA RTX 4090",
  "gpu_vram_gb": 24,
  "cpu_cores": 32,
  "profiles": {
    "low": { "estimated_fps": 240 },
    "medium": { "estimated_fps": 120 },
    "high": { "estimated_fps": 60 },
    "ultra": { "estimated_fps": 45 },
    "cinematic": { "estimated_fps": 25 }
  },
  "recommended_profile": "ultra"
}
```

### 5. **Stream Sensor Output with Quality Parameter**

```bash
GET /api/v1/sensors/rgb?quality=high&format=mp4

# OR specify custom params
GET /api/v1/sensors/rgb?resolution=1920x1080&fps=60&codec=h265&bitrate=50mbps

Response:
Video stream (H.265/H.264 encoded)
Headers:
  Content-Type: video/mp4
  X-Resolution: 1920x1080
  X-FPS: 60
  X-Bitrate: 50 Mbps
  X-GPU-Time-Ms: 16.7
```

### 6. **Batch Export with Quality Profiles**

```bash
POST /api/v1/export/batch
Content-Type: application/json

{
  "world_id": "world-12345",
  "export_formats": [
    {
      "profile": "medium",
      "output": "sensor_feed_720p.mp4",
      "sensors": ["rgb", "depth", "lidar"],
      "duration_seconds": 60
    },
    {
      "profile": "cinematic",
      "output": "showcase_4k.mp4",
      "sensors": ["rgb"],
      "duration_seconds": 30,
      "post_processing": ["color_grading", "lens_flare"]
    }
  ]
}

Response:
{
  "batch_id": "export-567",
  "status": "queued",
  "estimated_time_minutes": 45,
  "files": [ ... ]
}
```

---

## Hardware Detection & Auto-Optimization

### **UE5 Backend (C++)**

```cpp
// Detect GPU capabilities
FDeviceProfileManager::Get().GetActiveProfile()->DeviceType

// Auto-select profile based on hardware
void AutoSelectRenderingProfile(const FGPUInfo& gpu_info) {
  if (gpu_info.vram_gb >= 24) {
    selected_profile = RenderingProfile::Ultra;
  } else if (gpu_info.vram_gb >= 12) {
    selected_profile = RenderingProfile::High;
  } else if (gpu_info.vram_gb >= 6) {
    selected_profile = RenderingProfile::Medium;  // Default
  } else {
    selected_profile = RenderingProfile::Low;
  }
}

// Apply profile settings
void ApplyRenderingProfile(const RenderingProfile& profile) {
  IConsoleVariable* CVar_ScreenPercentage = 
    IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
  CVar_ScreenPercentage->Set(profile.temporal_super_resolution ? 75 : 100);
  
  IConsoleVariable* CVar_RayTracing = 
    IConsoleManager::Get().FindConsoleVariable(TEXT("r.RayTracing.Enabled"));
  CVar_RayTracing->Set(profile.ray_tracing_enabled);
  
  // ... apply other settings
}
```

### **Python Backend (FastAPI)**

```python
from backend.gpu_detector import GPUDetector
from backend.rendering_profiles import RenderingProfile

detector = GPUDetector()
gpu_info = detector.detect()

# Auto-select profile
if gpu_info.vram_gb >= 24:
    profile = RenderingProfile.ULTRA
elif gpu_info.vram_gb >= 12:
    profile = RenderingProfile.HIGH
else:
    profile = RenderingProfile.MEDIUM  # Safe default

# Get performance estimates
estimates = profile.estimate_performance(gpu_info)
print(f"Estimated FPS: {estimates.fps}")
print(f"Estimated latency: {estimates.latency_ms}ms")
print(f"Estimated bandwidth: {estimates.bandwidth_mbps} Mbps")
```

---

## Performance Benchmarking

### **Expected Performance (Parking Lot Scene)**

| Profile | GPU | Resolution | FPS | GPU Util | VRAM | Latency |
|---------|-----|-----------|-----|----------|------|---------|
| Low | GTX 1080 | 640×480 | 120 | 40% | 2GB | 20ms |
| Medium | RTX 3060 | 1280×720 | 45 | 70% | 6GB | 85ms |
| High | RTX 3080 | 1920×1080 | 55 | 85% | 10GB | 120ms |
| Ultra | RTX 4090 | 2560×1440 | 45 | 90% | 18GB | 150ms |
| Cinematic | RTX 4090 | 3840×2160 | 25 | 95% | 22GB | 250ms |

*Benchmarks on i9-13900K, 64GB RAM. Real-world results vary by scene complexity.*

---

## Video Codec & Streaming Options

### **Output Formats by Profile**

| Profile | Recommended Codec | Bitrate | Container | Use Case |
|---------|------------------|---------|-----------|----------|
| Low | H.264 (baseline) | 2–5 Mbps | MP4/WebM | Edge streaming, mobile |
| Medium | H.264 or H.265 | 10–25 Mbps | MP4 | Default, web playback |
| High | H.265 (Main 10) | 25–50 Mbps | MP4/MKV | HD archive, quality |
| Ultra | H.265 (Main 10) | 50–100 Mbps | MKV | 2K production |
| Cinematic | ProRes 422 HQ or DNxHR | 200–500 Mbps | MOV/MKV | 4K production, VFX |

### **Streaming Configuration**

```json
{
  "streaming": {
    "protocol": "rtmp" | "rtsp" | "http-hls" | "dash",
    "codec": "h264" | "h265" | "vp9",
    "bitrate_adaptive": true,  // Dynamically adjust for network
    "chunk_duration_seconds": 2,
    "buffer_size_seconds": 5,
    "target_latency_seconds": 2
  }
}
```

---

## Quality Scaling Workflow

### **Example 1: Start Low, Scale Up**

```python
# Day 1: Fast testing with low quality
world_spec = generate_world_spec(
    "Tokyo at sunset",
    rendering_quality={"profile": "low"}
)
# Result: 640×480 @ 15 FPS, instant feedback

# Day 5: Scale to medium for presentation
update_world_quality(world_id="world-12345", profile="medium")
# Reloads scene with 1280×720 @ 30 FPS

# Day 10: Final 4K render for publication
export_world(
    world_id="world-12345",
    profile="cinematic",
    output="showcase_4k.mp4"
)
# Outputs 3840×2160 @ 30 FPS (offline bake)
```

### **Example 2: Multi-Quality Export**

```python
# Export same world at multiple qualities
profiles_to_export = [
    ("low", "robot_feed_480p.mp4"),
    ("medium", "standard_720p.mp4"),
    ("high", "hd_1080p.mp4"),
    ("ultra", "2k_1440p.mp4"),
]

for profile, output_file in profiles_to_export:
    export_world(
        world_id="world-12345",
        profile=profile,
        output_file=output_file,
        duration_seconds=60
    )
# Generates all 4 versions in parallel (if multi-GPU available)
```

---

## Phase 0 Implementation Notes

### **Week 1: Core Setup**
- [ ] Define `RenderingProfile` enum (Low, Medium, High, Ultra, Cinematic)
- [ ] Implement profile validation in world spec schema
- [ ] Add GPU detection utility (`GPUDetector` class)

### **Week 2: UE5 Integration**
- [ ] Create UE5 console variables for each quality setting
- [ ] Blueprint: `BP_QualityManager` (applies profile settings)
- [ ] Test all profiles on target GPUs
- [ ] Measure latency + FPS for each profile

### **Week 3: API Endpoints**
- [ ] FastAPI endpoint: `POST /generate-world-with-quality`
- [ ] Endpoint: `POST /update-quality`
- [ ] Endpoint: `GET /rendering-profiles` (hardware-aware)
- [ ] Sensor endpoints support `?quality=` parameter

### **Success Criteria**
- [ ] Default 720p/30FPS output works on RTX 3060+
- [ ] Can scale to 4K on RTX 4090
- [ ] Can downscale to 480p on mobile GPU (Jetson)
- [ ] Quality change takes <5 seconds
- [ ] API latency <100ms (medium profile)

---

## Configuration Examples

### **Robotics Simulation (Default)**
```json
{
  "profile": "medium",
  "fps": 30,
  "resolution_width": 1280,
  "resolution_height": 720
}
```

### **Edge Robot Telemetry**
```json
{
  "profile": "low",
  "fps": 15,
  "resolution_width": 640,
  "resolution_height": 480
}
```

### **4K Cinematic Showcase**
```json
{
  "profile": "cinematic",
  "fps": 30,
  "resolution_width": 3840,
  "resolution_height": 2160
}
```

### **Custom Balance (Performance + Quality)**
```json
{
  "profile": "custom",
  "resolution_width": 1600,
  "resolution_height": 900,
  "fps": 45,
  "ray_tracing_quality": "medium",
  "anti_aliasing": "dlss"  // NVIDIA DLSS for performance
}
```

---

## GPU Memory Budget by Profile

| Profile | Estimated VRAM | Typical GPU | Notes |
|---------|---|---|---|
| Low | 2–3 GB | GTX 1050, Jetson Nano | Mobile/embedded |
| Medium | 5–7 GB | RTX 3060, RTX 3070 | **Default (recommended)** |
| High | 8–12 GB | RTX 3080, RTX 4070 | HD streaming |
| Ultra | 12–18 GB | RTX 4080, RTX 4090 | 2K production |
| Cinematic | 20–24 GB | RTX 4090 | 4K offline baking |

---

## Migration Guide (Scaling Up)

**Scenario:** Started with Medium profile, now need High quality.

1. **In-place upgrade** (if VRAM allows):
   ```bash
   POST /api/v1/worlds/{world_id}/update-quality
   { "profile": "high" }
   # Scene reloads with new settings; ~3–5 second downtime
   ```

2. **Parallel render** (keep old + start new):
   ```bash
   # Keep Medium running on GPU 0
   # Start High rendering on GPU 1
   POST /api/v1/worlds/{world_id}/duplicate?target_profile=high
   # Two independent instances
   ```

3. **Export to file** (highest quality, offline):
   ```bash
   POST /api/v1/export/batch
   {
     "world_id": "world-12345",
     "profile": "cinematic",
     "output": "final_render_4k.mp4",
     "duration_seconds": 120
   }
   # Bake 4K render offline; takes 5–10 minutes
   ```

---

**Default Recommendation:** Start with **Medium (720p, 30 FPS)** for Phase 0.  
**Scale up to High/Ultra** once robotics validation is complete.  
**Use Cinematic** for publication-grade assets only.

