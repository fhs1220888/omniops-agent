"""Ground truth records for deterministic demo benchmark scenarios."""

from __future__ import annotations

from pydantic import BaseModel


class ScenarioGroundTruth(BaseModel):
    scenario_name: str
    expected_root_cause: str
    expected_evidence: list[str]
    expected_remediation: list[str]


GROUND_TRUTH = {
    "redis_timeout": ScenarioGroundTruth(
        scenario_name="redis_timeout",
        expected_root_cause="Redis connection pool exhaustion in order-service.",
        expected_evidence=[
            "evidence-metric-latency-spike",
            "evidence-trace-redis-bottleneck",
        ],
        expected_remediation=[
            "Restore the Redis connection pool limit to the last known safe value.",
            "Confirm P95 latency returns below 250ms and Redis timeout logs stop.",
        ],
    ),
    "mysql_slow_query": ScenarioGroundTruth(
        scenario_name="mysql_slow_query",
        expected_root_cause="Missing database index caused slow payment_order queries in payment-service.",
        expected_evidence=[
            "evidence-log-mysql-slow-query",
            "evidence-metric-mysql-db-latency",
            "evidence-trace-mysql-query-bottleneck",
        ],
        expected_remediation=[
            "Add the missing composite index for payment_order lookups.",
            "Verify database latency and payment P95 latency return to baseline.",
        ],
    ),
    "kafka_lag": ScenarioGroundTruth(
        scenario_name="kafka_lag",
        expected_root_cause="Inventory consumer processing lag delayed stock updates.",
        expected_evidence=[
            "evidence-log-kafka-consumer-lag",
            "memory-HIST-CONFIG-001",
        ],
        expected_remediation=[
            "Scale or unblock inventory consumers.",
            "Monitor consumer lag and stock update latency until stable.",
        ],
    ),
    "bad_config_deploy": ScenarioGroundTruth(
        scenario_name="bad_config_deploy",
        expected_root_cause="Bad configuration deploy reduced connection capacity for order-service.",
        expected_evidence=[
            "evidence-log-bad-config-deploy",
            "memory-HIST-REDIS-001",
        ],
        expected_remediation=[
            "Rollback the bad configuration.",
            "Add a pre-deploy configuration validation check.",
        ],
    ),
}
