# PyRoboSimulator: ROS2 & NAV2 Integration + Browser Visualization

**Purpose:** Enable PyRoboSimulator to act as a digital twin for ROS2-based robots, publishing sensor data, receiving commands, and integrating with NAV2 navigation stack.

---

## Architecture: ROS2 Bridge Layer

```
┌──────────────────────────────────────────────────────────────┐
│             ROS2 Navigation Stack                            │
│  (NAV2, Nav2_Core, SLAM, Path Planning, Costmap)             │
│                                                               │
│  Subscribes: sensor_msgs/LaserScan, sensor_msgs/Image        │
│              nav_msgs/Odometry, tf/tfMessage                 │
│              geometry_msgs/Twist (commands)                  │
│                                                               │
│  Publishes: geometry_msgs/Path, nav_msgs/CostMap2D           │
│             nav_msgs/OccupancyGrid, visualization_msgs/*     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ ROS2 Topics & Services
                     │
┌────────────────────▼─────────────────────────────────────────┐
│         PyRoboSimulator ROS2 Bridge (Python)                 │
│  - rclpy node for world simulation                           │
│  - Publishes: RGB, Depth, Lidar, Odometry, TF frames        │
│  - Subscribes: velocity commands (cmd_vel)                  │
│  - Services: /reset_world, /set_robot_pose, /spawn_object   │
│  - Parameters: simulation_speed, physics_enabled             │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ gRPC/REST + Sensor Data Stream
                     │
┌────────────────────▼─────────────────────────────────────────┐
│         Unreal Engine 5 Simulation                           │
│  - Running world, physics, sensor simulation                │
│  - Responsive to ROS2 commands (robot movement)            │
│  - Generates sensor outputs (RGB, Lidar, Thermal)          │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
  ┌─────▼──┐  ┌─────▼──┐  ┌─────▼──┐
  │ Browser│  │ Desktop│  │ ROS2   │
  │ Pixel  │  │ Viewer │  │ RViz2  │
  │Stream  │  │ (UE5)  │  │ Visual │
  └────────┘  └────────┘  └────────┘
```

---

## ROS2 Topics Published by PyRoboSimulator

### **Sensor Topics**

```bash
# RGB Camera Feed
/camera/rgb/image_raw
  Type: sensor_msgs/Image
  Frame: camera_optical_frame
  Resolution: configurable (default 1280x720)
  FPS: configurable (default 30)
  Encoding: rgb8 or bgr8

# Depth Camera
/camera/depth/image_raw
  Type: sensor_msgs/Image
  Frame: camera_optical_frame
  Encoding: float32 (depth in meters)
  Range: 0.1m → 100m

# Lidar Point Cloud
/lidar/points
  Type: sensor_msgs/PointCloud2
  Frame: lidar_link
  Channels: x, y, z, intensity, ring
  Frequency: configurable (default 10 Hz)

# Thermal Image
/camera/thermal/image_raw
  Type: sensor_msgs/Image
  Frame: thermal_optical_frame
  Encoding: float32 (temperature in Celsius)

# IMU (if enabled)
/imu/data
  Type: sensor_msgs/Imu
  Frame: imu_link
  Angular velocity, linear acceleration

# Odometry
/odom
  Type: nav_msgs/Odometry
  Frame: odom → base_link
  Contains: pose, twist, covariance
```

### **Navigation Topics**

```bash
# Robot Pose Estimate (for localization)
/amcl_pose
  Type: geometry_msgs/PoseWithCovarianceStamped

# Global Costmap
/global_costmap/costmap
  Type: nav_msgs/OccupancyGrid

# Local Costmap
/local_costmap/costmap
  Type: nav_msgs/OccupancyGrid

# Robot Footprint Marker
/robot_footprint
  Type: visualization_msgs/Marker
```

---

## ROS2 Topics Subscribed by PyRoboSimulator

```bash
# Velocity Commands (from NAV2 controller)
/cmd_vel
  Type: geometry_msgs/Twist
  linear: [x, y, z] (m/s)
  angular: [x, y, z] (rad/s)
  → PyRoboSimulator applies to robot physics

# Goal Pose (from NAV2 goal setter)
/goal_pose
  Type: geometry_msgs/PoseStamped
  → PyRoboSimulator marks goal location, publishes progress

# Service: Reset World
/reset_world
  Type: std_srvs/Empty or custom
  → Resets simulation to initial state

# Service: Set Robot Pose
/set_robot_pose
  Type: geometry_msgs/PoseStamped
  → Teleports robot to pose (for testing)
```

---

## ROS2 Transform (TF2) Frames Published

```
world
  └─ odom
      └─ base_link
          ├─ camera_link
          │   └─ camera_optical_frame
          ├─ lidar_link
          ├─ imu_link
          └─ base_footprint

# All transforms published with proper covariance
# Frequency: 50 Hz (configurable)
```

---

## Browser Visualization with Pixel Streaming

### **Architecture**

```
Unreal Engine 5
  │
  ├─ Pixel Streaming Plugin (streams video + input)
  │
  └─ WebSocket Bridge
      │
      ├─ HTML5 Client (Browser)
      │   └─ Canvas renderer + UI controls
      │
      └─ Signaling Server (Node.js/Python)
          └─ Manages peer connections, WebRTC
```

### **Browser Interface Features**

#### **Main View**
- **3D World Viewport** (full-screen)
  - Mouse control: orbit camera, pan, zoom
  - Keyboard: WASD for camera movement, Space to toggle fly mode
  - Right-click + drag: rotate view
  - Scroll wheel: zoom
  
#### **Overlay UI Panel** (top-right)
```
┌──────────────────────────────────┐
│ PyRoboSimulator - Simulation View │
├──────────────────────────────────┤
│ World: Tokyo (Level 5 terrain)   │
│ FPS: 32 | Latency: 18ms          │
│ Physics: ON | Time: 12:35:42     │
│                                  │
│ 🎯 Goal: [32.5m, 18.2m]          │
│ 📍 Robot: [15.3m, 8.7m]          │
│ 📏 Distance to goal: 22.1m        │
│                                  │
│ [Pause] [Reset] [⚙️ Settings]     │
└──────────────────────────────────┘
```

#### **Right Sidebar** (sensor feeds)
- **RGB Preview** (small thumbnail)
- **Depth Heatmap** (live)
- **Lidar 2D Top-Down** (rings colored by height)
- **Thermal View** (optional toggle)

#### **Bottom Panel** (controls)
```
┌─────────────────────────────────────────┐
│ Camera: Orbit | Sensors: RGB+Lidar+Depth │
│ Quality: [⬇️ Low] [Medium] High [⬆️Ultra] │
│ Speed: [────●────] 1x                    │
│ [Fullscreen] [Export] [ROS2 Status: ✅] │
└─────────────────────────────────────────┘
```

---

## FastAPI Endpoints for ROS2 Integration

### **1. Get ROS2 Topic Configuration**

```bash
GET /api/v1/ros2/topics

Response:
{
  "publishers": {
    "/camera/rgb/image_raw": {
      "type": "sensor_msgs/Image",
      "frequency_hz": 30,
      "enabled": true
    },
    "/lidar/points": {
      "type": "sensor_msgs/PointCloud2",
      "frequency_hz": 10,
      "enabled": true
    },
    "/odom": {
      "type": "nav_msgs/Odometry",
      "frequency_hz": 50,
      "enabled": true
    }
  },
  "subscribers": {
    "/cmd_vel": {
      "type": "geometry_msgs/Twist",
      "last_message_age_ms": 150
    }
  }
}
```

### **2. Enable/Disable ROS2 Publishing**

```bash
POST /api/v1/ros2/publishers/{topic}/toggle
Content-Type: application/json

{
  "enabled": false  // Disable /lidar/points publishing
}

Response:
{
  "topic": "/lidar/points",
  "enabled": false,
  "status": "disabled"
}
```

### **3. Get ROS2 Node Status**

```bash
GET /api/v1/ros2/status

Response:
{
  "ros2_enabled": true,
  "node_name": "/pyrobosimulator_bridge",
  "connected_to_ros_master": true,
  "publishers_active": 8,
  "subscribers_active": 2,
  "services_advertised": 3,
  "latency_to_ros_ms": 2.5,
  "last_heartbeat": "2026-07-28T12:35:42Z"
}
```

### **4. Publish Robot Pose**

```bash
POST /api/v1/ros2/set_robot_pose
Content-Type: application/json

{
  "x": 25.0,
  "y": 15.0,
  "z": 0.0,
  "yaw": 1.57  // radians
}

Response:
{
  "status": "pose_set",
  "robot_position": [25.0, 15.0, 0.0],
  "broadcaster_latency_ms": 3
}
```

### **5. Reset Simulation**

```bash
POST /api/v1/ros2/reset

Response:
{
  "status": "reset_complete",
  "world_reloaded": true,
  "robot_pose": [0, 0, 0],
  "time_ms": 450
}
```

---

## Phase 0 Sprint: ROS2 Integration Tasks

### **Week 1: Pixel Streaming Setup**
- [ ] Enable UE5 Pixel Streaming plugin
- [ ] Create WebSocket signaling server (Python + Flask)
- [ ] Deploy signaling server on localhost:8000
- [ ] HTML5 client for browser viewing
- [ ] Test browser connectivity (Chrome, Firefox)
- [ ] Performance: < 50ms latency on local network

### **Week 2: ROS2 Bridge Implementation**
- [ ] Create rclpy node: `RoboSimulatorBridge`
- [ ] Implement publishers:
  - [ ] `/camera/rgb/image_raw` (sensor_msgs/Image)
  - [ ] `/lidar/points` (sensor_msgs/PointCloud2)
  - [ ] `/odom` (nav_msgs/Odometry)
  - [ ] `/tf` (TransformBroadcaster)
- [ ] Implement subscribers:
  - [ ] `/cmd_vel` (geometry_msgs/Twist) → move robot
- [ ] Test with `ros2 topic list` and `ros2 topic echo`

### **Week 3: NAV2 Integration Testing**
- [ ] Launch NAV2 bringup with PyRoboSimulator as sim
- [ ] Set Nav2 goal (through RViz2 or API)
- [ ] Verify robot follows NAV2 path
- [ ] Verify costmap updates reflect simulated world
- [ ] Test with real NAV2 navigation stack
- [ ] Capture video of successful NAV2 navigation

---

## Configuration: Enable/Disable ROS2 Mode

### **World Spec with ROS2 Enabled**

```json
{
  "location": { "name": "Tokyo", ... },
  "ros2": {
    "enabled": true,
    "namespace": "/robot1",
    "sim_time_enabled": true,  // Use sim_time instead of wall-clock
    "publishers": {
      "camera_rgb": true,
      "lidar": true,
      "depth": true,
      "thermal": false,
      "imu": true,
      "odometry": true
    },
    "subscribers": {
      "cmd_vel": true,
      "goal_pose": true
    },
    "publish_frequency_hz": {
      "camera": 30,
      "lidar": 10,
      "odom": 50,
      "tf": 50
    }
  }
}
```

### **API Call**

```bash
POST /api/v1/generate-world
Content-Type: application/json

{
  "prompt": "Tokyo parking lot for autonomous navigation testing",
  "rendering_quality": { "profile": "medium" },
  "terrain": { "detail_level": 5 },
  "ros2": {
    "enabled": true,
    "namespace": "/robot1"
  }
}
```

---

## Browser-to-ROS2 Workflow

### **Example: User in Browser Sets Goal**

1. **Browser UI:** Click on map to set goal
   ```javascript
   // Browser sends goal to FastAPI
   fetch('/api/v1/ros2/set_goal', {
     method: 'POST',
     body: JSON.stringify({
       x: 50.0,
       y: 30.0,
       yaw: 0.0
     })
   })
   ```

2. **FastAPI Bridge:** Receives goal, publishes to ROS2
   ```python
   goal_msg = PoseStamped()
   goal_msg.pose.position.x = 50.0
   goal_msg.pose.position.y = 30.0
   self.goal_publisher.publish(goal_msg)
   ```

3. **NAV2 Stack:** Plans path, publishes to `/cmd_vel`
   ```
   NAV2 → /cmd_vel (geometry_msgs/Twist)
   ```

4. **PyRoboSimulator:** Receives cmd_vel, moves robot
   ```python
   def cmd_vel_callback(msg: Twist):
       robot.velocity = [msg.linear.x, msg.linear.y]
       robot.angular_velocity = msg.angular.z
   ```

5. **UE5:** Renders new robot position
   ```cpp
   robot_mesh->AddMovement(velocity * delta_time);
   ```

6. **Browser:** Displays updated robot location (Pixel Streaming)
   ```
   [View in browser] ← Real-time update
   ```

---

## Testing Checklist: ROS2 + NAV2 Integration

- [ ] ROS2 node (`/pyrobosimulator_bridge`) appears in `ros2 node list`
- [ ] Topics published correctly:
  ```bash
  ros2 topic echo /camera/rgb/image_raw  # See live RGB
  ros2 topic echo /lidar/points          # See Lidar points
  ros2 topic echo /odom                  # See odometry
  ```
- [ ] Velocity commands work:
  ```bash
  ros2 topic pub /cmd_vel geometry_msgs/Twist \
    "linear: {x: 0.5, y: 0.0, z: 0.0} \
     angular: {x: 0.0, y: 0.0, z: 0.0}"
  # Robot moves in simulation
  ```
- [ ] NAV2 can plan path:
  ```bash
  ros2 launch nav2_bringup navigation_launch.py
  # In RViz2: set goal → NAV2 publishes /cmd_vel → robot moves
  ```
- [ ] Browser Pixel Streaming works:
  ```
  Open http://localhost:8000/pixel-stream in Chrome
  → See live 3D world rendered
  ```
- [ ] Costmap updates:
  ```bash
  ros2 topic echo /global_costmap/costmap
  # Should reflect simulated obstacles
  ```

---

## Performance Targets

| Metric | Target | How to Validate |
|--------|--------|-----|
| **Pixel Streaming Latency** | <50ms | Measure browser input to UE5 response |
| **ROS2 Topic Latency** | <20ms | Time-stamp diff: pub → sub |
| **NAV2 Path Planning** | <2s | Time from goal set to first cmd_vel |
| **Robot Movement Sync** | <100ms | Browser shows position within 100ms of real pose |
| **Lidar Point Cloud Rate** | 10 Hz (configurable) | `ros2 topic hz /lidar/points` |
| **RGB Camera Rate** | 30 FPS (configurable) | `ros2 topic hz /camera/rgb/image_raw` |

---

## File Structure for ROS2 Integration

```
PyRoboSimulator/
├── backend/
│   ├── ros2_bridge.py          # Main ROS2 node
│   ├── pixel_streaming_server.py # WebSocket signaling
│   └── api/
│       └── ros2_endpoints.py    # FastAPI ROS2 routes
├── html/
│   ├── index.html              # Pixel Streaming viewer
│   ├── pixel-stream.js         # WebRTC client
│   └── ui-controls.js          # Browser controls
├── unreal/
│   └── Plugins/
│       └── PyRoboSimBridge/     # UE5 plugin for ROS2 integration
└── docker/
    ├── Dockerfile.ros2         # ROS2 + PyRoboSimulator container
    └── docker-compose.yml      # Full stack: ROS2 + NAV2 + Sim
```

---

## Docker Deployment: Full Stack

### **docker-compose.yml**

```yaml
version: '3'
services:
  ros2:
    image: ros:iron-ros-base
    environment:
      - ROS_DOMAIN_ID=42
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix  # Display forwarding for RViz2
    command: ros2 launch nav2_bringup navigation_launch.py

  pyrobosimulator:
    build: .
    environment:
      - ROS_DOMAIN_ID=42
      - DISPLAY=:0
    ports:
      - "8000:8000"      # FastAPI
      - "8001:8001"      # Pixel Streaming signaling
    volumes:
      - ./worlds:/app/worlds  # World configs

  rviz2:
    image: ros:iron-ros-base
    environment:
      - ROS_DOMAIN_ID=42
      - DISPLAY=:0
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
    command: rviz2
```

**Start all services:**
```bash
docker-compose up
# ROS2 stack running on host, PyRoboSimulator on container
# Open browser: http://localhost:8000/pixel-stream
# Open RViz2: displays live simulated world
```

---

## Production Readiness (Phase 1)

- [ ] Multi-robot support (multiple namespaces)
- [ ] Distributed simulation (run on different hardware)
- [ ] Sensor plugin architecture (custom sensor types)
- [ ] Replay/record simulation (save & replay ROS2 bags)
- [ ] Real-world to sim calibration (import real sensor logs)

