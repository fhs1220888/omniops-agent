"""Check whether live Prometheus, Loki, Tempo, and OmniOps runtime are wired."""

from __future__ import annotations

import json
import os
import re

import httpx


PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100").rstrip("/")
TEMPO_URL = os.getenv("TEMPO_URL", "http://localhost:3200").rstrip("/")
OMNIOPS_URL = os.getenv("OMNIOPS_URL", "http://localhost:8001").rstrip("/")
SERVICE = os.getenv("SMOKE_SERVICE", "order-service")
EXPECTED_ENDPOINTS = [
    "/checkout",
    "/checkout/slow",
    "/checkout/error",
    "/checkout/redis-timeout",
    "/checkout/downstream-timeout",
    "/checkout/db-slow-query",
    "/checkout/app-exception",
    "/checkout/unhealthy",
]
EXPECTED_EVENTS = [
    "redis_timeout",
    "downstream_timeout",
    "db_slow_query",
    "application_exception",
    "service_unhealthy",
]


def main() -> None:
    prometheus = _check_prometheus()
    loki = _check_loki()
    trace_id = _trace_id_from_logs(loki.get("logs", []))
    tempo = _check_tempo(trace_id) if trace_id else _empty_tempo("no trace_id found in Loki logs")
    runtime = _check_runtime_status()
    output = {
        "service": SERVICE,
        "prometheus": prometheus,
        "loki": {
            "reachable": loki["reachable"],
            "log_count": len(loki.get("logs", [])),
            "events_found": _events_from_logs(loki.get("logs", [])),
            "expected_events_present": _expected_events_present(loki.get("logs", [])),
            "error": loki.get("error"),
        },
        "tempo": tempo,
        "runtime_status": runtime,
        "live_real_mode": (
            runtime.get("llm_mode") == "real"
            and runtime.get("tools_mode") == "real"
            and runtime.get("observability_backend") == "prometheus_loki_tempo"
            and runtime.get("fake_tools_enabled") is False
            and runtime.get("fake_llm_enabled") is False
        ),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def _check_prometheus() -> dict:
    query = f'up{{job="{SERVICE}"}} or up{{service="{SERVICE}"}}'
    endpoint_metrics = _check_endpoint_metrics()
    try:
        response = httpx.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=3.0,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("data", {}).get("result", [])
        return {
            "reachable": True,
            "query": query,
            "up": bool(result),
            "result_count": len(result),
            "endpoint_metrics": endpoint_metrics,
            "error": None,
        }
    except Exception as exc:
        return {
            "reachable": False,
            "query": query,
            "up": False,
            "result_count": 0,
            "endpoint_metrics": endpoint_metrics,
            "error": str(exc),
        }


def _check_endpoint_metrics() -> dict:
    results = {}
    for endpoint in EXPECTED_ENDPOINTS:
        query = (
            f'sum(order_service_requests_total{{service="{SERVICE}",'
            f'endpoint="{endpoint}"}})'
        )
        try:
            response = httpx.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=3.0,
            )
            response.raise_for_status()
            payload = response.json()
            values = payload.get("data", {}).get("result", [])
            value = 0.0
            if values:
                value = float(values[0].get("value", [None, 0])[1])
            results[endpoint] = {"found": value > 0, "count": value, "error": None}
        except Exception as exc:
            results[endpoint] = {"found": False, "count": 0, "error": str(exc)}
    return results


def _check_loki() -> dict:
    try:
        response = httpx.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={"query": f'{{service="{SERVICE}"}}', "limit": "200"},
            timeout=3.0,
        )
        response.raise_for_status()
        payload = response.json()
        logs = []
        for stream in payload.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for timestamp, message in stream.get("values", []):
                logs.append(
                    {
                        "timestamp": timestamp,
                        "message": message,
                        "labels": labels,
                    }
                )
        return {"reachable": True, "logs": logs, "error": None}
    except Exception as exc:
        return {"reachable": False, "logs": [], "error": str(exc)}


def _trace_id_from_logs(logs: list[dict]) -> str | None:
    for item in logs:
        message = item.get("message", "")
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict) and payload.get("trace_id"):
            return str(payload["trace_id"])
        match = re.search(r'"trace_id":\s*"([^"]+)"', message)
        if match:
            return match.group(1)
    return None


def _events_from_logs(logs: list[dict]) -> list[str]:
    events = set()
    for item in logs:
        payload = _json_message(item.get("message", ""))
        event = payload.get("event")
        if event:
            events.add(str(event))
    return sorted(events)


def _expected_events_present(logs: list[dict]) -> dict:
    events = set(_events_from_logs(logs))
    return {event: event in events for event in EXPECTED_EVENTS}


def _json_message(message: str) -> dict:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _check_tempo(trace_id: str) -> dict:
    try:
        response = httpx.get(f"{TEMPO_URL}/api/traces/{trace_id}", timeout=3.0)
        response.raise_for_status()
        payload = response.json()
        return {
            "reachable": True,
            "trace_id": trace_id,
            "found": bool(payload),
            "error": None,
        }
    except Exception as exc:
        return {
            "reachable": False,
            "trace_id": trace_id,
            "found": False,
            "error": str(exc),
        }


def _empty_tempo(reason: str) -> dict:
    return {
        "reachable": False,
        "trace_id": None,
        "found": False,
        "error": reason,
    }


def _check_runtime_status() -> dict:
    try:
        response = httpx.get(f"{OMNIOPS_URL}/api/runtime/status", timeout=3.0)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    main()
