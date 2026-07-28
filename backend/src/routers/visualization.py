"""Real-time visualization WebSocket endpoints."""

import asyncio
import json
import logging
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocketDisconnect, WebSocketException, status
from fastapi.websockets import WebSocket

from services.frame_streaming import (
    AgentFrame,
    ControlCommand,
    EventFrame,
    FrameBuffer,
    SensorData,
    Vector3,
    WorldFrame,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Global state for connected clients
connected_clients: Dict[int, Set[WebSocket]] = {}
frame_buffers: Dict[int, FrameBuffer] = {}
simulation_states: Dict[int, Dict] = {}  # simulation_id -> state


@router.websocket("/ws/simulations/{simulation_id}/stream")
async def websocket_stream(websocket: WebSocket, simulation_id: int):
    """WebSocket endpoint for real-time simulation streaming.

    Client connects and receives a continuous stream of WorldFrame messages
    encoded as MessagePack binary data.

    Message format:
    {
        "type": "frame",
        "frame_id": int,
        "timestamp_ms": float,
        "agents": [
            {
                "id": int,
                "pos": [x, y, z],
                "rot": [rx, ry, rz],
                "vel": [vx, vy, vz],
                "state": "moving|idle|goal_reached|collision"
            }
        ],
        "events": [
            {
                "id": int,
                "type": "collision|goal_reached",
                "agent_id": int,
                "pos": [x, y, z],
                "data": {...}
            }
        ],
        "sensors": {
            "1": {
                "rgb": "base64:...",
                "depth": "base64:...",
                "lidar": [[x,y,z], ...],
                "thermal": "base64:..."
            }
        }
    }
    """
    await websocket.accept()

    # Track client connection
    if simulation_id not in connected_clients:
        connected_clients[simulation_id] = set()
        frame_buffers[simulation_id] = FrameBuffer()
        simulation_states[simulation_id] = {
            "playing": True,
            "speed": 1.0,
            "camera": "free",
        }

    connected_clients[simulation_id].add(websocket)
    logger.info(f"Client connected to simulation {simulation_id}")

    try:
        last_received_frame_id = -1

        while True:
            # Check for control messages from client
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                command = ControlCommand.from_dict(json.loads(data))
                await handle_control_command(simulation_id, command)
            except asyncio.TimeoutError:
                pass  # No message available, continue
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")
                continue

            # Send buffered frames to client
            buffer = frame_buffers[simulation_id]
            new_frames = buffer.get_frames_since(last_received_frame_id)

            for frame in new_frames:
                try:
                    # Send as MessagePack binary for efficiency
                    await websocket.send_bytes(frame.to_msgpack())
                    last_received_frame_id = frame.frame_id
                except Exception as e:
                    logger.error(f"Error sending frame: {e}")
                    raise

            # Small sleep to prevent CPU spinning
            await asyncio.sleep(0.005)  # 5ms check interval

    except WebSocketDisconnect:
        connected_clients[simulation_id].discard(websocket)
        logger.info(f"Client disconnected from simulation {simulation_id}")

        # Clean up if no more clients
        if not connected_clients[simulation_id]:
            del connected_clients[simulation_id]
            del frame_buffers[simulation_id]
            del simulation_states[simulation_id]

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1011_SERVER_ERROR)


async def handle_control_command(simulation_id: int, command: ControlCommand) -> None:
    """Handle control command from client.

    Args:
        simulation_id: Simulation ID
        command: Control command
    """
    state = simulation_states.get(simulation_id)
    if not state:
        return

    if command.type == "play":
        state["playing"] = True
        logger.info(f"Simulation {simulation_id} resumed")

    elif command.type == "pause":
        state["playing"] = False
        logger.info(f"Simulation {simulation_id} paused")

    elif command.type == "speed":
        speed = command.payload.get("speed", 1.0)
        state["speed"] = max(0.1, min(4.0, speed))  # Clamp between 0.1x and 4x
        logger.info(f"Simulation {simulation_id} speed set to {state['speed']}x")

    elif command.type == "camera":
        camera = command.payload.get("camera", "free")
        state["camera"] = camera
        logger.info(f"Simulation {simulation_id} camera set to {camera}")

    elif command.type == "filter":
        state["filter"] = command.payload.get("filter")
        logger.info(f"Simulation {simulation_id} agent filter updated")


async def broadcast_frame(simulation_id: int, frame: WorldFrame) -> None:
    """Broadcast frame to all connected clients.

    Args:
        simulation_id: Simulation ID
        frame: World frame to broadcast
    """
    # Buffer the frame
    if simulation_id in frame_buffers:
        frame_buffers[simulation_id].add_frame(frame)

    # Broadcast to connected clients
    if simulation_id in connected_clients:
        clients = connected_clients[simulation_id].copy()
        for client in clients:
            try:
                await client.send_bytes(frame.to_msgpack())
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                connected_clients[simulation_id].discard(client)


def get_connected_clients_count(simulation_id: int) -> int:
    """Get number of connected clients for simulation.

    Args:
        simulation_id: Simulation ID

    Returns:
        Number of connected clients
    """
    return len(connected_clients.get(simulation_id, set()))


def get_simulation_state(simulation_id: int) -> Dict:
    """Get current simulation playback state.

    Args:
        simulation_id: Simulation ID

    Returns:
        Simulation state dictionary
    """
    return simulation_states.get(simulation_id, {})
