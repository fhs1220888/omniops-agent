"""Deterministic planner agent for dynamic investigation routing."""

from __future__ import annotations

from app.agents.state import IncidentState
from app.core.config import Settings
from app.models.incident import InvestigationPlan, SupportedTool

SUPPORTED_TOOLS: list[SupportedTool] = ["logs", "metrics", "traces", "memory"]


def planner_agent(state: IncidentState) -> dict:
    plan = build_investigation_plan(
        title=state["title"],
        service=state["service"],
        severity=state["severity"],
        description=state["description"],
    )
    plan = _broaden_plan_for_external_observability(plan)
    skipped_tools = [tool for tool in SUPPORTED_TOOLS if tool not in plan.required_tools]
    return {
        "investigation_plan": plan.model_dump(),
        "investigation_steps": [
            *state["investigation_steps"],
            "planner:selected_tools",
        ],
        "skipped_tools": skipped_tools,
    }


def build_investigation_plan(
    *,
    title: str,
    service: str,
    severity: str,
    description: str | None = None,
) -> InvestigationPlan:
    text = " ".join([title, service, severity, description or ""]).lower()

    if any(term in text for term in ["database timeout", "db timeout", "sql timeout"]):
        return InvestigationPlan(
            objectives=[
                "Confirm timeout symptoms across logs, metrics, and traces.",
                "Compare with historical incidents before RCA generation.",
            ],
            required_tools=["logs", "metrics", "traces", "memory"],
            reasoning="Database timeout incidents need error logs, latency metrics, trace bottlenecks, and historical context.",
        )

    if any(term in text for term in ["pod crash", "crashloop", "crash", "oomkilled"]):
        return InvestigationPlan(
            objectives=[
                "Inspect crash signatures in logs.",
                "Recall similar incidents for operational context.",
            ],
            required_tools=["logs", "memory"],
            reasoning="Crash incidents are best explained by log signatures and past crash patterns.",
        )

    if any(term in text for term in ["consumer lag", "stock update", "inventory updates"]):
        return InvestigationPlan(
            objectives=[
                "Inspect processing delay symptoms in logs.",
                "Compare with similar inventory incidents.",
            ],
            required_tools=["logs", "memory"],
            reasoning="Consumer lag demo incidents use logs and historical memory for deterministic local diagnosis.",
        )

    if any(term in text for term in ["bad config", "config deploy", "configuration deploy"]):
        return InvestigationPlan(
            objectives=[
                "Inspect configuration-related error signatures.",
                "Recall similar bad configuration incidents.",
            ],
            required_tools=["logs", "memory"],
            reasoning="Bad configuration incidents are best explained by logs and historical deployment context.",
        )

    if any(term in text for term in ["latency", "slow", "p95", "timeout"]):
        return InvestigationPlan(
            objectives=[
                "Measure latency impact.",
                "Localize the slow dependency through traces.",
            ],
            required_tools=["metrics", "traces"],
            reasoning="Latency incidents need metrics to quantify impact and traces to locate the bottleneck.",
        )

    return InvestigationPlan(
        objectives=[
            "Gather baseline logs and historical context.",
            "Produce an initial RCA from available deterministic evidence.",
        ],
        required_tools=["logs", "memory"],
        reasoning="Unclassified incidents use a conservative log and memory investigation path.",
    )


def _broaden_plan_for_external_observability(
    plan: InvestigationPlan,
) -> InvestigationPlan:
    if Settings.from_env().use_fake_tools:
        return plan
    required_tools = [
        tool
        for tool in SUPPORTED_TOOLS
        if tool in {*plan.required_tools, "logs", "metrics", "traces"}
    ]
    return plan.model_copy(
        update={
            "required_tools": required_tools,
            "reasoning": (
                f"{plan.reasoning} External observability mode broadens "
                "collection to logs, metrics, and traces."
            ),
        }
    )


def next_tool_after(state: IncidentState, current_tool: str | None = None) -> str:
    required_tools = state["investigation_plan"]["required_tools"]
    start_index = 0
    if current_tool is not None:
        start_index = SUPPORTED_TOOLS.index(current_tool) + 1
    for tool in SUPPORTED_TOOLS[start_index:]:
        if tool in required_tools:
            return _node_for_tool(tool)
    return "report"


def _node_for_tool(tool: str) -> str:
    if tool == "memory":
        return "recall_memory"
    return tool
