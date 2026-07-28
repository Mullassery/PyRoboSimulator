# UE5 Rendering Engine Integration

Architecture and implementation plan for Unreal Engine 5 integration with PyRoboSimulator backend.

## Overview

PyRoboSimulator uses UE5 as the rendering and sensor simulation engine, with the Python FastAPI backend handling simulation logic, AI agents, and physics. The two systems communicate via a bidirectional protocol.

```
Python Backend                    UE5 Engine
┌─────────────────────┐          ┌──────────────────────┐
│ Simulation Engine   │          │ Rendering Engine     │
│ - Physics loop      │  gRPC    │ - Scene rendering    │
│ - AI agents         │ ←------→ │ - Sensor simulation  │
│ - Events            │          │ - World streaming    │
│ - Logic             │          │ - Input handling     │
└─────────────────────┘          └──────────────────────┘
        │                                │
        └──── PostgreSQL/Redis ─────────┘
             (shared state)
```

## Communication Protocol

### gRPC with Protocol Buffers

Efficient, typed communication using gRPC.

**Proto Definition (world_sync.proto):**

```protobuf
syntax = "proto3";

package pyrobosim;

service WorldSync {
  rpc StartSimulation (SimulationConfig) returns (SimulationResponse);
  rpc UpdateWorldState (WorldState) returns (UpdateAck);
  rpc GetSensorReadings (SensorRequest) returns (SensorReadings);
  rpc StreamEvents (google.protobuf.Empty) returns (stream SimulationEvent);
}

message SimulationConfig {
  string scenario_name = 1;
  int32 num_agents = 2;
  float duration = 3;
  WorldBounds bounds = 4;
}

message WorldState {
  int32 simulation_id = 1;
  int64 timestamp_ms = 2;
  repeated AgentState agents = 3;
}

message AgentState {
  int32 agent_id = 1;
  Vector3 position = 2;
  Vector3 velocity = 3;
  Vector3 rotation = 4;
  string state = 5;  // "idle", "moving", "goal_reached"
}

message Vector3 {
  float x = 1;
  float y = 2;
  float z = 3;
}

message SensorRequest {
  int32 agent_id = 1;
  string sensor_type = 2;  // "rgb", "depth", "lidar", "thermal"
}

message SensorReadings {
  bytes rgb_image = 1;      // JPEG encoded
  bytes depth_map = 2;      // Float32 raw
  bytes lidar_cloud = 3;    // Point cloud XYZ
  bytes thermal_image = 4;  // Float32 raw
  int64 timestamp_ms = 5;
}

message SimulationEvent {
  int32 agent_id = 1;
  string event_type = 2;    // "collision", "goal_reached", etc.
  string data = 3;          // JSON
  int64 timestamp_ms = 4;
}
```

## Architecture

### Backend → UE5 (60 Hz)

1. **World State Update** (every ~16ms)
   - Agent positions, rotations, animations
   - Vehicle dynamics (wheels, steering)
   - Pedestrian animations
   - Environmental state (weather, time of day)

2. **Control Commands**
   - Camera movement
   - Scenario transitions
   - Pause/resume
   - Replay controls

### UE5 → Backend (on-demand)

1. **Sensor Readings**
   - RGB frames (1920×1080 @ 30 FPS)
   - Depth maps (512×512 float32)
   - Lidar point clouds (512 rays × 16 layers)
   - Thermal images (256×256 float32)

2. **Event Stream**
   - Collision reports (position, agents, force)
   - Goal reached notifications
   - Object interactions
   - Error/warning logs

## UE5 Scene Setup

### Level Layout

```
Content/
├── Levels/
│   ├── ParkingLot.umap
│   ├── Warehouse.umap
│   ├── UrbanStreet.umap
│   └── ProceduralWorld.umap (generated per scenario)
│
├── Blueprints/
│   ├── Agent.uasset (base agent pawn)
│   ├── Vehicle.uasset (autonomous vehicle)
│   ├── Pedestrian.uasset (human-like character)
│   ├── SensorMount.uasset (camera/lidar attachment)
│   └── WorldStreamer.uasset (chunk loading)
│
├── Materials/
│   ├── Asphalt.umat
│   ├── Grass.umat
│   ├── Concrete.umat
│   ├── Glass.umat
│   └── MetalShiny.umat
│
└── Plugins/
    ├── PyRoboSync.uplugin (gRPC communication)
    ├── SensorSimulator.uplugin (RGB/Depth/Lidar/Thermal)
    └── CloudRecorder.uplugin (telemetry capture)
```

### Agent Blueprint (C++)

```cpp
UCLASS()
class PYROBOSIM_API AAgent : public APawn
{
    GENERATED_BODY()

    // Properties
    UPROPERTY(EditAnywhere)
    int32 AgentID;

    UPROPERTY(EditAnywhere)
    FVector TargetPosition;

    UPROPERTY(EditAnywhere)
    float MaxSpeed = 50.0f;  // cm/s

    // Components
    UPROPERTY(VisibleAnywhere)
    class USkeletalMeshComponent* MeshComponent;

    UPROPERTY(VisibleAnywhere)
    class UCharacterMovementComponent* MovementComponent;

    UPROPERTY(VisibleAnywhere)
    class UCameraComponent* CameraComponent;

    // Sensors
    UPROPERTY(VisibleAnywhere)
    class URGBSensor* RGBSensor;

    UPROPERTY(VisibleAnywhere)
    class UDepthSensor* DepthSensor;

    UPROPERTY(VisibleAnywhere)
    class ULidarSensor* LidarSensor;

    UPROPERTY(VisibleAnywhere)
    class UThermalSensor* ThermalSensor;

public:
    AAgent();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

    // Update agent state from backend
    void UpdateState(const FVector& Position, const FVector& Rotation, const FString& State);

    // Sensor reading callbacks
    void OnRGBCaptured(const TArray<uint8>& ImageData);
    void OnDepthCaptured(const TArray<float>& DepthData);
    void OnLidarCaptured(const TArray<FVector>& PointCloud);
    void OnThermalCaptured(const TArray<float>& ThermalData);

    // Collision handling
    UFUNCTION()
    void OnCollision(AActor* OtherActor, FVector ImpactPoint, FVector ImpactNormal);
};
```

### Sensor Implementation

**RGB Camera**

```cpp
UCLASS()
class PYROBOSIM_API URGBSensor : public UActorComponent
{
    GENERATED_BODY()

private:
    class USceneCaptureComponent2D* CaptureComponent;
    class UTextureRenderTarget2D* RenderTarget;

    static constexpr int32 WIDTH = 1920;
    static constexpr int32 HEIGHT = 1080;
    static constexpr int32 FPS = 30;

public:
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
        FRGBCapturedSignature,
        const TArray<uint8>&,
        ImageData
    );

    UPROPERTY(BlueprintAssignable)
    FRGBCapturedSignature OnRGBCaptured;

    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    void CaptureFrame();
    TArray<uint8> ReadPixels();  // Returns JPEG encoded
};
```

**Depth Camera**

```cpp
UCLASS()
class PYROBOSIM_API UDepthSensor : public UActorComponent
{
    GENERATED_BODY()

private:
    class USceneCaptureComponent2D* CaptureComponent;
    class UTextureRenderTarget2D* RenderTarget;
    float MaxDistance = 3000.0f;  // cm (30 meters)

    static constexpr int32 WIDTH = 512;
    static constexpr int32 HEIGHT = 512;

public:
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
        FDepthCapturedSignature,
        const TArray<float>&,
        DepthData
    );

    UPROPERTY(BlueprintAssignable)
    FDepthCapturedSignature OnDepthCaptured;

    void CaptureDepth();
    TArray<float> ReadDepthPixels();  // Returns float32 array, normalized 0-1
};
```

**Lidar**

```cpp
UCLASS()
class PYROBOSIM_API ULidarSensor : public UActorComponent
{
    GENERATED_BODY()

private:
    static constexpr int32 NumRays = 512;
    static constexpr int32 NumLayers = 16;
    static constexpr float MaxRange = 30000.0f;  // cm (300m)

    float VerticalFOV = 30.0f;  // degrees
    float HorizontalFOV = 360.0f;

public:
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
        FPointCloudSignature,
        const TArray<FVector>&,
        PointCloud
    );

    UPROPERTY(BlueprintAssignable)
    FPointCloudSignature OnPointCloudCaptured;

    void CaptureScan();
    TArray<FVector> GetPointCloud();  // Returns 512*16 = 8192 points

    void PerformRaycast(int32 Ray, int32 Layer, FVector& OutPosition, bool& bHit);
};
```

**Thermal Camera**

```cpp
UCLASS()
class PYROBOSIM_API UThermalSensor : public UActorComponent
{
    GENERATED_BODY()

private:
    static constexpr int32 WIDTH = 256;
    static constexpr int32 HEIGHT = 256;
    float MinTemp = -20.0f;    // Celsius
    float MaxTemp = 60.0f;

public:
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
        FThermalCapturedSignature,
        const TArray<float>&,
        ThermalData
    );

    UPROPERTY(BlueprintAssignable)
    FThermalCapturedSignature OnThermalCaptured;

    void CaptureFrame();
    TArray<float> ReadThermalPixels();  // Returns temperature values
};
```

## World Streaming

### Chunked World Loading

For large environments (1000+ agents), use chunked streaming:

```cpp
UCLASS()
class PYROBOSIM_API AWorldStreamer : public AActor
{
    GENERATED_BODY()

private:
    static constexpr float ChunkSize = 5000.0f;  // 50m chunks
    TMap<FIntPoint, ULevel*> LoadedChunks;

    AAgent* TrackedAgent;

public:
    virtual void Tick(float DeltaTime) override;

    void UpdateStreamingForAgent(AAgent* Agent);
    void LoadChunk(int32 X, int32 Y);
    void UnloadChunk(int32 X, int32 Y);

    FIntPoint GetChunkCoordinates(const FVector& Position);
};
```

## Synchronization Strategy

### Update Frequency

- **Backend → UE5**: 60 Hz (16ms)
  - Agent positions/rotations
  - Animation state
  - World state

- **UE5 → Backend**: Event-based + polling
  - Collision detection (immediate)
  - Sensor readings (on demand)
  - Events (queued, sent periodically)

### Latency Management

Target: < 100ms end-to-end latency

1. **Network**
   - Use gRPC with connection pooling
   - Batch multiple agent updates
   - Compress sensor data (JPEG for RGB, zlib for depth)

2. **Rendering**
   - Decouple rendering from physics
   - Physics at 60 Hz, rendering at variable FPS
   - Interpolate between physics updates

3. **Sensors**
   - Asynchronous capture
   - Multi-threaded processing
   - Double-buffered render targets

## Integration Points

### Python Plugin (PyRoboSync)

1. **Initialization**
   ```python
   engine = UE5Engine(
       scenario="parking_lot",
       num_agents=100,
       rendering_enabled=True,
       server_address="localhost:50051"
   )
   engine.start()
   ```

2. **State Updates**
   ```python
   # Backend sends state to UE5
   await engine.update_world_state(
       agents=[
           {"id": 1, "pos": (100, 200), "rot": 45},
           {"id": 2, "pos": (150, 250), "rot": 90},
       ],
       timestamp=1234567890
   )
   ```

3. **Sensor Readings**
   ```python
   # Backend requests sensor data
   rgb = await engine.get_sensor(agent_id=1, sensor_type="rgb")
   depth = await engine.get_sensor(agent_id=1, sensor_type="depth")
   lidar = await engine.get_sensor(agent_id=1, sensor_type="lidar")
   ```

4. **Event Streaming**
   ```python
   # Backend receives events
   async for event in engine.stream_events():
       if event.type == "collision":
           handle_collision(event)
   ```

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Agent Update Latency | < 50ms | Backend → UE5 |
| Sensor Capture Latency | < 30ms | Per frame |
| RGB Throughput | 30 FPS @ 1920×1080 | 1080p |
| Depth Resolution | 512×512 @ 30 FPS | 100m range |
| Lidar Points/Sec | 512 × 16 × 30 = 245K | 512 rays × 16 layers |
| Thermal Resolution | 256×256 @ 30 FPS | -20°C to +60°C |
| Network Bandwidth | < 50 Mbps | 100 agents |

## Testing Strategy

### Unit Tests

```cpp
// Test sensor calibration
UPROPERTY(Category = "Tests")
void TestRGBCalibration();

UPROPERTY(Category = "Tests")
void TestDepthAccuracy();

UPROPERTY(Category = "Tests")
void TestLidarRaycast();

UPROPERTY(Category = "Tests")
void TestThermalResponse();
```

### Integration Tests

1. **Backend + UE5 Communication**
   - Start simulation
   - Update agent positions
   - Capture sensors
   - Verify output matches input

2. **Performance Tests**
   - 100 agents, 60 Hz updates
   - Monitor CPU/GPU utilization
   - Check network bandwidth

3. **Sensor Accuracy**
   - Place object at known distance
   - Verify depth reading
   - Compare with ground truth

### Simulation Tests

1. **Collision Detection**
   - Verify collisions reported correctly
   - Test edge cases (overlap, separation)

2. **Sensor Readings**
   - RGB: Check if objects visible
   - Depth: Verify distance accuracy
   - Lidar: Verify point cloud coverage
   - Thermal: Verify temperature response

## Deployment

### UE5 Project Setup

```bash
# Create UE5 project
unrealengine-launcher create-project \
  --engine-version 5.3 \
  --name PyRoboSimulator \
  --template blank

# Copy plugins
cp -r Plugins/* MyProject/Plugins/

# Build project
cd MyProject
./Binaries/Linux/UnrealEditor MyProject.uproject -server -buildmachine
```

### Package for Deployment

```bash
# Package for Linux server
./Binaries/Linux/UE4Editor \
  MyProject.uproject \
  -build \
  -buildmachine \
  -buildscriptsonly \
  -batch

# Run headless
./Binaries/Linux/UE4Server MyProject \
  -log=Logs/PyRoboSimulator.log \
  -server
```

## Future Enhancements

1. **GPU-accelerated Physics** (Phase 2)
   - Move physics to GPU
   - Use NVIDIA PhysX

2. **Advanced Rendering** (Phase 2)
   - Real-time ray tracing
   - HDR sensor simulation

3. **Multi-Scene Support** (Phase 3)
   - Load/unload scenes dynamically
   - Parallel simulations

4. **Machine Learning** (Phase 3+)
   - Training in simulation
   - Domain randomization
   - Synthetic data generation

---

**UE5 Integration Design Complete**

Ready for Phase 1 implementation (~8-12 weeks)
