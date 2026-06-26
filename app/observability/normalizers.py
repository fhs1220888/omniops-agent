"""Normalize provider responses into tool-agent friendly payloads."""

from __future__ import annotations


class ObservabilityProviderError(RuntimeError):
    """Raised when observability mode is misconfigured."""


def safe_id_part(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")


def time_bounds(time_window: dict[str, str] | None) -> tuple[str | None, str | None]:
    if not time_window:
        return None, None
    return time_window.get("start"), time_window.get("end")


def log_tool_payload(result: dict, service: str, time_window: dict[str, str] | None) -> dict:
    logs = result.get("logs", [])
    source = result.get("source", "logs")
    if result.get("empty") or result.get("error"):
        reason = result.get("error") or "no log records returned"
        return {
            "service": service,
            "time_window": time_window,
            "error_count": 0,
            "top_error": "empty_result",
            "sample": reason,
            "source": source,
            "empty": True,
            "error": result.get("error"),
            "evidence_id": f"evidence-log-{source}-{safe_id_part(service)}",
            "evidence_summary": f"{source} returned no log evidence for {service}.",
            "finding_summary": f"{source} log query returned empty evidence.",
            "observation_summary": f"{source} returned no logs for {service}: {reason}",
            "patterns": [reason],
        }
    messages = [
        str(item.get("message") or item.get("event") or item)
        for item in logs[:5]
    ]
    top_error = str(
        logs[0].get("error_type")
        or logs[0].get("exception")
        or logs[0].get("level")
        or "log_pattern"
    )
    return {
        "service": service,
        "time_window": time_window,
        "error_count": len(logs),
        "top_error": top_error,
        "sample": messages[0],
        "source": source,
        "empty": False,
        "error": None,
        "evidence_id": f"evidence-log-{source}-{safe_id_part(service)}",
        "evidence_summary": f"{source} logs contain {len(logs)} relevant entries for {service}.",
        "finding_summary": f"Log evidence was collected from {source}.",
        "observation_summary": f"Read {len(logs)} {source} log records for {service}.",
        "patterns": messages,
    }


def metric_tool_payload(result: dict, service: str, time_window: dict[str, str] | None) -> dict:
    source = result.get("source", "metrics")
    metrics = result.get("metrics", [])
    values = _metric_values(metrics)
    if result.get("empty") or result.get("error"):
        reason = result.get("error") or "no metric series returned"
        return {
            "service": service,
            "time_window": time_window,
            "p95_latency_ms": 0,
            "baseline_p95_latency_ms": 0,
            "error_rate_percent": 0,
            "source": source,
            "empty": True,
            "error": result.get("error"),
            "queries": result.get("queries", []),
            "evidence_id": f"evidence-metric-{source}-{safe_id_part(service)}",
            "evidence_summary": f"{source} returned no metric evidence for {service}.",
            "finding_summary": f"{source} metric query returned empty evidence.",
            "observation_summary": f"{source} returned no metrics for {service}: {reason}",
            "anomalies": [reason],
        }
    p95_latency = float(values.get("p95_latency_ms", values.get("latency_ms", 0)))
    baseline = float(values.get("baseline_p95_latency_ms", 0))
    error_rate = float(values.get("error_rate_percent", 0))
    anomalies = [f"{name}={value}" for name, value in values.items()][:5]
    return {
        "service": service,
        "time_window": time_window,
        "p95_latency_ms": p95_latency,
        "baseline_p95_latency_ms": baseline,
        "error_rate_percent": error_rate,
        "source": source,
        "empty": False,
        "error": None,
        "queries": result.get("queries", []),
        "evidence_id": f"evidence-metric-{source}-{safe_id_part(service)}",
        "evidence_summary": f"{source} metrics show signals for {service}.",
        "finding_summary": f"Metric evidence was collected from {source}.",
        "observation_summary": f"Read {len(metrics)} {source} metric records for {service}.",
        "anomalies": anomalies or ["Metric records were present."],
    }


def trace_tool_payload(result: dict, service: str, time_window: dict[str, str] | None) -> dict:
    source = result.get("source", "traces")
    traces = result.get("traces", [])
    if result.get("empty") or result.get("error"):
        reason = result.get("error") or "no trace records returned"
        return {
            "service": service,
            "time_window": time_window,
            "slowest_span": "empty_result",
            "slowest_span_ms": 0,
            "trace_count": 0,
            "source": source,
            "empty": True,
            "error": result.get("error"),
            "trace_ids": result.get("trace_ids", []),
            "evidence_id": f"evidence-trace-{source}-{safe_id_part(service)}",
            "evidence_summary": f"{source} returned no trace evidence for {service}.",
            "finding_summary": f"{source} trace query returned empty evidence.",
            "observation_summary": f"{source} returned no traces for {service}: {reason}",
            "bottlenecks": [reason],
        }
    slowest = max(traces, key=lambda item: float(item.get("duration_ms", 0)))
    slowest_span = str(slowest.get("span") or slowest.get("operation") or "unknown_span")
    slowest_ms = float(slowest.get("duration_ms", 0))
    bottlenecks = [
        str(record.get("span") or record.get("operation") or record)
        for record in traces[:5]
    ]
    return {
        "service": service,
        "time_window": time_window,
        "slowest_span": slowest_span,
        "slowest_span_ms": slowest_ms,
        "trace_count": len(traces),
        "source": source,
        "empty": False,
        "error": None,
        "trace_ids": result.get("trace_ids", []),
        "evidence_id": f"evidence-trace-{source}-{safe_id_part(service)}",
        "evidence_summary": f"{source} traces identify `{slowest_span}` as the slowest span.",
        "finding_summary": f"Trace evidence was collected from {source}.",
        "observation_summary": f"Read {len(traces)} {source} trace records for {service}.",
        "bottlenecks": bottlenecks,
    }


def _metric_values(records: list[dict]) -> dict[str, float]:
    values: dict[str, float] = {}
    for record in records:
        if "name" in record and "value" in record:
            values[str(record["name"])] = _float_or_zero(record["value"])
            continue
        for key, value in record.items():
            if key in {"service", "timestamp", "source", "query"}:
                continue
            if isinstance(value, int | float):
                values[key] = float(value)
    return values


def _float_or_zero(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
