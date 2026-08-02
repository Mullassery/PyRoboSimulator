"""
Real-time simulation statistics calculation and tracking.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import time


@dataclass
class AgentStateDistribution:
    """Distribution of agent states."""
    moving: int = 0
    idle: int = 0
    goal_reached: int = 0
    collision: int = 0
    other: int = 0

    def total(self) -> int:
        """Get total agent count."""
        return self.moving + self.idle + self.goal_reached + self.collision + self.other


@dataclass
class EventRates:
    """Event rates per second."""
    collisions_per_sec: float = 0.0
    goals_reached_per_sec: float = 0.0
    state_changes_per_sec: float = 0.0


@dataclass
class SimulationStats:
    """Complete simulation statistics snapshot."""
    timestamp_ms: int
    active_agents: int
    total_agents: int
    agent_state_distribution: AgentStateDistribution
    event_rates: EventRates
    uptime_seconds: float
    fps: float


class StatisticsCalculator:
    """Calculates real-time simulation statistics."""

    def __init__(self, window_size_seconds: int = 10):
        """Initialize statistics calculator.

        Args:
            window_size_seconds: Time window for rate calculation (default 10s)
        """
        self.window_size = window_size_seconds
        self.start_time = time.time()

        # Event tracking (as timestamps)
        self.collision_events: deque = deque()
        self.goal_events: deque = deque()
        self.state_change_events: deque = deque()

        # Frame tracking for FPS
        self.frame_times: deque = deque(maxlen=60)
        self.last_frame_time = time.time()

        # Agent state tracking
        self.agent_states: Dict[int, str] = {}
        self.last_update_time = time.time()

    def update_agent_state(self, agent_id: int, state: str) -> None:
        """Update an agent's state.

        Args:
            agent_id: Agent identifier
            state: New state ('moving', 'idle', 'goal_reached', 'collision', etc.)
        """
        old_state = self.agent_states.get(agent_id)
        self.agent_states[agent_id] = state

        # Track state change event if different
        if old_state and old_state != state:
            self.state_change_events.append(time.time())

    def record_collision(self) -> None:
        """Record a collision event."""
        self.collision_events.append(time.time())

    def record_goal_reached(self) -> None:
        """Record an agent reaching its goal."""
        self.goal_events.append(time.time())

    def record_frame(self) -> None:
        """Record frame timing for FPS calculation."""
        current_time = time.time()
        if self.last_frame_time:
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)
        self.last_frame_time = current_time

    def _prune_old_events(self, now: float) -> None:
        """Remove events older than window size.

        Args:
            now: Current time
        """
        cutoff = now - self.window_size

        while self.collision_events and self.collision_events[0] < cutoff:
            self.collision_events.popleft()

        while self.goal_events and self.goal_events[0] < cutoff:
            self.goal_events.popleft()

        while self.state_change_events and self.state_change_events[0] < cutoff:
            self.state_change_events.popleft()

    def _calculate_fps(self) -> float:
        """Calculate frames per second.

        Returns:
            FPS or 0 if no frames recorded
        """
        if not self.frame_times or len(self.frame_times) < 2:
            return 0.0

        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if avg_frame_time == 0:
            return 0.0

        return 1.0 / avg_frame_time

    def get_statistics(self) -> SimulationStats:
        """Get current simulation statistics.

        Returns:
            Complete statistics snapshot
        """
        now = time.time()
        self._prune_old_events(now)

        # Agent state distribution
        state_dist = AgentStateDistribution()
        for state in self.agent_states.values():
            if state == "moving":
                state_dist.moving += 1
            elif state == "idle":
                state_dist.idle += 1
            elif state == "goal_reached":
                state_dist.goal_reached += 1
            elif state == "collision":
                state_dist.collision += 1
            else:
                state_dist.other += 1

        # Event rates
        collision_rate = len(self.collision_events) / self.window_size if self.window_size > 0 else 0
        goal_rate = len(self.goal_events) / self.window_size if self.window_size > 0 else 0
        state_change_rate = len(self.state_change_events) / self.window_size if self.window_size > 0 else 0

        event_rates = EventRates(
            collisions_per_sec=collision_rate,
            goals_reached_per_sec=goal_rate,
            state_changes_per_sec=state_change_rate,
        )

        # Uptime
        uptime = now - self.start_time

        return SimulationStats(
            timestamp_ms=int(now * 1000),
            active_agents=len(self.agent_states),
            total_agents=len(self.agent_states),
            agent_state_distribution=state_dist,
            event_rates=event_rates,
            uptime_seconds=uptime,
            fps=self._calculate_fps(),
        )

    def to_dict(self) -> Dict:
        """Convert statistics to dictionary for serialization.

        Returns:
            Dictionary representation of statistics
        """
        stats = self.get_statistics()
        result = asdict(stats)
        result['agent_state_distribution'] = asdict(stats.agent_state_distribution)
        result['event_rates'] = asdict(stats.event_rates)
        return result


class StatisticsAggregator:
    """Aggregates statistics over time for trending and analysis."""

    def __init__(self, max_history: int = 1000):
        """Initialize aggregator.

        Args:
            max_history: Maximum number of statistics snapshots to keep
        """
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)

    def add_stats(self, stats: SimulationStats) -> None:
        """Add a statistics snapshot to history.

        Args:
            stats: Statistics snapshot
        """
        self.history.append(stats)

    def get_average_fps(self) -> float:
        """Get average FPS over history.

        Returns:
            Average FPS
        """
        if not self.history:
            return 0.0
        return sum(s.fps for s in self.history) / len(self.history)

    def get_average_active_agents(self) -> float:
        """Get average active agent count.

        Returns:
            Average agent count
        """
        if not self.history:
            return 0.0
        return sum(s.active_agents for s in self.history) / len(self.history)

    def get_trending_data(self, metric: str, points: int = 60) -> List[float]:
        """Get trending data for a specific metric.

        Args:
            metric: Metric name ('fps', 'active_agents', 'collisions_per_sec', etc.)
            points: Number of data points to return

        Returns:
            List of metric values
        """
        data = []
        start_idx = max(0, len(self.history) - points)

        for stats in list(self.history)[start_idx:]:
            if metric == "fps":
                data.append(stats.fps)
            elif metric == "active_agents":
                data.append(stats.active_agents)
            elif metric == "collisions_per_sec":
                data.append(stats.event_rates.collisions_per_sec)
            elif metric == "goals_reached_per_sec":
                data.append(stats.event_rates.goals_reached_per_sec)

        return data

    def get_history(self) -> List[Dict]:
        """Get entire history as dictionaries.

        Returns:
            List of statistics dictionaries
        """
        result = []
        for stats in self.history:
            data = asdict(stats)
            data['agent_state_distribution'] = asdict(stats.agent_state_distribution)
            data['event_rates'] = asdict(stats.event_rates)
            result.append(data)
        return result
