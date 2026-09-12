"""Analytics & Monitoring Dashboard - Phase 10 (CLI-based).

Real-time metrics visualization and simulation monitoring using Textual.
"""

from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.metrics_collector import (
    MetricsCollector,
    NarrativeMetrics,
    PerformanceMetrics,
    SensorMetrics,
    SimulationMetrics,
    ValidationMetrics,
)

# Optional CLI dashboard (requires textual)
try:
    from src.analytics.cli_dashboard import (
        AnalyticsDashboardApp,
        MetricsPanel,
        NarrativePanel,
        PerformancePanel,
        ProgressPanel,
        SensorPanel,
        SimulationDashboard,
        ValidationPanel,
    )
except ImportError:
    # Textual not installed, CLI dashboard not available
    SimulationDashboard = None
    AnalyticsDashboardApp = None
    MetricsPanel = None
    NarrativePanel = None
    PerformancePanel = None
    SensorPanel = None
    ValidationPanel = None
    ProgressPanel = None

__all__ = [
    "MetricsCollector",
    "SimulationMetrics",
    "PerformanceMetrics",
    "NarrativeMetrics",
    "SensorMetrics",
    "ValidationMetrics",
    "AnalyticsEngine",
    "SimulationDashboard",
    "AnalyticsDashboardApp",
    "MetricsPanel",
    "NarrativePanel",
    "PerformancePanel",
    "SensorPanel",
    "ValidationPanel",
    "ProgressPanel",
]
