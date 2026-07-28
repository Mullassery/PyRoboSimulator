"""Core simulation engine with physics loop."""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Vector3:
    """3D vector for physics calculations."""

    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        """Add vectors."""
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

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
    ):
        """Initialize simulation.

        Args:
            num_agents: Number of agents to spawn
            duration: Total simulation duration (seconds)
            timestep: Physics timestep (seconds)
            world_bounds: (x_min, x_max, y_min, y_max)
        """
        self.num_agents = num_agents
        self.duration = duration
        self.timestep = timestep
        self.x_min, self.x_max, self.y_min, self.y_max = world_bounds

        self.current_time = 0.0
        self.step_count = 0
        self.agents: dict[int, Agent] = {}
        self.events: list[Event] = []

        # Statistics
        self.total_collisions = 0
        self.goals_reached = 0

        self._spawn_agents()

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

    def step(self) -> list[Event]:
        """Execute one simulation step.

        Returns:
            List of events that occurred this step
        """
        step_events = []

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
                    step_events.append(event)

                    # Bounce agents apart
                    diff = agent_a.position - agent_b.position
                    diff = diff.normalize() * 0.5
                    agent_a.velocity = agent_a.velocity + diff
                    agent_b.velocity = agent_b.velocity - diff

        # 3. Goal reached detection
        for agent in self.agents.values():
            if agent.reached_goal and not agent.reached_goal:
                self.goals_reached += 1
                event = Event(
                    timestamp=self.current_time,
                    event_type="goal_reached",
                    agent_ids=[agent.id],
                )
                step_events.append(event)

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
