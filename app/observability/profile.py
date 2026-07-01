"""Observability profile loading for real project integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.config import PROJECT_ROOT, Settings


class ServiceProfile(BaseModel):
    default_service_label: str = "service"
    default_service_name: str | None = None


class PrometheusProfile(BaseModel):
    request_count_metric: str
    latency_bucket_metric: str
    service_label: str = "service"
    endpoint_label: str = "endpoint"
    status_label: str = "status"
    latency_window: str = "5m"


class LokiProfile(BaseModel):
    service_label: str = "service"
    trace_id_fields: list[str] = Field(default_factory=lambda: ["trace_id", "traceId", "traceID"])
    default_limit: int = 100


class TempoProfile(BaseModel):
    trace_id_source: str = "loki"


class ObservabilityProfile(BaseModel):
    name: str
    service: ServiceProfile = Field(default_factory=ServiceProfile)
    prometheus: PrometheusProfile
    loki: LokiProfile
    tempo: TempoProfile


class ObservabilityProfileError(ValueError):
    pass


def load_observability_profile(
    profile_name_or_path: str | None = None,
    *,
    settings: Settings | None = None,
) -> ObservabilityProfile:
    config = settings or Settings.from_env()
    requested = profile_name_or_path or config.observability_profile or "demo_order_service"
    path = _profile_path(requested, config)
    if not path.exists():
        raise ObservabilityProfileError(
            f"Observability profile not found: {requested}. Looked for {path}."
        )
    try:
        payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return ObservabilityProfile.model_validate(payload)
    except Exception as exc:
        raise ObservabilityProfileError(
            f"Failed to load observability profile {requested}: {exc}"
        ) from exc


def list_observability_profiles(settings: Settings | None = None) -> list[dict]:
    config = settings or Settings.from_env()
    profile_dir = _resolve_path(config.observability_profile_dir)
    if not profile_dir.exists():
        return []
    profiles = []
    for path in sorted(profile_dir.glob("*.yaml")):
        try:
            profile = load_observability_profile(str(path), settings=config)
            profiles.append(
                {
                    "name": profile.name,
                    "path": path.relative_to(PROJECT_ROOT).as_posix(),
                }
            )
        except ObservabilityProfileError:
            profiles.append(
                {
                    "name": path.stem,
                    "path": path.relative_to(PROJECT_ROOT).as_posix(),
                    "error": "failed_to_load",
                }
            )
    return profiles


def _profile_path(requested: str, config: Settings) -> Path:
    candidate = Path(requested)
    if candidate.suffix in {".yaml", ".yml"} or candidate.is_absolute() or "/" in requested:
        return _resolve_path(candidate)
    return _resolve_path(config.observability_profile_dir) / f"{requested}.yaml"


def _resolve_path(path: Path | str) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return PROJECT_ROOT / value
