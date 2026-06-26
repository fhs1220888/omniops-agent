"""Kafka lag demo scenario with fake local data only."""

from __future__ import annotations


def kafka_lag_scenario() -> dict:
    return {
        "scenario_name": "kafka_lag",
        "incident": {
            "id": "DEMO-KAFKA-LAG",
            "title": "InventoryService consumer lag delayed stock updates",
            "service": "inventory-service",
            "severity": "medium",
            "description": "Consumer lag increased and stock update latency rose.",
        },
        "logs": ["inventory consumer processing delay"],
        "metrics": {"consumer_lag": 12000, "update_latency_ms": 950},
        "traces": ["inventory-service downstream write took 800ms"],
    }
