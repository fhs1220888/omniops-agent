"""Tool metadata registry for the lightweight Tool Gateway."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ToolRiskLevel = Literal["low", "medium", "high", "critical"]


class ToolSpec(BaseModel):
    name: str
    description: str
    risk_level: ToolRiskLevel
    approval_required: bool
    timeout_seconds: float
    max_calls_per_incident: int


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "query_logs": ToolSpec(
        name="query_logs",
        description="Read-only fake log query.",
        risk_level="low",
        approval_required=False,
        timeout_seconds=2.0,
        max_calls_per_incident=5,
    ),
    "query_metrics": ToolSpec(
        name="query_metrics",
        description="Read-only fake metric query.",
        risk_level="low",
        approval_required=False,
        timeout_seconds=2.0,
        max_calls_per_incident=5,
    ),
    "query_traces": ToolSpec(
        name="query_traces",
        description="Read-only fake trace query.",
        risk_level="low",
        approval_required=False,
        timeout_seconds=2.0,
        max_calls_per_incident=5,
    ),
    "query_memory": ToolSpec(
        name="query_memory",
        description="Read-only local incident memory recall.",
        risk_level="low",
        approval_required=False,
        timeout_seconds=2.0,
        max_calls_per_incident=5,
    ),
    "restart_service": ToolSpec(
        name="restart_service",
        description="Restart a service.",
        risk_level="high",
        approval_required=True,
        timeout_seconds=10.0,
        max_calls_per_incident=1,
    ),
    "execute_sql": ToolSpec(
        name="execute_sql",
        description="Execute SQL against a database.",
        risk_level="high",
        approval_required=True,
        timeout_seconds=10.0,
        max_calls_per_incident=1,
    ),
    "read_env_vars": ToolSpec(
        name="read_env_vars",
        description="Read process environment variables.",
        risk_level="critical",
        approval_required=False,
        timeout_seconds=1.0,
        max_calls_per_incident=0,
    ),
    "delete_database": ToolSpec(
        name="delete_database",
        description="Delete database contents.",
        risk_level="critical",
        approval_required=False,
        timeout_seconds=1.0,
        max_calls_per_incident=0,
    ),
}


def get_tool_spec(tool_name: str) -> ToolSpec | None:
    return TOOL_REGISTRY.get(tool_name)
