from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_analyze_incident() -> None:
    create_response = client.post(
        "/api/incidents",
        json={
            "title": "OrderService P95 latency spike",
            "service": "order-service",
            "severity": "high",
        },
    )

    assert create_response.status_code == 201
    incident = create_response.json()
    assert incident["status"] == "created"

    analyze_response = client.post(f"/api/incidents/{incident['id']}/analyze")

    assert analyze_response.status_code == 200
    analyzed = analyze_response.json()
    assert analyzed["status"] == "completed"
    assert analyzed["diagnosis"]["report_markdown"].startswith("# RCA Report")
    assert analyzed["analysis"]["report_markdown"].startswith("# RCA Report")


def test_diagnose_incident_endpoint() -> None:
    create_response = client.post(
        "/api/incidents",
        json={
            "title": "OrderService checkout latency",
            "service": "order-service",
            "severity": "high",
            "description": "P95 latency increased during checkout.",
        },
    )

    assert create_response.status_code == 201
    incident = create_response.json()

    diagnose_response = client.post(f"/api/incidents/{incident['id']}/diagnose")

    assert diagnose_response.status_code == 200
    diagnosis = diagnose_response.json()
    assert diagnosis["incident_id"] == incident["id"]
    assert diagnosis["status"] == "completed"
    assert diagnosis["root_cause_analysis"]["root_cause"] == (
        "Redis connection pool exhaustion in order-service."
    )
    assert len(diagnosis["recommended_actions"]) == 3
    assert len(diagnosis["evidence"]) == 2
    assert diagnosis["executed_tools"] == ["metrics", "traces"]
    assert diagnosis["skipped_tools"] == ["logs", "memory"]
    assert diagnosis["similar_incidents"] == []


def test_history_and_resolve_endpoints() -> None:
    history_response = client.get("/api/incidents/history")

    assert history_response.status_code == 200
    initial_history = history_response.json()
    assert any(item["incident_id"] == "HIST-REDIS-001" for item in initial_history)

    create_response = client.post(
        "/api/incidents",
        json={
            "title": "OrderService Redis timeout after config change",
            "service": "order-service",
            "severity": "high",
        },
    )
    assert create_response.status_code == 201
    incident = create_response.json()

    resolve_response = client.post(f"/api/incidents/{incident['id']}/resolve")

    assert resolve_response.status_code == 200
    resolved = resolve_response.json()
    assert resolved["incident_id"] == incident["id"]
    assert resolved["root_cause"] == "Redis connection pool exhaustion in order-service."
    assert "redis" in resolved["tags"]
