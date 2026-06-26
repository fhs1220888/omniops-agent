from app.tools.log_tools import query_logs
from app.tools.metric_tools import query_metrics
from app.tools.trace_tools import query_traces


def test_real_file_mode_does_not_fallback_to_fake_data(monkeypatch, tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text('{"logs": [], "metrics": [], "traces": []}', encoding="utf-8")
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "file")
    monkeypatch.setenv("OBSERVABILITY_DATA_FILE", str(data_file))

    logs = query_logs("order-service", None)
    metrics = query_metrics("order-service", None)
    traces = query_traces("order-service", None)

    assert logs["source"] == "file"
    assert metrics["source"] == "file"
    assert traces["source"] == "file"
    assert logs["evidence_id"] == "evidence-log-file-order-service"
    assert metrics["evidence_id"] == "evidence-metric-file-order-service"
    assert traces["evidence_id"] == "evidence-trace-file-order-service"
    assert "redis" not in logs["evidence_summary"].lower()
    assert "redis" not in metrics["evidence_summary"].lower()
    assert "redis" not in traces["evidence_summary"].lower()


def test_live_mode_connection_errors_do_not_fallback_to_fake_data(monkeypatch) -> None:
    monkeypatch.setenv("USE_FAKE_TOOLS", "false")
    monkeypatch.setenv("OBSERVABILITY_BACKEND", "prometheus_loki_tempo")
    monkeypatch.setenv("PROMETHEUS_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("LOKI_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("TEMPO_URL", "http://127.0.0.1:1")

    logs = query_logs("order-service", None)
    metrics = query_metrics("order-service", None)
    traces = query_traces("order-service", None)

    assert logs["source"] == "loki"
    assert metrics["source"] == "prometheus"
    assert traces["source"] == "tempo"
    assert logs["empty"] is True
    assert metrics["empty"] is True
    assert traces["empty"] is True
    assert logs["error"]
    assert metrics["error"]
    assert traces["error"]
    assert "RedisTimeoutException" not in str(logs)
