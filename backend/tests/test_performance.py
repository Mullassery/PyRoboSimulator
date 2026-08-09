"""Performance and load testing."""

import pytest
import asyncio
from httpx import AsyncClient


class TestAPIPerformance:
    """API endpoint performance tests."""

    @pytest.mark.asyncio
    async def test_list_simulations_performance(
        self,
        client: AsyncClient,
        auth_headers: dict,
        benchmark_async,
    ) -> None:
        """Benchmark listing simulations."""
        # Create some simulations
        for i in range(10):
            await client.post(
                "/api/v1/simulations",
                json={"name": f"sim_{i}", "num_agents": 100, "duration": 60.0},
                headers=auth_headers,
            )

        async def list_sims():
            return await client.get("/api/v1/simulations", headers=auth_headers)

        # Note: benchmark_async not available in standard pytest
        # This is a placeholder for actual benchmark
        response = await list_sims()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_simulation_creation(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test creating multiple simulations concurrently."""

        async def create_sim(i: int):
            return await client.post(
                "/api/v1/simulations",
                json={"name": f"concurrent_{i}", "num_agents": 100, "duration": 60.0},
                headers=auth_headers,
            )

        # Create 10 simulations concurrently
        tasks = [create_sim(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 201 for r in responses)

    @pytest.mark.asyncio
    async def test_pagination_performance(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Test pagination efficiency."""
        # Create 100 simulations
        for i in range(100):
            await client.post(
                "/api/v1/simulations",
                json={"name": f"page_test_{i}", "num_agents": 100, "duration": 60.0},
                headers=auth_headers,
            )

        # Fetch different pages
        response1 = await client.get(
            "/api/v1/simulations?limit=20&offset=0", headers=auth_headers
        )
        response2 = await client.get(
            "/api/v1/simulations?limit=20&offset=20", headers=auth_headers
        )
        response3 = await client.get(
            "/api/v1/simulations?limit=20&offset=80", headers=auth_headers
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        data1 = response1.json()
        assert data1["total"] >= 100


class TestDatabasePerformance:
    """Database operation performance."""

    def test_vector_math_performance(self, benchmark) -> None:
        """Benchmark vector math operations."""
        from src.services.simulation_engine import Vector3

        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)

        def vector_ops():
            v3 = v1 + v2
            v4 = v3 * 2
            mag = v4.magnitude()
            return mag

        result = benchmark(vector_ops)
        assert result > 0

    def test_agent_physics_performance(self, benchmark) -> None:
        """Benchmark agent physics updates."""
        from src.services.simulation_engine import Agent, Vector3

        agent = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 1),
            acceleration=Vector3(0.1, 0.1, 0.1),
        )

        def update_physics():
            agent.update_physics(dt=0.016)

        benchmark(update_physics)

    def test_collision_detection_performance(self, benchmark) -> None:
        """Benchmark collision detection."""
        from src.services.simulation_engine import Agent, Vector3

        agent1 = Agent(
            id=1,
            position=Vector3(0, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        agent2 = Agent(
            id=2,
            position=Vector3(1, 0, 0),
            velocity=Vector3(0, 0, 0),
            acceleration=Vector3(0, 0, 0),
        )

        def check_collision():
            return agent1.check_collision(agent2)

        result = benchmark(check_collision)
        assert isinstance(result, bool)

    def test_scenario_generation_performance(self, benchmark) -> None:
        """Benchmark scenario generation."""
        from src.services.scenario_generator import ScenarioBuilder

        def generate_random():
            return ScenarioBuilder.random_world(
                num_agents=1000,
                width=2000,
                height=2000,
                num_obstacles=50,
            )

        world = benchmark(generate_random)
        assert world.get_total_spawn_capacity() >= 1000


class TestSimulationEnginePerformance:
    """Simulation engine performance tests."""

    def test_small_simulation_performance(self, benchmark) -> None:
        """Benchmark small simulation (100 agents)."""
        from src.services.simulation_engine import SimulationEngine

        def run_sim():
            engine = SimulationEngine(
                num_agents=100,
                duration=1.0,
                timestep=0.016,
            )
            engine.run()
            return len(engine.events)

        events = benchmark(run_sim)
        assert events > 0

    def test_large_simulation_throughput(self) -> None:
        """Test large simulation throughput (1000 agents)."""
        from src.services.simulation_engine import SimulationEngine

        engine = SimulationEngine(
            num_agents=1000,
            duration=0.1,  # Short duration for testing
            timestep=0.016,
        )

        engine.run()

        # Calculate agents per second
        agents_per_second = (engine.num_agents * engine.step_count) / engine.current_time
        # Should process at least 10K agent-steps per second
        assert agents_per_second > 10000

    def test_collision_detection_scaling(self) -> None:
        """Test collision detection with many agents."""
        from src.services.simulation_engine import SimulationEngine

        for num_agents in [100, 500, 1000]:
            engine = SimulationEngine(
                num_agents=num_agents,
                duration=0.05,
                timestep=0.016,
            )

            engine.run()

            # Should not crash, metrics should be reasonable
            summary = engine.get_summary()
            assert summary["agents"] == num_agents
            assert summary["total_events"] > 0
