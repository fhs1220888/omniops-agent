"""Loki HTTP API provider."""

from __future__ import annotations

import re

import httpx


class LokiProvider:
    def __init__(self, base_url: str, limit: int = 100, timeout_seconds: float = 5.0) -> None:
        if not base_url:
            raise ValueError("LOKI_URL is required for prometheus_loki_tempo backend.")
        self.base_url = base_url.rstrip("/")
        self.limit = limit
        self.timeout_seconds = timeout_seconds

    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        params = {
            "query": f'{{service="{service}"}}',
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
                "logs": [],
                "empty": True,
                "error": str(exc),
            }
        if payload.get("status") != "success":
            return {
                "source": "loki",
                "service": service,
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
                        "trace_id": _extract_trace_id(message),
                    }
                )
        return {
            "source": "loki",
            "service": service,
            "logs": logs,
            "empty": not logs,
            "error": None,
        }


def _extract_trace_id(message: str) -> str | None:
    match = re.search(r"(?:trace_id|traceId|traceID)=([a-zA-Z0-9_-]+)", message)
    if match:
        return match.group(1)
    return None
