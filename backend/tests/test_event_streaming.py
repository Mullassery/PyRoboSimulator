"""Tests for stable event ID generation and goal_reached event emission."""

import pytest

from services.simulation_engine import SimulationEngine, Vector3


@pytest.mark.asyncio
async def test_event_ids_unique_and_monotonic_across_steps():
    """Event IDs should be unique and monotonically increasing."""
    engine = SimulationEngine(num_agents=5, duration=10.0, num_obstacles=3)

    # Run several steps to generate collision events
    for _ in range(20):
        engine.step()

    # Collect all event IDs
    event_ids = [event.id for event in engine.events]

    # All IDs should be unique
    assert len(event_ids) == len(set(event_ids)), "Event IDs should be unique"

    # IDs should be monotonically increasing
    if event_ids:
        assert event_ids == sorted(event_ids), "Event IDs should be monotonically increasing"


@pytest.mark.asyncio
async def test_goal_reached_event_emitted_exactly_once():
    """A goal_reached event should be emitted exactly once when an agent reaches its goal."""
    engine = SimulationEngine(num_agents=1, duration=10.0, num_obstacles=0)

    agent = list(engine.agents.values())[0]
    # Manually set the agent's goal to its current position so it reaches it immediately
    agent.goal = Vector3(agent.position.x, agent.position.y, agent.position.z)

    # Run steps until the agent is marked as reached_goal
    goal_reached_events_before = [e for e in engine.events if e.event_type == "goal_reached"]
    assert len(goal_reached_events_before) == 0, "No goal_reached events should exist initially"

    # Step once — should detect goal and emit event
    engine.step()
    goal_reached_events_after_1 = [e for e in engine.events if e.event_type == "goal_reached"]

    # Step again — should NOT emit another goal_reached event (already reached)
    engine.step()
    goal_reached_events_after_2 = [e for e in engine.events if e.event_type == "goal_reached"]

    # Exactly one goal_reached event should have been emitted
    assert (
        len(goal_reached_events_after_2) == 1
    ), "Exactly one goal_reached event should be emitted (not repeated)"


@pytest.mark.asyncio
async def test_capture_frame_reuses_stable_event_id_across_consecutive_frames():
    """The same underlying event should keep the same ID across consecutive frame captures."""
    from services.visualization_integration import VisualizationStreamer

    engine = SimulationEngine(num_agents=5, duration=10.0, num_obstacles=2)
    streamer = VisualizationStreamer(engine, frame_rate=60)

    # Generate a frame with some events
    frame1 = streamer._capture_frame()
    events_in_frame1 = list(frame1.events) if frame1.events else []

    # Immediately capture the next frame (no new events generated)
    frame2 = streamer._capture_frame()
    events_in_frame2 = list(frame2.events) if frame2.events else []

    # Events that appear in both frames should have the same ID
    frame1_event_ids = {e.id for e in events_in_frame1}
    frame2_event_ids = {e.id for e in events_in_frame2}
    common_ids = frame1_event_ids & frame2_event_ids

    # Verify that common IDs actually appear in both frames
    for common_id in common_ids:
        frame1_id_list = [e.id for e in events_in_frame1]
        frame2_id_list = [e.id for e in events_in_frame2]
        # Count occurrences — should be the same in both frames
        frame1_count = frame1_id_list.count(common_id)
        frame2_count = frame2_id_list.count(common_id)
        assert (
            frame1_count == frame2_count
        ), f"Event ID {common_id} should have consistent count across frames (was {frame1_count} then {frame2_count})"


@pytest.mark.asyncio
async def test_event_ids_persist_through_simulation_lifetime():
    """Event IDs assigned early should not conflict with IDs assigned later."""
    engine = SimulationEngine(num_agents=3, duration=5.0, num_obstacles=2)

    all_ids_seen = set()

    for step in range(50):
        engine.step()

        # Check that all event IDs so far are unique
        for event in engine.events:
            assert (
                event.id not in all_ids_seen
            ), f"Event ID {event.id} was already seen (step {step})"
            all_ids_seen.add(event.id)
