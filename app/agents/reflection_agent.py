"""Reflection agent for evidence sufficiency checks and bounded replanning."""

from __future__ import annotations

from app.agents.planner_agent import SUPPORTED_TOOLS
from app.agents.state import IncidentState

ReflectionDecision = str

SOURCE_TO_TOOL = {
    "log": "logs",
    "metric": "metrics",
    "trace": "traces",
    "memory": "memory",
}


def reflection_agent(state: IncidentState) -> dict:
    decision, reason, additional_tools = _reflect(state)
    can_replan = (
        decision == "need_more_evidence"
        and state["investigation_round"] < state["max_investigation_rounds"]
    )
    merged_tools = _merge_tools(
        state["investigation_plan"]["required_tools"],
        additional_tools if can_replan else [],
    )
    skipped_tools = [tool for tool in SUPPORTED_TOOLS if tool not in merged_tools]
    return {
        "reflection_decision": decision,
        "reflection_reason": reason,
        "replanning_requested": can_replan,
        "additional_tools": additional_tools if can_replan else [],
        "investigation_plan": {
            **state["investigation_plan"],
            "required_tools": merged_tools,
        },
        "skipped_tools": skipped_tools,
        "investigation_steps": [
            *state["investigation_steps"],
            f"reflection:{decision}",
        ],
    }


def should_reinvestigate(state: IncidentState) -> str:
    if state["replanning_requested"]:
        return "investigate"
    return "report"


def _reflect(state: IncidentState) -> tuple[str, str, list[str]]:
    if state["denied_tools"] or state["approval_required_tools"]:
        blocked = [
            item["tool_name"] for item in state["denied_tools"]
        ] + [
            item["tool_name"] for item in state["approval_required_tools"]
        ]
        return (
            "sufficient",
            f"Policy blocked tools {blocked}; report should mention evidence limitations.",
            [],
        )

    if not state["evidence_items"]:
        return (
            "need_more_evidence",
            "No evidence items were collected.",
            _missing_tools(state),
        )

    retryable_failed_tools = [
        item["tool_name"]
        for item in state["failed_tools"]
        if item["tool_name"] not in state["executed_tools"]
    ]
    if retryable_failed_tools:
        return (
            "need_more_evidence",
            f"Important evidence tools failed or timed out: {retryable_failed_tools}.",
            _merge_tools([], retryable_failed_tools),
        )

    confidence = _current_confidence(state)
    if confidence < 0.75:
        return (
            "need_more_evidence",
            f"Evidence confidence {confidence:.2f} is below threshold 0.75.",
            _missing_tools(state),
        )

    return (
        "sufficient",
        f"Evidence confidence {confidence:.2f} is sufficient for report generation.",
        [],
    )


def _current_confidence(state: IncidentState) -> float:
    if state.get("root_cause_analysis") is not None:
        return float(state["root_cause_analysis"].get("confidence", 0))
    if not state["evidence_items"]:
        return 0
    return max(float(item["confidence"]) for item in state["evidence_items"])


def _missing_tools(state: IncidentState) -> list[str]:
    observed_sources = {item["source"] for item in state["evidence_items"]}
    missing = [
        SOURCE_TO_TOOL[source]
        for source in ["log", "metric", "trace", "memory"]
        if source not in observed_sources
    ]
    return [
        tool
        for tool in missing
        if tool not in state["executed_tools"]
    ]


def _merge_tools(existing: list[str], additional: list[str]) -> list[str]:
    merged = [tool for tool in SUPPORTED_TOOLS if tool in existing]
    for tool in SUPPORTED_TOOLS:
        if tool in additional and tool not in merged:
            merged.append(tool)
    return merged
