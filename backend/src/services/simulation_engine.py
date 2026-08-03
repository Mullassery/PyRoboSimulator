"""Core simulation engine with physics loop."""

import base64
import io
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from PIL import Image


@dataclass
class Vector3:
    """3D vector for physics calculations."""

    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        """Add vectors."""
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        """Subtract vectors."""
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        """Multiply by scalar."""
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> "Vector3":
        """Normalize to unit vector."""
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    def distance_to(self, other: "Vector3") -> float:
        """Calculate distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


@dataclass
class Agent:
    """Represents a single agent in simulation."""

    id: int
    position: Vector3
    velocity: Vector3
    acceleration: Vector3
    agent_type: str = "vehicle"
    max_velocity: float = 10.0
    collision_radius: float = 0.5
    goal: Optional[Vector3] = None
    reached_goal: bool = False
    state: str = "idle"  # idle, moving, goal_reached, collision

    def __post_init__(self):
        """Initialize agent after dataclass creation."""
        self._rgb_frame_count = 0
        self.trajectory: list = []  # List of (x, y) positions over time
        self._prev_reached_goal: bool = False  # Track previous goal state for edge detection
        self._prev_depth_map: Optional[np.ndarray] = None  # For temporal filtering

    def generate_lidar_cloud(
        self,
        rain_intensity: float = 0.0,
        beam_spread: float = 0.1,
        multipath_probability: float = 0.05,
        add_temporal_jitter: bool = True
    ) -> list:
        """Generate synthetic lidar point cloud with realistic effects.

        Args:
            rain_intensity: Rain intensity (0-1, where 1 = 80% point loss)
            beam_spread: Beam spread angle in degrees (angular resolution)
            multipath_probability: Probability of multi-path returns per ray
            add_temporal_jitter: Add temporal noise (frame-to-frame jitter)

        Returns:
            List of [x, y, z] points with realistic artifacts
        """
        # 512 rays × 16 layers = 8192 points
        num_rays = 512
        num_layers = 16
        max_range = 300  # meters

        points = []

        for layer_idx in range(num_layers):
            # Vertical angle for this layer (-15 to +15 degrees)
            vertical_angle = -15 + (layer_idx / num_layers) * 30

            for ray_idx in range(num_rays):
                # Horizontal angle for this ray (0 to 360 degrees)
                horizontal_angle = (ray_idx / num_rays) * 360

                # Check rain occlusion (stochastic based on intensity)
                if rain_intensity > 0:
                    # Rain causes point loss: probability increases with intensity
                    # At 1.0 intensity, ~80% of points are lost
                    rain_drop_prob = rain_intensity * 0.8
                    if np.random.rand() < rain_drop_prob:
                        continue  # Skip this ray (rain occlusion)

                # Base distance with agent position influence
                distance = np.random.uniform(5, max_range)
                distance_mod = 20 + (self.position.x / 1000) * 30
                distance = np.clip(distance + distance_mod, 5, max_range)

                # Apply beam spread (angular noise)
                if beam_spread > 0:
                    # Add small random angle to each ray
                    spread_angle = np.random.normal(0, beam_spread)
                    horizontal_angle += spread_angle

                # Add temporal jitter (frame-to-frame noise)
                if add_temporal_jitter:
                    distance += np.random.normal(0, 0.01 * distance)  # 1% jitter

                # Convert spherical to cartesian coordinates
                vert_rad = np.radians(vertical_angle)
                horz_rad = np.radians(horizontal_angle)

                x = distance * np.cos(vert_rad) * np.cos(horz_rad)
                y = distance * np.cos(vert_rad) * np.sin(horz_rad)
                z = distance * np.sin(vert_rad)

                points.append([float(x), float(y), float(z)])

                # Multi-path returns (secondary reflections from ground)
                if multipath_probability > 0 and np.random.rand() < multipath_probability:
                    # Secondary return from ground (~80% of primary distance)
                    secondary_distance = distance * 0.8
                    # Slightly different angle (simulating ground reflection)
                    reflect_angle = horizontal_angle + np.random.normal(0, 2)
                    reflect_vert = -vertical_angle  # Bounce from ground

                    x2 = secondary_distance * np.cos(np.radians(reflect_vert)) * np.cos(np.radians(reflect_angle))
                    y2 = secondary_distance * np.cos(np.radians(reflect_vert)) * np.sin(np.radians(reflect_angle))
                    z2 = secondary_distance * np.sin(np.radians(reflect_vert))

                    points.append([float(x2), float(y2), float(z2)])

        return points

    def generate_depth_map(
        self,
        min_range: float = 0.1,
        max_range: float = 300.0,
        quantization: float = 0.001,
        temporal_filter: bool = True
    ) -> str:
        """Generate synthetic depth map with realistic sensor effects (float32 base64 encoded).

        Args:
            min_range: Minimum detectable range (meters, default 0.1m)
            max_range: Maximum detectable range (meters, default 300m)
            quantization: Depth quantization step (meters, default 0.001m = 1mm)
            temporal_filter: Apply temporal filtering (frame averaging)

        Returns:
            Base64-encoded depth map (512x512 float32 array)
        """
        # Create depth map based on agent position (simulates distance variation)
        width, height = 512, 512

        # Vectorized depth map generation
        cx, cy = width // 2, height // 2
        yy, xx = np.mgrid[0:height, 0:width]
        dx = (xx - cx) / width
        dy = (yy - cy) / height

        # Distance from center increases with position
        depth_map = np.sqrt(dx**2 + dy**2) * max_range

        # Add based on agent position (simulated parallax)
        depth_map += (self.position.x / 1000) * 50
        depth_map = np.clip(depth_map, min_range, max_range).astype(np.float32)

        # Apply depth sensor effects
        depth_map = self._apply_depth_sensor_effects(
            depth_map,
            min_range=min_range,
            max_range=max_range,
            quantization=quantization,
            temporal_filter=temporal_filter
        )

        # Encode as base64
        depth_bytes = depth_map.astype(np.float32).tobytes()
        base64_str = base64.b64encode(depth_bytes).decode("utf-8")
        return base64_str

    def _apply_depth_sensor_effects(
        self,
        depth_map: np.ndarray,
        min_range: float = 0.1,
        max_range: float = 300.0,
        quantization: float = 0.001,
        temporal_filter: bool = True
    ) -> np.ndarray:
        """Apply realistic depth camera sensor effects.

        Args:
            depth_map: Input depth map (H×W float32)
            min_range: Near clip plane (meters)
            max_range: Far clip plane (meters)
            quantization: Quantization step (meters)
            temporal_filter: Use frame averaging for smoothing

        Returns:
            Depth map with applied sensor effects (float32)
        """
        from services.sensor_effects import add_gaussian_noise, quantize

        result = depth_map.astype(np.float32)

        # 1. Near/far clip plane enforcement
        result = np.clip(result, min_range, max_range)

        # 2. Range-based Gaussian noise (higher at far ranges)
        # Noise increases with distance (1% of range), vectorized
        noise_sigma = result * 0.01
        noise = np.random.normal(0, 1, result.shape).astype(np.float32)
        result = result + noise * noise_sigma

        # 3. Clip to valid range after noise
        result = np.clip(result, min_range, max_range)

        # 4. Quantization (1mm steps default)
        if quantization > 0:
            result = quantize(result, quantization)

        # 5. Edge artifact simulation (higher uncertainty at depth discontinuities)
        # Vectorized edge detection using numpy gradient
        gradient_y, gradient_x = np.gradient(result)
        gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)

        # Add extra noise at edges (threshold: 10% of max_range)
        edge_threshold = max_range * 0.1
        edge_mask = gradient_mag > edge_threshold

        if np.any(edge_mask):
            edge_noise = np.random.normal(0, max_range * 0.02, result.shape)
            result[edge_mask] = np.clip(result[edge_mask] + edge_noise[edge_mask], min_range, max_range)

        # 6. Temporal filtering (frame averaging with previous frame)
        if temporal_filter and self._prev_depth_map is not None:
            # Simple exponential moving average (alpha=0.3)
            alpha = 0.3
            result = alpha * result + (1 - alpha) * self._prev_depth_map

        # Store for next frame's temporal filtering
        self._prev_depth_map = result.copy()

        return result

    def generate_rgb_frame(self, iso: int = 100, color_grading: str = "daylight") -> str:
        """Generate synthetic RGB frame with realistic sensor effects (JPEG encoded in base64).

        Args:
            iso: ISO sensitivity (100, 400, 1600, 3200) - higher = more noise
            color_grading: Preset ("daylight", "night", "thermal_tint", "none")

        Returns:
            Base64-encoded JPEG image with sensor artifacts
        """
        # Create synthetic RGB image based on agent state
        width, height = 640, 480
        color = self._get_color_by_state()

        # Create gradient image
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(height):
            img_array[i, :] = [
                int(color[0] * (i / height)),
                int(color[1] * (i / height)),
                int(color[2] * (i / height)),
            ]

        # Apply sensor effects
        img_array = self._apply_sensor_effects(
            img_array,
            iso=iso,
            color_grading=color_grading
        )

        # Convert to JPEG
        img = Image.fromarray(img_array, "RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        jpeg_bytes = buffer.getvalue()

        # Encode to base64
        base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
        self._rgb_frame_count += 1
        return base64_str

    def _apply_sensor_effects(
        self, img_array: np.ndarray, iso: int = 100, color_grading: str = "daylight"
    ) -> np.ndarray:
        """Apply realistic RGB camera sensor effects.

        Args:
            img_array: Input RGB image (H×W×3 uint8)
            iso: ISO sensitivity (100-3200)
            color_grading: Preset ("daylight", "night", "thermal_tint", "none")

        Returns:
            Image with applied effects (uint8)
        """
        from services.sensor_effects import (
            add_gaussian_noise,
            apply_radial_distortion,
            apply_motion_blur,
            apply_color_grading,
        )

        result = img_array.astype(np.float32)

        # 1. ISO-based Gaussian noise (higher ISO = more noise)
        iso_noise_map = {100: 3.0, 400: 8.0, 1600: 20.0, 3200: 45.0}
        noise_sigma = iso_noise_map.get(iso, 3.0)
        result = add_gaussian_noise(result, noise_sigma, 0, 255)

        # 2. Lens distortion (slight barrel distortion)
        result = apply_radial_distortion(result, k1=0.05, k2=0.01)

        # 3. Motion blur based on velocity magnitude
        speed = self.velocity.magnitude()
        if speed > 0.1:
            # Normalize velocity to get direction
            vel_norm = self.velocity.normalize()
            direction = (vel_norm.x, vel_norm.y)
            result = apply_motion_blur(result, speed, direction, max_kernel=15)

        # 4. Color grading preset
        result = apply_color_grading(result.astype(np.uint8), color_grading)

        return result.astype(np.uint8)

    def generate_thermal_image(
        self,
        min_temp: float = -20.0,
        max_temp: float = 60.0,
        calibration_error: float = 2.0
    ) -> str:
        """Generate synthetic thermal image with realistic sensor effects (float32 base64 encoded).

        Args:
            min_temp: Minimum temperature range (Celsius, default -20°C)
            max_temp: Maximum temperature range (Celsius, default +60°C)
            calibration_error: Sensor calibration uncertainty (±degrees)

        Returns:
            Base64-encoded thermal image (256x256 float32 array)
        """
        width, height = 256, 256

        # Vectorized thermal map generation
        yy, xx = np.mgrid[0:height, 0:width]
        cx, cy = width // 2, height // 2

        dx = (xx - cx) / width
        dy = (yy - cy) / height
        distance = np.sqrt(dx**2 + dy**2)

        # Generate temperature map based on distance and agent position
        base_temp = 20.0  # Baseline room temperature
        distance_effect = distance * (max_temp - min_temp) / 2
        thermal_map = base_temp + distance_effect + (self.position.x / 1000) * 10

        # Apply material-based emissivity variation
        thermal_map = self._apply_thermal_effects(
            thermal_map,
            min_temp=min_temp,
            max_temp=max_temp,
            calibration_error=calibration_error
        )

        # Encode as base64
        thermal_bytes = thermal_map.astype(np.float32).tobytes()
        base64_str = base64.b64encode(thermal_bytes).decode("utf-8")
        return base64_str

    def _apply_thermal_effects(
        self,
        thermal_map: np.ndarray,
        min_temp: float = -20.0,
        max_temp: float = 60.0,
        calibration_error: float = 2.0
    ) -> np.ndarray:
        """Apply realistic thermal camera sensor effects.

        Args:
            thermal_map: Input temperature map (H×W float32, °C)
            min_temp: Temperature range minimum
            max_temp: Temperature range maximum
            calibration_error: Calibration uncertainty (±degrees)

        Returns:
            Thermal map with applied effects (float32, °C)
        """
        result = thermal_map.astype(np.float32)

        # 1. Material emissivity variation (11 materials with different values)
        # Create spatial patches with different emissivity
        material_emissivity = {
            "asphalt": 0.95,      # High thermal absorption
            "concrete": 0.92,     # High
            "metal": 0.15,        # Very low
            "glass": 0.85,        # High
            "water": 0.98,        # Very high
            "grass": 0.90,        # High
            "bark": 0.94,         # High
            "leaves": 0.96,       # High
            "soil": 0.93,         # High
            "plastic": 0.85,      # Medium
            "brick": 0.93,        # High
        }

        h, w = result.shape
        # Divide into regions with different materials
        materials_list = list(material_emissivity.items())
        num_materials = len(materials_list)

        # Create material patches horizontally
        patch_w = w // num_materials

        for mat_idx, (material, emissivity) in enumerate(materials_list):
            x_start = mat_idx * patch_w
            x_end = (mat_idx + 1) * patch_w if mat_idx < num_materials - 1 else w

            # Apply emissivity factor (scale apparent temperature)
            # Lower emissivity = lower apparent temperature (scale down less, but visible effect)
            # Modulate around baseline, not multiply from zero
            base_offset = (max_temp + min_temp) / 2
            result[:, x_start:x_end] = (
                (result[:, x_start:x_end] - base_offset) * emissivity + base_offset
            )

        # 2. View factor effect (directional sensitivity)
        # Simulate that viewing angle affects measurement
        yy, xx = np.mgrid[0:h, 0:w]
        center_dist = np.sqrt((yy - h/2)**2 + (xx - w/2)**2) / max(h, w)
        view_factor = 0.8 + 0.2 * (1 - center_dist)  # Reduce at edges (off-axis)

        result = result * view_factor

        # 3. Temperature range clipping and calibration
        result = np.clip(result, min_temp, max_temp)

        # 4. Calibration error (±2°C uncertainty)
        if calibration_error > 0:
            calib_offset = np.random.normal(0, calibration_error, result.shape)
            result = np.clip(result + calib_offset, min_temp, max_temp)

        # 5. Sensor noise (thermal sensor noise, ~0.2°C)
        thermal_noise = np.random.normal(0, 0.2, result.shape)
        result = np.clip(result + thermal_noise, min_temp, max_temp)

        return result

    def _get_color_by_state(self) -> tuple[int, int, int]:
        """Get RGB color based on agent state."""
        if self.state == "moving":
            return (0, 255, 0)  # Green
        elif self.state == "goal_reached":
            return (255, 255, 0)  # Yellow
        elif self.state == "collision":
            return (255, 0, 0)  # Red
        else:
            return (0, 150, 255)  # Blue (idle)

    def update_physics(self, dt: float) -> None:
        """Update agent physics using Euler integration.

        Args:
            dt: Timestep in seconds
        """
        # v = v + a*dt
        self.velocity = self.velocity + self.acceleration * dt

        # Clamp velocity to max
        vel_mag = self.velocity.magnitude()
        if vel_mag > self.max_velocity:
            self.velocity = self.velocity.normalize() * self.max_velocity

        # x = x + v*dt
        self.position = self.position + self.velocity * dt

        # Reset acceleration (forces applied each frame)
        self.acceleration = Vector3(0, 0, 0)

    def apply_force(self, force: Vector3) -> None:
        """Apply force to agent (simplified: F = ma, a = F/1.0 for m=1)."""
        self.acceleration = self.acceleration + force

    def distance_to_agent(self, other: "Agent") -> float:
        """Calculate distance to another agent."""
        return self.position.distance_to(other.position)

    def check_collision(self, other: "Agent") -> bool:
        """Check if this agent collides with another."""
        min_distance = self.collision_radius + other.collision_radius
        actual_distance = self.distance_to_agent(other)
        return actual_distance < min_distance

    def move_towards_goal(self, force_magnitude: float = 1.0) -> None:
        """Apply force towards goal if set."""
        if self.goal is None or self.reached_goal:
            return

        direction = self.goal - self.position
        distance = direction.magnitude()

        if distance < 1.0:  # Goal reached threshold
            self.reached_goal = True
            self.velocity = Vector3(0, 0, 0)
            return

        direction = direction.normalize()
        force = direction * force_magnitude
        self.apply_force(force)

    def clamp_position(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        """Clamp agent position to world bounds."""
        self.position.x = max(x_min, min(x_max, self.position.x))
        self.position.y = max(y_min, min(y_max, self.position.y))
        # Bounce off boundaries
        if self.position.x <= x_min or self.position.x >= x_max:
            self.velocity.x *= -0.5
        if self.position.y <= y_min or self.position.y >= y_max:
            self.velocity.y *= -0.5


class Event:
    """Simulation event."""

    def __init__(
        self,
        timestamp: float,
        event_type: str,
        agent_ids: Optional[list[int]] = None,
        data: Optional[dict] = None,
    ):
        """Initialize event."""
        self.timestamp = timestamp
        self.event_type = event_type
        self.agent_ids = agent_ids or []
        self.data = data or {}


class SimulationEngine:
    """Main simulation engine with physics loop."""

    def __init__(
        self,
        num_agents: int,
        duration: float,
        timestep: float = 0.016,
        world_bounds: tuple[float, float, float, float] = (0, 1000, 0, 1000),
        num_obstacles: int = 10,
    ):
        """Initialize simulation.

        Args:
            num_agents: Number of agents to spawn
            duration: Total simulation duration (seconds)
            timestep: Physics timestep (seconds)
            world_bounds: (x_min, x_max, y_min, y_max)
            num_obstacles: Number of obstacles to generate
        """
        self.num_agents = num_agents
        self.duration = duration
        self.timestep = timestep
        self.x_min, self.x_max, self.y_min, self.y_max = world_bounds
        self.num_obstacles = num_obstacles

        self.current_time = 0.0
        self.step_count = 0
        self.agents: dict[int, Agent] = {}
        self.events: list[Event] = []
        self.obstacles: list = []
        self._next_event_id: int = 0  # Monotonic event ID counter

        # Statistics
        self.total_collisions = 0
        self.goals_reached = 0
        self.is_running: bool = True

        self._spawn_agents()
        self._spawn_obstacles()

    def _spawn_agents(self) -> None:
        """Spawn agents randomly in world."""
        np.random.seed(42)  # Deterministic for testing

        for i in range(self.num_agents):
            x = np.random.uniform(self.x_min, self.x_max)
            y = np.random.uniform(self.y_min, self.y_max)

            agent = Agent(
                id=i,
                position=Vector3(x, y, 0),
                velocity=Vector3(0, 0, 0),
                acceleration=Vector3(0, 0, 0),
            )

            # Assign random goal
            goal_x = np.random.uniform(self.x_min, self.x_max)
            goal_y = np.random.uniform(self.y_min, self.y_max)
            agent.goal = Vector3(goal_x, goal_y, 0)

            self.agents[i] = agent

    def _spawn_obstacles(self) -> None:
        """Generate obstacles in world."""
        np.random.seed(42)

        for i in range(self.num_obstacles):
            x = np.random.uniform(self.x_min + 50, self.x_max - 50)
            y = np.random.uniform(self.y_min + 50, self.y_max - 50)

            width = np.random.uniform(20, 80)
            height = np.random.uniform(20, 80)

            obstacle = {
                "id": i,
                "position": {"x": x, "y": y, "z": 0},
                "size": {"x": width, "y": height, "z": 5},
                "type": "wall",
            }
            self.obstacles.append(obstacle)

    def _update_agent_states(self) -> None:
        """Update agent states based on motion and status."""
        for agent in self.agents.values():
            if agent.reached_goal:
                agent.state = "goal_reached"
            elif agent.velocity.magnitude() > 0.1:
                agent.state = "moving"
            else:
                agent.state = "idle"

            agent.trajectory.append((agent.position.x, agent.position.y))

    def step(self) -> list[Event]:
        """Execute one simulation step.

        Returns:
            List of events that occurred this step
        """
        step_events = []

        # 0. Update agent states
        self._update_agent_states()

        # 1. Update agent physics
        for agent in self.agents.values():
            agent.move_towards_goal(force_magnitude=2.0)
            agent.update_physics(self.timestep)
            agent.clamp_position(self.x_min, self.x_max, self.y_min, self.y_max)

        # 2. Collision detection
        agent_list = list(self.agents.values())
        for i in range(len(agent_list)):
            for j in range(i + 1, len(agent_list)):
                agent_a = agent_list[i]
                agent_b = agent_list[j]

                if agent_a.check_collision(agent_b):
                    # Record collision
                    self.total_collisions += 1
                    event = Event(
                        timestamp=self.current_time,
                        event_type="collision",
                        agent_ids=[agent_a.id, agent_b.id],
                        data={
                            "position": {
                                "x": agent_a.position.x,
                                "y": agent_a.position.y,
                            }
                        },
                    )
                    event.id = self._next_event_id
                    self._next_event_id += 1
                    step_events.append(event)

                    # Bounce agents apart
                    diff = agent_a.position - agent_b.position
                    diff = diff.normalize() * 0.5
                    agent_a.velocity = agent_a.velocity + diff
                    agent_b.velocity = agent_b.velocity - diff

        # 3. Goal reached detection
        for agent in self.agents.values():
            if agent.reached_goal and not agent._prev_reached_goal:
                self.goals_reached += 1
                event = Event(
                    timestamp=self.current_time,
                    event_type="goal_reached",
                    agent_ids=[agent.id],
                )
                event.id = self._next_event_id
                self._next_event_id += 1
                step_events.append(event)
            agent._prev_reached_goal = agent.reached_goal

        # 4. Emit step complete event
        step_event = Event(
            timestamp=self.current_time,
            event_type="step_complete",
            data={"step": self.step_count, "agents": len(self.agents)},
        )
        step_events.append(step_event)

        # Update time
        self.current_time += self.timestep
        self.step_count += 1

        # Store events
        self.events.extend(step_events)

        return step_events

    def run(self) -> None:
        """Run entire simulation to completion."""
        max_steps = int(self.duration / self.timestep)

        for _ in range(max_steps):
            if self.current_time >= self.duration:
                break
            self.step()

    def get_agent_state(self, agent_id: int) -> dict:
        """Get current state of an agent."""
        if agent_id not in self.agents:
            return {}

        agent = self.agents[agent_id]
        return {
            "id": agent.id,
            "position": {
                "x": agent.position.x,
                "y": agent.position.y,
                "z": agent.position.z,
            },
            "velocity": {
                "x": agent.velocity.x,
                "y": agent.velocity.y,
                "z": agent.velocity.z,
            },
        }

    def get_summary(self) -> dict:
        """Get simulation summary statistics."""
        return {
            "total_steps": self.step_count,
            "current_time": self.current_time,
            "total_events": len(self.events),
            "total_collisions": self.total_collisions,
            "goals_reached": self.goals_reached,
            "agents": len(self.agents),
        }

    def get_agent_rgb_frame(self, agent_id: int) -> Optional[str]:
        """Get RGB frame (JPEG base64) from agent.

        Args:
            agent_id: Agent ID

        Returns:
            Base64-encoded JPEG string or None if agent not found
        """
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        return agent.generate_rgb_frame()

    def get_all_agents_rgb_frames(self) -> dict[int, str]:
        """Get RGB frames for all agents.

        Returns:
            Dictionary mapping agent_id to base64-encoded JPEG
        """
        frames = {}
        for agent_id, agent in self.agents.items():
            frames[agent_id] = agent.generate_rgb_frame()
        return frames

    def get_agent_depth_map(self, agent_id: int) -> Optional[str]:
        """Get depth map (base64 encoded) from agent.

        Args:
            agent_id: Agent ID

        Returns:
            Base64-encoded depth map or None if agent not found
        """
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        return agent.generate_depth_map()

    def get_all_agents_depth_maps(self) -> dict[int, str]:
        """Get depth maps for all agents.

        Returns:
            Dictionary mapping agent_id to base64-encoded depth map
        """
        maps = {}
        for agent_id, agent in self.agents.items():
            maps[agent_id] = agent.generate_depth_map()
        return maps

    def get_agent_lidar_cloud(self, agent_id: int) -> Optional[list]:
        """Get lidar point cloud from agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of [x, y, z] points or None if agent not found
        """
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        return agent.generate_lidar_cloud()

    def get_all_agents_lidar_clouds(self) -> dict[int, list]:
        """Get lidar point clouds for all agents.

        Returns:
            Dictionary mapping agent_id to point cloud (list of [x, y, z])
        """
        clouds = {}
        for agent_id, agent in self.agents.items():
            clouds[agent_id] = agent.generate_lidar_cloud()
        return clouds

    def get_agent_thermal_image(self, agent_id: int) -> Optional[str]:
        """Get thermal image (base64 encoded) from agent.

        Args:
            agent_id: Agent ID

        Returns:
            Base64-encoded thermal image or None if agent not found
        """
        if agent_id not in self.agents:
            return None
        agent = self.agents[agent_id]
        return agent.generate_thermal_image()

    def get_all_agents_thermal_images(self) -> dict[int, str]:
        """Get thermal images for all agents.

        Returns:
            Dictionary mapping agent_id to base64-encoded thermal image
        """
        images = {}
        for agent_id, agent in self.agents.items():
            images[agent_id] = agent.generate_thermal_image()
        return images

    def get_obstacles(self) -> list:
        """Get all obstacles in world.

        Returns:
            List of obstacle dictionaries
        """
        return self.obstacles

    def get_agent_trajectory(self, agent_id: int, max_points: int = 500) -> list:
        """Get trajectory for an agent (limited to max_points most recent).

        Args:
            agent_id: Agent ID
            max_points: Maximum trajectory points to return

        Returns:
            List of [x, y] positions or empty list if agent not found
        """
        if agent_id not in self.agents:
            return []
        agent = self.agents[agent_id]
        return agent.trajectory[-max_points:] if agent.trajectory else []

    def get_all_agent_trajectories(self, max_points: int = 500) -> dict[int, list]:
        """Get trajectories for all agents.

        Args:
            max_points: Maximum trajectory points per agent

        Returns:
            Dictionary mapping agent_id to trajectory (list of [x, y])
        """
        trajectories = {}
        for agent_id, agent in self.agents.items():
            trajectories[agent_id] = agent.trajectory[-max_points:] if agent.trajectory else []
        return trajectories
