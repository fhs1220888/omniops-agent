"""Prometheus HTTP API provider."""

from __future__ import annotations

import httpx


class PrometheusProvider:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        if not base_url:
            raise ValueError("PROMETHEUS_URL is required for prometheus_loki_tempo backend.")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        queries = _prometheus_queries(service)
        metrics: list[dict] = []
        errors: list[str] = []
        for name, query in queries:
            result = self._query(query)
            if result["error"]:
                errors.append(f"{name}: {result['error']}")
                continue
            values = result["values"]
            if values:
                metrics.append(
                    {
                        "service": service,
                        "name": name,
                        "value": values[0],
                        "query": query,
                    }
                )
        return {
            "source": "prometheus",
            "service": service,
            "queries": [query for _, query in queries],
            "metrics": metrics,
            "empty": not metrics,
            "error": "; ".join(errors) if errors and not metrics else None,
        }

    def _query(self, query: str) -> dict:
        try:
            response = httpx.get(
                f"{self.base_url}/api/v1/query",
                params={"query": query},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return {"values": [], "error": str(exc)}
        if payload.get("status") != "success":
            return {"values": [], "error": str(payload.get("error") or payload)}
        result = payload.get("data", {}).get("result", [])
        values = []
        for item in result:
            value = item.get("value", [None, None])[1]
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
        return {"values": values, "error": None}


def _prometheus_queries(service: str) -> list[tuple[str, str]]:
    selector = f'service="{service}"'
    return [
        ("service_up", f'up{{job="{service}"}} or up{{{selector}}}'),
        (
            "request_rate",
            f'sum(rate(order_service_requests_total{{{selector}}}[5m])) or sum(rate(http_requests_total{{{selector}}}[5m]))',
        ),
        (
            "error_rate_percent",
            f'100 * sum(rate(order_service_requests_total{{{selector},status=~"5.."}}[5m])) / clamp_min(sum(rate(order_service_requests_total{{{selector}}}[5m])), 1) '
            f'or 100 * sum(rate(http_requests_total{{{selector},status=~"5.."}}[5m])) / clamp_min(sum(rate(http_requests_total{{{selector}}}[5m])), 1)',
        ),
        (
            "p95_latency_ms",
            f'1000 * histogram_quantile(0.95, sum(rate(order_service_request_duration_seconds_bucket{{{selector}}}[5m])) by (le)) '
            f'or 1000 * histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{{selector}}}[5m])) by (le))',
        ),
    ]
