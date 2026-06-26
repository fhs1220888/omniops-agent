"""File-backed observability provider."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.observability.normalizers import ObservabilityProviderError


class FileObservabilityProvider:
    def __init__(self, data_file: str) -> None:
        if not data_file:
            raise ObservabilityProviderError(
                "OBSERVABILITY_DATA_FILE is required for file observability backend."
            )
        self.data_file = Path(data_file).expanduser()

    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        records = self._records_for("logs", service)
        return {
            "source": "file",
            "service": service,
            "logs": records,
            "empty": not records,
            "error": None,
        }

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        records = self._records_for("metrics", service)
        return {
            "source": "file",
            "service": service,
            "queries": [],
            "metrics": records,
            "empty": not records,
            "error": None,
        }

    def query_traces(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        records = self._records_for("traces", service)
        return {
            "source": "file",
            "service": service,
            "traces": records,
            "trace_ids": [
                str(record["trace_id"])
                for record in records
                if record.get("trace_id")
            ],
            "empty": not records,
            "error": None,
        }

    @classmethod
    def from_settings(cls, settings: Settings) -> "FileObservabilityProvider":
        return cls(settings.observability_data_file)

    def _records_for(self, kind: str, service: str) -> list[dict]:
        payload = self._load()
        records = _records(payload.get(kind, []), kind)
        filtered = [
            record
            for record in records
            if str(record.get("service", "")).lower() == service.lower()
        ]
        return filtered or records

    def _load(self) -> dict[str, Any]:
        if not self.data_file.exists():
            raise ObservabilityProviderError(f"Observability data file not found: {self.data_file}")
        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ObservabilityProviderError("Observability data file must contain valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ObservabilityProviderError("Observability data file must contain a JSON object.")
        return payload


def _records(value: Any, key: str) -> list[dict]:
    if not isinstance(value, list):
        raise ObservabilityProviderError(f"{key} must be a list of objects.")
    if not all(isinstance(item, dict) for item in value):
        raise ObservabilityProviderError(f"{key} must contain only objects.")
    return value
