"""Deterministic demo fault scenarios."""

from app.demo.faults.bad_config_deploy import bad_config_deploy_scenario
from app.demo.faults.kafka_lag import kafka_lag_scenario
from app.demo.faults.mysql_slow_query import mysql_slow_query_scenario
from app.demo.faults.redis_timeout import redis_timeout_scenario

SCENARIOS = {
    "redis_timeout": redis_timeout_scenario,
    "mysql_slow_query": mysql_slow_query_scenario,
    "kafka_lag": kafka_lag_scenario,
    "bad_config_deploy": bad_config_deploy_scenario,
}
