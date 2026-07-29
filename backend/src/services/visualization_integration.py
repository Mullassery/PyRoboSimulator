"""Integration between SimulationEngine and real-time visualization."""

import asyncio
import time
from typing import List, Optional

from services.frame_streaming import (
    AgentFrame,
    EventFrame,
    Obstacle,
    SensorData,
    Vector3,
    WorldFrame,
)
from services.simulation_engine import SimulationEngine


class VisualizationStreamer:
    """Streams simulation frames to connected clients in real-time."""

    def __init__(self, simulation_engine: SimulationEngine, simulation_id: int):
        """Initialize streamer.

        Args:
            simulation_engine: Running simulation engine
            simulation_id: Simulation ID for tracking
        """
        self.engine = simulation_engine
        self.simulation_id = simulation_id
        self.frame_id = 0
        self.start_time = time.time()
        self.broadcast_callback = None
        self.frame_rate = 60  # Target 60 FPS

    def set_broadcast_callback(self, callback):
        """Set callback for broadcasting frames.

        Args:
            callback: Async function(simulation_id, frame) to broadcast frame
        """
        self.broadcast_callback = callback

    async def stream_simulation(self) -> None:
        """Main streaming loop - run during simulation.

        Capture engine state and broadcast frames at target frame rate.
        """
        frame_interval = 1.0 / self.frame_rate
        last_frame_time = time.time()

        while self.engine.is_running or len(self.engine.events) > 0:
            current_time = time.time()
            elapsed = current_time - last_frame_time

            if elapsed >= frame_interval:
                # Capture and broadcast frame
                frame = self._capture_frame()
                if self.broadcast_callback:
                    await self.broadcast_callback(self.simulation_id, frame)

                self.frame_id += 1
                last_frame_time = current_time
            else:
                # Sleep until next frame
                await asyncio.sleep(frame_interval - elapsed)

    def _capture_frame(self) -> WorldFrame:
        """Capture current simulation state as frame.

        Returns:
            WorldFrame with agent positions, events, and sensor data
        """
        # Capture agent states and trajectories
        agent_frames = []
        trajectories = self.engine.get_all_agent_trajectories(max_points=100)

        for agent in self.engine.agents.values():
            agent_frame = AgentFrame(
                id=agent.id,
                position=Vector3(agent.position.x, agent.position.y, 0.0),
                rotation=Vector3(0.0, 0.0, 0.0),
                velocity=Vector3(agent.velocity.x, agent.velocity.y, 0.0),
                state=agent.state,
                trajectory=trajectories.get(agent.id),
            )
            agent_frames.append(agent_frame)

        # Capture recent events
        event_frames = []
        for event in self.engine.events[-10:]:  # Last 10 events only
            agent_id = event.agent_ids[0] if event.agent_ids else -1
            event_pos_data = event.data.get("position", {"x": 0, "y": 0}) if event.data else {"x": 0, "y": 0}
            event_frame = EventFrame(
                id=event.id,
                type=event.event_type,
                agent_id=agent_id,
                position=Vector3(event_pos_data.get("x", 0), event_pos_data.get("y", 0), 0.0),
                timestamp_ms=event.timestamp * 1000,
                data=event.data,
            )
            event_frames.append(event_frame)

        # Capture sensor data (optional, computationally expensive)
        sensors = None
        if False:  # Disabled by default (can be toggled)
            sensors = self._capture_sensors()

        # Capture obstacles
        obstacles = []
        for obs_dict in self.engine.get_obstacles():
            obstacles.append(
                Obstacle(
                    id=obs_dict["id"],
                    position=Vector3(
                        obs_dict["position"]["x"],
                        obs_dict["position"]["y"],
                        obs_dict["position"]["z"],
                    ),
                    size=Vector3(
                        obs_dict["size"]["x"],
                        obs_dict["size"]["y"],
                        obs_dict["size"]["z"],
                    ),
                    obstacle_type=obs_dict.get("type", "wall"),
                )
            )

        # Create frame
        timestamp_ms = (time.time() - self.start_time) * 1000
        return WorldFrame(
            frame_id=self.frame_id,
            timestamp_ms=timestamp_ms,
            agents=agent_frames,
            events=event_frames,
            sensors=sensors,
            obstacles=obstacles if obstacles else None,
        )

    def _capture_sensors(self) -> Optional[dict]:
        """Capture sensor data for all agents.

        Returns:
            Dictionary mapping agent_id to SensorData
        """
        sensors = {}

        # Capture sensor frames from all agents
        rgb_frames = self.engine.get_all_agents_rgb_frames()
        depth_maps = self.engine.get_all_agents_depth_maps()
        lidar_clouds = self.engine.get_all_agents_lidar_clouds()
        thermal_images = self.engine.get_all_agents_thermal_images()

        for agent_id, agent in self.engine.agents.items():
            # Get sensor manager if available
            sensor_data_dict = {}

            if hasattr(agent, "sensors"):
                sensor_data = agent.sensors.get_all_sensor_readings()
                sensor_data_dict = sensor_data

            # Get RGB, depth, lidar, and thermal
            rgb_base64 = rgb_frames.get(agent_id)
            depth_base64 = depth_maps.get(agent_id)
            lidar_cloud = lidar_clouds.get(agent_id)
            thermal_base64 = thermal_images.get(agent_id)

            sensors[agent_id] = SensorData(
                rgb=rgb_base64,  # Already base64 string
                depth=depth_base64,  # Already base64 string
                lidar=lidar_cloud,  # List of [x, y, z] points
                thermal=thermal_base64 or sensor_data_dict.get("thermal"),
            )

        return sensors if sensors else None


async def create_streaming_simulation(
    engine: SimulationEngine,
    simulation_id: int,
    broadcast_callback,
) -> VisualizationStreamer:
    """Create a simulation with real-time streaming.

    Args:
        engine: Simulation engine
        simulation_id: Simulation ID
        broadcast_callback: Async callback for frame broadcasting

    Returns:
        VisualizationStreamer instance
    """
    streamer = VisualizationStreamer(engine, simulation_id)
    streamer.set_broadcast_callback(broadcast_callback)
    return streamer
