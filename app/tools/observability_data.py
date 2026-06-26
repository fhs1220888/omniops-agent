"""File-backed observability data provider for non-fake local runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings


class ObservabilityDataError(RuntimeError):
    """Raised when real observability data is requested but unavailable."""


def load_observability_data(settings: Settings | None = None) -> dict[str, list[dict]]:
    config = settings or Settings.from_env()
    if not config.observability_data_file:
        raise ObservabilityDataError(
            "OBSERVABILITY_DATA_FILE is required when USE_FAKE_TOOLS=false."
        )
    path = Path(config.observability_data_file).expanduser()
    if not path.exists():
        raise ObservabilityDataError(f"Observability data file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ObservabilityDataError("Observability data file must contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ObservabilityDataError("Observability data file must contain a JSON object.")
    return {
        "logs": _records(payload.get("logs", []), "logs"),
        "metrics": _records(payload.get("metrics", []), "metrics"),
        "traces": _records(payload.get("traces", []), "traces"),
    }


def records_for(kind: str, service: str, settings: Settings | None = None) -> list[dict]:
    records = load_observability_data(settings).get(kind, [])
    filtered = [
        record
        for record in records
        if str(record.get("service", "")).lower() == service.lower()
    ]
    return filtered or records


def _records(value: Any, key: str) -> list[dict]:
    if not isinstance(value, list):
        raise ObservabilityDataError(f"{key} must be a list of objects.")
    if not all(isinstance(item, dict) for item in value):
        raise ObservabilityDataError(f"{key} must contain only objects.")
    return value


def safe_id_part(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")
