"""Fake log query tools for the Week 1 MVP."""

from __future__ import annotations

from app.core.config import Settings
from app.core.incident_scenarios import detect_incident_scenario
from app.observability.factory import get_provider
from app.observability.normalizers import log_tool_payload, time_bounds


def query_logs(
    service: str,
    time_window: dict[str, str] | None,
    title: str = "",
    description: str | None = None,
) -> dict:
    settings = Settings.from_env()
    if settings.use_fake_tools:
        return query_fake_logs(service, time_window, title, description)
    start_time, end_time = time_bounds(time_window)
    result = get_provider(settings).query_logs(service, start_time, end_time)
    return log_tool_payload(result, service, time_window)


def query_fake_logs(
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
            "error_count": 31,
            "top_error": "MySQLQueryTimeout",
            "sample": "payment_order lookup exceeded 1500ms without composite index",
            "evidence_id": "evidence-log-mysql-slow-query",
            "evidence_summary": "MySQL slow query timeouts increased for payment_order lookups.",
            "finding_summary": "Log evidence points to repeated MySQL payment_order slow queries.",
            "observation_summary": "Found 31 MySQL slow query timeout log entries.",
            "patterns": [
                "payment_order lookup exceeded the slow query threshold.",
                "Timeouts began inside the selected investigation window.",
            ],
        }
    if scenario == "kafka_lag":
        return {
            "service": service,
            "time_window": time_window,
            "error_count": 24,
            "top_error": "ConsumerLagWarning",
            "sample": "inventory consumer lag exceeded threshold for stock-updates",
            "evidence_id": "evidence-log-kafka-consumer-lag",
            "evidence_summary": "Inventory consumer lag warnings increased during stock update delays.",
            "finding_summary": "Log evidence points to delayed inventory consumer processing.",
            "observation_summary": "Found 24 consumer lag warning log entries.",
            "patterns": [
                "stock update consumer lag exceeded threshold.",
                "Inventory processing delay started in the investigation window.",
            ],
        }
    if scenario == "bad_config_deploy":
        return {
            "service": service,
            "time_window": time_window,
            "error_count": 19,
            "top_error": "ConnectionCapacityReduced",
            "sample": "config deploy changed max connections from 100 to 20",
            "evidence_id": "evidence-log-bad-config-deploy",
            "evidence_summary": "Config deploy reduced connection capacity before timeout errors began.",
            "finding_summary": "Log evidence points to a bad configuration deploy.",
            "observation_summary": "Found 19 configuration-related connection error log entries.",
            "patterns": [
                "Connection capacity changed immediately before timeout errors.",
                "Errors began after the configuration deploy.",
            ],
        }
    return {
        "service": service,
        "time_window": time_window,
        "error_count": 42,
        "top_error": "RedisTimeoutException",
        "sample": "checkout failed: RedisTimeoutException after 250ms",
        "evidence_id": "evidence-log-redis-timeout",
        "evidence_summary": "Redis timeout errors increased during the investigation window.",
        "finding_summary": "Log evidence suggests cache dependency timeouts.",
        "observation_summary": "Found 42 Redis timeout log entries.",
        "patterns": [
            "RedisTimeoutException appeared repeatedly in checkout requests.",
            "Timeouts began inside the selected investigation window.",
        ],
    }
