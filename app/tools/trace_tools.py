"""Fake trace query tools for the Week 1.5 MVP."""

from __future__ import annotations

from app.core.config import Settings
from app.core.incident_scenarios import detect_incident_scenario
from app.observability.factory import get_provider
from app.observability.normalizers import time_bounds, trace_tool_payload


def query_traces(
    service: str,
    time_window: dict[str, str] | None,
    title: str = "",
    description: str | None = None,
) -> dict:
    settings = Settings.from_env()
    if settings.use_fake_tools:
        return query_fake_traces(service, time_window, title, description)
    start_time, end_time = time_bounds(time_window)
    result = get_provider(settings).query_traces(service, start_time, end_time)
    return trace_tool_payload(result, service, time_window)


def query_fake_traces(
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
            "slowest_span": "payment-service -> mysql SELECT payment_order",
            "slowest_span_ms": 1600,
            "trace_count": 22,
            "evidence_id": "evidence-trace-mysql-query-bottleneck",
            "evidence_summary": "Slow traces spend most time in MySQL payment_order lookups.",
            "finding_summary": "Trace evidence localizes the bottleneck to MySQL queries.",
            "observation_summary": "Slowest span is payment-service MySQL payment_order lookup.",
            "bottlenecks": [
                "Most slow traces wait on MySQL payment_order lookup.",
                "Redis and downstream service spans remain within baseline.",
            ],
        }
    return {
        "service": service,
        "time_window": time_window,
        "slowest_span": "order-service -> redis GET cart",
        "slowest_span_ms": 1850,
        "trace_count": 18,
        "evidence_id": "evidence-trace-redis-bottleneck",
        "evidence_summary": "Slow traces spend most time waiting on Redis cart reads.",
        "finding_summary": "Trace evidence localizes the bottleneck to Redis calls.",
        "observation_summary": "Slowest span is order-service Redis cart lookup.",
        "bottlenecks": [
            "Most slow traces wait on Redis GET cart.",
            "Database and downstream payment spans remain within baseline.",
        ],
    }
