"""Triage agent for deterministic Week 1 incident scoping."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.agents.state import IncidentState
from app.models.incident import AgentFinding


def triage_agent(state: IncidentState) -> dict:
    now = datetime.now(UTC)
    time_window = {
        "start": (now - timedelta(minutes=30)).isoformat(),
        "end": now.isoformat(),
    }
    finding = AgentFinding(
        agent_name="triage_agent",
        confidence=0.82,
        summary=f"{state['service']} is the primary affected service.",
        findings=[
            f"Incident severity is {state['severity']}.",
            "Using a fake 30-minute investigation window for the MVP.",
        ],
        evidence_ids=[],
        next_suggestion="Collect logs, metrics, and traces for the affected service.",
        risk_level="low",
    )
    return {
        "status": "running",
        "time_window": time_window,
        "affected_services": [state["service"]],
        "findings": [*state["findings"], finding.model_dump()],
        "investigation_steps": [*state["investigation_steps"], "triage:set_scope"],
    }
