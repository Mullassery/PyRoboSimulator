"""Tests for environment filtering and layer visibility."""

import pytest

from services.simulation_engine import SimulationEngine
from services.frame_streaming import WorldFrame, AgentFrame, Vector3


class TestEnvironmentFiltering:
    """Test environment layer filtering."""

    def test_frame_includes_all_data_for_filtering(self):
        """Test that WorldFrame includes all necessary data for client-side filtering."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        engine.step()

        # Simulate frame capture
        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        # Check that frame has all necessary data
        assert len(frame.agents) > 0
        assert frame.obstacles is not None
        assert len(frame.obstacles) > 0

        # Check agent data
        for agent_frame in frame.agents:
            assert agent_frame.id is not None
            assert agent_frame.position is not None
            assert agent_frame.state is not None
            assert agent_frame.trajectory is not None

    def test_frame_serialization_preserves_visibility_data(self):
        """Test that serialized frames preserve all visibility-relevant data."""
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 0, 0),
                state="moving",
                trajectory=[[100, 100], [101, 101]],
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
            obstacles=[],
        )

        frame_dict = frame.to_dict()

        # Verify structure for client-side filtering
        assert "agents" in frame_dict
        assert "obstacles" in frame_dict
        assert len(frame_dict["agents"]) > 0
        assert "pos" in frame_dict["agents"][0]
        assert "state" in frame_dict["agents"][0]
        assert "traj" in frame_dict["agents"][0]

    def test_msgpack_supports_filtered_rendering(self):
        """Test that MessagePack serialization is efficient for filtered rendering."""
        engine = SimulationEngine(
            num_agents=10,
            duration=1.0,
            timestep=0.016,
            num_obstacles=20,
        )

        for _ in range(3):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()
        msgpack_bytes = frame.to_msgpack()

        # Verify serialization is compact
        assert len(msgpack_bytes) > 0
        assert isinstance(msgpack_bytes, bytes)

    def test_obstacle_visibility_data_in_frame(self):
        """Test that obstacles provide sufficient data for visibility control."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        assert frame.obstacles is not None
        for obstacle in frame.obstacles:
            assert obstacle.id is not None
            assert obstacle.position is not None
            assert obstacle.size is not None
            assert obstacle.obstacle_type is not None


class TestLayerDataStructures:
    """Test data structures for layer filtering."""

    def test_agent_state_for_visibility(self):
        """Test that agent state enables color-coded visibility."""
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 0, 0),
                state="moving",
            ),
            AgentFrame(
                id=1,
                position=Vector3(200, 200, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(0, 0, 0),
                state="idle",
            ),
            AgentFrame(
                id=2,
                position=Vector3(300, 300, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(0, 0, 0),
                state="goal_reached",
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
        )

        frame_dict = frame.to_dict()
        states = [agent["state"] for agent in frame_dict["agents"]]

        assert "moving" in states
        assert "idle" in states
        assert "goal_reached" in states

    def test_trajectory_data_for_trail_rendering(self):
        """Test that trajectory data enables efficient trail rendering."""
        trajectory = [[100 + i, 100 + i] for i in range(10)]
        agent = AgentFrame(
            id=0,
            position=Vector3(110, 110, 0),
            rotation=Vector3(0, 0, 0),
            velocity=Vector3(1, 1, 0),
            state="moving",
            trajectory=trajectory,
        )

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[agent],
            events=[],
        )

        frame_dict = frame.to_dict()
        agent_dict = frame_dict["agents"][0]

        assert "traj" in agent_dict
        assert len(agent_dict["traj"]) == 10
        assert agent_dict["traj"][0] == [100, 100]
        assert agent_dict["traj"][-1] == [109, 109]

    def test_obstacle_type_for_styled_rendering(self):
        """Test that obstacle type enables styled rendering."""
        from services.frame_streaming import Obstacle

        obstacles = [
            Obstacle(
                id=0,
                position=Vector3(100, 100, 0),
                size=Vector3(50, 50, 5),
                obstacle_type="wall",
            ),
            Obstacle(
                id=1,
                position=Vector3(200, 200, 0),
                size=Vector3(30, 30, 5),
                obstacle_type="wall",
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=[],
            events=[],
            obstacles=obstacles,
        )

        frame_dict = frame.to_dict()

        for obs_dict in frame_dict["obstacles"]:
            assert "type" in obs_dict
            assert obs_dict["type"] == "wall"


class TestPerformanceWithFiltering:
    """Test performance implications of filtering."""

    def test_frame_size_with_full_data(self):
        """Test frame size when including all data for filtering."""
        import sys

        engine = SimulationEngine(
            num_agents=50,
            duration=1.0,
            timestep=0.016,
            num_obstacles=50,
        )

        for _ in range(5):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()
        msgpack_bytes = frame.to_msgpack()

        # Verify frame size is reasonable
        frame_size_kb = len(msgpack_bytes) / 1024
        assert frame_size_kb < 500  # Should be under 500 KB

    def test_multiple_frames_with_filtering_data(self):
        """Test that multiple frames with filtering data are manageable."""
        import time

        engine = SimulationEngine(
            num_agents=20,
            duration=1.0,
            timestep=0.016,
            num_obstacles=30,
        )

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)

        start = time.time()
        for _ in range(30):
            engine.step()
            frame = streamer._capture_frame()
            msgpack_bytes = frame.to_msgpack()
            assert len(msgpack_bytes) > 0

        elapsed = time.time() - start
        assert elapsed < 5.0  # 30 frames in under 5 seconds


class TestFilteringDataCompleteness:
    """Test that filtering data is complete for all use cases."""

    def test_visibility_toggle_requires_no_backend_changes(self):
        """Test that visibility toggling is purely client-side."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)

        engine.step()
        frame1 = streamer._capture_frame()

        engine.step()
        frame2 = streamer._capture_frame()

        # Verify same structure for client-side filtering
        frame1_dict = frame1.to_dict()
        frame2_dict = frame2.to_dict()

        assert len(frame1_dict["agents"]) == len(frame2_dict["agents"])
        assert len(frame1_dict["obstacles"]) == len(frame2_dict["obstacles"])

    def test_all_layers_have_required_data(self):
        """Test that all layers have data needed for visibility control."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=3,
        )

        for _ in range(2):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()
        frame_dict = frame.to_dict()

        # Agents layer
        assert len(frame_dict["agents"]) == 3
        for agent in frame_dict["agents"]:
            assert "pos" in agent  # Position for rendering
            assert "id" in agent  # Identity for tracking

        # Obstacles layer
        assert len(frame_dict["obstacles"]) == 3
        for obs in frame_dict["obstacles"]:
            assert "pos" in obs  # Position for rendering
            assert "id" in obs  # Identity for tracking

    def test_filtering_works_for_zero_agents_or_obstacles(self):
        """Test filtering works gracefully with no agents or obstacles."""
        from services.frame_streaming import Obstacle

        # Frame with agents but no obstacles
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 0, 0),
                state="moving",
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
            obstacles=[],
        )

        frame_dict = frame.to_dict()
        assert len(frame_dict["agents"]) == 1
        assert len(frame_dict["obstacles"]) == 0

        # Frame with no agents but obstacles
        obstacles = [
            Obstacle(
                id=0,
                position=Vector3(100, 100, 0),
                size=Vector3(50, 50, 5),
            ),
        ]

        frame2 = WorldFrame(
            frame_id=2,
            timestamp_ms=2000.0,
            agents=[],
            events=[],
            obstacles=obstacles,
        )

        frame2_dict = frame2.to_dict()
        assert len(frame2_dict["agents"]) == 0
        assert len(frame2_dict["obstacles"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
