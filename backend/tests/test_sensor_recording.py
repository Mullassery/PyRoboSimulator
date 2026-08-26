"""Tests for Phase 1C.10: Sensor Data Recording."""

import tempfile
import time
from pathlib import Path

import numpy as np
import pytest

from src.services.sensor_recording import (
    RingBuffer,
    RecordingConfig,
    SensorFrame,
    SensorRecordingService,
)


class TestSensorFrame:
    """Test sensor frame."""

    def test_frame_creation(self):
        """Test creating sensor frame."""
        data = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        frame = SensorFrame(
            timestamp=1000.0,
            frame_number=1,
            agent_id="agent_1",
            sensor_type="rgb",
            data=data,
        )
        assert frame.timestamp == 1000.0
        assert frame.sensor_type == "rgb"

    def test_frame_serialization(self):
        """Test frame serialization."""
        data = np.array([1, 2, 3, 4], dtype=np.int32)
        frame = SensorFrame(
            timestamp=1000.0,
            frame_number=1,
            agent_id="agent_1",
            sensor_type="rgb",
            data=data,
            metadata={"resolution": "1920x1080"},
        )

        binary = frame.to_bytes()
        assert len(binary) > 0
        assert isinstance(binary, bytes)

    def test_frame_metadata(self):
        """Test frame metadata."""
        data = np.array([1, 2, 3], dtype=np.float32)
        metadata = {"iso": 100, "shutter_speed": 30}

        frame = SensorFrame(
            timestamp=1000.0,
            frame_number=1,
            agent_id="agent_1",
            sensor_type="rgb",
            data=data,
            metadata=metadata,
        )

        assert frame.metadata["iso"] == 100


class TestRecordingConfig:
    """Test recording configuration."""

    def test_default_config(self):
        """Test default config."""
        config = RecordingConfig()
        assert config.storage_format == "hdf5"
        assert config.compression == "lz4"

    def test_custom_config(self):
        """Test custom config."""
        config = RecordingConfig(
            storage_format="zarr",
            compression="zstd",
            max_buffer_size_mb=200,
        )
        assert config.storage_format == "zarr"
        assert config.compression == "zstd"


class TestRingBuffer:
    """Test ring buffer."""

    def test_buffer_creation(self):
        """Test creating ring buffer."""
        buffer = RingBuffer(max_frames=100)
        assert buffer.max_frames == 100
        assert buffer.size() == 0

    def test_add_frame(self):
        """Test adding frames."""
        buffer = RingBuffer(max_frames=10)
        data = np.array([1, 2, 3], dtype=np.float32)

        for i in range(5):
            frame = SensorFrame(
                timestamp=1000.0 + i,
                frame_number=i,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            buffer.add_frame(frame)

        assert buffer.size() == 5

    def test_buffer_wrapping(self):
        """Test ring buffer wrapping."""
        buffer = RingBuffer(max_frames=5)
        data = np.array([1, 2, 3], dtype=np.float32)

        # Add more frames than capacity
        for i in range(10):
            frame = SensorFrame(
                timestamp=1000.0 + i,
                frame_number=i,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            buffer.add_frame(frame)

        # Should still be at max capacity
        assert buffer.size() == 5

    def test_get_frame(self):
        """Test getting frame by index."""
        buffer = RingBuffer()
        data = np.array([1, 2, 3], dtype=np.float32)

        frame = SensorFrame(
            timestamp=1000.0,
            frame_number=1,
            agent_id="agent_1",
            sensor_type="rgb",
            data=data,
        )
        buffer.add_frame(frame)

        retrieved = buffer.get_frame(0)
        assert retrieved is not None
        assert retrieved.frame_number == 1

    def test_get_frames_by_timestamp(self):
        """Test querying by timestamp."""
        buffer = RingBuffer()
        data = np.array([1, 2, 3], dtype=np.float32)

        for i in range(5):
            frame = SensorFrame(
                timestamp=1000.0 + i,
                frame_number=i,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            buffer.add_frame(frame)

        frames = buffer.get_frames_by_timestamp(1000.5, 1003.5)
        assert len(frames) == 3

    def test_get_frames_by_agent(self):
        """Test querying by agent."""
        buffer = RingBuffer()
        data = np.array([1, 2, 3], dtype=np.float32)

        # Add frames for multiple agents
        for i in range(5):
            frame = SensorFrame(
                timestamp=1000.0 + i,
                frame_number=i,
                agent_id="agent_1" if i % 2 == 0 else "agent_2",
                sensor_type="rgb",
                data=data,
            )
            buffer.add_frame(frame)

        frames = buffer.get_frames_by_agent("agent_1")
        assert len(frames) == 3
        assert all(f.agent_id == "agent_1" for f in frames)

    def test_clear_buffer(self):
        """Test clearing buffer."""
        buffer = RingBuffer()
        data = np.array([1, 2, 3], dtype=np.float32)

        frame = SensorFrame(
            timestamp=1000.0,
            frame_number=1,
            agent_id="agent_1",
            sensor_type="rgb",
            data=data,
        )
        buffer.add_frame(frame)

        buffer.clear()
        assert buffer.size() == 0


class TestSensorRecordingService:
    """Test sensor recording service."""

    def test_service_creation(self):
        """Test creating recording service."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            assert service.output_dir.exists()
            assert not service.recording_active

    def test_start_stop_recording(self):
        """Test starting and stopping recording."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)

            filename = service.start_recording("test_session")
            assert service.recording_active
            assert filename is not None

            stats = service.stop_recording()
            assert not service.recording_active
            assert "file" in stats

    def test_add_frame_rgb(self):
        """Test adding RGB frame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )

            service.add_frame(frame)
            assert service.ring_buffer.size() == 1

            service.stop_recording()

    def test_add_frame_depth(self):
        """Test adding depth frame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.random.rand(512, 512).astype(np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="depth",
                data=data,
            )

            service.add_frame(frame)
            assert service.ring_buffer.size() == 1

    def test_add_frame_lidar(self):
        """Test adding lidar frame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            # Lidar: 512 rays * 16 layers = 8192 points, 3D coordinates
            data = np.random.rand(8192, 3).astype(np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="lidar",
                data=data,
            )

            service.add_frame(frame)
            assert service.ring_buffer.size() == 1

    def test_add_frame_thermal(self):
        """Test adding thermal frame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.random.rand(256, 256).astype(np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="thermal",
                data=data,
            )

            service.add_frame(frame)
            assert service.ring_buffer.size() == 1

    def test_multiple_agents(self):
        """Test recording from multiple agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.array([1, 2, 3], dtype=np.float32)

            for agent_id in ["agent_1", "agent_2", "agent_3"]:
                frame = SensorFrame(
                    timestamp=time.time(),
                    frame_number=1,
                    agent_id=agent_id,
                    sensor_type="rgb",
                    data=data,
                )
                service.add_frame(frame)

            assert service.ring_buffer.size() == 3

    def test_flush_recording(self):
        """Test flushing to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RecordingConfig(storage_format="raw")
            service = SensorRecordingService(output_dir=tmpdir, config=config)
            service.start_recording("test")

            data = np.array([1, 2, 3], dtype=np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            service.add_frame(frame)

            count = service.flush()
            assert count >= 1

    def test_query_frames(self):
        """Test querying frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.array([1, 2, 3], dtype=np.float32)
            start_time = time.time()

            # Add frames for different agents and sensors
            for i in range(5):
                for agent_id in ["agent_1", "agent_2"]:
                    for sensor_type in ["rgb", "depth"]:
                        frame = SensorFrame(
                            timestamp=start_time + i * 0.1,
                            frame_number=i,
                            agent_id=agent_id,
                            sensor_type=sensor_type,
                            data=data,
                        )
                        service.add_frame(frame)

            # Query by agent
            frames = service.query_frames(agent_id="agent_1")
            assert len(frames) == 10  # 5 frames * 2 sensors

            # Query by sensor type
            frames = service.query_frames(sensor_type="rgb")
            assert len(frames) == 10  # 5 frames * 2 agents

            # Query by timestamp
            frames = service.query_frames(
                start_timestamp=start_time,
                end_timestamp=start_time + 0.3
            )
            assert len(frames) > 0

    def test_statistics(self):
        """Test getting statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.array([1, 2, 3], dtype=np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            service.add_frame(frame)

            stats = service.get_statistics()
            assert stats["recording_active"]
            assert stats["buffer_size"] == 1
            assert stats["agents_recorded"] == 1

    def test_estimate_size(self):
        """Test size estimation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)

            # Add 1080p RGB frame
            data = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )
            service.add_frame(frame)

            size_mb = service.estimate_size_mb()
            # 1920*1080*3 bytes = 6,220,800 bytes = ~5.93 MB
            assert size_mb > 5

    def test_cleanup_old_recordings(self):
        """Test cleanup of old recordings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)

            # Create a dummy old file
            old_file = Path(tmpdir) / "recording_test_1.raw"
            old_file.touch()

            # Set modification time to 2 days ago
            import os
            old_time = time.time() - (2 * 24 * 3600)
            os.utime(old_file, (old_time, old_time))

            # Cleanup files older than 1 day
            deleted = service.cleanup_old_recordings(max_age_hours=24)
            assert deleted == 1

    def test_ring_buffer_size_limit(self):
        """Test ring buffer size limiting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.ring_buffer = RingBuffer(max_frames=5)

            data = np.array([1, 2, 3], dtype=np.float32)

            # Add more frames than capacity
            for i in range(10):
                frame = SensorFrame(
                    timestamp=time.time() + i * 0.1,
                    frame_number=i,
                    agent_id="agent_1",
                    sensor_type="rgb",
                    data=data,
                )
                service.add_frame(frame)

            # Should not exceed max frames
            assert service.ring_buffer.size() <= 5

    def test_recording_without_active_flag(self):
        """Test that frames aren't recorded when inactive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)

            data = np.array([1, 2, 3], dtype=np.float32)
            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
            )

            # Should not record when inactive
            service.add_frame(frame)
            assert service.ring_buffer.size() == 0

    def test_metadata_in_frame(self):
        """Test frame with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = SensorRecordingService(output_dir=tmpdir)
            service.start_recording("test")

            data = np.array([1, 2, 3], dtype=np.float32)
            metadata = {
                "iso": 100,
                "exposure": 1.0,
                "white_balance": "daylight",
            }

            frame = SensorFrame(
                timestamp=time.time(),
                frame_number=1,
                agent_id="agent_1",
                sensor_type="rgb",
                data=data,
                metadata=metadata,
            )

            service.add_frame(frame)
            assert service.ring_buffer.size() == 1
            assert service.ring_buffer.frames[0].metadata == metadata
