"""Metric agent using fake metric data only."""

from __future__ import annotations

import asyncio

from app.agents.state import IncidentState
from app.models.incident import AgentFinding, EvidenceItem, ToolObservation
from app.tools.metric_tools import query_metrics


async def metric_agent(state: IncidentState) -> dict:
    await asyncio.sleep(0)
    metrics = query_metrics(
        service=state["service"],
        time_window=state["time_window"],
        title=state["title"],
        description=state.get("description"),
    )
    evidence = EvidenceItem(
        id=metrics["evidence_id"],
        source=metrics.get("source", "metrics"),
        type="metric_anomaly",
        summary=metrics["evidence_summary"],
        metadata={
            "service": state["service"],
            "p95_latency_ms": metrics["p95_latency_ms"],
            "baseline_p95_latency_ms": metrics["baseline_p95_latency_ms"],
            "error_rate_percent": metrics["error_rate_percent"],
            "empty": str(metrics.get("empty", False)),
            "error": str(metrics.get("error") or ""),
            **{
                key: value
                for key, value in metrics.items()
                if key
                in {
                    "redis_connections_used",
                    "redis_connections_limit",
                    "db_cpu_percent",
                    "slow_query_count",
                }
            },
        },
    )
    finding = AgentFinding(
        agent_name="metric_agent",
        confidence=0.84,
        summary=metrics["finding_summary"],
        findings=metrics["anomalies"],
        evidence_ids=[evidence.id],
        next_suggestion="Inspect traces for dependency wait time.",
        risk_level="low",
    )
    observation = ToolObservation(
        tool_name="query_metrics",
        source=metrics.get("source", "metrics"),
        summary=metrics["observation_summary"],
        raw=metrics,
    )
    return {
        "evidence": [*state["evidence"], evidence.model_dump()],
        "findings": [*state["findings"], finding.model_dump()],
        "tool_observations": [*state["tool_observations"], observation.model_dump()],
        "executed_tools": [*state["executed_tools"], "metrics"],
        "investigation_steps": [*state["investigation_steps"], "metrics:query_metrics"],
    }
