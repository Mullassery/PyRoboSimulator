"""State synchronization between Python backend and UE5.

Handles bidirectional state synchronization with conflict resolution,
validation, rollback, and network interruption handling.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Direction of synchronization."""

    BACKEND_TO_UE5 = "backend_to_ue5"
    UE5_TO_BACKEND = "ue5_to_backend"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolutionStrategy(Enum):
    """Strategy for resolving state conflicts."""

    LAST_WRITE_WINS = "last_write_wins"
    BACKEND_WINS = "backend_wins"
    UE5_WINS = "ue5_wins"
    CUSTOM = "custom"


@dataclass
class StateSnapshot:
    """Snapshot of world state at a point in time."""

    timestamp: float
    frame_number: int
    state_hash: str  # Hash of serialized state
    state_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "state_hash": self.state_hash,
            "state_data": self.state_data,
            "metadata": self.metadata,
        }


@dataclass
class StateSyncMessage:
    """Message for state synchronization."""

    sender: str  # "backend" or "ue5"
    direction: SyncDirection
    frame_number: int
    timestamp: float
    data: Dict[str, Any]
    data_hash: str  # Hash of data for integrity check
    requires_ack: bool = True
    sequence_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sender": self.sender,
            "direction": self.direction.value,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "data": self.data,
            "data_hash": self.data_hash,
            "requires_ack": self.requires_ack,
            "sequence_number": self.sequence_number,
        }


class ConflictResolver:
    """Resolves conflicts between backend and UE5 state."""

    def __init__(
        self,
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS,
        custom_resolver: Optional[Callable[[Any, Any], Any]] = None,
    ):
        """Initialize conflict resolver.

        Args:
            strategy: Resolution strategy
            custom_resolver: Custom resolver function(backend_state, ue5_state) -> resolved_state
        """
        self.strategy = strategy
        self.custom_resolver = custom_resolver
        self.conflict_count = 0

    def resolve(
        self,
        backend_state: Any,
        backend_timestamp: float,
        ue5_state: Any,
        ue5_timestamp: float,
    ) -> Tuple[Any, str]:
        """Resolve conflict between two states.

        Args:
            backend_state: State from backend
            backend_timestamp: Timestamp from backend
            ue5_state: State from UE5
            ue5_timestamp: Timestamp from UE5

        Returns:
            Tuple of (resolved_state, conflict_description)
        """
        self.conflict_count += 1

        if self.strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            if backend_timestamp > ue5_timestamp:
                return backend_state, "backend_newer"
            else:
                return ue5_state, "ue5_newer"

        elif self.strategy == ConflictResolutionStrategy.BACKEND_WINS:
            return backend_state, "backend_priority"

        elif self.strategy == ConflictResolutionStrategy.UE5_WINS:
            return ue5_state, "ue5_priority"

        elif self.strategy == ConflictResolutionStrategy.CUSTOM:
            if self.custom_resolver:
                resolved = self.custom_resolver(backend_state, ue5_state)
                return resolved, "custom_resolution"
            else:
                logger.warning("Custom resolver not provided, using last_write_wins")
                if backend_timestamp > ue5_timestamp:
                    return backend_state, "backend_newer"
                return ue5_state, "ue5_newer"

        else:
            raise ValueError(f"Unknown conflict strategy: {self.strategy}")


class StateValidator:
    """Validates state integrity and consistency."""

    def __init__(self):
        """Initialize validator."""
        self.validation_rules: Dict[str, Callable[[Any], bool]] = {}
        self.validation_errors: List[str] = []

    def add_rule(self, field_name: str, validator: Callable[[Any], bool]) -> None:
        """Add validation rule.

        Args:
            field_name: Name of field to validate
            validator: Function returning True if valid
        """
        self.validation_rules[field_name] = validator

    def validate(self, state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate state.

        Args:
            state: State dictionary to validate

        Returns:
            Tuple of (is_valid, error_list)
        """
        self.validation_errors.clear()
        is_valid = True

        for field_name, validator in self.validation_rules.items():
            if field_name not in state:
                self.validation_errors.append(f"Missing field: {field_name}")
                is_valid = False
                continue

            try:
                if not validator(state[field_name]):
                    self.validation_errors.append(f"Validation failed for field: {field_name}")
                    is_valid = False
            except Exception as e:
                self.validation_errors.append(f"Validation error for {field_name}: {str(e)}")
                is_valid = False

        return is_valid, self.validation_errors


class SyncTelemetry:
    """Tracks synchronization metrics."""

    def __init__(self):
        """Initialize telemetry."""
        self.messages_sent = 0
        self.messages_received = 0
        self.messages_acked = 0
        self.sync_latency_ms: List[float] = []
        self.conflicts_detected = 0
        self.rollbacks_executed = 0
        self.validation_failures = 0
        self.network_errors = 0

    def record_sync_latency(self, latency_ms: float) -> None:
        """Record sync latency.

        Args:
            latency_ms: Latency in milliseconds
        """
        self.sync_latency_ms.append(latency_ms)
        if len(self.sync_latency_ms) > 1000:
            self.sync_latency_ms = self.sync_latency_ms[-1000:]

    def get_average_latency(self) -> float:
        """Get average sync latency."""
        if not self.sync_latency_ms:
            return 0.0
        return sum(self.sync_latency_ms) / len(self.sync_latency_ms)

    def get_statistics(self) -> Dict[str, Any]:
        """Get telemetry statistics.

        Returns:
            Dictionary with metrics
        """
        return {
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "messages_acked": self.messages_acked,
            "average_latency_ms": self.get_average_latency(),
            "conflicts_detected": self.conflicts_detected,
            "rollbacks_executed": self.rollbacks_executed,
            "validation_failures": self.validation_failures,
            "network_errors": self.network_errors,
        }


class StateSynchronizationService:
    """Manages bidirectional state synchronization."""

    def __init__(
        self,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS,
        max_history_size: int = 100,
    ):
        """Initialize synchronization service.

        Args:
            conflict_strategy: Strategy for conflict resolution
            max_history_size: Maximum number of state snapshots to keep
        """
        self.conflict_strategy = conflict_strategy
        self.max_history_size = max_history_size
        self.state_history: List[StateSnapshot] = []
        self.pending_messages: List[StateSyncMessage] = []
        self.conflict_resolver = ConflictResolver(conflict_strategy)
        self.validator = StateValidator()
        self.telemetry = SyncTelemetry()

        self.backend_state: Dict[str, Any] = {}
        self.ue5_state: Dict[str, Any] = {}
        self.last_sync_timestamp = 0.0
        self.sequence_number = 0
        self.network_timeout_s = 5.0

    def add_validation_rule(self, field_name: str, validator: Callable[[Any], bool]) -> None:
        """Add state validation rule.

        Args:
            field_name: Name of field
            validator: Validation function
        """
        self.validator.add_rule(field_name, validator)

    def update_backend_state(self, state_data: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """Update backend state.

        Args:
            state_data: New state data
            metadata: Optional metadata

        Returns:
            Whether update was successful
        """
        # Validate state
        is_valid, errors = self.validator.validate(state_data)
        if not is_valid:
            self.telemetry.validation_failures += 1
            logger.warning(f"Backend state validation failed: {errors}")
            return False

        # Update state
        self.backend_state = state_data.copy()
        state_hash = self._compute_hash(state_data)

        # Record snapshot
        snapshot = StateSnapshot(
            timestamp=time.time(),
            frame_number=self._get_next_frame_number(),
            state_hash=state_hash,
            state_data=state_data.copy(),
            metadata=metadata or {},
        )
        self._add_snapshot(snapshot)

        self.telemetry.messages_sent += 1
        return True

    def update_ue5_state(self, state_data: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """Update UE5 state.

        Args:
            state_data: New state data from UE5
            metadata: Optional metadata

        Returns:
            Whether update was successful
        """
        # Validate state
        is_valid, errors = self.validator.validate(state_data)
        if not is_valid:
            self.telemetry.validation_failures += 1
            logger.warning(f"UE5 state validation failed: {errors}")
            return False

        # Check for conflicts
        conflicts = self._detect_conflicts(self.backend_state, state_data)
        if conflicts:
            self.telemetry.conflicts_detected += 1
            logger.info(f"Conflict detected in fields: {conflicts}")

        # Update state
        self.ue5_state = state_data.copy()
        state_hash = self._compute_hash(state_data)

        # Record snapshot
        snapshot = StateSnapshot(
            timestamp=time.time(),
            frame_number=self._get_next_frame_number(),
            state_hash=state_hash,
            state_data=state_data.copy(),
            metadata=metadata or {},
        )
        self._add_snapshot(snapshot)

        self.telemetry.messages_received += 1
        return True

    def synchronize(self) -> Tuple[bool, Dict[str, Any]]:
        """Synchronize states and resolve conflicts.

        Returns:
            Tuple of (success, result_state)
        """
        if not self.backend_state or not self.ue5_state:
            return False, {}

        conflicts = self._detect_conflicts(self.backend_state, self.ue5_state)
        if not conflicts:
            return True, self.backend_state

        # Resolve conflicts
        resolved_state = self.backend_state.copy()
        backend_time = time.time()
        ue5_time = time.time()

        for field in conflicts:
            resolved_value, strategy = self.conflict_resolver.resolve(
                self.backend_state.get(field),
                backend_time,
                self.ue5_state.get(field),
                ue5_time,
            )
            resolved_state[field] = resolved_value
            logger.info(f"Resolved conflict in {field} using {strategy}")

        return True, resolved_state

    def create_sync_message(self, data: Dict[str, Any], direction: SyncDirection) -> StateSyncMessage:
        """Create a sync message.

        Args:
            data: Data to sync
            direction: Direction of sync

        Returns:
            StateSyncMessage instance
        """
        self.sequence_number += 1
        data_hash = self._compute_hash(data)

        message = StateSyncMessage(
            sender="backend",
            direction=direction,
            frame_number=self._get_next_frame_number(),
            timestamp=time.time(),
            data=data,
            data_hash=data_hash,
            requires_ack=True,
            sequence_number=self.sequence_number,
        )

        self.pending_messages.append(message)
        return message

    def acknowledge_message(self, sequence_number: int) -> bool:
        """Acknowledge receipt of sync message.

        Args:
            sequence_number: Sequence number of message

        Returns:
            Whether ack was processed
        """
        for msg in self.pending_messages:
            if msg.sequence_number == sequence_number:
                self.telemetry.messages_acked += 1
                self.pending_messages.remove(msg)
                return True

        return False

    def rollback_to_snapshot(self, frame_number: int) -> bool:
        """Rollback state to a previous snapshot.

        Args:
            frame_number: Frame number to rollback to

        Returns:
            Whether rollback was successful
        """
        for snapshot in reversed(self.state_history):
            if snapshot.frame_number == frame_number:
                self.backend_state = snapshot.state_data.copy()
                self.telemetry.rollbacks_executed += 1
                logger.info(f"Rolled back to frame {frame_number}")
                return True

        logger.warning(f"Snapshot for frame {frame_number} not found")
        return False

    def get_state_hash(self) -> str:
        """Get hash of current state.

        Returns:
            SHA256 hash of backend state
        """
        return self._compute_hash(self.backend_state)

    def verify_state_integrity(self) -> bool:
        """Verify state integrity.

        Returns:
            Whether state is valid
        """
        is_valid, _ = self.validator.validate(self.backend_state)
        return is_valid

    def get_pending_messages(self) -> List[StateSyncMessage]:
        """Get pending unacknowledged messages.

        Returns:
            List of pending messages
        """
        return self.pending_messages.copy()

    def clear_pending_messages(self) -> int:
        """Clear all pending messages.

        Returns:
            Number of messages cleared
        """
        count = len(self.pending_messages)
        self.pending_messages.clear()
        return count

    def get_state_history(self, limit: Optional[int] = None) -> List[StateSnapshot]:
        """Get state history.

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots
        """
        if limit is None:
            return self.state_history.copy()
        return self.state_history[-limit:].copy()

    def get_telemetry(self) -> Dict[str, Any]:
        """Get synchronization telemetry.

        Returns:
            Dictionary with metrics
        """
        return self.telemetry.get_statistics()

    def _detect_conflicts(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> List[str]:
        """Detect conflicting fields.

        Args:
            state1: First state
            state2: Second state

        Returns:
            List of conflicting field names
        """
        conflicts = []

        for key in state1:
            if key not in state2:
                continue
            if state1[key] != state2[key]:
                conflicts.append(key)

        return conflicts

    def _add_snapshot(self, snapshot: StateSnapshot) -> None:
        """Add snapshot to history.

        Args:
            snapshot: Snapshot to add
        """
        self.state_history.append(snapshot)

        # Trim history if too large
        if len(self.state_history) > self.max_history_size:
            self.state_history = self.state_history[-self.max_history_size :]

    def _get_next_frame_number(self) -> int:
        """Get next frame number.

        Returns:
            Frame number
        """
        if not self.state_history:
            return 0
        return self.state_history[-1].frame_number + 1

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute SHA256 hash of data.

        Args:
            data: Data to hash

        Returns:
            Hex string of hash
        """
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
