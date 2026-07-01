"""LangGraph workflow for deterministic diagnosis with local memory recall."""

from __future__ import annotations

import asyncio

from langgraph.graph import END, StateGraph

from app.agents.investigation_agent import execute_selected_tools
from app.agents.planner_agent import planner_agent
from app.agents.reflection_agent import reflection_agent, should_reinvestigate
from app.agents.report_agent import report_agent
from app.agents.state import IncidentState
from app.agents.tracing import trace_async_agent, trace_sync_agent
from app.agents.triage_agent import triage_agent
from app.memory.incident_store import IncidentStore
from app.models.incident import Incident, IncidentDiagnosis


def build_incident_graph(store: IncidentStore | None = None):
    async def investigate_node(state: IncidentState) -> dict:
        return await execute_selected_tools(state, store)

    graph = StateGraph(IncidentState)
    graph.add_node(
        "planner",
        trace_sync_agent("planner", "Selected investigation tools.", planner_agent),
    )
    graph.add_node(
        "triage",
        trace_sync_agent("triage", "Scoped affected service and time window.", triage_agent),
    )
    graph.add_node(
        "investigate",
        trace_async_agent(
            "investigation",
            "Executed selected tools through Tool Gateway.",
            investigate_node,
        ),
    )
    graph.add_node(
        "reflection",
        trace_sync_agent(
            "reflection",
            "Checked evidence sufficiency and replanning need.",
            reflection_agent,
        ),
    )
    graph.add_node(
        "report",
        trace_sync_agent("report", "Generated RCA report.", report_agent),
    )

    graph.set_entry_point("planner")
    graph.add_edge("planner", "triage")
    graph.add_edge("triage", "investigate")
    graph.add_edge("investigate", "reflection")
    graph.add_conditional_edges("reflection", should_reinvestigate)
    graph.add_edge("report", END)
    return graph.compile()


incident_graph = build_incident_graph()


def run_incident_analysis(
    incident_id: str,
    title: str,
    service: str,
    severity: str,
) -> IncidentState:
    incident = Incident(
        id=incident_id,
        title=title,
        service=service,
        severity=severity,
        status="running",
    )
    return run_incident_diagnosis(incident).model_dump()


def run_incident_diagnosis(incident: Incident) -> IncidentDiagnosis:
    return asyncio.run(run_incident_diagnosis_async(incident))


def run_incident_diagnosis_with_store(
    incident: Incident,
    store: IncidentStore,
) -> IncidentDiagnosis:
    return asyncio.run(run_incident_diagnosis_with_store_async(incident, store))


async def run_incident_diagnosis_async(incident: Incident) -> IncidentDiagnosis:
    return await _run_incident_diagnosis_with_graph(incident, incident_graph)


async def run_incident_diagnosis_with_store_async(
    incident: Incident,
    store: IncidentStore,
) -> IncidentDiagnosis:
    return await _run_incident_diagnosis_with_graph(incident, build_incident_graph(store))


async def _run_incident_diagnosis_with_graph(incident: Incident, graph) -> IncidentDiagnosis:
    initial_state: IncidentState = {
        "incident_id": incident.id,
        "title": incident.title,
        "service": incident.service,
        "severity": incident.severity,
        "description": incident.description,
        "status": "running",
        "time_window": None,
        "affected_services": [],
        "investigation_plan": None,
        "investigation_steps": [],
        "executed_tools": [],
        "skipped_tools": [],
        "reflection_decision": None,
        "reflection_reason": None,
        "replanning_requested": False,
        "additional_tools": [],
        "investigation_round": 0,
        "max_investigation_rounds": 2,
        "tool_timings": [],
        "failed_tools": [],
        "policy_records": [],
        "denied_tools": [],
        "approval_required_tools": [],
        "total_investigation_duration_ms": 0,
        "evidence": [],
        "evidence_items": [],
        "evidence_graph": {"nodes": [], "edges": []},
        "findings": [],
        "tool_observations": [],
        "agent_traces": [],
        "tool_traces": [],
        "similar_incidents": [],
        "retrieved_knowledge": [],
        "selected_skills": [],
        "root_cause_analysis": None,
        "recommended_actions": [],
        "report_markdown": None,
    }
    result = await graph.ainvoke(initial_state)
    return IncidentDiagnosis(
        incident_id=result["incident_id"],
        status="completed",
        affected_services=result["affected_services"],
        investigation_plan=result["investigation_plan"],
        investigation_steps=result["investigation_steps"],
        executed_tools=result["executed_tools"],
        skipped_tools=result["skipped_tools"],
        reflection_decision=result["reflection_decision"],
        reflection_reason=result["reflection_reason"],
        replanning_requested=result["replanning_requested"],
        additional_tools=result["additional_tools"],
        investigation_round=result["investigation_round"],
        max_investigation_rounds=result["max_investigation_rounds"],
        tool_timings=result["tool_timings"],
        failed_tools=result["failed_tools"],
        policy_records=result["policy_records"],
        denied_tools=result["denied_tools"],
        approval_required_tools=result["approval_required_tools"],
        total_investigation_duration_ms=result["total_investigation_duration_ms"],
        evidence=result["evidence"],
        evidence_items=result["evidence_items"],
        evidence_graph=result["evidence_graph"],
        agent_traces=result["agent_traces"],
        tool_traces=result["tool_traces"],
        findings=result["findings"],
        similar_incidents=result["similar_incidents"],
        retrieved_knowledge=result.get("retrieved_knowledge", []),
        selected_skills=result.get("selected_skills", []),
        root_cause_analysis=result["root_cause_analysis"],
        recommended_actions=result["recommended_actions"],
        report_markdown=result["report_markdown"] or "",
    )
