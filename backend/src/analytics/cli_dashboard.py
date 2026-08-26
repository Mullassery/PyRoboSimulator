"""CLI Dashboard - Real-time metrics visualization using Textual.

Interactive terminal UI for simulation monitoring and control.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from textual.app import ComposeResult, RenderableType
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, Button, ProgressBar
from textual.binding import Binding
from textual.screen import Screen
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Console
from rich.live import Live

from src.analytics.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class MetricsPanel(Static):
    """Display real-time simulation metrics."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render metrics panel."""
        latest_sim = self._collector.get_latest_simulation_metrics()

        if not latest_sim:
            return Panel("No simulation data", title="Metrics")

        # Create metrics table
        table = Table(title="Simulation Metrics", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Time", f"{latest_sim.elapsed_time_sec:.2f}s")
        table.add_row("Position", f"({latest_sim.current_position[0]:.2f}, {latest_sim.current_position[1]:.2f}, {latest_sim.current_position[2]:.2f})")
        table.add_row("Velocity", f"{latest_sim.current_velocity:.2f} m/s")
        table.add_row("Acceleration", f"{latest_sim.current_acceleration:.2f} m/s²")
        table.add_row("Distance", f"{latest_sim.distance_traveled:.2f} m")
        table.add_row("Goals", f"{latest_sim.goals_completed}/{latest_sim.goals_total}")
        table.add_row("Constraints Violated", str(latest_sim.constraints_violated))
        table.add_row("Simulation Speed", f"{latest_sim.simulation_speed:.1f}x")
        table.add_row("Sensor Frames", str(latest_sim.sensor_frames_received))

        return Panel(table, title="Metrics", expand=True)


class NarrativePanel(Static):
    """Display narrative execution progress."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render narrative panel."""
        narrative = self._collector.get_narrative_metrics()

        if not narrative:
            return Panel("No narrative loaded", title="Narrative")

        # Create narrative table
        table = Table(title=f"Narrative: {narrative.narrative_type}", show_header=True, header_style="bold blue")
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("ID", narrative.narrative_id)
        table.add_row("Type", narrative.narrative_type)
        table.add_row("Sequence", f"{narrative.current_sequence}/{narrative.total_sequences}")
        table.add_row("Progress", f"{narrative.sequence_progress_pct:.1f}%")
        table.add_row("Events", f"{narrative.events_triggered}/{narrative.total_events}")

        # Add goal progress
        for goal_id, progress in narrative.goal_progress.items():
            table.add_row(f"Goal: {goal_id}", f"{progress:.1%}")

        # Add active constraints
        if narrative.active_constraints:
            table.add_row("Constraints", ", ".join(narrative.active_constraints[:2]))

        return Panel(table, title="Narrative", expand=True)


class PerformancePanel(Static):
    """Display performance metrics."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render performance panel."""
        latest_perf = self._collector.get_latest_performance_metrics()

        if not latest_perf:
            return Panel("No performance data", title="Performance")

        # Create performance table
        table = Table(title="Performance", show_header=True, header_style="bold yellow")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("FPS", f"{latest_perf.simulation_fps:.1f}")
        table.add_row("Frame Time", f"{latest_perf.average_frame_time_ms:.2f} ms")
        table.add_row("CPU Usage", f"{latest_perf.cpu_usage_pct:.1f}%")
        table.add_row("Memory", f"{latest_perf.memory_usage_mb:.1f} MB")
        table.add_row("Events/sec", f"{latest_perf.events_per_second:.1f}")
        table.add_row("Total Events", str(latest_perf.total_events_processed))

        return Panel(table, title="Performance", expand=True)


class SensorPanel(Static):
    """Display sensor status."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render sensor panel."""
        sensors = self._collector.get_sensor_metrics()

        if not sensors:
            return Panel("No sensors", title="Sensors")

        # Create sensor table
        table = Table(title="Active Sensors", show_header=True, header_style="bold green")
        table.add_column("Sensor", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("FPS", style="green")
        table.add_column("Latency", style="green")

        for sensor_name, metrics in sensors.items():
            if metrics.is_active:
                table.add_row(
                    sensor_name,
                    metrics.sensor_type,
                    f"{metrics.fps:.1f}",
                    f"{metrics.frame_latency_ms:.1f} ms",
                )

        return Panel(table, title="Sensors", expand=True)


class ValidationPanel(Static):
    """Display sim/real validation results."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render validation panel."""
        validation = self._collector.get_validation_metrics()

        if not validation:
            return Panel("No validation data", title="Validation")

        # Color code based on validity
        validity_color = "green" if validation.is_valid else "red"
        validity_text = "✓ VALID" if validation.is_valid else "✗ INVALID"

        # Create validation table
        table = Table(title="Sim/Real Validation", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Error", style="green")

        table.add_row("Distance Error", f"{validation.real_vs_sim_distance_error:.1f}%")
        table.add_row("Velocity Error", f"{validation.real_vs_sim_velocity_error:.1f}%")
        table.add_row("Time Error", f"{validation.real_vs_sim_time_error:.1f}%")
        table.add_row("Overall Similarity", f"{validation.overall_similarity:.1%}")

        text_validity = Text(validity_text, style=validity_color)
        panel_content = f"{table}\n{validity_text}"

        return Panel(table, title=f"Validation [{validity_text}]", expand=True)


class ProgressPanel(Static):
    """Display simulation progress."""

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector

    def render(self) -> RenderableType:
        """Render progress panel."""
        latest_sim = self._collector.get_latest_simulation_metrics()
        narrative = self._collector.get_narrative_metrics()

        progress_lines = []

        # Simulation progress
        if latest_sim and narrative and narrative.goals_total > 0:
            goal_progress = (latest_sim.goals_completed / narrative.goals_total) * 100
            progress_lines.append(f"Goals:        [{goal_progress:5.1f}%] {'█' * int(goal_progress / 5)}{'░' * (20 - int(goal_progress / 5))}")

        # Sequence progress
        if narrative and narrative.total_sequences > 0:
            seq_progress = narrative.sequence_progress_pct
            progress_lines.append(f"Sequence:     [{seq_progress:5.1f}%] {'█' * int(seq_progress / 5)}{'░' * (20 - int(seq_progress / 5))}")

        # Event progress
        if narrative and narrative.total_events > 0:
            event_progress = (narrative.events_triggered / narrative.total_events) * 100
            progress_lines.append(f"Events:       [{event_progress:5.1f}%] {'█' * int(event_progress / 5)}{'░' * (20 - int(event_progress / 5))}")

        if not progress_lines:
            return Panel("No progress data", title="Progress")

        content = "\n".join(progress_lines)
        return Panel(content, title="Progress Bars")


class ControlPanel(Static):
    """Display control commands."""

    def render(self) -> RenderableType:
        """Render control panel."""
        content = """
[cyan]Keyboard Controls:[/cyan]
[yellow]p[/yellow] - Play/Pause        [yellow]s[/yellow] - Stop           [yellow]r[/yellow] - Reset
[yellow]+[/yellow] - Speed up          [yellow]-[/yellow] - Slow down      [yellow]h[/yellow] - History (10s)
[yellow]v[/yellow] - Toggle sensors    [yellow]t[/yellow] - Toggle narrative [yellow]q[/yellow] - Quit
        """
        return Panel(content, title="Controls")


class SimulationDashboard(Screen):
    """Main simulation monitoring dashboard."""

    BINDINGS = [
        Binding("p", "play_pause", "Play/Pause"),
        Binding("s", "stop", "Stop"),
        Binding("r", "reset", "Reset"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, collector: MetricsCollector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collector = collector
        self._is_playing = False

    def compose(self) -> ComposeResult:
        """Compose dashboard layout."""
        yield Header()

        with Vertical():
            # Top row: Metrics and Narrative
            with Horizontal():
                yield MetricsPanel(self._collector, id="metrics", border=True)
                yield NarrativePanel(self._collector, id="narrative", border=True)

            # Middle row: Performance and Sensors
            with Horizontal():
                yield PerformancePanel(self._collector, id="performance", border=True)
                yield SensorPanel(self._collector, id="sensors", border=True)

            # Validation row
            yield ValidationPanel(self._collector, id="validation", border=True)

            # Progress row
            yield ProgressPanel(self._collector, id="progress", border=True)

            # Control row
            yield ControlPanel(id="controls", border=True)

        yield Footer()

    def action_play_pause(self) -> None:
        """Toggle play/pause."""
        self._is_playing = not self._is_playing
        title = "Play" if not self._is_playing else "Pause"
        self.notify(f"{title} simulation", timeout=2)

    def action_stop(self) -> None:
        """Stop simulation."""
        self._is_playing = False
        self.notify("Simulation stopped", timeout=2)

    def action_reset(self) -> None:
        """Reset metrics."""
        self._collector.reset()
        self.notify("Metrics reset", timeout=2)

    def action_quit(self) -> None:
        """Quit application."""
        self.app.exit()


class AnalyticsDashboardApp:
    """Analytics dashboard application controller."""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize dashboard app.

        Args:
            collector: Metrics collector (creates new if not provided)
        """
        self._collector = collector or MetricsCollector()

    def run(self) -> None:
        """Run dashboard in interactive mode."""
        from textual.app import App

        class DashboardApp(App):
            def on_mount(self) -> None:
                self.push_screen(SimulationDashboard(self._collector))

            _collector = self._collector

        app = DashboardApp()
        app.run()

    def get_collector(self) -> MetricsCollector:
        """Get metrics collector.

        Returns:
            MetricsCollector instance
        """
        return self._collector

    def print_summary(self) -> None:
        """Print metrics summary to console."""
        from rich.console import Console

        console = Console()
        summary = self._collector.get_summary()

        # Print summary
        table = Table(title="Simulation Summary", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Metric", style="yellow")
        table.add_column("Value", style="green")

        for category, data in summary.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    table.add_row(category, key, str(value))
            else:
                table.add_row(category, "Value", str(data))

        console.print(table)
