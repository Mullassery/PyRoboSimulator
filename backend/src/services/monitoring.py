"""Monitoring and observability with Prometheus."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time
from typing import Callable

# Metrics
api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

api_request_count = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["query_type"],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5),
)

cache_hits = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

active_simulations = Gauge(
    "active_simulations",
    "Number of active simulations",
)

simulation_events = Counter(
    "simulation_events_total",
    "Total events recorded across simulations",
    ["event_type"],
)


class PrometheusMiddleware:
    """FastAPI middleware for Prometheus metrics."""

    def __init__(self, app):
        """Initialize middleware."""
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Process request and record metrics."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip metrics endpoint
        if scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Record request start time
        start_time = time.time()

        async def send_wrapper(message):
            """Wrap send to record response status."""
            if message["type"] == "http.response.start":
                status = message["status"]

                # Record metrics
                duration = time.time() - start_time
                api_request_duration.labels(method=method, endpoint=path).observe(duration)
                api_request_count.labels(
                    method=method,
                    endpoint=path,
                    status=status,
                ).inc()

            await send(message)

        await self.app(scope, receive, send_wrapper)


async def metrics_endpoint():
    """Prometheus metrics endpoint.

    Returns:
        Plain text metrics in Prometheus format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


class MetricsRecorder:
    """Utility for recording metrics in services."""

    @staticmethod
    def record_db_query(query_type: str, duration: float) -> None:
        """Record database query duration.

        Args:
            query_type: Type of query (select, insert, update, delete)
            duration: Query duration in seconds
        """
        db_query_duration.labels(query_type=query_type).observe(duration)

    @staticmethod
    def record_cache_hit(cache_type: str) -> None:
        """Record cache hit.

        Args:
            cache_type: Type of cache (scenario, simulation, etc.)
        """
        cache_hits.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_cache_miss(cache_type: str) -> None:
        """Record cache miss.

        Args:
            cache_type: Type of cache
        """
        cache_misses.labels(cache_type=cache_type).inc()

    @staticmethod
    def set_active_simulations(count: int) -> None:
        """Set number of active simulations.

        Args:
            count: Current number of active simulations
        """
        active_simulations.set(count)

    @staticmethod
    def record_simulation_event(event_type: str) -> None:
        """Record simulation event.

        Args:
            event_type: Type of event (collision, goal_reached, etc.)
        """
        simulation_events.labels(event_type=event_type).inc()
