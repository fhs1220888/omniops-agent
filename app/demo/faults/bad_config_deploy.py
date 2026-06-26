"""Bad config deploy demo scenario."""

from __future__ import annotations


def bad_config_deploy_scenario() -> dict:
    return {
        "scenario_name": "bad_config_deploy",
        "incident": {
            "id": "DEMO-BAD-CONFIG",
            "title": "OrderService bad config deploy caused connection errors",
            "service": "order-service",
            "severity": "high",
            "description": "Bad config deploy reduced connection capacity and caused timeouts.",
        },
        "logs": ["configuration max connections changed", "timeout errors after deploy"],
        "metrics": {"error_rate_percent": 7.4, "connection_capacity": "reduced"},
        "traces": ["order-service retries increased after deploy"],
    }
