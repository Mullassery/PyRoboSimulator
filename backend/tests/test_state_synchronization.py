"""Tests for Phase 1C.9: State Synchronization."""

import pytest

from backend.src.services.state_synchronization import (
    ConflictResolutionStrategy,
    ConflictResolver,
    StateSnapshot,
    StateSyncMessage,
    StateSynchronizationService,
    StateValidator,
    SyncDirection,
    SyncTelemetry,
)


class TestStateSnapshot:
    """Test state snapshot."""

    def test_snapshot_creation(self):
        """Test creating snapshot."""
        snapshot = StateSnapshot(
            timestamp=1000.0,
            frame_number=1,
            state_hash="abc123",
            state_data={"x": 10, "y": 20},
        )
        assert snapshot.timestamp == 1000.0
        assert snapshot.frame_number == 1

    def test_snapshot_to_dict(self):
        """Test snapshot serialization."""
        snapshot = StateSnapshot(
            timestamp=1000.0,
            frame_number=1,
            state_hash="abc123",
            state_data={"x": 10, "y": 20},
        )
        d = snapshot.to_dict()
        assert d["frame_number"] == 1
        assert d["state_data"]["x"] == 10


class TestStateSyncMessage:
    """Test sync message."""

    def test_message_creation(self):
        """Test creating sync message."""
        msg = StateSyncMessage(
            sender="backend",
            direction=SyncDirection.BACKEND_TO_UE5,
            frame_number=1,
            timestamp=1000.0,
            data={"x": 10},
            data_hash="abc123",
        )
        assert msg.sender == "backend"
        assert msg.frame_number == 1

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = StateSyncMessage(
            sender="backend",
            direction=SyncDirection.BACKEND_TO_UE5,
            frame_number=1,
            timestamp=1000.0,
            data={"x": 10},
            data_hash="abc123",
        )
        d = msg.to_dict()
        assert d["sender"] == "backend"
        assert d["frame_number"] == 1


class TestStateValidator:
    """Test state validator."""

    def test_add_and_validate_rule(self):
        """Test adding and validating rules."""
        validator = StateValidator()
        validator.add_rule("x", lambda v: isinstance(v, (int, float)) and v >= 0)
        validator.add_rule("y", lambda v: isinstance(v, (int, float)) and v >= 0)

        state = {"x": 10, "y": 20}
        is_valid, errors = validator.validate(state)
        assert is_valid
        assert len(errors) == 0

    def test_validation_failure(self):
        """Test validation failure."""
        validator = StateValidator()
        validator.add_rule("x", lambda v: v > 100)

        state = {"x": 10}
        is_valid, errors = validator.validate(state)
        assert not is_valid
        assert len(errors) > 0

    def test_missing_field(self):
        """Test missing required field."""
        validator = StateValidator()
        validator.add_rule("x", lambda v: True)

        state = {"y": 10}
        is_valid, errors = validator.validate(state)
        assert not is_valid
        assert any("Missing" in e for e in errors)


class TestConflictResolver:
    """Test conflict resolution."""

    def test_last_write_wins_backend(self):
        """Test last_write_wins strategy (backend newer)."""
        resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
        resolved, strategy = resolver.resolve({"x": 20}, 1000.0, {"x": 10}, 999.0)
        assert resolved == {"x": 20}
        assert strategy == "backend_newer"

    def test_last_write_wins_ue5(self):
        """Test last_write_wins strategy (UE5 newer)."""
        resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
        resolved, strategy = resolver.resolve({"x": 20}, 999.0, {"x": 10}, 1000.0)
        assert resolved == {"x": 10}
        assert strategy == "ue5_newer"

    def test_backend_wins(self):
        """Test backend_wins strategy."""
        resolver = ConflictResolver(ConflictResolutionStrategy.BACKEND_WINS)
        resolved, strategy = resolver.resolve({"x": 20}, 999.0, {"x": 10}, 1000.0)
        assert resolved == {"x": 20}
        assert strategy == "backend_priority"

    def test_ue5_wins(self):
        """Test ue5_wins strategy."""
        resolver = ConflictResolver(ConflictResolutionStrategy.UE5_WINS)
        resolved, strategy = resolver.resolve({"x": 20}, 1000.0, {"x": 10}, 999.0)
        assert resolved == {"x": 10}
        assert strategy == "ue5_priority"

    def test_custom_resolver(self):
        """Test custom resolver."""

        def custom(backend, ue5):
            return {"x": max(backend["x"], ue5["x"])}

        resolver = ConflictResolver(
            ConflictResolutionStrategy.CUSTOM, custom_resolver=custom
        )
        resolved, strategy = resolver.resolve({"x": 20}, 999.0, {"x": 30}, 1000.0)
        assert resolved == {"x": 30}

    def test_conflict_counter(self):
        """Test conflict counter."""
        resolver = ConflictResolver()
        assert resolver.conflict_count == 0

        resolver.resolve({"x": 10}, 1000.0, {"x": 20}, 999.0)
        assert resolver.conflict_count == 1

        resolver.resolve({"x": 10}, 1000.0, {"x": 20}, 999.0)
        assert resolver.conflict_count == 2


class TestSyncTelemetry:
    """Test sync telemetry."""

    def test_telemetry_creation(self):
        """Test creating telemetry."""
        telemetry = SyncTelemetry()
        assert telemetry.messages_sent == 0
        assert telemetry.conflicts_detected == 0

    def test_record_latency(self):
        """Test recording latency."""
        telemetry = SyncTelemetry()
        telemetry.record_sync_latency(10.5)
        telemetry.record_sync_latency(15.3)

        avg = telemetry.get_average_latency()
        assert abs(avg - 12.9) < 0.1

    def test_get_statistics(self):
        """Test getting statistics."""
        telemetry = SyncTelemetry()
        telemetry.messages_sent = 100
        telemetry.messages_received = 95
        telemetry.conflicts_detected = 2

        stats = telemetry.get_statistics()
        assert stats["messages_sent"] == 100
        assert stats["messages_received"] == 95
        assert stats["conflicts_detected"] == 2


class TestStateSynchronizationService:
    """Test state synchronization service."""

    def test_service_creation(self):
        """Test creating service."""
        service = StateSynchronizationService()
        assert service.conflict_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS

    def test_add_validation_rule(self):
        """Test adding validation rule."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: isinstance(v, (int, float)))

        is_valid = service.update_backend_state({"x": 10})
        assert is_valid

    def test_update_backend_state(self):
        """Test updating backend state."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)
        service.add_validation_rule("y", lambda v: True)

        state = {"x": 10, "y": 20}
        result = service.update_backend_state(state)
        assert result
        assert service.backend_state == state

    def test_update_ue5_state(self):
        """Test updating UE5 state."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)
        service.add_validation_rule("y", lambda v: True)

        state = {"x": 15, "y": 25}
        result = service.update_ue5_state(state)
        assert result
        assert service.ue5_state == state

    def test_validation_failure_backend(self):
        """Test validation failure on backend."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: v > 100)

        result = service.update_backend_state({"x": 10})
        assert not result

    def test_validation_failure_ue5(self):
        """Test validation failure on UE5."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: v > 100)

        result = service.update_ue5_state({"x": 10})
        assert not result

    def test_detect_conflicts(self):
        """Test conflict detection."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)
        service.add_validation_rule("y", lambda v: True)

        service.update_backend_state({"x": 10, "y": 20})
        service.update_ue5_state({"x": 15, "y": 20})

        conflicts = service._detect_conflicts(service.backend_state, service.ue5_state)
        assert "x" in conflicts
        assert "y" not in conflicts

    def test_synchronize_no_conflicts(self):
        """Test synchronization without conflicts."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)
        service.add_validation_rule("y", lambda v: True)

        state = {"x": 10, "y": 20}
        service.update_backend_state(state)
        service.update_ue5_state(state)

        success, resolved = service.synchronize()
        assert success
        assert resolved["x"] == 10

    def test_synchronize_with_conflicts(self):
        """Test synchronization with conflicts."""
        service = StateSynchronizationService(
            ConflictResolutionStrategy.BACKEND_WINS
        )
        service.add_validation_rule("x", lambda v: True)
        service.add_validation_rule("y", lambda v: True)

        service.update_backend_state({"x": 10, "y": 20})
        service.update_ue5_state({"x": 15, "y": 20})

        success, resolved = service.synchronize()
        assert success
        assert resolved["x"] == 10  # Backend wins

    def test_create_sync_message(self):
        """Test creating sync message."""
        service = StateSynchronizationService()
        data = {"x": 10, "y": 20}
        msg = service.create_sync_message(data, SyncDirection.BACKEND_TO_UE5)

        assert msg.sender == "backend"
        assert msg.frame_number == 0
        assert len(service.pending_messages) == 1

    def test_acknowledge_message(self):
        """Test acknowledging message."""
        service = StateSynchronizationService()
        data = {"x": 10}
        msg = service.create_sync_message(data, SyncDirection.BACKEND_TO_UE5)

        result = service.acknowledge_message(msg.sequence_number)
        assert result
        assert len(service.pending_messages) == 0

    def test_acknowledge_nonexistent_message(self):
        """Test acknowledging nonexistent message."""
        service = StateSynchronizationService()
        result = service.acknowledge_message(999)
        assert not result

    def test_state_history(self):
        """Test state history tracking."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)

        service.update_backend_state({"x": 10})
        service.update_backend_state({"x": 20})
        service.update_backend_state({"x": 30})

        history = service.get_state_history()
        assert len(history) >= 3

    def test_rollback(self):
        """Test state rollback."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)

        service.update_backend_state({"x": 10})
        snapshot1 = service.state_history[-1]

        service.update_backend_state({"x": 20})
        service.update_backend_state({"x": 30})

        result = service.rollback_to_snapshot(snapshot1.frame_number)
        assert result
        assert service.backend_state["x"] == 10

    def test_get_state_hash(self):
        """Test state hashing."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)

        service.update_backend_state({"x": 10})
        hash1 = service.get_state_hash()

        service.update_backend_state({"x": 20})
        hash2 = service.get_state_hash()

        assert hash1 != hash2

    def test_verify_state_integrity(self):
        """Test state integrity check."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: isinstance(v, (int, float)))

        service.update_backend_state({"x": 10})
        assert service.verify_state_integrity()

        service.backend_state = {"x": "invalid"}
        assert not service.verify_state_integrity()

    def test_get_pending_messages(self):
        """Test getting pending messages."""
        service = StateSynchronizationService()

        service.create_sync_message({"x": 10}, SyncDirection.BACKEND_TO_UE5)
        service.create_sync_message({"y": 20}, SyncDirection.BACKEND_TO_UE5)

        pending = service.get_pending_messages()
        assert len(pending) == 2

    def test_clear_pending_messages(self):
        """Test clearing pending messages."""
        service = StateSynchronizationService()

        service.create_sync_message({"x": 10}, SyncDirection.BACKEND_TO_UE5)
        service.create_sync_message({"y": 20}, SyncDirection.BACKEND_TO_UE5)

        count = service.clear_pending_messages()
        assert count == 2
        assert len(service.pending_messages) == 0

    def test_telemetry_integration(self):
        """Test telemetry integration."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)

        service.update_backend_state({"x": 10})
        service.update_ue5_state({"x": 20})

        stats = service.get_telemetry()
        assert stats["messages_sent"] == 1
        assert stats["messages_received"] == 1

    def test_sequence_number_increment(self):
        """Test sequence number increment."""
        service = StateSynchronizationService()

        msg1 = service.create_sync_message({"x": 10}, SyncDirection.BACKEND_TO_UE5)
        msg2 = service.create_sync_message({"x": 20}, SyncDirection.BACKEND_TO_UE5)

        assert msg1.sequence_number < msg2.sequence_number

    def test_history_trimming(self):
        """Test history trimming."""
        service = StateSynchronizationService(max_history_size=10)
        service.add_validation_rule("x", lambda v: True)

        for i in range(20):
            service.update_backend_state({"x": i})

        history = service.get_state_history()
        assert len(history) <= 10

    def test_get_history_with_limit(self):
        """Test getting limited history."""
        service = StateSynchronizationService()
        service.add_validation_rule("x", lambda v: True)

        for i in range(10):
            service.update_backend_state({"x": i})

        history = service.get_state_history(limit=3)
        assert len(history) == 3
