"""Trace agent using fake trace data only."""

from __future__ import annotations

import asyncio

from app.agents.state import IncidentState
from app.models.incident import AgentFinding, EvidenceItem, ToolObservation
from app.tools.trace_tools import query_traces


async def trace_agent(state: IncidentState) -> dict:
    await asyncio.sleep(0)
    traces = query_traces(
        service=state["service"],
        time_window=state["time_window"],
        title=state["title"],
        description=state.get("description"),
    )
    evidence = EvidenceItem(
        id=traces["evidence_id"],
        source=traces.get("source", "traces"),
        type="trace_bottleneck",
        summary=traces["evidence_summary"],
        metadata={
            "service": state["service"],
            "slowest_span": traces["slowest_span"],
            "slowest_span_ms": traces["slowest_span_ms"],
            "trace_count": traces["trace_count"],
            "empty": str(traces.get("empty", False)),
            "error": str(traces.get("error") or ""),
        },
    )
    finding = AgentFinding(
        agent_name="trace_agent",
        confidence=0.86,
        summary=traces["finding_summary"],
        findings=traces["bottlenecks"],
        evidence_ids=[evidence.id],
        next_suggestion="Produce RCA and recommended actions.",
        risk_level="low",
    )
    observation = ToolObservation(
        tool_name="query_traces",
        source=traces.get("source", "traces"),
        summary=traces["observation_summary"],
        raw=traces,
    )
    return {
        "evidence": [*state["evidence"], evidence.model_dump()],
        "findings": [*state["findings"], finding.model_dump()],
        "tool_observations": [*state["tool_observations"], observation.model_dump()],
        "executed_tools": [*state["executed_tools"], "traces"],
        "investigation_steps": [*state["investigation_steps"], "traces:query_traces"],
    }
