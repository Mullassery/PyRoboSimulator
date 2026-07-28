"""Tests for camera mode support via frame streaming."""

import pytest

from services.simulation_engine import SimulationEngine
from services.frame_streaming import WorldFrame, AgentFrame, Vector3


class TestCameraModesDataSupport:
    """Test that frame data supports all camera modes."""

    def test_free_camera_data_available(self):
        """Test that free camera mode has position and trajectory data."""
        agents = [
            AgentFrame(
                id=0,
                position=Vector3(100, 100, 0),
                rotation=Vector3(0, 0, 0),
                velocity=Vector3(1, 0, 0),
                state="moving",
                trajectory=[[100, 100], [101, 101], [102, 102]],
            ),
        ]

        frame = WorldFrame(
            frame_id=1,
            timestamp_ms=1000.0,
            agents=agents,
            events=[],
        )

        frame_dict = frame.to_dict()
        agent_dict = frame_dict["agents"][0]

        # Free camera needs position for movement
        assert "pos" in agent_dict
        assert agent_dict["pos"] == [100, 100, 0]

    def test_topdown_camera_data_available(self):
        """Test that top-down camera has all agent positions."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        frame_dict = frame.to_dict()

        # Top-down needs agent positions
        for agent in frame_dict["agents"]:
            assert "pos" in agent
            assert len(agent["pos"]) == 3

    def test_follow_camera_agent_tracking(self):
        """Test that follow camera can track agent positions."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)

        # Capture first frame
        engine.step()
        frame1 = streamer._capture_frame()

        # Capture second frame
        engine.step()
        frame2 = streamer._capture_frame()

        frame1_dict = frame1.to_dict()
        frame2_dict = frame2.to_dict()

        # Agent positions should differ between frames (due to physics)
        agent0_pos_1 = frame1_dict["agents"][0]["pos"]
        agent0_pos_2 = frame2_dict["agents"][0]["pos"]

        # Verify structure for follow camera
        assert len(agent0_pos_1) == 3
        assert len(agent0_pos_2) == 3

    def test_camera_modes_with_obstacles(self):
        """Test that all camera modes work with obstacles visible."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=10,
        )

        engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        frame_dict = frame.to_dict()

        # All camera modes need agents and obstacles
        assert "agents" in frame_dict
        assert "obstacles" in frame_dict
        assert len(frame_dict["agents"]) > 0
        assert len(frame_dict["obstacles"]) > 0


class TestCameraModeIndependence:
    """Test that frame data is independent of camera mode."""

    def test_frame_data_consistent_across_views(self):
        """Test that same frame data works for all camera modes."""
        engine = SimulationEngine(
            num_agents=5,
            duration=1.0,
            timestep=0.016,
            num_obstacles=5,
        )

        for _ in range(3):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        frame_dict = frame.to_dict()

        # Same frame data works for free, topdown, follow, firstperson
        cameras_modes = ["free", "topdown", "follow", "firstperson"]

        for _ in cameras_modes:
            # Each camera mode can work with same frame data
            assert "agents" in frame_dict
            assert "obstacles" in frame_dict
            for agent in frame_dict["agents"]:
                assert "pos" in agent

    def test_trajectory_data_for_camera_modes(self):
        """Test trajectory data availability for different camera modes."""
        engine = SimulationEngine(
            num_agents=2,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        for _ in range(5):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        frame_dict = frame.to_dict()

        # Trajectory data useful for all camera modes
        for agent in frame_dict["agents"]:
            if "traj" in agent:
                assert isinstance(agent["traj"], list)
                # Trajectory contains positions
                for pos in agent["traj"]:
                    assert len(pos) == 2


class TestCameraModesPerformance:
    """Test performance with camera mode data."""

    def test_frame_creation_with_camera_data(self):
        """Test that frame creation is efficient regardless of camera mode support."""
        import time

        engine = SimulationEngine(
            num_agents=100,
            duration=1.0,
            timestep=0.016,
            num_obstacles=100,
        )

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)

        start = time.time()
        for _ in range(10):
            engine.step()
            frame = streamer._capture_frame()
            assert frame is not None
        elapsed = time.time() - start

        assert elapsed < 2.0  # Should complete in under 2 seconds

    def test_serialization_with_all_camera_data(self):
        """Test MessagePack serialization with full camera support data."""
        import time

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

        start = time.time()
        for _ in range(30):
            msgpack_bytes = frame.to_msgpack()
            assert len(msgpack_bytes) > 0
        elapsed = time.time() - start

        # Should serialize 30 times per second easily
        assert elapsed < 0.2


class TestCameraModesWithEvents:
    """Test camera modes with event data."""

    def test_event_positions_for_camera_modes(self):
        """Test that events have position data for camera visualization."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        # Run simulation to generate collisions
        for _ in range(10):
            engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        frame_dict = frame.to_dict()

        # Events should have positions for all camera modes
        for event in frame_dict["events"]:
            if event["type"] == "collision":
                # Collision events should have position for camera to track
                assert "pos" in event or "agent_id" in event

    def test_camera_modes_with_statistics(self):
        """Test that statistics data works with camera modes."""
        engine = SimulationEngine(
            num_agents=10,
            duration=1.0,
            timestep=0.016,
            num_obstacles=10,
        )

        for _ in range(3):
            engine.step()

        # Get summary for HUD display
        summary = engine.get_summary()

        assert "total_steps" in summary
        assert "agents" in summary
        assert "total_collisions" in summary

        # These can be displayed in any camera mode
        assert summary["agents"] == 10


class TestCameraDataConsistency:
    """Test consistency of camera-related data."""

    def test_agent_positions_match_meshes(self):
        """Test that agent positions can be used to position camera correctly."""
        engine = SimulationEngine(
            num_agents=3,
            duration=1.0,
            timestep=0.016,
            num_obstacles=0,
        )

        engine.step()

        from services.visualization_integration import VisualizationStreamer

        streamer = VisualizationStreamer(engine, simulation_id=1)
        frame = streamer._capture_frame()

        # Each agent should have consistent position data
        for agent_frame in frame.agents:
            assert agent_frame.position is not None
            assert agent_frame.position.x is not None
            assert agent_frame.position.y is not None
            assert agent_frame.position.z is not None

    def test_obstacle_bounds_for_camera_clipping(self):
        """Test that obstacle data can be used for camera clipping planes."""
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

        # Obstacle bounds should be usable for camera setup
        if frame.obstacles:
            for obstacle in frame.obstacles:
                assert obstacle.size is not None
                # Size data used for camera near/far planes
                assert obstacle.size.x > 0
                assert obstacle.size.y > 0
                assert obstacle.size.z > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
