from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_skills_status_api() -> None:
    response = client.get("/api/skills/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["skill_count"] >= 8


def test_skills_select_api() -> None:
    response = client.post(
        "/api/skills/select",
        json={
            "incident": {
                "title": "Redis timeout during checkout",
                "service": "order-service",
                "symptom": "Checkout returns 504",
            },
            "evidence_summary": "Logs contain redis_timeout.",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["selected_skills"]]
    assert "redis_timeout_diagnosis" in ids
    assert "rca_report_generation" in ids


def test_skills_get_api() -> None:
    response = client.get("/api/skills/redis_timeout_diagnosis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Redis Timeout Diagnosis Skill"
    assert "## Guardrails" in payload["content"]
