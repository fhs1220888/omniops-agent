"""Report agent with optional LLM RCA generation and deterministic fallback."""

from __future__ import annotations

import json

from app.agents.state import IncidentState
from app.core.config import Settings
from app.core.incident_scenarios import detect_incident_scenario
from app.llm.client import LLMClient, build_llm_client, validate_rca_json
from app.models.incident import AgentFinding, RecommendedAction, RootCauseAnalysis


def report_agent(state: IncidentState) -> dict:
    root_cause, action_models = generate_rca_from_state(state)
    evidence_lines = "\n".join(
        f"- {item['id']}: {item['summary']}" for item in state["evidence"]
    ) or "- No evidence was collected."
    missing_evidence = _format_missing_evidence(state)
    report = f"""# RCA Report: {state['title']}

## Summary
The diagnosis points to `{root_cause.root_cause}` affecting `{state['service']}`.

## Evidence
{evidence_lines}

## Evidence Summary
{_format_evidence_summary(state)}

## Agent Timeline
{_format_agent_timeline(state)}

## Tool Timeline
{_format_tool_timeline(state)}

## Confidence Scores
{_format_confidence_scores(state, root_cause)}

## Reflection
{_format_reflection(state)}

## Missing Evidence
{missing_evidence}

## Policy Decisions
{_format_policy_decisions(state)}

## Root Cause
{root_cause.root_cause}

## Recommended Actions
{_format_actions(action_models)}
"""
    finding = AgentFinding(
        agent_name="report_agent",
        confidence=0.87,
        summary="Generated deterministic RCA with recommended actions.",
        findings=[root_cause.root_cause],
        evidence_ids=root_cause.supporting_evidence_ids,
        next_suggestion=None,
        risk_level="low",
    )
    return {
        "status": "completed",
        "findings": [*state["findings"], finding.model_dump()],
        "root_cause_analysis": root_cause.model_dump(),
        "recommended_actions": [action.model_dump() for action in action_models],
        "report_markdown": report,
    }


def generate_rca_from_state(
    state: IncidentState,
    client: LLMClient | None = None,
) -> tuple[RootCauseAnalysis, list[RecommendedAction]]:
    prompt = build_rca_prompt(state)
    llm_client = client or build_llm_client()
    try:
        result = validate_rca_json(llm_client.diagnose(prompt))
        root_cause = _limit_supporting_evidence(
            state,
            result.root_cause_analysis,
        )
        if not _rca_matches_incident_context(state, root_cause):
            return build_fake_rca(state)
        return root_cause, result.recommended_actions
    except Exception:
        return build_fake_rca(state)


def build_rca_prompt(state: IncidentState) -> str:
    settings = Settings.from_env()
    payload = {
        "incident": {
            "id": state["incident_id"],
            "title": state["title"],
            "service": state["service"],
            "severity": state["severity"],
            "affected_services": state["affected_services"],
            "time_window": state["time_window"],
        },
        "execution_metadata": {
            "investigation_plan": state["investigation_plan"],
            "investigation_steps": state["investigation_steps"],
            "executed_tools": state["executed_tools"],
            "skipped_tools": state["skipped_tools"],
            "failed_tools": state["failed_tools"],
            "policy_records": state["policy_records"],
            "denied_tools": state["denied_tools"],
            "approval_required_tools": state["approval_required_tools"],
            "tool_timings": state["tool_timings"],
            "total_investigation_duration_ms": state["total_investigation_duration_ms"],
            "reflection": {
                "decision": state.get("reflection_decision"),
                "reason": state.get("reflection_reason"),
                "replanning_requested": state.get("replanning_requested", False),
                "additional_tools": state.get("additional_tools", []),
                "investigation_round": state.get("investigation_round", 0),
                "max_investigation_rounds": state.get("max_investigation_rounds", 2),
            },
        },
        "tool_observations": state["tool_observations"],
        "evidence": state["evidence"],
        "evidence_items": state["evidence_items"],
        "evidence_graph": state["evidence_graph"],
        "similar_historical_incidents": state["similar_incidents"],
        "required_json_schema": {
            "root_cause_analysis": {
                "root_cause": "string",
                "confidence": "number between 0 and 1",
                "impact": "string",
                "supporting_evidence_ids": ["evidence id strings"],
            },
            "recommended_actions": [
                {
                    "action_type": "investigate | mitigate | verify",
                    "description": "string",
                    "owner": "string",
                    "priority": "low | medium | high",
                }
            ],
        },
    }
    guardrails = (
        "Base the RCA only on the provided evidence, tool observations, and "
        "evidence graph. If logs, metrics, or traces are empty or contain "
        "provider errors, say evidence is insufficient instead of guessing. "
        "Do not infer root cause from demo scenario names or historical memory "
        "alone."
    )
    mode_context = (
        f"Tool mode: {'fake' if settings.use_fake_tools else 'real'}; "
        f"observability_backend: {settings.observability_backend}."
    )
    return (
        "Diagnose the incident using the provided logs, metrics, traces, and "
        "similar historical incidents as context. "
        f"{guardrails} {mode_context} Return one JSON object and no markdown.\n\n"
        f"{json.dumps(payload, default=str, indent=2, sort_keys=True)}"
    )


def build_fake_rca(state: IncidentState) -> tuple[RootCauseAnalysis, list[RecommendedAction]]:
    scenario = _detect_demo_scenario(state)
    if scenario == "mysql_slow_query":
        return _limit_supporting_evidence(
            state,
            RootCauseAnalysis(
                root_cause="Missing database index caused slow payment_order queries in payment-service.",
                confidence=0.84,
                impact="Payment requests experienced elevated database latency.",
                supporting_evidence_ids=[item["id"] for item in state["evidence"]],
            ),
        ), [
            RecommendedAction(
                action_type="mitigate",
                description="Add the missing composite index for payment_order lookups.",
                owner="payment-service",
                priority="high",
            ),
            RecommendedAction(
                action_type="verify",
                description="Verify database latency and payment P95 latency return to baseline.",
                owner="service-oncall",
                priority="high",
            ),
        ]
    if scenario == "kafka_lag":
        return _limit_supporting_evidence(
            state,
            RootCauseAnalysis(
                root_cause="Inventory consumer processing lag delayed stock updates.",
                confidence=0.8,
                impact="Inventory updates were delayed while consumer lag accumulated.",
                supporting_evidence_ids=[item["id"] for item in state["evidence"]],
            ),
        ), [
            RecommendedAction(
                action_type="mitigate",
                description="Scale or unblock inventory consumers.",
                owner="inventory-service",
                priority="high",
            ),
            RecommendedAction(
                action_type="verify",
                description="Monitor consumer lag and stock update latency until stable.",
                owner="service-oncall",
                priority="medium",
            ),
        ]
    if scenario == "bad_config_deploy":
        return _limit_supporting_evidence(
            state,
            RootCauseAnalysis(
                root_cause="Bad configuration deploy reduced connection capacity for order-service.",
                confidence=0.82,
                impact="Order service requests saw connection-related failures after deploy.",
                supporting_evidence_ids=[item["id"] for item in state["evidence"]],
            ),
        ), [
            RecommendedAction(
                action_type="mitigate",
                description="Rollback the bad configuration.",
                owner="platform-oncall",
                priority="high",
            ),
            RecommendedAction(
                action_type="investigate",
                description="Add a pre-deploy configuration validation check.",
                owner="order-service",
                priority="medium",
            ),
        ]

    root_cause = RootCauseAnalysis(
        root_cause="Redis connection pool exhaustion in order-service.",
        confidence=0.87,
        impact="Checkout requests experienced elevated latency and timeout errors.",
        supporting_evidence_ids=[item["id"] for item in state["evidence"]],
    )
    actions = [
        RecommendedAction(
            action_type="mitigate",
            description="Restore the Redis connection pool limit to the last known safe value.",
            owner="platform-oncall",
            priority="high",
        ),
        RecommendedAction(
            action_type="verify",
            description="Confirm P95 latency returns below 250ms and Redis timeout logs stop.",
            owner="service-oncall",
            priority="high",
        ),
        RecommendedAction(
            action_type="investigate",
            description="Review the deploy/configuration change that reduced Redis pool capacity.",
            owner="order-service",
            priority="medium",
        ),
    ]
    return _limit_supporting_evidence(state, root_cause), actions


def _detect_demo_scenario(state: IncidentState) -> str | None:
    scenario = detect_incident_scenario(
        title=state["title"],
        service=state["service"],
        description=state.get("description"),
    )
    return None if scenario in {"generic", "redis_timeout"} else scenario


def _rca_matches_incident_context(
    state: IncidentState,
    root_cause: RootCauseAnalysis,
) -> bool:
    scenario = detect_incident_scenario(
        title=state["title"],
        service=state["service"],
        description=state.get("description"),
    )
    root_cause_text = root_cause.root_cause.lower()
    required_terms_by_scenario = {
        "mysql_slow_query": ["mysql", "database", "index", "payment_order", "query"],
        "kafka_lag": ["consumer", "lag", "inventory", "stock"],
        "bad_config_deploy": ["config", "deploy", "connection", "capacity"],
        "redis_timeout": ["redis", "connection", "pool", "timeout"],
    }
    blocked_terms_by_scenario = {
        "mysql_slow_query": ["redis", "kafka"],
        "kafka_lag": ["redis", "mysql"],
        "bad_config_deploy": ["mysql", "kafka"],
        "redis_timeout": ["mysql", "kafka"],
    }.get(scenario)
    required_terms = required_terms_by_scenario.get(scenario)
    if required_terms is None:
        return True
    blocked_terms = blocked_terms_by_scenario or []
    return (
        sum(1 for term in required_terms if term in root_cause_text) >= 2
        and not any(term in root_cause_text for term in blocked_terms)
    )


def _limit_supporting_evidence(
    state: IncidentState,
    root_cause: RootCauseAnalysis,
) -> RootCauseAnalysis:
    available_ids = {item["id"] for item in state["evidence"]}
    supporting_ids = [
        evidence_id
        for evidence_id in root_cause.supporting_evidence_ids
        if evidence_id in available_ids
    ]
    if not supporting_ids:
        supporting_ids = [item["id"] for item in state["evidence"]]
    return root_cause.model_copy(
        update={"supporting_evidence_ids": supporting_ids}
    )


def _format_actions(actions: list[RecommendedAction]) -> str:
    return "\n".join(
        f"- [{action.priority}] {action.description} Owner: {action.owner}."
        for action in actions
    )


def _format_missing_evidence(state: IncidentState) -> str:
    lines = []
    for tool in state["skipped_tools"]:
        lines.append(f"- {tool}: skipped by investigation plan.")
    for failure in state["failed_tools"]:
        suffix = "timeout" if failure["timeout"] else "failure"
        lines.append(f"- {failure['tool_name']}: {suffix}: {failure['error_message']}")
    for denied in state["denied_tools"]:
        lines.append(f"- {denied['tool_name']}: denied by policy: {denied['reason']}")
    for approval in state["approval_required_tools"]:
        approval_id = approval.get("approval_id") or "unknown"
        lines.append(
            f"- {approval['tool_name']}: requires approval ({approval_id}): {approval['reason']}"
        )
    return "\n".join(lines) if lines else "- None."


def _format_policy_decisions(state: IncidentState) -> str:
    if not state["policy_records"]:
        return "- No policy decisions recorded."
    return "\n".join(
        f"- {record['tool_name']}: {record['policy_decision']} ({record['risk_level']}, {record['status']})"
        + (f" Error: {record['error']}" if record.get("error") else "")
        for record in state["policy_records"]
    )


def _format_reflection(state: IncidentState) -> str:
    limitation_lines = []
    if state["denied_tools"]:
        limitation_lines.append(
            "Denied tools: "
            + ", ".join(item["tool_name"] for item in state["denied_tools"])
        )
    if state["approval_required_tools"]:
        limitation_lines.append(
            "Approval required tools: "
            + ", ".join(
                f"{item['tool_name']} ({item.get('approval_id') or 'pending'})"
                for item in state["approval_required_tools"]
            )
        )
    limitations = "; ".join(limitation_lines) if limitation_lines else "None"
    return "\n".join(
        [
            f"- Decision: {state.get('reflection_decision')}",
            f"- Reason: {state.get('reflection_reason')}",
            f"- Replanning requested: {state.get('replanning_requested', False)}",
            f"- Additional tools: {state.get('additional_tools', [])}",
            f"- Investigation rounds: {state.get('investigation_round', 0)}/{state.get('max_investigation_rounds', 2)}",
            f"- Policy limitations: {limitations}",
        ]
    )


def _format_agent_timeline(state: IncidentState) -> str:
    if not state["agent_traces"]:
        return "- No agent traces recorded."
    return "\n".join(
        f"- {trace['agent_name']}: {trace['status']} in {trace['duration_ms']}ms. {trace['summary']}"
        for trace in state["agent_traces"]
    )


def _format_tool_timeline(state: IncidentState) -> str:
    if not state["tool_traces"]:
        return "- No tool traces recorded."
    return "\n".join(
        f"- {trace['tool_name']}: {trace['status']} ({trace['policy_decision']}, {trace['risk_level']}) in {trace['duration_ms']}ms"
        + (f". Error: {trace['error']}" if trace.get("error") else ".")
        for trace in state["tool_traces"]
    )


def _format_evidence_summary(state: IncidentState) -> str:
    if not state["evidence_items"]:
        return "- No normalized evidence items were produced."
    return "\n".join(
        f"- {item['evidence_id']} [{item['source']}]: {item['content']}"
        for item in state["evidence_items"]
    )


def _format_confidence_scores(
    state: IncidentState,
    root_cause: RootCauseAnalysis,
) -> str:
    evidence_scores = [
        f"- {item['evidence_id']}: {item['confidence']}"
        for item in state["evidence_items"]
    ]
    return "\n".join(
        [
            f"- root_cause: {root_cause.confidence}",
            *evidence_scores,
        ]
    )
