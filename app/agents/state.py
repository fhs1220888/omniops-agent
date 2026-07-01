"""Shared state types for the Week 1.5 LangGraph workflow."""

from __future__ import annotations

from typing import Literal, TypedDict

IncidentStatus = Literal["running", "completed", "failed"]


class IncidentState(TypedDict):
    incident_id: str
    title: str
    service: str
    severity: str
    description: str | None
    status: IncidentStatus
    time_window: dict[str, str] | None
    affected_services: list[str]
    investigation_plan: dict | None
    investigation_steps: list[str]
    executed_tools: list[str]
    skipped_tools: list[str]
    reflection_decision: str | None
    reflection_reason: str | None
    replanning_requested: bool
    additional_tools: list[str]
    investigation_round: int
    max_investigation_rounds: int
    tool_timings: list[dict]
    failed_tools: list[dict]
    policy_records: list[dict]
    denied_tools: list[dict]
    approval_required_tools: list[dict]
    total_investigation_duration_ms: float
    evidence: list[dict]
    evidence_items: list[dict]
    evidence_graph: dict
    findings: list[dict]
    tool_observations: list[dict]
    agent_traces: list[dict]
    tool_traces: list[dict]
    similar_incidents: list[dict]
    retrieved_knowledge: list[dict]
    selected_skills: list[dict]
    root_cause_analysis: dict | None
    recommended_actions: list[dict]
    report_markdown: str | None
