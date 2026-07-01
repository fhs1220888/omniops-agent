"""Loki HTTP API provider."""

from __future__ import annotations

import re
import json

import httpx

from app.observability.profile import ObservabilityProfile, load_observability_profile


class LokiProvider:
    def __init__(
        self,
        base_url: str,
        profile: ObservabilityProfile | None = None,
        limit: int | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        if not base_url:
            raise ValueError("LOKI_URL is required for prometheus_loki_tempo backend.")
        self.base_url = base_url.rstrip("/")
        self.profile = profile or load_observability_profile()
        self.limit = limit or self.profile.loki.default_limit
        self.timeout_seconds = timeout_seconds

    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        selector = loki_selector(service, self.profile)
        params = {
            "query": selector,
            "limit": str(self.limit),
        }
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        try:
            response = httpx.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            return {
                "source": "loki",
                "service": service,
                "profile_name": self.profile.name,
                "loki_selector": selector,
                "trace_id_fields": self.profile.loki.trace_id_fields,
                "logs": [],
                "empty": True,
                "error": str(exc),
            }
        if payload.get("status") != "success":
            return {
                "source": "loki",
                "service": service,
                "profile_name": self.profile.name,
                "loki_selector": selector,
                "trace_id_fields": self.profile.loki.trace_id_fields,
                "logs": [],
                "empty": True,
                "error": str(payload.get("error") or payload),
            }
        logs = []
        for stream in payload.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for timestamp, message in stream.get("values", []):
                logs.append(
                    {
                        "service": service,
                        "timestamp": timestamp,
                        "message": message,
                        "labels": labels,
                        "trace_id": extract_trace_id(message, self.profile.loki.trace_id_fields),
                    }
                )
        return {
            "source": "loki",
            "service": service,
            "profile_name": self.profile.name,
            "loki_selector": selector,
            "trace_id_fields": self.profile.loki.trace_id_fields,
            "logs": logs,
            "empty": not logs,
            "error": None,
        }


def loki_selector(service: str, profile: ObservabilityProfile | None = None) -> str:
    config = profile or load_observability_profile()
    return f'{{{config.loki.service_label}="{service}"}}'


def extract_trace_id(message: str, fields: list[str] | None = None) -> str | None:
    trace_fields = fields or ["trace_id", "traceId", "traceID"]
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        payload = {}
    if isinstance(payload, dict):
        for field in trace_fields:
            if payload.get(field):
                return str(payload[field])
    pattern = "|".join(re.escape(field) for field in trace_fields)
    match = re.search(rf"(?:{pattern})=([a-zA-Z0-9_-]+)", message)
    if match:
        return match.group(1)
    return None
