"""Redis timeout demo scenario."""

from __future__ import annotations


def redis_timeout_scenario() -> dict:
    return {
        "scenario_name": "redis_timeout",
        "incident": {
            "id": "DEMO-REDIS-TIMEOUT",
            "title": "OrderService Redis timeout and checkout latency",
            "service": "order-service",
            "severity": "high",
            "description": "RedisTimeoutException, P95 latency spike, Redis pool saturation.",
        },
        "logs": ["RedisTimeoutException after 250ms", "checkout request failed"],
        "metrics": {"p95_latency_ms": 2400, "redis_connections": "100/100"},
        "traces": ["order-service -> redis GET cart took 1850ms"],
    }
