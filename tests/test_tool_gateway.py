import asyncio

from app.agents import investigation_agent
from app.agents.investigation_agent import execute_selected_tools
from app.tools.gateway import (
    HumanApprovalRequired,
    ToolDenied,
    ToolGatewayTimeout,
    execute_tool_via_gateway,
)


def _state(required_tools: list[str] | None = None) -> dict:
    required = required_tools or ["logs", "metrics"]
    return {
        "incident_id": "INC-GATEWAY",
        "title": "Gateway test",
        "service": "order-service",
        "severity": "high",
        "description": None,
        "status": "running",
        "time_window": {"start": "2026-06-23T00:00:00Z", "end": "2026-06-23T00:30:00Z"},
        "affected_services": ["order-service"],
        "investigation_plan": {
            "objectives": ["test gateway"],
            "required_tools": required,
            "reasoning": "test fixture",
        },
        "investigation_steps": ["planner:selected_tools", "triage:set_scope"],
        "executed_tools": [],
        "skipped_tools": [tool for tool in ["logs", "metrics", "traces", "memory"] if tool not in required],
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
        "root_cause_analysis": None,
        "recommended_actions": [],
        "report_markdown": None,
    }


async def _ok_executor(**kwargs) -> dict:
    return {"ok": True, "arguments": kwargs}


def test_low_risk_tool_allowed_and_executed() -> None:
    result = asyncio.run(
        execute_tool_via_gateway(
            tool_name="query_logs",
            arguments={"service": "order-service"},
            incident_state=_state(),
            executor=_ok_executor,
        )
    )

    assert result["result"]["ok"] is True
    assert result["policy_record"]["tool_name"] == "query_logs"
    assert result["policy_record"]["policy_decision"] == "allow"
    assert result["policy_record"]["status"] == "completed"


def test_critical_tool_denied() -> None:
    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="read_env_vars",
                arguments={},
                incident_state=_state(),
                executor=_ok_executor,
            )
        )
    except ToolDenied as exc:
        assert exc.record.policy_decision == "deny"
        assert exc.record.risk_level == "critical"
    else:
        raise AssertionError("read_env_vars should be denied")


def test_high_risk_tool_requires_approval() -> None:
    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="restart_service",
                arguments={"service": "order-service"},
                incident_state=_state(),
                executor=_ok_executor,
            )
        )
    except HumanApprovalRequired as exc:
        assert exc.record.policy_decision == "review"
        assert exc.record.status == "review_required"
    else:
        raise AssertionError("restart_service should require approval")


def test_unknown_tool_denied() -> None:
    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="unknown_tool",
                arguments={},
                incident_state=_state(),
                executor=_ok_executor,
            )
        )
    except ToolDenied as exc:
        assert exc.record.policy_decision == "deny"
        assert "Unknown tool" in exc.reason
    else:
        raise AssertionError("unknown tools should be denied")


def test_gateway_timeout() -> None:
    async def slow_executor(**kwargs) -> dict:
        await asyncio.sleep(0.05)
        return {"ok": True}

    try:
        asyncio.run(
            execute_tool_via_gateway(
                tool_name="query_logs",
                arguments={},
                incident_state=_state(),
                executor=slow_executor,
                timeout_seconds=0.01,
            )
        )
    except ToolGatewayTimeout as exc:
        assert exc.record.status == "timeout"
        assert exc.record.policy_decision == "allow"
    else:
        raise AssertionError("slow gateway call should time out")


def test_investigation_continues_when_one_selected_tool_is_denied(monkeypatch) -> None:
    monkeypatch.setitem(
        investigation_agent.TOOL_GATEWAY_NAMES,
        "metrics",
        "read_env_vars",
    )

    result = asyncio.run(execute_selected_tools(_state(["metrics", "traces"])))

    assert result["executed_tools"] == ["traces"]
    assert [tool["tool_name"] for tool in result["denied_tools"]] == ["metrics"]
    assert [tool["tool_name"] for tool in result["failed_tools"]] == ["metrics"]
    assert [record["policy_decision"] for record in result["policy_records"]] == [
        "deny",
        "allow",
    ]
    assert len(result["evidence"]) == 1
