from app.agents import investigation_agent
from app.agents.graph import run_incident_diagnosis
from app.agents.reflection_agent import reflection_agent
from app.models.incident import Incident


def test_replanning_runs_at_most_max_investigation_rounds(monkeypatch) -> None:
    async def failing_metrics(state):
        raise RuntimeError("metric backend unavailable")

    async def successful_traces(state):
        return {
            "evidence": [
                {
                    "id": "evidence-trace-redis-bottleneck",
                    "source": "fake_traces",
                    "type": "trace_bottleneck",
                    "summary": "Slow traces wait on Redis.",
                    "metadata": {"service": "order-service", "slowest_span_ms": 1850},
                }
            ],
            "findings": [],
            "tool_observations": [],
        }

    monkeypatch.setattr(
        investigation_agent,
        "build_tool_agents",
        lambda store=None: {
            "logs": successful_traces,
            "metrics": failing_metrics,
            "traces": successful_traces,
            "memory": successful_traces,
        },
    )

    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-REPLAN",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    assert diagnosis.investigation_round == diagnosis.max_investigation_rounds
    assert [tool.tool_name for tool in diagnosis.failed_tools] == ["metrics", "metrics"]
    assert diagnosis.reflection_decision == "need_more_evidence"
    assert diagnosis.replanning_requested is False


def test_additional_tools_are_merged_without_duplicates() -> None:
    state = {
        "investigation_plan": {
            "objectives": ["test"],
            "required_tools": ["metrics"],
            "reasoning": "test",
        },
        "investigation_steps": [],
        "executed_tools": ["metrics"],
        "evidence_items": [
            {
                "evidence_id": "weak-evidence",
                "source": "metric",
                "content": "Weak signal",
                "confidence": 0.5,
            }
        ],
        "failed_tools": [],
        "denied_tools": [],
        "approval_required_tools": [],
        "investigation_round": 1,
        "max_investigation_rounds": 2,
    }

    result = reflection_agent(state)

    assert result["additional_tools"] == ["logs", "traces", "memory"]
    assert result["investigation_plan"]["required_tools"] == [
        "metrics",
        "logs",
        "traces",
        "memory",
    ]


def test_report_includes_reflection_information() -> None:
    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-REFLECTION-REPORT",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    assert "## Reflection" in diagnosis.report_markdown
    assert "Decision:" in diagnosis.report_markdown
    assert "Investigation rounds:" in diagnosis.report_markdown
