import asyncio

from app.agents import investigation_agent
from app.agents.graph import run_incident_diagnosis
from app.agents.investigation_agent import execute_selected_tools
from app.models.incident import Incident


def _state(required_tools: list[str]) -> dict:
    return {
        "incident_id": "INC-ASYNC",
        "title": "Async investigation test",
        "service": "order-service",
        "severity": "high",
        "description": None,
        "status": "running",
        "time_window": {"start": "2026-06-23T00:00:00Z", "end": "2026-06-23T00:30:00Z"},
        "affected_services": ["order-service"],
        "investigation_plan": {
            "objectives": ["test parallel execution"],
            "required_tools": required_tools,
            "reasoning": "test fixture",
        },
        "investigation_steps": ["planner:selected_tools", "triage:set_scope"],
        "executed_tools": [],
        "skipped_tools": [tool for tool in ["logs", "metrics", "traces", "memory"] if tool not in required_tools],
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


def _update(tool: str) -> dict:
    return {
        "evidence": [
            {
                "id": f"evidence-{tool}",
                "source": f"fake_{tool}",
                "type": "metric_anomaly" if tool == "metrics" else "trace_bottleneck",
                "summary": f"{tool} evidence",
                "metadata": {"tool": tool},
            }
        ],
        "findings": [],
        "tool_observations": [],
    }


def test_successful_parallel_execution(monkeypatch) -> None:
    both_started = asyncio.Event()
    started: list[str] = []

    async def make_agent(tool: str):
        started.append(tool)
        if len(started) == 2:
            both_started.set()
        await both_started.wait()
        return _update(tool)

    monkeypatch.setattr(
        investigation_agent,
        "build_tool_agents",
        lambda store=None: {
            "logs": lambda state: make_agent("logs"),
            "metrics": lambda state: make_agent("metrics"),
            "traces": lambda state: make_agent("traces"),
            "memory": lambda state: make_agent("memory"),
        },
    )

    result = asyncio.run(
        execute_selected_tools(_state(["metrics", "traces"]), timeout_seconds=0.5)
    )

    assert started == ["metrics", "traces"]
    assert result["executed_tools"] == ["metrics", "traces"]
    assert result["failed_tools"] == []
    assert [record["tool_name"] for record in result["policy_records"]] == [
        "query_metrics",
        "query_traces",
    ]
    assert len(result["tool_timings"]) == 2
    assert result["total_investigation_duration_ms"] >= 0


def test_one_tool_failure_still_produces_diagnosis(monkeypatch) -> None:
    async def failing_metrics(state):
        raise RuntimeError("metric backend unavailable")

    async def successful_traces(state):
        return _update("traces")

    monkeypatch.setattr(
        investigation_agent,
        "build_tool_agents",
        lambda store=None: {
            "logs": failing_metrics,
            "metrics": failing_metrics,
            "traces": successful_traces,
            "memory": successful_traces,
        },
    )

    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-PARTIAL-FAILURE",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    assert diagnosis.status == "completed"
    assert diagnosis.executed_tools == ["traces"]
    assert [failure.tool_name for failure in diagnosis.failed_tools] == ["metrics", "metrics"]
    assert diagnosis.failed_tools[0].timeout is False
    assert diagnosis.policy_records[0].policy_decision == "allow"
    assert len(diagnosis.evidence) == 1
    assert "metrics: failure" in diagnosis.report_markdown


def test_one_tool_timeout_still_produces_diagnosis(monkeypatch) -> None:
    async def slow_metrics(state):
        await asyncio.sleep(0.05)
        return _update("metrics")

    async def successful_traces(state):
        return _update("traces")

    monkeypatch.setattr(investigation_agent, "TOOL_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(
        investigation_agent,
        "build_tool_agents",
        lambda store=None: {
            "logs": slow_metrics,
            "metrics": slow_metrics,
            "traces": successful_traces,
            "memory": successful_traces,
        },
    )

    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-PARTIAL-TIMEOUT",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    assert diagnosis.status == "completed"
    assert diagnosis.executed_tools == ["traces"]
    assert [failure.tool_name for failure in diagnosis.failed_tools] == ["metrics", "metrics"]
    assert diagnosis.failed_tools[0].timeout is True
    assert diagnosis.policy_records[0].status == "timeout"
    assert len(diagnosis.tool_timings) == 3
    assert "metrics: timeout" in diagnosis.report_markdown
