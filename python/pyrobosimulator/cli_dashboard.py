"""PyRoboSimulator Dashboard - World gen, missions, ROS 2 integration"""

import sys, platform, json
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DashboardMetrics:
    timestamp: str
    title: str
    metrics: Dict[str, Any]
    alerts: list
    recommendations: list


def get_dashboard_impl(product_name: str):
    try:
        from rich.console import Console
        return RichDashboard(product_name)
    except ImportError:
        return SimpleDashboard(product_name)


class SimpleDashboard:
    def __init__(self, product_name: str):
        self.product_name = product_name

    def render(self, data: DashboardMetrics) -> None:
        print(f"\n{'='*80}\n✓ {data.title}\n  {data.timestamp}\n{'='*80}\n")
        for key, value in data.metrics.items():
            print(f"  {key}: {value}")


class RichDashboard:
    def __init__(self, product_name: str):
        self.product_name = product_name
        from rich.console import Console
        self.console = Console()

    def render(self, data: DashboardMetrics) -> None:
        from rich.table import Table
        self.console.print(f"\n[bold cyan]✓ {data.title}[/bold cyan]")
        table = Table()
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for key, value in data.metrics.items():
            table.add_row(key, str(value))
        self.console.print(table)


class PyRoboSimulatorDashboard:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "./pyrobosimulator.yaml"
        self.dashboard = get_dashboard_impl("PyRoboSimulator v0.1")

    def get_mock_metrics(self) -> DashboardMetrics:
        # NOTE: these are hardcoded sample values, not a live read of any
        # running simulation -- this CLI has no wiring to the FastAPI
        # backend or a real World instance. Labeled "(sample data)" in the
        # title so this can't be mistaken for real telemetry.
        return DashboardMetrics(
            datetime.now().isoformat(),
            "PyRoboSimulator World Engine Dashboard (sample data, not live)",
            {
                "Status": "example only — not connected to a running simulation",
                "World Instances": "3 (sample)",
                "Agents": "12 (sample)",
                "Narratives": "47 (sample)",
                "ROS 2 Nodes": "8 (sample)",
                "Sensor Fidelity": "RGB/Depth/Lidar/Thermal (sample)",
                "Physics Accuracy": "98.4% (sample)",
                "UE5 Render FPS": "120 fps (sample)",
            },
            [],
            []
        )

    def run_dashboard(self, interactive: bool = True) -> None:
        metrics = self.get_mock_metrics()
        if interactive:
            self.dashboard.run()
        else:
            self.dashboard.render(metrics)

    def export_json(self, output_file: str) -> None:
        metrics = self.get_mock_metrics()
        with open(output_file, 'w') as f:
            json.dump({"metrics": metrics.metrics}, f)
