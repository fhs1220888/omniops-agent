"""Fake metric query tools for the Week 1 MVP."""

from __future__ import annotations

from app.core.config import Settings
from app.core.incident_scenarios import detect_incident_scenario
from app.observability.factory import get_provider
from app.observability.normalizers import metric_tool_payload, time_bounds


def query_metrics(
    service: str,
    time_window: dict[str, str] | None,
    title: str = "",
    description: str | None = None,
) -> dict:
    settings = Settings.from_env()
    if settings.use_fake_tools:
        return query_fake_metrics(service, time_window, title, description)
    start_time, end_time = time_bounds(time_window)
    result = get_provider(settings).query_metrics(service, start_time, end_time)
    return metric_tool_payload(result, service, time_window)


def query_fake_metrics(
    service: str,
    time_window: dict[str, str] | None,
    title: str = "",
    description: str | None = None,
) -> dict:
    scenario = detect_incident_scenario(
        title=title,
        service=service,
        description=description,
    )
    if scenario == "mysql_slow_query":
        return {
            "service": service,
            "time_window": time_window,
            "p95_latency_ms": 1800,
            "baseline_p95_latency_ms": 130,
            "error_rate_percent": 5.8,
            "db_cpu_percent": 91,
            "slow_query_count": 64,
            "evidence_id": "evidence-metric-mysql-db-latency",
            "evidence_summary": "Database CPU, slow query count, and payment latency spiked together.",
            "finding_summary": "Metrics support a MySQL slow query saturation hypothesis.",
            "observation_summary": "P95 latency and MySQL slow query count are both above threshold.",
            "anomalies": [
                "P95 latency increased from 130ms to 1800ms.",
                "MySQL CPU reached 91% while slow query count spiked.",
            ],
        }
    return {
        "service": service,
        "time_window": time_window,
        "p95_latency_ms": 2400,
        "baseline_p95_latency_ms": 120,
        "error_rate_percent": 8.5,
        "redis_connections_used": 100,
        "redis_connections_limit": 100,
        "evidence_id": "evidence-metric-latency-spike",
        "evidence_summary": "P95 latency and Redis connection usage spiked together.",
        "finding_summary": "Metrics support a Redis connection saturation hypothesis.",
        "observation_summary": "P95 latency and Redis connection usage are both above threshold.",
        "anomalies": [
            "P95 latency increased from 120ms to 2400ms.",
            "Redis connections reached 100/100 during the same window.",
        ],
    }
