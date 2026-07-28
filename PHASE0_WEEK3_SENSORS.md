# PyRoboSimulator Phase 0 Week 3: Sensor Output & Validation

## Overview

**Goal:** Implement real sensor capture from UE5, create end-to-end pipeline, and validate physics/rendering accuracy.

**Timeline:** 1 week (3 days sensor implementation + 2 days validation + 2 days buffer)  
**Team:** 1 UE5 engineer + 1 Python engineer (collaborative)  
**Success Metric:** All 7 validation tests passing with > 90% accuracy  

---

## Sensor Implementation Details

### 1. RGB Camera  [DESIGN]

#### Hardware Specification
- **Resolution:** 1920 × 1080 (16:9)
- **FPS:** 30 frames per second
- **Output Format:** PNG (lossless)
- **Color Space:** sRGB (tone-mapped)
- **Bit Depth:** 8-bit per channel (RGB888)

#### UE5 Implementation

**Component Type:** Scene Capture 2D  
**Capture Method:** Post-process render target

```cpp
// UE5 C++
class ARGBCameraActor : public AActor {
public:
    USceneCaptureCom Component* CaptureComponent;
    UTextureRenderTarget2D* RenderTarget;
    
    ARGBCameraActor();
    
    virtual void BeginPlay() override;
    void SetupCapture();
    void CaptureFrame(int32 FrameNumber);
    void SaveToPNG(FString FilePath);
};
```

**Settings:**
```cpp
CaptureComponent->CaptureSource = SCS_SceneColorHDR;
CaptureComponent->bCaptureEveryFrame = false;
CaptureComponent->bCaptureOnMovement = false;
CaptureComponent->MaxDrawDistance = 10000.0f;
RenderTarget->Format = RTF_RGBA16f;  // Capture high-precision, tonemap to 8-bit
```

#### Data Format

**File:** `rgb/frame_XXXX.png`  
**Size:** 1920 × 1080 × 3 bytes = 6.2 MB per frame  
**30 FPS:** ~186 MB/second → ~11 GB/minute

**Python Post-Processing:**
```python
import imageio
import numpy as np

# Load PNG
rgb_array = imageio.imread("frame_0000.png")  # Shape: (1080, 1920, 3), dtype: uint8

# Validate
assert rgb_array.shape == (1080, 1920, 3)
assert rgb_array.dtype == np.uint8
```

#### Validation Tests

**Test 1: Clear Day (No Rain)**
```
Input:  world_spec with rain_intensity=0.0, cloud_coverage=0.1
        hour=12 (noon), season="summer"
Expected: Bright image, high contrast, blue sky, dark shadows
Verify: Mean brightness > 100, std > 50
```

**Test 2: Sunset Lighting**
```
Input:  hour=18, sun_angle_elevation=-10°
Expected: Warm orange cast, long shadows, low sun angle
Verify: Hue histogram shifted toward orange, R > G > B in average
```

**Test 3: Wet Asphalt Reflections**
```
Input:  rain_intensity=0.8, time=noon
Expected: Visible specular highlights on parking surface
Verify: High-frequency texture details visible in reflections
```

---

### 2. Depth Camera  [DESIGN]

#### Hardware Specification
- **Resolution:** 1920 × 1080 (same as RGB)
- **Range:** 0-300m (practical range: 0-100m for parking lot)
- **Output Format:** 32-bit float (m)
- **Alignment:** Pixel-perfect match with RGB
- **FPS:** 30 (synchronized with RGB)

#### UE5 Implementation

**Component Type:** Scene Capture 2D (Depth)

```cpp
class ADepthCameraActor : public AActor {
public:
    USceneCaptureCom Component* DepthCapture;
    UTextureRenderTarget2D* DepthRenderTarget;
    
    virtual void BeginPlay() override;
    void CaptureDepthFrame(int32 FrameNumber);
    void SaveToNPY(FString FilePath);
    
private:
    void ConvertRawDepthToMeters(TArray<uint8>& RawData, 
                                  TArray<float>& DepthMeters);
};
```

**Settings:**
```cpp
DepthCapture->CaptureSource = SCS_SceneDepth;
DepthCapture->TextureTarget = DepthRenderTarget;
DepthRenderTarget->Format = RTF_R32f;  // Float32
```

**Depth Conversion:**
```cpp
// UE5: Convert raw depth to meters
float ConvertRawDepthToMeters(float RawDepth, float NearClip, float FarClip) {
    // RawDepth is 0-1 normalized, convert to world units
    float LinearDepth = 1.0f / (RawDepth * (1.0f/FarClip - 1.0f/NearClip) + 1.0f/NearClip);
    return LinearDepth;
}

// Camera: NearClip=0.1m, FarClip=300m
```

#### Data Format

**File:** `depth/frame_XXXX.npy`  
**Shape:** (1080, 1920)  
**Dtype:** float32  
**Values:** Depth in meters (0-300)  

**Python Example:**
```python
import numpy as np

# Load and verify
depth = np.load("frame_0000.npy")  # Shape: (1080, 1920), dtype: float32

# Validation
assert depth.shape == (1080, 1920)
assert depth.dtype == np.float32
assert np.all(depth >= 0) and np.all(depth <= 300)

# Visualize
depth_normalized = (depth / 100.0).clip(0, 1)  # 0-100m → 0-1
depth_uint8 = (depth_normalized * 255).astype(np.uint8)
# Can save as PNG for visualization
```

#### Alignment Guarantee

**RGB and Depth must be perfectly aligned:**
```python
# In Python, after capturing both:
assert rgb.shape[:2] == depth.shape
# Same pixel (x, y) corresponds to same world position
```

#### Validation Tests

**Test 1: Depth Range**
```
Input:  Parking lot scene (max distance ~100m)
Expected: All depth values 0-100m (no far clipping)
Verify: np.all(depth < 100) and np.all(depth > 0.5)
```

**Test 2: Depth Discontinuities**
```
Input:  Scene with buildings, vehicles
Expected: Sharp edges at object boundaries
Verify: High-frequency content at object edges (use edge detection)
```

**Test 3: Alignment with RGB**
```
Input:  Load RGB and Depth from same frame
Expected: Bright objects (high luminance) at close depth, dark sky at far depth
Verify: Correlation between RGB brightness and inverse depth
```

---

### 3. Lidar Scanner  [DESIGN]

#### Specification
- **Channels:** 16 (vertical lines)
- **Horizontal Resolution:** 32 rays per channel
- **Total Rays:** 512 per frame (16 × 32)
- **FOV:** 90° horizontal, 30° vertical
- **Range:** 0-100m
- **Max Range Accuracy:** ±0.1m (typical)
- **Frequency:** 10 Hz (100ms per frame)
- **Output Format:** PCD (Point Cloud Data)

#### Lidar Physics

**Ray Casting:**
```
For each of 512 rays:
  - Cast ray from camera origin
  - Test collision with scene geometry
  - If hit: record (X, Y, Z, intensity)
  - If miss (> 100m): drop ray
  - intensity = 255 - (distance_m / 100) * 255  // Far = dim
```

#### UE5 Implementation (C++)

```cpp
class ALidarComponent : public UActorComponent {
public:
    UPROPERTY(EditAnywhere) float MaxRange = 100.0f;
    UPROPERTY(EditAnywhere) int32 HorizontalRays = 32;
    UPROPERTY(EditAnywhere) int32 VerticalChannels = 16;
    
    virtual void BeginPlay() override;
    void CaptureFrame(int32 FrameNumber);
    
private:
    struct FLidarPoint {
        FVector Position;      // World coordinates
        uint8 Intensity;       // 0-255
    };
    
    TArray<FLidarPoint> CastRays();
    void SaveToPCD(const TArray<FLidarPoint>& Points, FString FilePath);
};

// Async ray casting (non-blocking)
void ALidarComponent::CaptureFrame(int32 FrameNumber) {
    // Queue rays for async execution
    // Return immediately (will save on completion)
}
```

**Ray Casting Logic:**
```cpp
TArray<FLidarPoint> ALidarComponent::CastRays() {
    TArray<FLidarPoint> Points;
    
    FVector CameraPos = GetComponentLocation();
    float VerticalFOV = 30.0f;  // degrees
    float HorizontalFOV = 90.0f;
    
    for (int32 Channel = 0; Channel < VerticalChannels; ++Channel) {
        // Vertical angle from -15° to +15° (30° span)
        float VertAngle = -15.0f + (Channel / (float)VerticalChannels) * VerticalFOV;
        
        for (int32 Ray = 0; Ray < HorizontalRays; ++Ray) {
            // Horizontal angle from -45° to +45° (90° span)
            float HorizAngle = -45.0f + (Ray / (float)HorizontalRays) * HorizontalFOV;
            
            // Convert to direction
            FVector Direction = FRotationMatrix(
                FRotator(VertAngle, HorizAngle, 0.0f)
            ).GetUnitAxis(EAxis::X);  // Forward axis
            
            // Cast ray
            FHitResult HitResult;
            FCollisionQueryParams QueryParams;
            QueryParams.AddIgnoredActor(GetOwner());
            
            bool bHit = GetWorld()->LineTraceSingleByChannel(
                HitResult,
                CameraPos,
                CameraPos + Direction * MaxRange,
                ECC_Visibility,
                QueryParams
            );
            
            if (bHit) {
                FLidarPoint Point;
                Point.Position = HitResult.ImpactPoint;
                Point.Intensity = 255 - (HitResult.Distance / MaxRange) * 255;
                Points.Add(Point);
            }
        }
    }
    
    return Points;
}
```

#### PCD Output Format

**File:** `lidar/frame_XXXX.pcd`  
**Format:** ASCII (for Phase 0), binary (Phase 1)  

```
# Example PCD file (ASCII)
VERSION .7
FIELDS x y z intensity
SIZE 4 4 4 1
TYPE f f f u
COUNT 512

0.5 1.2 3.4 240
1.1 0.9 3.2 235
...
```

**Python Reading:**
```python
import numpy as np

def read_pcd(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    # Parse header
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('DATA'):
            data_start = i + 1
            break
    
    # Parse points
    points = []
    for line in lines[data_start:]:
        parts = line.strip().split()
        points.append([float(p) for p in parts])
    
    return np.array(points)  # Shape: (N, 4), columns: [x, y, z, intensity]
```

#### Rain Scatter Simulation

**Physics:** Heavy rain causes 20-30% of rays to be occluded  
**Implementation:** Fake by random ray drop

```cpp
void ALidarComponent::ApplyRainOcclusion(TArray<FLidarPoint>& Points, float RainIntensity) {
    // RainIntensity: 0-1, where 1.0 = heavy rain
    float OcclusionRate = RainIntensity * 0.3f;  // Up to 30% occlusion
    
    for (int32 i = Points.Num() - 1; i >= 0; --i) {
        if (FMath::FRand() < OcclusionRate) {
            Points.RemoveAt(i);
        }
    }
}
```

#### Validation Tests

**Test 1: Point Density (No Rain)**
```
Input:  Clear day, rain_intensity=0.0
Expected: 512 points (all rays hit something)
Verify: num_points == 512
```

**Test 2: Rain Occlusion**
```
Input:  Heavy rain, rain_intensity=0.8
Expected: ~30% fewer points (512 * 0.7 ≈ 358 points)
Verify: 300 < num_points < 400
```

**Test 3: Range Accuracy**
```
Input:  Parking lot (known distances)
Expected: Points within ±0.5m of ground truth
Verify: np.allclose(measured_distances, ground_truth, atol=0.5)
```

---

### 4. Thermal Camera  [DESIGN]

#### Specification
- **Resolution:** 320 × 240 (typical thermal)
- **Range:** -20°C to +60°C (typical automotive)
- **Output:** Grayscale (32-bit float, °C)
- **Accuracy:** ±5°C typical
- **Material Emissivity:** Per-material lookup table
- **FPS:** 10 Hz (matching Lidar)

#### Emissivity Reference Table

| Material | Emissivity | Temp Range |
|----------|-----------|-----------|
| Asphalt | 0.95 | Heated by sun |
| Water | 0.93 | Same as ambient |
| Concrete | 0.90 | Slightly heated |
| Metal | 0.10-0.20 | Reflective, cold |
| Grass | 0.98 | Ambient temp |
| Leaves | 0.97 | Ambient temp |

**Thermal Calculation:**
```
Thermal_Value = BaseTemperature * Emissivity
```

#### UE5 Implementation

**Method 1: Custom Material-Based (Simpler)**
```cpp
class AThermalCamera : public AActor {
public:
    USceneCaptureComponent2D* ThermalCapture;
    UTextureRenderTarget2D* ThermalRenderTarget;
    
    UPROPERTY(EditAnywhere) float AmbientTemperature = 22.0f;  // °C
    UPROPERTY(EditAnywhere) TMap<FString, float> MaterialEmissivity;
    
    virtual void BeginPlay() override;
    void CaptureThermalFrame(int32 FrameNumber);
};
```

**Method 2: Post-Process Material (More Realistic)**
- Use screen-space material IDs to lookup emissivity
- Apply temperature gradient based on sun heating

#### Temperature Simulation

**Base Temperature Logic:**
```cpp
float CalculateTemperature(FString MaterialType, float AmbientTemp, float SunIntensity) {
    float BaseTemp = AmbientTemp;
    
    // Sun heating for dark materials
    if (MaterialType == "Asphalt" || MaterialType == "WetAsphalt") {
        BaseTemp += 10.0f * SunIntensity;  // Up to +10°C from sun
    } else if (MaterialType == "Concrete") {
        BaseTemp += 5.0f * SunIntensity;   // Up to +5°C
    } else if (MaterialType == "Metal") {
        BaseTemp += 15.0f * SunIntensity;  // Up to +15°C (reflects, heats up)
    }
    
    return BaseTemp;
}

// Thermal value = BaseTemp * Emissivity
float ThermalValue = CalculateTemperature(Material, Ambient, SunIntensity) 
                   * MaterialEmissivity[Material];
```

#### Data Format

**File:** `thermal/frame_XXXX.npy`  
**Shape:** (240, 320)  
**Dtype:** float32  
**Range:** -20 to 60 °C  

**Python Visualization:**
```python
import numpy as np
import matplotlib.pyplot as plt

# Load
thermal = np.load("frame_0000.npy")  # Shape: (240, 320), values: -20 to 60

# Normalize to grayscale
thermal_norm = (thermal - (-20)) / (60 - (-20))  # 0-1
thermal_uint8 = (thermal_norm * 255).astype(np.uint8)

# Visualize with thermal colormap
plt.imshow(thermal, cmap='hot')
plt.colorbar(label='Temperature (°C)')
plt.title('Thermal Image')
plt.show()
```

#### Validation Tests

**Test 1: Emissivity Ordering**
```
Input:  scene with asphalt, water, metal (all at same ambient temp)
Expected: asphalt_thermal > water_thermal > metal_thermal
Verify: mean(asphalt) > mean(water) > mean(metal)
```

**Test 2: Sun Heating**
```
Input:  compare hour=12 vs hour=6
Expected: Noon darker objects hotter by ~10°C
Verify: mean_temp_noon > mean_temp_morning by at least 5°C
```

**Test 3: Rain Cooling**
```
Input:  rain_intensity=0.0 vs rain_intensity=0.8
Expected: Wet surfaces cooler (water evaporation)
Verify: mean_temp_wet < mean_temp_dry by 2-5°C
```

---

## End-to-End Pipeline

### Data Flow

```
NLP Prompt
    ↓
Python: Claude generates WorldSpec
    ↓
Python: POST /api/v1/load-world with spec
    ↓
UE5: Receive spec via HTTP
    ↓
UE5: Load scene (objects, lighting, weather, materials)
    ↓
UE5: Configure cameras (RGB, Depth, Lidar, Thermal)
    ↓
UE5: For each frame (30 FPS RGB, 10 FPS others):
    - RGB: Scene capture → PNG
    - Depth: Scene capture → NPY
    - Lidar: Ray cast → PCD
    - Thermal: Material lookup → NPY
    ↓
UE5: Save files to /tmp/pyrobo_sensor_output/{world_id}/
    ↓
Python: GET /api/v1/sensors/{world_id}/{sensor_type}?frame=N
    ↓
Python: Return file path + metadata
    ↓
Python: Load and validate all sensors
```

### Demo Script (End-to-End)

```python
# Phase 0 Demo: Complete pipeline
import requests
import time
from pyrobosimulator.world_gen import WorldGenerator
from pathlib import Path

# 1. Generate world from NLP
generator = WorldGenerator()
spec = generator.generate(
    "A parking lot at sunset with 5 parked cars and light rain"
)

# 2. Load world in UE5
load_response = requests.post(
    "http://localhost:8000/api/v1/load-world",
    json={"spec": spec.model_dump()}
)
world_id = load_response.json()["world_id"]

# 3. Wait for UE5 to render
time.sleep(2)

# 4. Collect sensor outputs
sensors = ["rgb", "depth", "lidar", "thermal"]
outputs = {}

for sensor_type in sensors:
    response = requests.get(
        f"http://localhost:8000/api/v1/sensors/{world_id}/{sensor_type}?frame=0"
    )
    outputs[sensor_type] = response.json()

# 5. Validate (check files exist + dimensions)
print(f"✓ World generated: {world_id}")
print(f"✓ Sensors captured:")
for sensor_type, data in outputs.items():
    print(f"  - {sensor_type}: {data['data_path']}")
```

---

## Validation Test Suite

### Test Matrix (7 Tests)

| Test | Input | Expected | Validation |
|------|-------|----------|-----------|
| **RGB Quality** | 1080p, 30 FPS, clear day | Sharp, bright image | Visual + histogram |
| **Depth Range** | Max distance 100m | All values 0-100m | Range check |
| **Lidar Rain** | rain_intensity=0.8 | ~30% point loss | 300-400 points |
| **Thermal Emissivity** | Mixed materials | asphalt > water > metal | Mean values ordered |
| **Wet Asphalt** | rain_intensity=0.8 | Visible reflections | Texture analysis |
| **Sunset Lighting** | hour=18 | Warm orange cast | Color histogram |
| **API Latency** | Sensor query | < 100ms response | Timer |

### Validation Script (Python)

```python
# validation.py
import numpy as np
import requests
import time
from pathlib import Path

class ValidationSuite:
    def __init__(self, world_id):
        self.world_id = world_id
        self.base_url = "http://localhost:8000"
        self.results = {}
    
    def test_rgb_quality(self):
        """Test 1: RGB image quality (brightness, contrast)"""
        response = requests.get(
            f"{self.base_url}/api/v1/sensors/{self.world_id}/rgb?frame=0"
        )
        rgb_path = Path(response.json()["data_path"])
        
        rgb = imageio.imread(rgb_path)
        brightness = rgb.mean()
        contrast = rgb.std()
        
        self.results["rgb_quality"] = {
            "brightness": brightness,
            "contrast": contrast,
            "pass": brightness > 100 and contrast > 50
        }
    
    def test_depth_range(self):
        """Test 2: Depth values in expected range"""
        response = requests.get(
            f"{self.base_url}/api/v1/sensors/{self.world_id}/depth?frame=0"
        )
        depth_path = Path(response.json()["data_path"])
        
        depth = np.load(depth_path)
        valid_range = np.all(depth >= 0) and np.all(depth <= 300)
        
        self.results["depth_range"] = {
            "min": float(depth.min()),
            "max": float(depth.max()),
            "pass": valid_range
        }
    
    def test_lidar_rain_scatter(self):
        """Test 3: Lidar point density with rain"""
        # Load with rain_intensity=0.8
        baseline = self._get_lidar_points(rain_intensity=0.0)
        rainy = self._get_lidar_points(rain_intensity=0.8)
        
        loss_rate = 1.0 - (len(rainy) / len(baseline))
        
        self.results["lidar_rain"] = {
            "baseline_points": len(baseline),
            "rainy_points": len(rainy),
            "loss_rate": loss_rate,
            "pass": 0.2 < loss_rate < 0.4  # 20-40% loss
        }
    
    def test_thermal_emissivity(self):
        """Test 4: Thermal emissivity ordering"""
        # Create scene with asphalt, water, metal at same temp
        thermal = np.load(...)
        
        # Sample areas
        asphalt_mean = thermal[...region...].mean()
        water_mean = thermal[...region...].mean()
        metal_mean = thermal[...region...].mean()
        
        ordered = (asphalt_mean > water_mean > metal_mean)
        
        self.results["thermal_emissivity"] = {
            "asphalt": float(asphalt_mean),
            "water": float(water_mean),
            "metal": float(metal_mean),
            "pass": ordered
        }
    
    def run_all(self):
        """Execute all validation tests"""
        self.test_rgb_quality()
        self.test_depth_range()
        self.test_lidar_rain_scatter()
        self.test_thermal_emissivity()
        
        # Print results
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        
        for test_name, result in self.results.items():
            status = "✓ PASS" if result.get("pass") else "✗ FAIL"
            print(f"{test_name}: {status}")
            print(f"  Details: {result}")
        
        return all(r.get("pass", False) for r in self.results.values())

# Run validation
if __name__ == "__main__":
    suite = ValidationSuite("parking_lot_demo")
    all_passed = suite.run_all()
    exit(0 if all_passed else 1)
```

---

## Week 3 Implementation Checklist

### Day 1: RGB & Depth Capture
- [ ] Implement RGB Scene Capture 2D component
- [ ] Implement Depth Scene Capture 2D component
- [ ] Verify pixel-perfect alignment
- [ ] Test PNG export (RGB)
- [ ] Test NPY export (Depth, float32)
- [ ] Synchronize captures (same frame = same timestamp)

### Day 2: Lidar & Thermal
- [ ] Implement Lidar ray-caster (C++)
- [ ] Test 512-ray grid generation
- [ ] Test rain occlusion (30% point drop)
- [ ] Implement PCD export (ASCII first, then binary)
- [ ] Implement Thermal camera (material emissivity lookup)
- [ ] Test temperature calculation (ambient + sun heating)

### Day 3: gRPC/REST Bridge
- [ ] Implement HTTP server in UE5 (or use Blueprint HTTP node)
- [ ] Handle POST /load-world requests
- [ ] Parse WorldSpec JSON
- [ ] Load scene dynamically based on spec
- [ ] Test world loading from Python
- [ ] Implement file output structure (/tmp/pyrobo_sensor_output/)

### Day 4: Integration & Demo
- [ ] Create end-to-end demo script (NLP → render → sensors)
- [ ] Test all 4 sensor types from Python
- [ ] Verify file formats (PNG, NPY, PCD)
- [ ] Test API latency (< 100ms)
- [ ] Create validation test suite

### Day 5: Validation Testing
- [ ] Test RGB quality (brightness, contrast)
- [ ] Test Depth range (0-100m)
- [ ] Test Lidar rain occlusion (20-40% loss)
- [ ] Test Thermal emissivity ordering
- [ ] Test wet asphalt reflections
- [ ] Test sunset lighting (warm orange)
- [ ] Performance profiling (FPS, memory)

### Day 5+: Buffer
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] Documentation

---

## Success Criteria (Week 3)

| Metric | Target | How to Validate |
|--------|--------|-----|
| RGB Output | 1920×1080, 30 FPS, PNG | File dimensions + frame rate |
| Depth Accuracy | 0-100m range, ±0.1m error | Range check + ground truth comparison |
| Lidar Points | 512 rays, 300-400 with rain | Point count with/without rain |
| Thermal Emissivity | Correct ordering | mean(asphalt) > mean(water) > mean(metal) |
| Wet Asphalt | Visible reflections | High-frequency content in reflections |
| Sunset Color | Warm orange (R>G>B) | Color histogram shift at hour=18 |
| API Latency | < 100ms per request | Timer on requests |
| End-to-End | NLP → render → sensors | Complete demo script |

---

## Integration with Python Backend

### Python Side (Already Ready)

**Implemented:**
-  World Spec schema validation
-  FastAPI endpoints (load-world, sensor queries)
-  Claude integration for world generation
-  File structure (/tmp/pyrobo_sensor_output/)

**TODO (Week 3):**
- [ ] Sensor data validation (test suite)
- [ ] Visualization tools (RGB, depth maps, point clouds)
- [ ] Performance metrics (FPS, latency)

### UE5 Side

**Implementation (Week 3):**
- [ ] Scene Capture components (RGB, Depth)
- [ ] Lidar ray-caster (C++)
- [ ] Thermal camera (material lookup)
- [ ] HTTP server (world loading)
- [ ] File export (PNG, NPY, PCD)

---

## File Locations (Phase 0 Complete)

```
/tmp/pyrobo_sensor_output/{world_id}/
├── world_spec.json                 # Loaded spec
├── rgb/
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── depth/
│   ├── frame_0000.npy
│   ├── frame_0001.npy
│   └── ...
├── lidar/
│   ├── frame_0000.pcd
│   ├── frame_0001.pcd
│   └── ...
└── thermal/
    ├── frame_0000.npy
    ├── frame_0001.npy
    └── ...
```

---

**Status:** Week 3 Design Complete. Ready for Sensor Implementation.

**Phase 0 PoC Target:** By end of Week 3, achieve end-to-end loop: NLP → world generation → UE5 rendering → sensor output → Python validation.
