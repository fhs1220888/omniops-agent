"""Tempo HTTP API provider."""

from __future__ import annotations

import httpx


class TempoProvider:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        if not base_url:
            raise ValueError("TEMPO_URL is required for prometheus_loki_tempo backend.")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def query_traces(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
        trace_ids: list[str] | None = None,
    ) -> dict:
        ids = [trace_id for trace_id in trace_ids or [] if trace_id]
        if not ids:
            return {
                "source": "tempo",
                "service": service,
                "traces": [],
                "trace_ids": [],
                "empty": True,
                "error": "No trace_id values were found in logs.",
            }
        traces = []
        errors = []
        for trace_id in ids[:10]:
            result = self._query_trace(trace_id)
            if result["error"]:
                errors.append(f"{trace_id}: {result['error']}")
                continue
            traces.extend(_spans_from_trace(service, trace_id, result["payload"]))
        return {
            "source": "tempo",
            "service": service,
            "traces": traces,
            "trace_ids": ids,
            "empty": not traces,
            "error": "; ".join(errors) if errors and not traces else None,
        }

    def _query_trace(self, trace_id: str) -> dict:
        try:
            response = httpx.get(
                f"{self.base_url}/api/traces/{trace_id}",
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return {"payload": response.json(), "error": None}
        except Exception as exc:
            return {"payload": {}, "error": str(exc)}


def _spans_from_trace(service: str, trace_id: str, payload: dict) -> list[dict]:
    spans = []
    batches = payload.get("batches", [])
    for batch in batches:
        for scope_span in batch.get("scopeSpans", []):
            for span in scope_span.get("spans", []):
                name = span.get("name") or "unknown_span"
                duration_ms = _duration_ms(span)
                spans.append(
                    {
                        "service": service,
                        "trace_id": trace_id,
                        "span": name,
                        "duration_ms": duration_ms,
                    }
                )
    return spans


def _duration_ms(span: dict) -> float:
    try:
        start = int(span.get("startTimeUnixNano", 0))
        end = int(span.get("endTimeUnixNano", 0))
    except (TypeError, ValueError):
        return 0.0
    if end <= start:
        return 0.0
    return round((end - start) / 1_000_000, 3)
