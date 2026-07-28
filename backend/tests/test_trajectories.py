"""Tests for trajectory visualization functionality."""

import pytest

from services.simulation_engine import SimulationEngine, Vector3
from services.frame_streaming import AgentFrame, WorldFrame
from services.visualization_integration import VisualizationStreamer


class TestAgentTrajectory:
    """Test agent trajectory tracking."""

    def test_agent_trajectory_initialized(self):
        """Test that agents have trajectory tracking."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for agent in engine.agents.values():
            assert hasattr(agent, "trajectory")
            assert isinstance(agent.trajectory, list)
            assert len(agent.trajectory) == 0

    def test_trajectory_recorded_after_step(self):
        """Test that positions are recorded after each step."""
        engine = SimulationEngine(
            num_agents=1,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        agent = engine.agents[0]
        initial_pos = (agent.position.x, agent.position.y)

        engine.step()

        assert len(agent.trajectory) == 1
        assert agent.trajectory[0] == initial_pos

    def test_trajectory_accumulates(self):
        """Test that trajectory accumulates over multiple steps."""
        engine = SimulationEngine(
            num_agents=1,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        agent = engine.agents[0]

        for i in range(5):
            engine.step()

        assert len(agent.trajectory) == 5

    def test_trajectory_contains_xy_positions(self):
        """Test that trajectory contains (x, y) tuples."""
        engine = SimulationEngine(
            num_agents=1,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        agent = engine.agents[0]

        for _ in range(3):
            engine.step()

        for pos in agent.trajectory:
            assert isinstance(pos, tuple)
            assert len(pos) == 2
            assert isinstance(pos[0], (int, float))
            assert isinstance(pos[1], (int, float))

    def test_get_agent_trajectory(self):
        """Test getting trajectory for specific agent."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(3):
            engine.step()

        traj = engine.get_agent_trajectory(0)
        assert len(traj) == 3
        assert all(isinstance(pos, tuple) for pos in traj)

    def test_get_agent_trajectory_invalid_id(self):
        """Test getting trajectory for invalid agent."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        traj = engine.get_agent_trajectory(999)
        assert traj == []

    def test_get_all_agent_trajectories(self):
        """Test getting trajectories for all agents."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(5):
            engine.step()

        all_trajs = engine.get_all_agent_trajectories()
        assert len(all_trajs) == 3
        for agent_id in range(3):
            assert agent_id in all_trajs
            assert len(all_trajs[agent_id]) == 5

    def test_trajectory_max_points_limit(self):
        """Test that max_points parameter limits trajectory size."""
        engine = SimulationEngine(
            num_agents=1,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(20):
            engine.step()

        traj = engine.get_agent_trajectory(0, max_points=10)
        assert len(traj) == 10
        assert traj == engine.agents[0].trajectory[-10:]

    def test_all_trajectories_max_points_limit(self):
        """Test max_points in get_all_agent_trajectories."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(15):
            engine.step()

        all_trajs = engine.get_all_agent_trajectories(max_points=8)
        for agent_id in range(2):
            assert len(all_trajs[agent_id]) == 8


class TestTrajectoryFrameStreaming:
    """Test trajectories in frame streaming."""

    def test_agent_frame_trajectory_optional(self):
        """Test that AgentFrame trajectory is optional."""
        agent_frame = AgentFrame(
            id=0,
            position=Vector3(100, 100, 0),
            rotation=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 0),
            state="moving",
        )

        assert agent_frame.trajectory is None

    def test_agent_frame_with_trajectory(self):
        """Test AgentFrame with trajectory data."""
        traj = [[100, 100], [101, 101], [102, 102]]
        agent_frame = AgentFrame(
            id=0,
            position=Vector3(102, 102, 0),
            rotation=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 0),
            state="moving",
            trajectory=traj,
        )

        assert agent_frame.trajectory == traj

    def test_agent_frame_serialization_with_trajectory(self):
        """Test AgentFrame serialization includes trajectory."""
        traj = [[100, 100], [101, 101], [102, 102]]
        agent_frame = AgentFrame(
            id=0,
            position=Vector3(102, 102, 0),
            rotation=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 0),
            state="moving",
            trajectory=traj,
        )

        frame_dict = agent_frame.to_dict()
        assert "traj" in frame_dict
        assert frame_dict["traj"] == traj

    def test_agent_frame_serialization_without_trajectory(self):
        """Test AgentFrame serialization without trajectory."""
        agent_frame = AgentFrame(
            id=0,
            position=Vector3(100, 100, 0),
            rotation=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 0),
            state="moving",
        )

        frame_dict = agent_frame.to_dict()
        assert "traj" not in frame_dict

    def test_world_frame_with_trajectories(self):
        """Test WorldFrame with agent trajectories."""
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 1, 0),
                state="moving",
                trajectory=[[100, 100], [101, 101]],
            ),
            AgentFrame(
                id=1,
                position=Vector3(200, 200, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 1, 0),
                state="moving",
                trajectory=[[200, 200], [201, 201]],
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
        )

        frame_dict = frame.to_dict()
        assert frame_dict["agents"][0]["traj"] == [[100, 100], [101, 101]]
        assert frame_dict["agents"][1]["traj"] == [[200, 200], [201, 201]]


class TestVisualizationStreamerTrajectories:
    """Test trajectories in VisualizationStreamer."""

    def test_streamer_includes_trajectories(self):
        """Test that VisualizationStreamer includes trajectories in frames."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        streamer = VisualizationStreamer(engine, simulation_id=1)

        for _ in range(5):
            engine.step()

        frame = streamer._capture_frame()

        assert len(frame.agents) == 2
        for agent_frame in frame.agents:
            assert agent_frame.trajectory is not None
            assert len(agent_frame.trajectory) == 5

    def test_trajectory_max_points_in_streamer(self):
        """Test that VisualizationStreamer respects max_points."""
        engine = SimulationEngine(
            num_agents=1,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        streamer = VisualizationStreamer(engine, simulation_id=1)

        for _ in range(20):
            engine.step()

        frame = streamer._capture_frame()

        agent_frame = frame.agents[0]
        assert agent_frame.trajectory is not None
        assert len(agent_frame.trajectory) <= 100

    def test_trajectory_msgpack_serialization(self):
        """Test that trajectories serialize in MessagePack."""
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 1, 0),
                state="moving",
                trajectory=[[100 + i, 100 + i] for i in range(5)],
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
        )

        msgpack_bytes = frame.to_msgpack()
        assert len(msgpack_bytes) > 0
        assert isinstance(msgpack_bytes, bytes)


class TestTrajectoryPerformance:
    """Test trajectory performance."""

    def test_trajectory_recording_overhead(self):
        """Test that trajectory recording doesn't significantly impact performance."""
        import time

        engine = SimulationEngine(
            num_agents=100,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        start = time.time()
        for _ in range(10):
            engine.step()
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should be reasonably fast

    def test_large_trajectory_retrieval(self):
        """Test retrieving large trajectories."""
        import time

        engine = SimulationEngine(
            num_agents=10,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(100):
            engine.step()

        start = time.time()
        all_trajs = engine.get_all_agent_trajectories(max_points=500)
        elapsed = time.time() - start

        assert len(all_trajs) == 10
        assert elapsed < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
