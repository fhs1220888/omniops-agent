from app.agents.graph import (
    run_incident_analysis,
    run_incident_diagnosis,
    run_incident_diagnosis_with_store,
)
from app.memory.incident_store import IncidentStore
from app.models.incident import Incident


def test_run_incident_analysis_generates_report() -> None:
    result = run_incident_analysis(
        incident_id="INC-TEST",
        title="OrderService latency spike",
        service="order-service",
        severity="high",
    )

    assert result["status"] == "completed"
    assert result["affected_services"] == ["order-service"]
    assert result["report_markdown"] is not None
    assert "Redis" in result["report_markdown"]
    assert len(result["evidence"]) == 2
    assert result["executed_tools"] == ["metrics", "traces"]
    assert result["skipped_tools"] == ["logs", "memory"]


def test_run_incident_diagnosis_produces_rca_and_actions() -> None:
    incident = Incident(
        id="INC-DIAGNOSE",
        title="OrderService checkout latency",
        service="order-service",
        severity="high",
    )

    diagnosis = run_incident_diagnosis(incident)

    assert diagnosis.status == "completed"
    assert diagnosis.root_cause_analysis.confidence == 0.87
    assert "Redis connection pool exhaustion" in diagnosis.root_cause_analysis.root_cause
    assert len(diagnosis.evidence) == 2
    assert [item.type for item in diagnosis.evidence] == [
        "metric_anomaly",
        "trace_bottleneck",
    ]
    assert len(diagnosis.recommended_actions) == 3
    assert diagnosis.recommended_actions[0].action_type == "mitigate"
    assert diagnosis.executed_tools == ["metrics", "traces"]
    assert diagnosis.skipped_tools == ["logs", "memory"]


def test_run_incident_diagnosis_includes_similar_incidents(tmp_path) -> None:
    incident = Incident(
        id="INC-SIMILAR",
        title="OrderService database timeout during checkout",
        service="order-service",
        severity="high",
    )
    store = IncidentStore(tmp_path / "incidents.json")

    diagnosis = run_incident_diagnosis_with_store(incident, store)

    assert len(diagnosis.similar_incidents) == 3
    assert diagnosis.similar_incidents[0].incident_id == "HIST-REDIS-001"
    assert diagnosis.executed_tools == ["logs", "metrics", "traces", "memory"]
    assert diagnosis.skipped_tools == []
