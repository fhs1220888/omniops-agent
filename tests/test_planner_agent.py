from app.agents.planner_agent import build_investigation_plan, planner_agent
from app.models.incident import Incident
from app.agents.graph import run_incident_diagnosis_with_store
from app.memory.incident_store import IncidentStore


def test_planner_selects_metrics_and_traces_for_latency() -> None:
    plan = build_investigation_plan(
        title="OrderService P95 latency spike",
        service="order-service",
        severity="high",
    )

    assert plan.required_tools == ["metrics", "traces"]
    assert "latency" in plan.reasoning.lower()


def test_planner_selects_logs_and_memory_for_pod_crash() -> None:
    plan = build_investigation_plan(
        title="Payment pod crash loop",
        service="payment-service",
        severity="critical",
    )

    assert plan.required_tools == ["logs", "memory"]


def test_planner_selects_all_tools_for_database_timeout() -> None:
    plan = build_investigation_plan(
        title="OrderService database timeout",
        service="order-service",
        severity="high",
    )

    assert plan.required_tools == ["logs", "metrics", "traces", "memory"]


def test_planner_broadens_observability_tools_for_external_mode(monkeypatch) -> None:
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")

    result = planner_agent(
        {
            "title": "CheckoutService payment provider latency",
            "service": "checkout-service",
            "severity": "high",
            "description": "Use exported observability records.",
            "investigation_steps": [],
        }
    )

    assert result["investigation_plan"]["required_tools"] == [
        "logs",
        "metrics",
        "traces",
    ]
    assert result["skipped_tools"] == ["memory"]


def test_routing_skips_unnecessary_nodes_for_pod_crash(tmp_path) -> None:
    incident = Incident(
        id="INC-POD-CRASH",
        title="Payment pod crash loop",
        service="payment-service",
        severity="critical",
    )
    store = IncidentStore(tmp_path / "incidents.json")

    diagnosis = run_incident_diagnosis_with_store(incident, store)

    assert diagnosis.executed_tools == ["logs", "memory"]
    assert diagnosis.skipped_tools == ["metrics", "traces"]
    assert [item.type for item in diagnosis.evidence] == ["log_pattern"]
    assert diagnosis.investigation_steps == [
        "planner:selected_tools",
        "triage:set_scope",
        "logs:query_logs",
        "memory:find_similar",
        "reflection:sufficient",
    ]
