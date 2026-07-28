"""Results and events streaming endpoints."""

from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.models import EventBatch, EventResponse, EventType, SimulationSummary

router = APIRouter(prefix="/simulations", tags=["Results"])

# In-memory event storage for demo (Task #11 will use database)
events_db: dict[int, list[dict]] = {}


@router.get("/{sim_id}/results", response_model=EventBatch)
async def get_results(
    sim_id: int,
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
) -> EventBatch:
    """Fetch simulation results (events).

    Query parameters:
    - agent_id: Filter events by agent ID
    - event_type: Filter by event type
    - limit: Results per page (1-10000, default 100)
    - offset: Skip N results

    Returns:
        Paginated list of events from simulation
    """
    if sim_id not in events_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    all_events = events_db[sim_id]

    # Apply filters
    filtered = all_events
    if agent_id is not None:
        filtered = [e for e in filtered if e.get("agent_id") == agent_id]
    if event_type:
        filtered = [e for e in filtered if e["event_type"] == event_type]

    # Sort by timestamp
    filtered = sorted(filtered, key=lambda e: e["timestamp"])

    total = len(filtered)
    events = filtered[offset : offset + limit]

    return EventBatch(
        events=[EventResponse(**e) for e in events],
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
    )


@router.get("/{sim_id}/agents", response_model=list[dict])
async def get_agents(sim_id: int) -> list[dict]:
    """Get final agent positions and states.

    Returns:
        List of agents with final positions and velocities
    """
    if sim_id not in events_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # For demo, return empty list
    # Task #11 will fetch from agents table
    return []


@router.get("/{sim_id}/summary", response_model=SimulationSummary)
async def get_summary(sim_id: int) -> SimulationSummary:
    """Get aggregate statistics for simulation.

    Returns:
        Summary with total events, collisions, goals reached, etc.
    """
    if sim_id not in events_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    events = events_db[sim_id]

    # Calculate summary stats
    collisions = sum(1 for e in events if e["event_type"] == "collision")
    goals_reached = sum(1 for e in events if e["event_type"] == "goal_reached")
    max_timestamp = max((e["timestamp"] for e in events), default=0.0)

    return SimulationSummary(
        simulation_id=sim_id,
        total_events=len(events),
        total_collisions=collisions,
        goals_reached=goals_reached,
        simulation_duration=max_timestamp,
        average_agent_velocity=1.5,
    )


@router.get("/{sim_id}/stream")
async def stream_results(
    sim_id: int,
    agent_id: Optional[int] = Query(None),
) -> StreamingResponse:
    """Stream simulation events in real-time (Server-Sent Events).

    Query parameters:
    - agent_id: Filter events by agent ID

    Returns:
        SSE stream of events with Content-Type: text/event-stream
    """
    if sim_id not in events_db:
        raise HTTPException(status_code=404, detail="Simulation not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events from simulation."""
        events = events_db[sim_id]

        # Filter by agent if specified
        if agent_id is not None:
            events = [e for e in events if e.get("agent_id") == agent_id]

        for event in events:
            # SSE format: "data: {json}\n\n"
            import json

            event_json = json.dumps(event)
            yield f"data: {event_json}\n\n"

            # Add a keepalive comment every 5 events
            if events.index(event) % 5 == 0:
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
