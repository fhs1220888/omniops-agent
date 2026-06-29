"""Harness policy facade over the existing Tool Gateway policy."""

from __future__ import annotations

from app.agents.state import IncidentState
from app.harness.config import HarnessConfig
from app.tools.policy import evaluate_tool_call


class HarnessPolicy:
    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config

    def allow_tool(self, tool_name: str, context: dict) -> bool:
        decision = evaluate_tool_call(
            tool_name,
            context.get("arguments", {}),
            _incident_state_from_context(context),
        )
        return decision.decision == "allow"

    def require_human_approval(self, tool_name: str, context: dict) -> bool:
        decision = evaluate_tool_call(
            tool_name,
            context.get("arguments", {}),
            _incident_state_from_context(context),
        )
        return decision.decision == "review"

    def allow_report(self, evidence_count: int, failed_tools: list[str]) -> bool:
        if self.config and self.config.require_evidence_for_report:
            return evidence_count > 0
        return evidence_count > 0 or bool(failed_tools)

    def summary(self) -> dict:
        return {
            "requires_evidence_for_report": (
                self.config.require_evidence_for_report if self.config else True
            ),
            "zero_evidence_behavior": "mark_evidence_insufficient",
            "failed_tools_included_in_result": True,
            "real_mode_fake_tool_fallback_allowed": False,
        }


def _incident_state_from_context(context: dict) -> IncidentState:
    return {
        "incident_id": context.get("incident_id", ""),
        "title": context.get("title", ""),
        "service": context.get("service", ""),
        "severity": context.get("severity", "medium"),
        "description": context.get("description"),
        "status": context.get("status", "running"),
        "time_window": context.get("time_window", {}),
        "affected_services": context.get("affected_services", []),
        "investigation_plan": context.get("investigation_plan"),
        "investigation_steps": context.get("investigation_steps", []),
        "executed_tools": context.get("executed_tools", []),
        "skipped_tools": context.get("skipped_tools", []),
        "reflection_decision": context.get("reflection_decision"),
        "reflection_reason": context.get("reflection_reason"),
        "replanning_requested": context.get("replanning_requested", False),
        "additional_tools": context.get("additional_tools", []),
        "investigation_round": context.get("investigation_round", 0),
        "max_investigation_rounds": context.get("max_investigation_rounds", 2),
        "tool_timings": context.get("tool_timings", []),
        "failed_tools": context.get("failed_tools", []),
        "policy_records": context.get("policy_records", []),
        "denied_tools": context.get("denied_tools", []),
        "approval_required_tools": context.get("approval_required_tools", []),
        "total_investigation_duration_ms": context.get(
            "total_investigation_duration_ms",
            0,
        ),
        "evidence": context.get("evidence", []),
        "evidence_items": context.get("evidence_items", []),
        "evidence_graph": context.get("evidence_graph", {}),
        "agent_traces": context.get("agent_traces", []),
        "tool_traces": context.get("tool_traces", []),
        "tool_observations": context.get("tool_observations", []),
        "similar_incidents": context.get("similar_incidents", []),
        "findings": context.get("findings", []),
        "root_cause_analysis": context.get("root_cause_analysis"),
        "recommended_actions": context.get("recommended_actions", []),
        "report_markdown": context.get("report_markdown"),
    }
