from fastapi.testclient import TestClient

from app.main import app
from app.services.runtime_status import get_runtime_status


def test_runtime_status_reports_modes(monkeypatch) -> None:
    monkeypatch.setenv("USE_FAKE_LLM", "false")
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "prometheus_loki_tempo")
    monkeypatch.setenv("PROMETHEUS_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("LOKI_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("TEMPO_URL", "http://127.0.0.1:1")

    status = get_runtime_status()

    assert status["llm_mode"] == "real"
    assert status["tools_mode"] == "real"
    assert status["observability_backend"] == "prometheus_loki_tempo"
    assert status["prometheus_reachable"] is False
    assert status["loki_reachable"] is False
    assert status["tempo_reachable"] is False
    assert status["fake_tools_enabled"] is False
    assert status["fake_llm_enabled"] is False


def test_runtime_status_api_returns_200(monkeypatch) -> None:
    monkeypatch.setenv("USE_FAKE_TOOLS", "true")
    client = TestClient(app)

    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    assert "fake_tools_enabled" in response.json()
