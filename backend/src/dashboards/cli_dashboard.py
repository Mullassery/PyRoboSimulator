"""
CLI-based statistics dashboard using Textual.
Real-time terminal UI for monitoring simulation statistics.
"""

from textual.app import ComposeResult, App
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Header, Footer
from textual.reactive import reactive
from datetime import datetime
from typing import Optional

from src.services.statistics import StatisticsCalculator, StatisticsAggregator


class StatMetric(Static):
    """A single statistic metric display."""

    def __init__(self, label: str, initial_value: str = "0", color: str = "cyan"):
        super().__init__()
        self.label = label
        self.value = initial_value
        self.metric_color = color

    def render(self) -> str:
        """Render the metric."""
        return f"[{self.metric_color}]{self.label}[/]: {self.value}"

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self.value = value
        self.update(self.render())


class StateDistributionWidget(Static):
    """Display agent state distribution as ASCII bars."""

    def __init__(self):
        super().__init__()
        self.moving = 0
        self.idle = 0
        self.goal_reached = 0
        self.collision = 0

    def render(self) -> str:
        """Render state distribution bars."""
        max_width = 30
        total = self.moving + self.idle + self.goal_reached + self.collision

        if total == 0:
            return "[dim]No agents[/]"

        moving_pct = (self.moving / total) * 100 if total > 0 else 0
        idle_pct = (self.idle / total) * 100 if total > 0 else 0
        goal_pct = (self.goal_reached / total) * 100 if total > 0 else 0
        collision_pct = (self.collision / total) * 100 if total > 0 else 0

        moving_bar = "=" * int((moving_pct / 100) * max_width)
        idle_bar = "=" * int((idle_pct / 100) * max_width)
        goal_bar = "=" * int((goal_pct / 100) * max_width)
        collision_bar = "=" * int((collision_pct / 100) * max_width)

        return (
            f"[blue]Moving[/]       [{len(moving_bar):2d}%] {moving_bar:<{max_width}} {self.moving}\n"
            f"[dim]Idle[/]         [{len(idle_bar):2d}%] {idle_bar:<{max_width}} {self.idle}\n"
            f"[green]Goal Reached[/]  [{len(goal_bar):2d}%] {goal_bar:<{max_width}} {self.goal_reached}\n"
            f"[red]Collision[/]     [{len(collision_bar):2d}%] {collision_bar:<{max_width}} {self.collision}"
        )

    def update_distribution(self, moving: int, idle: int, goal_reached: int, collision: int) -> None:
        """Update state distribution."""
        self.moving = moving
        self.idle = idle
        self.goal_reached = goal_reached
        self.collision = collision
        self.update(self.render())


class EventRatesWidget(Static):
    """Display event rates."""

    def __init__(self):
        super().__init__()
        self.collisions = 0.0
        self.goals = 0.0
        self.state_changes = 0.0

    def render(self) -> str:
        """Render event rates."""
        return (
            f"[red]Collisions/sec[/]:      {self.collisions:6.2f}\n"
            f"[green]Goals Reached/sec[/]:   {self.goals:6.2f}\n"
            f"[cyan]State Changes/sec[/]:   {self.state_changes:6.2f}"
        )

    def update_rates(self, collisions: float, goals: float, state_changes: float) -> None:
        """Update event rates."""
        self.collisions = collisions
        self.goals = goals
        self.state_changes = state_changes
        self.update(self.render())


class PerformanceWidget(Static):
    """Display performance metrics with visual indicators."""

    def __init__(self):
        super().__init__()
        self.fps = 0.0
        self.uptime = 0.0

    def render(self) -> str:
        """Render performance metrics."""
        # FPS indicator
        if self.fps >= 60:
            fps_color = "green"
            fps_status = "▓" * 10
        elif self.fps >= 30:
            fps_color = "yellow"
            fps_status = "▓" * 5 + "░" * 5
        else:
            fps_color = "red"
            fps_status = "░" * 10

        hours = int(self.uptime // 3600)
        minutes = int((self.uptime % 3600) // 60)
        seconds = int(self.uptime % 60)

        return (
            f"[{fps_color}]FPS[/]: {self.fps:6.1f}  {fps_status}\n"
            f"[cyan]Uptime[/]: {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

    def update_performance(self, fps: float, uptime: float) -> None:
        """Update performance metrics."""
        self.fps = fps
        self.uptime = uptime
        self.update(self.render())


class SimulationDashboard(App):
    """CLI Dashboard for simulation statistics."""

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }

    #stats-container {
        border: solid $accent;
        padding: 1;
    }

    #core-metrics {
        height: 5;
        border: solid $accent;
        padding: 1;
    }

    #state-distribution {
        height: 7;
        border: solid $accent;
        padding: 1;
    }

    #event-rates {
        height: 5;
        border: solid $accent;
        padding: 1;
    }

    #performance {
        height: 4;
        border: solid $accent;
        padding: 1;
    }

    Static {
        width: 1fr;
    }

    .section-title {
        width: 1fr;
        text-align: left;
        text-style: bold;
    }
    """

    TITLE = "PyRoboSimulator - Statistics Dashboard"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
        super().__init__()
        self.calculator: Optional[StatisticsCalculator] = None
        self.update_interval = 0.1  # Update every 100ms

    def compose(self) -> ComposeResult:
        """Create the dashboard layout."""
        yield Header()

        with ScrollableContainer(id="stats-container"):
            # Core Metrics
            with Vertical(id="core-metrics"):
                yield Static("[bold]Core Metrics[/]", classes="section-title")
                with Horizontal():
                    self.agents_metric = StatMetric("Active Agents", "0", "cyan")
                    self.fps_metric = StatMetric("FPS", "0.0", "green")
                    yield self.agents_metric
                    yield self.fps_metric

            # State Distribution
            with Vertical(id="state-distribution"):
                yield Static("[bold]Agent State Distribution[/]", classes="section-title")
                self.state_widget = StateDistributionWidget()
                yield self.state_widget

            # Event Rates
            with Vertical(id="event-rates"):
                yield Static("[bold]Event Rates[/]", classes="section-title")
                self.event_widget = EventRatesWidget()
                yield self.event_widget

            # Performance
            with Vertical(id="performance"):
                yield Static("[bold]Performance[/]", classes="section-title")
                self.performance_widget = PerformanceWidget()
                yield self.performance_widget

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the dashboard."""
        self.title = "PyRoboSimulator - Statistics Dashboard"
        self.set_interval(self.update_display, self.update_interval)

    def set_calculator(self, calculator: StatisticsCalculator) -> None:
        """Set the statistics calculator."""
        self.calculator = calculator

    def update_display(self) -> None:
        """Update all display widgets with current statistics."""
        if not self.calculator:
            return

        stats = self.calculator.get_statistics()

        # Update core metrics
        self.agents_metric.update_value(str(stats.active_agents))
        self.fps_metric.update_value(f"{stats.fps:.1f}")

        # Update state distribution
        self.state_widget.update_distribution(
            stats.agent_state_distribution.moving,
            stats.agent_state_distribution.idle,
            stats.agent_state_distribution.goal_reached,
            stats.agent_state_distribution.collision,
        )

        # Update event rates
        self.event_widget.update_rates(
            stats.event_rates.collisions_per_sec,
            stats.event_rates.goals_reached_per_sec,
            stats.event_rates.state_changes_per_sec,
        )

        # Update performance
        self.performance_widget.update_performance(stats.fps, stats.uptime_seconds)


def create_dashboard(calculator: StatisticsCalculator) -> SimulationDashboard:
    """Create and initialize a statistics dashboard.

    Args:
        calculator: Statistics calculator instance

    Returns:
        Configured dashboard instance
    """
    dashboard = SimulationDashboard()
    dashboard.set_calculator(calculator)
    return dashboard


if __name__ == "__main__":
    # Example usage
    from src.services.statistics import StatisticsCalculator
    import asyncio

    calculator = StatisticsCalculator()

    # Simulate some data
    async def simulate():
        for i in range(100):
            calculator.update_agent_state(i, "moving" if i % 3 == 0 else "idle")
            calculator.record_frame()
            if i % 10 == 0:
                calculator.record_collision()
            if i % 15 == 0:
                calculator.record_goal_reached()
            await asyncio.sleep(0.01)

    app = create_dashboard(calculator)
    # Run dashboard in a separate way since it's async
    app.run()
