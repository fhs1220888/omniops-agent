"""Log agent using fake log data only."""

from __future__ import annotations

import asyncio

from app.agents.state import IncidentState
from app.models.incident import AgentFinding, EvidenceItem, ToolObservation
from app.tools.log_tools import query_logs


async def log_agent(state: IncidentState) -> dict:
    await asyncio.sleep(0)
    logs = query_logs(
        service=state["service"],
        time_window=state["time_window"],
        title=state["title"],
        description=state.get("description"),
    )
    evidence = EvidenceItem(
        id=logs["evidence_id"],
        source=logs.get("source", "logs"),
        type="log_pattern",
        summary=logs["evidence_summary"],
        metadata={
            "service": state["service"],
            "error_count": logs["error_count"],
            "top_error": logs["top_error"],
            "sample": logs["sample"],
            "empty": str(logs.get("empty", False)),
            "error": str(logs.get("error") or ""),
        },
    )
    finding = AgentFinding(
        agent_name="log_agent",
        confidence=0.78,
        summary=logs["finding_summary"],
        findings=logs["patterns"],
        evidence_ids=[evidence.id],
        next_suggestion="Compare the timeout window with service metrics.",
        risk_level="low",
    )
    observation = ToolObservation(
        tool_name="query_logs",
        source=logs.get("source", "logs"),
        summary=logs["observation_summary"],
        raw=logs,
    )
    return {
        "evidence": [*state["evidence"], evidence.model_dump()],
        "findings": [*state["findings"], finding.model_dump()],
        "tool_observations": [*state["tool_observations"], observation.model_dump()],
        "executed_tools": [*state["executed_tools"], "logs"],
        "investigation_steps": [*state["investigation_steps"], "logs:query_logs"],
    }
