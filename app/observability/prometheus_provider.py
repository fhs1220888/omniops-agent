"""Prometheus HTTP API provider."""

from __future__ import annotations

import httpx

from app.observability.profile import ObservabilityProfile, load_observability_profile


class PrometheusProvider:
    def __init__(
        self,
        base_url: str,
        profile: ObservabilityProfile | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        if not base_url:
            raise ValueError("PROMETHEUS_URL is required for prometheus_loki_tempo backend.")
        self.base_url = base_url.rstrip("/")
        self.profile = profile or load_observability_profile()
        self.timeout_seconds = timeout_seconds

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        queries = prometheus_queries(service, self.profile)
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
                        "profile_name": self.profile.name,
                    }
                )
        return {
            "source": "prometheus",
            "service": service,
            "profile_name": self.profile.name,
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


def prometheus_queries(
    service: str,
    profile: ObservabilityProfile | None = None,
) -> list[tuple[str, str]]:
    config = profile or load_observability_profile()
    prometheus = config.prometheus
    selector = f'{prometheus.service_label}="{service}"'
    status_selector = (
        f'{prometheus.service_label}="{service}",'
        f'{prometheus.status_label}=~"5.."'
    )
    window = prometheus.latency_window
    return [
        ("service_up", f'up{{job="{service}"}} or up{{{selector}}}'),
        (
            "request_rate",
            f"sum(rate({prometheus.request_count_metric}{{{selector}}}[{window}]))",
        ),
        (
            "error_rate_percent",
            f"100 * sum(rate({prometheus.request_count_metric}{{{status_selector}}}[{window}])) / "
            f"clamp_min(sum(rate({prometheus.request_count_metric}{{{selector}}}[{window}])), 1)",
        ),
        (
            "p95_latency_ms",
            f"1000 * histogram_quantile(0.95, "
            f"sum(rate({prometheus.latency_bucket_metric}{{{selector}}}[{window}])) by (le))",
        ),
    ]
