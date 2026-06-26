"""MySQL slow query demo scenario."""

from __future__ import annotations


def mysql_slow_query_scenario() -> dict:
    return {
        "scenario_name": "mysql_slow_query",
        "incident": {
            "id": "DEMO-MYSQL-SLOW-QUERY",
            "title": "PaymentService MySQL slow query database timeout",
            "service": "payment-service",
            "severity": "high",
            "description": "Database timeout and slow payment_order query without index.",
        },
        "logs": ["slow query payment_order lookup exceeded threshold"],
        "metrics": {"db_cpu_percent": 91, "p95_latency_ms": 1800},
        "traces": ["payment-service -> mysql payment_order query took 1600ms"],
    }
