"""Async parallel investigation executor for selected fake tools."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter

from app.agents.log_agent import log_agent
from app.agents.memory_agent import recall_similar_incidents
from app.agents.metric_agent import metric_agent
from app.agents.planner_agent import SUPPORTED_TOOLS
from app.agents.state import IncidentState
from app.agents.trace_agent import trace_agent
from app.core.incident_scenarios import detect_incident_scenario
from app.memory.incident_store import IncidentStore
from app.models.incident import FailedTool, SupportedTool, ToolTiming
from app.models.incident import ApprovalRequiredTool, DeniedTool
from app.models.evidence import EvidenceItem as ExplainableEvidenceItem
from app.rag.graph_store import EvidenceGraph
from app.tools.gateway import (
    HumanApprovalRequired,
    ToolDenied,
    ToolGatewayTimeout,
    execute_tool_via_gateway,
)

ToolAgent = Callable[[IncidentState], Awaitable[dict]]

TOOL_TIMEOUT_SECONDS = 2.0
TOOL_STEP_LABELS = {
    "logs": "logs:query_logs",
    "metrics": "metrics:query_metrics",
    "traces": "traces:query_traces",
    "memory": "memory:find_similar",
}
TOOL_GATEWAY_NAMES = {
    "logs": "query_logs",
    "metrics": "query_metrics",
    "traces": "query_traces",
    "memory": "query_memory",
}


def build_tool_agents(store: IncidentStore | None = None) -> dict[SupportedTool, ToolAgent]:
    async def memory_agent(state: IncidentState) -> dict:
        return await recall_similar_incidents(state, store)

    return {
        "logs": log_agent,
        "metrics": metric_agent,
        "traces": trace_agent,
        "memory": memory_agent,
    }


async def execute_selected_tools(
    state: IncidentState,
    store: IncidentStore | None = None,
    timeout_seconds: float | None = None,
) -> dict:
    timeout = timeout_seconds if timeout_seconds is not None else TOOL_TIMEOUT_SECONDS
    required_tools = state["investigation_plan"]["required_tools"]
    tool_agents = build_tool_agents(store)
    total_started = perf_counter()

    tasks = [
        _run_tool(tool, state, tool_agents[tool], timeout)
        for tool in SUPPORTED_TOOLS
        if tool in required_tools and tool not in state["executed_tools"]
    ]
    results = await asyncio.gather(*tasks)

    evidence = [*state["evidence"]]
    findings = [*state["findings"]]
    observations = [*state["tool_observations"]]
    similar_incidents = [*state["similar_incidents"]]
    executed_tools = [*state["executed_tools"]]
    failed_tools = [*state["failed_tools"]]
    policy_records = [*state["policy_records"]]
    tool_traces = [*state["tool_traces"]]
    denied_tools = [*state["denied_tools"]]
    approval_required_tools = [*state["approval_required_tools"]]
    tool_timings = [*state["tool_timings"]]
    investigation_steps = [*state["investigation_steps"]]

    for result in results:
        tool = result["tool"]
        tool_timings.append(result["timing"].model_dump())
        if result["policy_record"] is not None:
            policy_records.append(result["policy_record"])
        if result["tool_trace"] is not None:
            tool_traces.append(result["tool_trace"])
        if result["denied_tool"] is not None:
            denied_tools.append(result["denied_tool"].model_dump())
        if result["approval_required_tool"] is not None:
            approval_required_tools.append(result["approval_required_tool"].model_dump())
        if result["failed_tool"] is not None:
            failed_tools.append(result["failed_tool"].model_dump())
            investigation_steps.append(f"{tool}:failed")
            continue

        executed_tools.append(tool)
        investigation_steps.append(TOOL_STEP_LABELS[tool])
        update = result["update"]
        evidence.extend(_list_delta(state, update, "evidence"))
        findings.extend(_list_delta(state, update, "findings"))
        observations.extend(_list_delta(state, update, "tool_observations"))
        if tool == "memory":
            similar_incidents = update.get("similar_incidents", [])

    evidence_items = _build_evidence_items(evidence, similar_incidents)
    evidence_graph = _build_evidence_graph(
        service=state["service"],
        title=state["title"],
        description=state.get("description"),
        evidence=evidence,
        similar_incidents=similar_incidents,
    )

    return {
        "evidence": evidence,
        "evidence_items": [item.model_dump() for item in evidence_items],
        "evidence_graph": evidence_graph.export_graph(),
        "findings": findings,
        "tool_observations": observations,
        "similar_incidents": similar_incidents,
        "executed_tools": executed_tools,
        "failed_tools": failed_tools,
        "policy_records": policy_records,
        "tool_traces": tool_traces,
        "denied_tools": denied_tools,
        "approval_required_tools": approval_required_tools,
        "tool_timings": tool_timings,
        "investigation_steps": investigation_steps,
        "investigation_round": state.get("investigation_round", 0) + 1,
        "total_investigation_duration_ms": round(
            state["total_investigation_duration_ms"]
            + (perf_counter() - total_started) * 1000,
            3,
        ),
    }


async def _run_tool(
    tool: SupportedTool,
    state: IncidentState,
    agent: ToolAgent,
    timeout_seconds: float,
) -> dict:
    started_at = datetime.now(UTC)
    started_perf = perf_counter()
    failed_tool = None
    denied_tool = None
    approval_required_tool = None
    policy_record = None
    tool_trace = None
    update: dict = {}
    try:
        gateway_result = await execute_tool_via_gateway(
            tool_name=TOOL_GATEWAY_NAMES[tool],
            arguments={"state": state},
            incident_state=state,
            executor=agent,
            timeout_seconds=timeout_seconds,
        )
        update = gateway_result["result"]
        policy_record = gateway_result["policy_record"]
        tool_trace = gateway_result["tool_trace"]
    except ToolDenied as exc:
        policy_record = exc.record.model_dump()
        tool_trace = exc.tool_trace.model_dump()
        denied_tool = DeniedTool(tool_name=tool, reason=exc.reason)
        failed_tool = FailedTool(
            tool_name=tool,
            error_message=exc.reason,
            timeout=False,
        )
    except HumanApprovalRequired as exc:
        policy_record = exc.record.model_dump()
        tool_trace = exc.tool_trace.model_dump()
        approval_required_tool = ApprovalRequiredTool(
            tool_name=tool,
            reason=exc.reason,
            approval_id=exc.approval_id,
        )
        failed_tool = FailedTool(
            tool_name=tool,
            error_message=exc.reason,
            timeout=False,
        )
    except ToolGatewayTimeout as exc:
        policy_record = exc.record.model_dump()
        tool_trace = exc.tool_trace.model_dump()
        failed_tool = FailedTool(
            tool_name=tool,
            error_message=exc.reason,
            timeout=True,
        )
    except Exception as exc:
        policy_record = getattr(exc, "gateway_record", None)
        if policy_record is not None:
            policy_record = policy_record.model_dump()
        tool_trace = getattr(exc, "gateway_trace", None)
        if tool_trace is not None:
            tool_trace = tool_trace.model_dump()
        failed_tool = FailedTool(
            tool_name=tool,
            error_message=str(exc),
            timeout=False,
        )
    finished_at = datetime.now(UTC)
    timing = ToolTiming(
        tool_name=tool,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=round((perf_counter() - started_perf) * 1000, 3),
    )
    return {
        "tool": tool,
        "update": update,
        "failed_tool": failed_tool,
        "denied_tool": denied_tool,
        "approval_required_tool": approval_required_tool,
        "policy_record": policy_record,
        "tool_trace": tool_trace,
        "timing": timing,
    }


def _list_delta(state: IncidentState, update: dict, key: str) -> list:
    return update.get(key, [])[len(state[key]) :]


def _build_evidence_items(
    evidence: list[dict],
    similar_incidents: list[dict],
) -> list[ExplainableEvidenceItem]:
    items = []
    for item in evidence:
        items.append(
            ExplainableEvidenceItem(
                evidence_id=item["id"],
                source=_source_from_evidence_type(item["type"]),
                content=item["summary"],
                confidence=_confidence_from_evidence_type(item["type"]),
            )
        )
    for incident in similar_incidents:
        items.append(
            ExplainableEvidenceItem(
                evidence_id=f"memory-{incident['incident_id']}",
                source="memory",
                content=f"{incident['title']}: {incident['root_cause']}",
                confidence=min(0.95, 0.5 + incident["similarity_score"] / 20),
            )
        )
    return items


def _build_evidence_graph(
    *,
    service: str,
    title: str,
    description: str | None,
    evidence: list[dict],
    similar_incidents: list[dict],
) -> EvidenceGraph:
    graph = EvidenceGraph()
    service_id = f"service:{service}"
    hypothesis_id, hypothesis_label = _hypothesis_for_scenario(
        detect_incident_scenario(
            title=title,
            service=service,
            description=description,
        )
    )
    graph.add_node(service_id, "Service", service)
    graph.add_node(hypothesis_id, "LogPattern", hypothesis_label)
    graph.add_edge(hypothesis_id, service_id, "caused_by")

    for item in evidence:
        node_type = _node_type_from_evidence_type(item["type"])
        graph.add_node(
            item["id"],
            node_type,
            item["summary"],
            metadata=item.get("metadata", {}),
        )
        graph.add_edge(item["id"], hypothesis_id, "supports")
        graph.add_edge(item["id"], service_id, "related_to")

    for incident in similar_incidents:
        node_id = f"memory-{incident['incident_id']}"
        graph.add_node(
            node_id,
            "Memory",
            incident["title"],
            metadata={"similarity_score": incident["similarity_score"]},
        )
        graph.add_edge(node_id, hypothesis_id, "supports")
    return graph


def _hypothesis_for_scenario(scenario: str) -> tuple[str, str]:
    return {
        "mysql_slow_query": (
            "hypothesis:mysql_missing_index",
            "mysql_missing_index",
        ),
        "kafka_lag": (
            "hypothesis:consumer_processing_lag",
            "consumer_processing_lag",
        ),
        "bad_config_deploy": (
            "hypothesis:bad_config_connection_capacity",
            "bad_config_connection_capacity",
        ),
        "redis_timeout": (
            "hypothesis:redis_pool_exhaustion",
            "redis_pool_exhaustion",
        ),
    }.get(
        scenario,
        ("hypothesis:incident_dependency_bottleneck", "incident_dependency_bottleneck"),
    )


def _source_from_evidence_type(evidence_type: str) -> str:
    return {
        "log_pattern": "log",
        "metric_anomaly": "metric",
        "trace_bottleneck": "trace",
    }[evidence_type]


def _node_type_from_evidence_type(evidence_type: str) -> str:
    return {
        "log_pattern": "LogPattern",
        "metric_anomaly": "Metric",
        "trace_bottleneck": "TraceSpan",
    }[evidence_type]


def _confidence_from_evidence_type(evidence_type: str) -> float:
    return {
        "log_pattern": 0.78,
        "metric_anomaly": 0.84,
        "trace_bottleneck": 0.86,
    }[evidence_type]
