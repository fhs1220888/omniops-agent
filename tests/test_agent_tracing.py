from app.agents.graph import run_incident_diagnosis
from app.models.incident import Incident


def test_agent_trace_recording() -> None:
    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-TRACE",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    agent_names = [trace.agent_name for trace in diagnosis.agent_traces]

    assert agent_names == ["planner", "triage", "investigation", "reflection", "report"]
    assert all(trace.status == "success" for trace in diagnosis.agent_traces)
    assert all(trace.duration_ms >= 0 for trace in diagnosis.agent_traces)


def test_tool_trace_recording_and_evidence_generation() -> None:
    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-TOOL-TRACE",
            title="OrderService database timeout during checkout",
            service="order-service",
            severity="high",
        )
    )

    assert [trace.tool_name for trace in diagnosis.tool_traces] == [
        "query_logs",
        "query_metrics",
        "query_traces",
        "query_memory",
    ]
    assert all(trace.policy_decision == "allow" for trace in diagnosis.tool_traces)
    assert {item.source for item in diagnosis.evidence_items} >= {
        "log",
        "metric",
        "trace",
        "memory",
    }
    assert diagnosis.evidence_graph["nodes"]
    assert diagnosis.evidence_graph["edges"]


def test_report_contains_agentops_and_evidence_sections() -> None:
    diagnosis = run_incident_diagnosis(
        Incident(
            id="INC-REPORT-TRACE",
            title="OrderService latency issue",
            service="order-service",
            severity="high",
        )
    )

    assert "## Agent Timeline" in diagnosis.report_markdown
    assert "## Tool Timeline" in diagnosis.report_markdown
    assert "## Evidence Summary" in diagnosis.report_markdown
    assert "## Confidence Scores" in diagnosis.report_markdown
