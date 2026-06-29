from fastapi.testclient import TestClient

from app.core.config import Settings
from app.harness.config import HarnessConfig
from app.harness.policy import HarnessPolicy
from app.harness.runtime import OmniOpsHarnessRuntime
from app.main import app


def test_harness_describe_includes_core_capabilities() -> None:
    config = HarnessConfig(
        llm_mode="fake",
        tools_mode="fake",
        observability_backend="fake",
        fake_llm_enabled=True,
        fake_tools_enabled=True,
        max_agent_steps=None,
    )
    runtime = OmniOpsHarnessRuntime(config, HarnessPolicy(config))

    description = runtime.describe()

    assert description["name"] == "OmniOps Agent Harness"
    assert "multi_agent_orchestration" in description["capabilities"]
    assert "tool_governance" in description["capabilities"]
    assert "observability_connectors" in description["capabilities"]
    assert "evidence_tracking" in description["capabilities"]


def test_harness_config_from_settings_reports_fake_mode() -> None:
    settings = Settings(use_fake_llm=True, use_fake_tools=True)

    config = HarnessConfig.from_settings(settings)

    assert config.llm_mode == "fake"
    assert config.tools_mode == "fake"
    assert config.observability_backend == "fake"
    assert config.fake_llm_enabled is True
    assert config.fake_tools_enabled is True


def test_harness_config_real_mode_does_not_enable_fake_fallback() -> None:
    settings = Settings(
        use_fake_llm=False,
        use_fake_tools=False,
        observability_backend="prometheus_loki_tempo",
    )
    config = HarnessConfig.from_settings(settings)
    runtime = OmniOpsHarnessRuntime(config, HarnessPolicy(config))

    status = runtime.validate_runtime()

    assert config.llm_mode == "real"
    assert config.tools_mode == "real"
    assert config.fake_tools_enabled is False
    assert config.live_observability_enabled is True
    assert status["real_mode_fake_fallback_allowed"] is False


def test_summarize_result_extracts_harness_fields() -> None:
    config = HarnessConfig(
        llm_mode="real",
        tools_mode="real",
        observability_backend="prometheus_loki_tempo",
        fake_llm_enabled=False,
        fake_tools_enabled=False,
        max_agent_steps=None,
    )
    runtime = OmniOpsHarnessRuntime(config, HarnessPolicy(config))

    result = runtime.summarize_result(
        {
            "root_cause_analysis": {
                "root_cause": "Redis connection pool exhaustion in order-service.",
                "confidence": 0.87,
            },
            "executed_tools": ["logs", "metrics", "traces"],
            "failed_tools": [{"tool_name": "memory", "error_message": "unavailable"}],
            "evidence_items": [
                {"evidence_id": "log-1", "source": "log", "content": "timeout"},
                {"evidence_id": "metric-1", "source": "metric", "content": "p95 spike"},
            ],
            "evidence": [
                {"id": "log-1", "source": "loki"},
                {"id": "metric-1", "source": "prometheus"},
            ],
        }
    )

    assert result.root_cause == "Redis connection pool exhaustion in order-service."
    assert result.confidence == 0.87
    assert result.evidence_count == 2
    assert result.executed_tools == ["logs", "metrics", "traces"]
    assert result.failed_tools == ["memory"]
    assert result.tool_sources == ["loki", "prometheus", "log", "metric"]
    assert result.evidence_sufficient is True


def test_harness_status_api_returns_status() -> None:
    client = TestClient(app)

    response = client.get("/api/harness/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "OmniOps Agent Harness"
    assert "runtime_status" in payload["capabilities"]
    assert "live_backend_reachability" in payload
    assert payload["evidence_policy"]["real_mode_fake_tool_fallback_allowed"] is False
