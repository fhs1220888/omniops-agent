from app.agents.reflection_agent import reflection_agent


def _state(
    *,
    evidence_items: list[dict] | None = None,
    failed_tools: list[dict] | None = None,
    denied_tools: list[dict] | None = None,
    approval_required_tools: list[dict] | None = None,
    executed_tools: list[str] | None = None,
    required_tools: list[str] | None = None,
    investigation_round: int = 1,
) -> dict:
    return {
        "incident_id": "INC-REFLECT",
        "title": "Reflection test",
        "service": "order-service",
        "severity": "high",
        "description": None,
        "status": "running",
        "time_window": None,
        "affected_services": ["order-service"],
        "investigation_plan": {
            "objectives": ["test"],
            "required_tools": required_tools or ["metrics"],
            "reasoning": "test",
        },
        "investigation_steps": [],
        "executed_tools": executed_tools or [],
        "skipped_tools": [],
        "reflection_decision": None,
        "reflection_reason": None,
        "replanning_requested": False,
        "additional_tools": [],
        "investigation_round": investigation_round,
        "max_investigation_rounds": 2,
        "tool_timings": [],
        "failed_tools": failed_tools or [],
        "policy_records": [],
        "denied_tools": denied_tools or [],
        "approval_required_tools": approval_required_tools or [],
        "total_investigation_duration_ms": 0,
        "evidence": [],
        "evidence_items": evidence_items or [],
        "evidence_graph": {"nodes": [], "edges": []},
        "findings": [],
        "tool_observations": [],
        "agent_traces": [],
        "tool_traces": [],
        "similar_incidents": [],
        "root_cause_analysis": None,
        "recommended_actions": [],
        "report_markdown": None,
    }


def test_no_evidence_triggers_need_more_evidence() -> None:
    result = reflection_agent(_state(evidence_items=[]))

    assert result["reflection_decision"] == "need_more_evidence"
    assert result["replanning_requested"] is True
    assert result["additional_tools"]


def test_high_confidence_evidence_is_sufficient() -> None:
    result = reflection_agent(
        _state(
            evidence_items=[
                {
                    "evidence_id": "evidence-metric-latency-spike",
                    "source": "metric",
                    "content": "P95 latency spike",
                    "confidence": 0.84,
                }
            ],
            executed_tools=["metrics"],
        )
    )

    assert result["reflection_decision"] == "sufficient"
    assert result["replanning_requested"] is False


def test_low_confidence_triggers_replanning() -> None:
    result = reflection_agent(
        _state(
            evidence_items=[
                {
                    "evidence_id": "weak-evidence",
                    "source": "metric",
                    "content": "Weak signal",
                    "confidence": 0.5,
                }
            ],
            executed_tools=["metrics"],
            required_tools=["metrics"],
        )
    )

    assert result["reflection_decision"] == "need_more_evidence"
    assert result["replanning_requested"] is True
    assert result["additional_tools"] == ["logs", "traces", "memory"]


def test_denied_tool_is_sufficient_with_limitation() -> None:
    result = reflection_agent(
        _state(
            evidence_items=[
                {
                    "evidence_id": "evidence-trace",
                    "source": "trace",
                    "content": "Trace evidence",
                    "confidence": 0.86,
                }
            ],
            denied_tools=[{"tool_name": "metrics", "reason": "denied"}],
        )
    )

    assert result["reflection_decision"] == "sufficient"
    assert "Policy blocked" in result["reflection_reason"]
