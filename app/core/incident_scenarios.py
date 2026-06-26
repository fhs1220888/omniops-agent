"""Small deterministic incident scenario helpers for local demo data."""

from __future__ import annotations


def detect_incident_scenario(
    *,
    title: str = "",
    service: str = "",
    description: str | None = None,
) -> str:
    text = " ".join([title, service, description or ""]).lower()
    if "mysql" in text or "payment_order" in text or "slow query" in text:
        return "mysql_slow_query"
    if "consumer lag" in text or "stock update" in text or "inventory updates" in text:
        return "kafka_lag"
    if "bad config" in text or "config deploy" in text or "configuration deploy" in text:
        return "bad_config_deploy"
    if "redis" in text:
        return "redis_timeout"
    if "order-service" in text and (
        "checkout" in text or "latency" in text or "timeout" in text
    ):
        return "redis_timeout"
    return "generic"
