"""Tests for simulation engine physics and logic."""

import pytest
import math
from src.services.simulation_engine import (
    SimulationEngine,
    Agent,
    Vector3,
    Event,
)


class TestVector3:
    """Vector3 math operations."""

    def test_vector_addition(self) -> None:
        """Test vector addition."""
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)
        result = v1 + v2

        assert result.x == 5
        assert result.y == 7
        assert result.z == 9

    def test_vector_multiplication(self) -> None:
        """Test scalar multiplication."""
        v = Vector3(1, 2, 3)
        result = v * 2

        assert result.x == 2
        assert result.y == 4
        assert result.z == 6

    def test_vector_magnitude(self) -> None:
        """Test vector magnitude calculation."""
        v = Vector3(3, 4, 0)
        assert v.magnitude() == 5.0

    def test_vector_normalize(self) -> None:
        """Test vector normalization."""
        v = Vector3(3, 4, 0)
        normalized = v.normalize()

        assert abs(normalized.magnitude() - 1.0) < 0.001
        assert abs(normalized.x - 0.6) < 0.001
        assert abs(normalized.y - 0.8) < 0.001

    def test_vector_distance(self) -> None:
        """Test distance calculation."""
        v1 = Vector3(0, 0, 0)
        v2 = Vector3(3, 4, 0)
        assert v1.distance_to(v2) == 5.0


class TestAgent:
    """Agent physics and behavior."""

    def test_agent_creation(self) -> None:
        """Test agent initialization."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(1, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        assert agent.id == 1
        assert agent.position.x == 0
        assert agent.velocity.x == 1

    def test_agent_physics_update(self) -> None:
        """Test physics update (Euler integration)."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(1, 0, 0),
            acceleration=Vector3(1, 0, 0),
        )

        agent.update_physics(dt=1.0)

        # v = v + a*dt = 1 + 1*1 = 2
        assert agent.velocity.x == 2.0
        # x = x + v*dt = 0 + 1*1 = 1
        assert agent.position.x == 1.0

    def test_agent_velocity_clamping(self) -> None:
        """Test velocity is clamped to max."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            max_velocity=5.0,
        )

        # Apply large force
        agent.apply_force(Vector3(100, 0, 0))
        agent.update_physics(dt=1.0)

        # Velocity should be clamped to max_velocity
        assert agent.velocity.magnitude() <= agent.max_velocity + 0.001

    def test_agent_collision_detection(self) -> None:
        """Test collision detection between agents."""
        agent1 = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            collision_radius=1.0,
        )

        agent2 = Agent(
            id=2,
            position=Vector3(1.5, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            collision_radius=1.0,
        )

        # Collision radius sum = 2.0, distance = 1.5, should collide
        assert agent1.check_collision(agent2)

    def test_agent_no_collision_when_far(self) -> None:
        """Test no collision when agents are far apart."""
        agent1 = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            collision_radius=0.5,
        )

        agent2 = Agent(
            id=2,
            position=Vector3(10, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            collision_radius=0.5,
        )

        assert not agent1.check_collision(agent2)

    def test_agent_move_towards_goal(self) -> None:
        """Test goal-seeking behavior."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            goal=Vector3(10, 0, 0),
        )

        agent.move_towards_goal(force_magnitude=1.0)
        assert agent.acceleration.x > 0  # Force applied towards goal

    def test_agent_goal_reached(self) -> None:
        """Test goal reached detection."""
        agent = Agent(
            id=1,
            position=Vector3(9.9, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
            goal=Vector3(10, 0, 0),
        )

        agent.move_towards_goal(force_magnitude=1.0)
        assert agent.reached_goal

    def test_agent_boundary_clamping(self) -> None:
        """Test position clamping to world bounds."""
        agent = Agent(
            id=1,
            position=Vector3(1000, 1000, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent.clamp_position(x_min=0, x_max=500, y_min=0, y_max=500)

        assert agent.position.x == 500
        assert agent.position.y == 500
        # Velocity should bounce
        assert agent.velocity.x != 0


class TestSimulationEngine:
    """Core simulation engine tests."""

    def test_engine_initialization(self) -> None:
        """Test engine creation."""
        engine = SimulationEngine(
            num_agents=100,
            duration=60.0,
            timestep=0.016,
        )

        assert engine.num_agents == 100
        assert engine.duration == 60.0
        assert len(engine.agents) == 100

    def test_engine_step(self) -> None:
        """Test single step execution."""
        engine = SimulationEngine(
            num_agents=10,
            duration=1.0,
            timestep=0.016,
        )

        events = engine.step()

        assert len(events) > 0
        assert engine.step_count == 1
        assert engine.current_time > 0

    def test_engine_produces_events(self) -> None:
        """Test engine produces various events."""
        engine = SimulationEngine(
            num_agents=100,
            duration=60.0,
            timestep=0.016,
        )

        # Run for several steps
        for _ in range(100):
            engine.step()

        # Should have produced various events
        event_types = set(e.event_type for e in engine.events)
        assert "step_complete" in event_types

    def test_engine_collision_detection(self) -> None:
        """Test collision detection produces events."""
        engine = SimulationEngine(
            num_agents=10,
            duration=60.0,
            timestep=0.016,
        )

        # Place two agents very close
        agent1 = engine.agents[0]
        agent2 = engine.agents[1]
        agent1.position = Vector3(0, 0, 0)
        agent2.position = Vector3(0.5, 0, 0)

        engine.step()

        collisions = [e for e in engine.events if e.event_type == "collision"]
        assert len(collisions) > 0

    def test_engine_run_to_completion(self) -> None:
        """Test running entire simulation."""
        engine = SimulationEngine(
            num_agents=50,
            duration=1.0,
            timestep=0.016,
        )

        engine.run()

        assert engine.current_time >= engine.duration - 0.1
        assert engine.step_count > 50

    def test_engine_summary_statistics(self) -> None:
        """Test summary generation."""
        engine = SimulationEngine(
            num_agents=50,
            duration=1.0,
            timestep=0.016,
        )

        engine.run()
        summary = engine.get_summary()

        assert summary["total_steps"] > 0
        assert summary["agents"] == 50
        assert summary["total_events"] > 0

    def test_agent_state_retrieval(self) -> None:
        """Test getting individual agent state."""
        engine = SimulationEngine(
            num_agents=10,
            duration=1.0,
            timestep=0.016,
        )

        state = engine.get_agent_state(0)

        assert "position" in state
        assert "velocity" in state
        assert state["id"] == 0

    @pytest.mark.benchmark
    def test_engine_performance_1k_agents(self, benchmark) -> None:
        """Benchmark: 1000 agents, 1 second simulation."""

        def run_simulation():
            engine = SimulationEngine(
                num_agents=1000,
                duration=1.0,
                timestep=0.016,
            )
            engine.run()
            return len(engine.events)

        result = benchmark(run_simulation)
        assert result > 0

    @pytest.mark.benchmark
    def test_agent_physics_update_throughput(self, benchmark) -> None:
        """Benchmark: agent physics update speed."""
        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 1),
            acceleration=Vector3(0.1, 0.1, 0.1),
        )

        def update():
            agent.update_physics(dt=0.016)

        benchmark.pedantic(update, rounds=1000, iterations=10)

    @pytest.mark.benchmark
    def test_collision_detection_throughput(self, benchmark) -> None:
        """Benchmark: collision detection between 100 agents."""
        agents = [
            Agent(
                id=i,
                position=Vector3(i * 10, i * 10, 0),
                velocity=Vector3(0, 0, 0),
                acceleration=Vector3(0, 0, 0),
            )
            for i in range(100)
        ]

        def check_collisions():
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    agents[i].check_collision(agents[j])

        benchmark(check_collisions)
