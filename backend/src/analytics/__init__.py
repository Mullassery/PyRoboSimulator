"""Analytics & Monitoring Dashboard - Phase 10 (CLI-based).

Real-time metrics visualization and simulation monitoring using Textual.
"""

from backend.src.analytics.metrics_collector import (
    MetricsCollector,
    SimulationMetrics,
    PerformanceMetrics,
    NarrativeMetrics,
    SensorMetrics,
    ValidationMetrics,
)
from backend.src.analytics.analytics_engine import AnalyticsEngine

# Optional CLI dashboard (requires textual)
try:
    from backend.src.analytics.cli_dashboard import (
        SimulationDashboard,
        AnalyticsDashboardApp,
        MetricsPanel,
        NarrativePanel,
        PerformancePanel,
        SensorPanel,
        ValidationPanel,
        ProgressPanel,
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
