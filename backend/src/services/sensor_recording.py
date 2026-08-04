"""Sensor data recording for playback and analysis.

Records sensor data with compression and indexing for efficient retrieval.
"""

import io
import json
import logging
import os
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

try:
    import zarr
    HAS_ZARR = True
except ImportError:
    HAS_ZARR = False


@dataclass
class SensorFrame:
    """Single frame of sensor data."""

    timestamp: float
    frame_number: int
    agent_id: str
    sensor_type: str  # "rgb", "depth", "lidar", "thermal"
    data: np.ndarray  # Raw data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        buffer = io.BytesIO()

        # Write header
        buffer.write(struct.pack("<d", self.timestamp))
        buffer.write(struct.pack("<I", self.frame_number))

        # Agent ID (variable length)
        agent_bytes = self.agent_id.encode("utf-8")
        buffer.write(struct.pack("<H", len(agent_bytes)))
        buffer.write(agent_bytes)

        # Sensor type
        type_bytes = self.sensor_type.encode("utf-8")
        buffer.write(struct.pack("<H", len(type_bytes)))
        buffer.write(type_bytes)

        # Data shape
        buffer.write(struct.pack("<I", len(self.data.shape)))
        for dim in self.data.shape:
            buffer.write(struct.pack("<I", dim))

        # Data dtype
        dtype_str = str(self.data.dtype)
        dtype_bytes = dtype_str.encode("utf-8")
        buffer.write(struct.pack("<H", len(dtype_bytes)))
        buffer.write(dtype_bytes)

        # Data
        buffer.write(self.data.tobytes())

        # Metadata JSON
        metadata_json = json.dumps(self.metadata)
        metadata_bytes = metadata_json.encode("utf-8")
        buffer.write(struct.pack("<I", len(metadata_bytes)))
        buffer.write(metadata_bytes)

        return buffer.getvalue()


@dataclass
class RecordingConfig:
    """Configuration for sensor recording."""

    storage_format: str = "hdf5"  # "hdf5", "zarr", "raw"
    compression: str = "lz4"  # "lz4", "zstd", "gzip", "none"
    max_buffer_size_mb: int = 100
    indexing_enabled: bool = True
    auto_flush_interval_s: float = 5.0


class RingBuffer:
    """Circular buffer for sensor data."""

    def __init__(self, max_frames: int = 10000):
        """Initialize ring buffer.

        Args:
            max_frames: Maximum number of frames to store
        """
        self.max_frames = max_frames
        self.frames: List[SensorFrame] = []
        self.write_index = 0

    def add_frame(self, frame: SensorFrame) -> None:
        """Add frame to buffer.

        Args:
            frame: Sensor frame to add
        """
        if len(self.frames) < self.max_frames:
            self.frames.append(frame)
        else:
            self.frames[self.write_index] = frame

        self.write_index = (self.write_index + 1) % self.max_frames

    def get_frame(self, index: int) -> Optional[SensorFrame]:
        """Get frame by index.

        Args:
            index: Frame index

        Returns:
            Sensor frame or None
        """
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None

    def get_frames_by_timestamp(self, start_ts: float, end_ts: float) -> List[SensorFrame]:
        """Get frames within timestamp range.

        Args:
            start_ts: Start timestamp
            end_ts: End timestamp

        Returns:
            List of frames
        """
        return [f for f in self.frames if start_ts <= f.timestamp <= end_ts]

    def get_frames_by_agent(self, agent_id: str) -> List[SensorFrame]:
        """Get all frames for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of frames
        """
        return [f for f in self.frames if f.agent_id == agent_id]

    def clear(self) -> None:
        """Clear buffer."""
        self.frames.clear()
        self.write_index = 0

    def size(self) -> int:
        """Get current buffer size."""
        return len(self.frames)


class SensorRecordingService:
    """Service for recording sensor data."""

    def __init__(
        self,
        output_dir: str = "./sensor_data",
        config: Optional[RecordingConfig] = None,
    ):
        """Initialize recording service.

        Args:
            output_dir: Directory for recordings
            config: Recording configuration
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or RecordingConfig()

        self.recording_active = False
        self.ring_buffer = RingBuffer()
        self.frame_index: Dict[str, List[Tuple[float, int]]] = {}  # agent_id -> [(timestamp, frame_idx)]
        self.current_file: Optional[str] = None
        self.frames_written = 0
        self.start_time: Optional[float] = None
        self.last_flush_time = time.time()

    def start_recording(self, session_id: str) -> str:
        """Start recording session.

        Args:
            session_id: Session identifier

        Returns:
            Recording filename
        """
        self.recording_active = True
        self.start_time = time.time()
        self.frames_written = 0

        timestamp = int(self.start_time * 1000)
        self.current_file = f"recording_{session_id}_{timestamp}"

        logger.info(f"Started recording: {self.current_file}")
        return self.current_file

    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording session.

        Returns:
            Recording statistics
        """
        self.recording_active = False
        self.flush()

        stats = {
            "file": self.current_file,
            "frames_written": self.frames_written,
            "buffer_frames": self.ring_buffer.size(),
            "duration_s": (time.time() - self.start_time) if self.start_time else 0,
        }

        logger.info(f"Stopped recording: {stats}")
        return stats

    def add_frame(self, frame: SensorFrame) -> None:
        """Add sensor frame to recording.

        Args:
            frame: Sensor frame
        """
        if not self.recording_active:
            return

        # Add to ring buffer
        self.ring_buffer.add_frame(frame)

        # Update index
        if frame.agent_id not in self.frame_index:
            self.frame_index[frame.agent_id] = []

        self.frame_index[frame.agent_id].append((frame.timestamp, self.ring_buffer.size() - 1))

        # Flush if needed
        if time.time() - self.last_flush_time > self.config.auto_flush_interval_s:
            self.flush()

    def flush(self) -> int:
        """Flush buffer to disk.

        Returns:
            Number of frames written
        """
        if not self.current_file:
            return 0

        count = 0

        if self.config.storage_format == "hdf5" and HAS_H5PY:
            count = self._write_hdf5()
        elif self.config.storage_format == "zarr" and HAS_ZARR:
            count = self._write_zarr()
        else:
            count = self._write_raw()

        self.frames_written += count
        self.last_flush_time = time.time()

        logger.debug(f"Flushed {count} frames")
        return count

    def _write_hdf5(self) -> int:
        """Write buffer to HDF5 file."""
        if not HAS_H5PY:
            logger.warning("h5py not available, skipping HDF5 write")
            return 0

        try:
            filepath = self.output_dir / f"{self.current_file}.h5"
            frames = self.ring_buffer.frames

            with h5py.File(filepath, "a") as f:
                for agent_id in self.frame_index:
                    agent_frames = self.ring_buffer.get_frames_by_agent(agent_id)

                    if agent_frames:
                        grp = f.require_group(agent_id)

                        for frame in agent_frames:
                            dataset_name = f"{frame.sensor_type}_{frame.frame_number}"

                            if dataset_name not in grp:
                                grp.create_dataset(
                                    dataset_name,
                                    data=frame.data,
                                    compression=self.config.compression or "gzip",
                                )
                                grp[dataset_name].attrs["timestamp"] = frame.timestamp
                                grp[dataset_name].attrs["metadata"] = json.dumps(frame.metadata)

            return len(frames)

        except Exception as e:
            logger.error(f"Error writing HDF5: {e}")
            return 0

    def _write_zarr(self) -> int:
        """Write buffer to Zarr file."""
        if not HAS_ZARR:
            logger.warning("zarr not available, skipping Zarr write")
            return 0

        try:
            filepath = str(self.output_dir / f"{self.current_file}.zarr")
            frames = self.ring_buffer.frames

            store = zarr.DirectoryStore(filepath)
            root = zarr.group(store=store, overwrite=False)

            for agent_id in self.frame_index:
                agent_frames = self.ring_buffer.get_frames_by_agent(agent_id)

                if agent_frames:
                    grp = root.require_group(agent_id)

                    for frame in agent_frames:
                        dataset_name = f"{frame.sensor_type}_{frame.frame_number}"

                        if dataset_name not in grp:
                            grp.create_dataset(
                                dataset_name,
                                data=frame.data,
                                compressor=zarr.Blosc(cname=self.config.compression or "lz4"),
                            )
                            grp[dataset_name].attrs["timestamp"] = frame.timestamp
                            grp[dataset_name].attrs["metadata"] = json.dumps(frame.metadata)

            return len(frames)

        except Exception as e:
            logger.error(f"Error writing Zarr: {e}")
            return 0

    def _write_raw(self) -> int:
        """Write buffer to raw binary file."""
        try:
            filepath = self.output_dir / f"{self.current_file}.raw"

            with open(filepath, "ab") as f:
                for frame in self.ring_buffer.frames:
                    f.write(frame.to_bytes())

            return len(self.ring_buffer.frames)

        except Exception as e:
            logger.error(f"Error writing raw: {e}")
            return 0

    def query_frames(
        self,
        agent_id: Optional[str] = None,
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
        sensor_type: Optional[str] = None,
    ) -> List[SensorFrame]:
        """Query frames from buffer.

        Args:
            agent_id: Filter by agent
            start_timestamp: Start time
            end_timestamp: End time
            sensor_type: Filter by sensor type

        Returns:
            List of matching frames
        """
        results = self.ring_buffer.frames.copy()

        if agent_id:
            results = [f for f in results if f.agent_id == agent_id]

        if start_timestamp and end_timestamp:
            results = [f for f in results if start_timestamp <= f.timestamp <= end_timestamp]

        if sensor_type:
            results = [f for f in results if f.sensor_type == sensor_type]

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get recording statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "recording_active": self.recording_active,
            "current_file": self.current_file,
            "frames_written": self.frames_written,
            "buffer_size": self.ring_buffer.size(),
            "agents_recorded": len(self.frame_index),
            "storage_format": self.config.storage_format,
            "compression": self.config.compression,
        }

    def cleanup_old_recordings(self, max_age_hours: float = 24) -> int:
        """Remove old recordings.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of files deleted
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted = 0

        for filepath in self.output_dir.glob("recording_*"):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    if filepath.is_dir():
                        import shutil
                        shutil.rmtree(filepath)
                    else:
                        filepath.unlink()
                    deleted += 1
                except Exception as e:
                    logger.error(f"Error deleting {filepath}: {e}")

        return deleted

    def estimate_size_mb(self) -> float:
        """Estimate buffer size in MB.

        Returns:
            Size in megabytes
        """
        total_bytes = 0
        for frame in self.ring_buffer.frames:
            total_bytes += frame.data.nbytes

        return total_bytes / (1024 * 1024)
