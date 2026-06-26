from pathlib import Path

from fastapi.testclient import TestClient

from app.demo.faults import SCENARIOS
from app.demo.ground_truth import GROUND_TRUTH
from app.main import app
from app.services.benchmark_service import list_scenarios, run_benchmark, run_scenario


client = TestClient(app)


def test_demo_scenarios_are_registered() -> None:
    scenarios = list_scenarios()
    names = {scenario["scenario_name"] for scenario in scenarios}

    assert names == {
        "redis_timeout",
        "mysql_slow_query",
        "kafka_lag",
        "bad_config_deploy",
    }
    assert set(SCENARIOS) == set(GROUND_TRUTH)


def test_run_single_scenario() -> None:
    result = run_scenario("redis_timeout")

    assert result.scenario_name == "redis_timeout"
    assert result.rca_correct is True
    assert result.evidence_precision == 1.0
    assert result.tool_timeline
    assert result.agent_timeline
    assert result.confidence > 0


def test_run_benchmark_generates_markdown_report(tmp_path) -> None:
    report_path = tmp_path / "benchmark_report.md"

    summary = run_benchmark(report_path=report_path)

    assert summary.scenario_count == 4
    assert summary.rca_accuracy == 1.0
    assert summary.evidence_precision > 0
    assert summary.average_agent_count > 0
    assert summary.average_tool_count > 0
    assert Path(summary.report_path).exists()

    report = report_path.read_text(encoding="utf-8")
    assert "# OmniOps Agent Benchmark Report" in report
    assert "## redis_timeout" in report
    assert "### Tool timeline" in report
    assert "### Agent timeline" in report
    assert "Confidence" in report


def test_demo_api_scenarios() -> None:
    response = client.get("/api/demo/scenarios")

    assert response.status_code == 200
    assert len(response.json()) == 4


def test_demo_api_run_scenario() -> None:
    response = client.post("/api/demo/run/mysql_slow_query")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_name"] == "mysql_slow_query"
    assert payload["rca_correct"] is True


def test_demo_api_benchmark() -> None:
    response = client.get("/api/demo/benchmark")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_count"] == 4
    assert payload["rca_accuracy"] == 1.0
    assert payload["report_path"] == "benchmark_report.md"
