"""Risk policy evaluation for Tool Gateway calls."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.agents.state import IncidentState
from app.tools.registry import ToolRiskLevel, get_tool_spec

PolicyDecision = Literal["allow", "review", "deny"]


class ToolPolicyResult(BaseModel):
    tool_name: str
    decision: PolicyDecision
    risk_level: ToolRiskLevel
    reason: str


def evaluate_tool_call(
    tool_name: str,
    arguments: dict,
    incident_state: IncidentState,
) -> ToolPolicyResult:
    spec = get_tool_spec(tool_name)
    if spec is None:
        return ToolPolicyResult(
            tool_name=tool_name,
            decision="deny",
            risk_level="critical",
            reason=f"Unknown tool: {tool_name}",
        )

    if spec.risk_level == "critical":
        return ToolPolicyResult(
            tool_name=tool_name,
            decision="deny",
            risk_level=spec.risk_level,
            reason=f"Critical tool is denied by policy: {tool_name}",
        )

    calls_so_far = sum(
        1
        for record in incident_state.get("policy_records", [])
        if record.get("tool_name") == tool_name
        and record.get("status") in {"allowed", "completed"}
    )
    if calls_so_far >= spec.max_calls_per_incident:
        return ToolPolicyResult(
            tool_name=tool_name,
            decision="deny",
            risk_level=spec.risk_level,
            reason=f"Tool call limit exceeded for {tool_name}",
        )

    if spec.approval_required:
        return ToolPolicyResult(
            tool_name=tool_name,
            decision="review",
            risk_level=spec.risk_level,
            reason=f"Tool requires human approval: {tool_name}",
        )

    return ToolPolicyResult(
        tool_name=tool_name,
        decision="allow",
        risk_level=spec.risk_level,
        reason="Low-risk read-only tool allowed.",
    )
