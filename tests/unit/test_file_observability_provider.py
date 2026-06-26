import json

from app.observability.file_provider import FileObservabilityProvider


def test_file_provider_reads_logs_metrics_and_traces(tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text(
        json.dumps(
            {
                "logs": [{"service": "svc", "message": "trace_id=abc timeout"}],
                "metrics": [{"service": "svc", "name": "p95_latency_ms", "value": 900}],
                "traces": [{"service": "svc", "trace_id": "abc", "span": "svc -> db", "duration_ms": 800}],
            }
        ),
        encoding="utf-8",
    )
    provider = FileObservabilityProvider(str(data_file))

    logs = provider.query_logs("svc", None, None)
    metrics = provider.query_metrics("svc", None, None)
    traces = provider.query_traces("svc", None, None)

    assert logs["source"] == "file"
    assert logs["logs"][0]["message"] == "trace_id=abc timeout"
    assert metrics["metrics"][0]["name"] == "p95_latency_ms"
    assert traces["trace_ids"] == ["abc"]


def test_file_provider_filters_by_service_and_falls_back_to_all_records(tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text(
        json.dumps(
            {
                "logs": [{"service": "other", "message": "shared export"}],
                "metrics": [],
                "traces": [],
            }
        ),
        encoding="utf-8",
    )
    provider = FileObservabilityProvider(str(data_file))

    logs = provider.query_logs("missing-service", None, None)

    assert logs["logs"] == [{"service": "other", "message": "shared export"}]
