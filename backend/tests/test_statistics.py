"""
Tests for the statistics calculator and aggregator.
"""

import pytest
import time
from src.services.statistics import (
    StatisticsCalculator,
    StatisticsAggregator,
    AgentStateDistribution,
    EventRates,
)


class TestStatisticsCalculator:
    """Test statistics calculation."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = StatisticsCalculator(window_size_seconds=10)
        assert calc.window_size == 10
        assert len(calc.agent_states) == 0

    def test_update_agent_state(self):
        """Test updating agent state."""
        calc = StatisticsCalculator()
        calc.update_agent_state(1, "moving")
        assert calc.agent_states[1] == "moving"

        calc.update_agent_state(1, "idle")
        assert calc.agent_states[1] == "idle"

    def test_record_collision(self):
        """Test recording collision events."""
        calc = StatisticsCalculator()
        calc.record_collision()
        calc.record_collision()
        assert len(calc.collision_events) == 2

    def test_record_goal_reached(self):
        """Test recording goal reached events."""
        calc = StatisticsCalculator()
        calc.record_goal_reached()
        assert len(calc.goal_events) == 1

    def test_state_change_tracking(self):
        """Test state change event tracking."""
        calc = StatisticsCalculator()
        calc.update_agent_state(1, "idle")
        calc.update_agent_state(1, "moving")
        assert len(calc.state_change_events) == 1  # Transition from idle to moving

    def test_get_statistics_with_no_agents(self):
        """Test statistics with no agents."""
        calc = StatisticsCalculator()
        stats = calc.get_statistics()

        assert stats.active_agents == 0
        assert stats.total_agents == 0
        assert stats.agent_state_distribution.total() == 0

    def test_get_statistics_with_agents(self):
        """Test statistics calculation with agents."""
        calc = StatisticsCalculator()

        # Add various agents in different states
        calc.update_agent_state(1, "moving")
        calc.update_agent_state(2, "moving")
        calc.update_agent_state(3, "idle")
        calc.update_agent_state(4, "goal_reached")
        calc.update_agent_state(5, "collision")

        stats = calc.get_statistics()

        assert stats.active_agents == 5
        assert stats.agent_state_distribution.moving == 2
        assert stats.agent_state_distribution.idle == 1
        assert stats.agent_state_distribution.goal_reached == 1
        assert stats.agent_state_distribution.collision == 1

    def test_event_rates_calculation(self):
        """Test event rate calculations."""
        calc = StatisticsCalculator(window_size_seconds=1)

        # Record some events
        calc.record_collision()
        calc.record_collision()
        calc.record_goal_reached()

        stats = calc.get_statistics()

        # Rates should be approximately equal to counts (within 1 second window)
        assert stats.event_rates.collisions_per_sec >= 1.5
        assert stats.event_rates.goals_reached_per_sec >= 0.5

    def test_uptime_calculation(self):
        """Test uptime tracking."""
        calc = StatisticsCalculator()
        time.sleep(0.1)

        stats = calc.get_statistics()
        assert stats.uptime_seconds >= 0.1

    def test_fps_calculation(self):
        """Test FPS calculation."""
        calc = StatisticsCalculator()

        # Record some frames
        for _ in range(60):
            calc.record_frame()
            time.sleep(0.01)  # ~10ms per frame = ~100 FPS

        stats = calc.get_statistics()
        # FPS should be around 100, with some tolerance
        assert 50 < stats.fps < 150

    def test_event_pruning(self):
        """Test old events are pruned."""
        calc = StatisticsCalculator(window_size_seconds=0.1)

        # Record event
        calc.record_collision()
        assert len(calc.collision_events) == 1

        # Wait for event to become stale
        time.sleep(0.2)

        # Get statistics (which should prune old events)
        calc.get_statistics()
        assert len(calc.collision_events) == 0

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        calc = StatisticsCalculator()
        calc.update_agent_state(1, "moving")
        calc.record_collision()

        stats_dict = calc.to_dict()

        assert "timestamp_ms" in stats_dict
        assert "active_agents" in stats_dict
        assert stats_dict["active_agents"] == 1
        assert "agent_state_distribution" in stats_dict
        assert "event_rates" in stats_dict


class TestStatisticsAggregator:
    """Test statistics aggregation and trending."""

    def test_initialization(self):
        """Test aggregator initialization."""
        agg = StatisticsAggregator(max_history=100)
        assert len(agg.history) == 0

    def test_add_stats(self):
        """Test adding statistics snapshots."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()
        calc.update_agent_state(1, "moving")

        stats = calc.get_statistics()
        agg.add_stats(stats)

        assert len(agg.history) == 1

    def test_max_history_limit(self):
        """Test that history is limited by max_history."""
        agg = StatisticsAggregator(max_history=5)
        calc = StatisticsCalculator()

        for i in range(10):
            calc.update_agent_state(i, "moving")
            stats = calc.get_statistics()
            agg.add_stats(stats)

        # Should only keep 5 most recent
        assert len(agg.history) == 5

    def test_average_fps(self):
        """Test average FPS calculation."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        for _ in range(5):
            calc.record_frame()
            stats = calc.get_statistics()
            agg.add_stats(stats)

        avg_fps = agg.get_average_fps()
        assert avg_fps >= 0

    def test_average_active_agents(self):
        """Test average active agent count."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        # Progressively add agents
        for i in range(1, 6):
            for j in range(i):
                calc.update_agent_state(j, "moving")
            stats = calc.get_statistics()
            agg.add_stats(stats)

        avg_agents = agg.get_average_active_agents()
        assert avg_agents > 0

    def test_trending_data_fps(self):
        """Test getting trending FPS data."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        for _ in range(10):
            calc.record_frame()
            stats = calc.get_statistics()
            agg.add_stats(stats)

        trending = agg.get_trending_data("fps", points=10)
        assert len(trending) <= 10

    def test_trending_data_agents(self):
        """Test getting trending agent count data."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        for i in range(5):
            for j in range(i):
                calc.update_agent_state(j, "moving")
            stats = calc.get_statistics()
            agg.add_stats(stats)

        trending = agg.get_trending_data("active_agents", points=5)
        assert len(trending) > 0

    def test_trending_data_collisions(self):
        """Test getting trending collision data."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        for i in range(5):
            if i % 2 == 0:
                calc.record_collision()
            stats = calc.get_statistics()
            agg.add_stats(stats)

        trending = agg.get_trending_data("collisions_per_sec", points=5)
        assert len(trending) > 0

    def test_get_history(self):
        """Test retrieving entire history."""
        agg = StatisticsAggregator()
        calc = StatisticsCalculator()

        for i in range(3):
            calc.update_agent_state(i, "moving")
            stats = calc.get_statistics()
            agg.add_stats(stats)

        history = agg.get_history()
        assert len(history) == 3

        # Each history item should be a dict
        for item in history:
            assert isinstance(item, dict)
            assert "timestamp_ms" in item
            assert "agent_state_distribution" in item


class TestAgentStateDistribution:
    """Test agent state distribution."""

    def test_initialization(self):
        """Test distribution initialization."""
        dist = AgentStateDistribution()
        assert dist.moving == 0
        assert dist.idle == 0
        assert dist.total() == 0

    def test_total_calculation(self):
        """Test total calculation."""
        dist = AgentStateDistribution(moving=2, idle=1, goal_reached=3)
        assert dist.total() == 6


class TestEventRates:
    """Test event rates."""

    def test_initialization(self):
        """Test event rates initialization."""
        rates = EventRates()
        assert rates.collisions_per_sec == 0.0
        assert rates.goals_reached_per_sec == 0.0


@pytest.mark.integration
class TestStatisticsIntegration:
    """Integration tests for statistics system."""

    def test_full_workflow(self):
        """Test complete statistics workflow."""
        calc = StatisticsCalculator()
        agg = StatisticsAggregator()

        # Simulate a small scenario
        for step in range(10):
            # Add agents
            for i in range(step):
                if i % 3 == 0:
                    calc.update_agent_state(i, "moving")
                elif i % 3 == 1:
                    calc.update_agent_state(i, "idle")
                else:
                    calc.update_agent_state(i, "goal_reached")

            # Record some events
            if step % 2 == 0:
                calc.record_collision()
            if step % 3 == 0:
                calc.record_goal_reached()

            # Record frame and get stats
            calc.record_frame()
            stats = calc.get_statistics()
            agg.add_stats(stats)

        # Verify aggregator has history
        assert len(agg.history) == 10
        assert agg.get_average_active_agents() > 0
        assert len(agg.get_history()) == 10
