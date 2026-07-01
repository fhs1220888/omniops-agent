"""Observability provider factory."""

from __future__ import annotations

from app.core.config import Settings
from app.observability.base import ObservabilityProvider
from app.observability.file_provider import FileObservabilityProvider
from app.observability.loki_provider import LokiProvider
from app.observability.normalizers import ObservabilityProviderError
from app.observability.profile import ObservabilityProfileError, load_observability_profile
from app.observability.prometheus_provider import PrometheusProvider
from app.observability.tempo_provider import TempoProvider


class PrometheusLokiTempoProvider:
    def __init__(self, settings: Settings) -> None:
        self.profile_error: str | None = None
        try:
            profile = load_observability_profile(settings=settings)
        except ObservabilityProfileError as exc:
            self.profile_error = str(exc)
            profile = None
        self.profile = profile
        self.prometheus = (
            PrometheusProvider(settings.prometheus_url, profile)
            if profile is not None
            else None
        )
        self.loki = LokiProvider(settings.loki_url, profile) if profile is not None else None
        self.tempo = TempoProvider(settings.tempo_url, profile) if profile is not None else None

    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        if self.loki is None:
            return _profile_error_result("loki", service, self.profile_error)
        return self.loki.query_logs(service, start_time, end_time)

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        if self.prometheus is None:
            return _profile_error_result("prometheus", service, self.profile_error)
        return self.prometheus.query_metrics(service, start_time, end_time)

    def query_traces(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        if self.loki is None or self.tempo is None:
            return _profile_error_result("tempo", service, self.profile_error)
        logs = self.loki.query_logs(service, start_time, end_time)
        trace_ids = [
            str(item["trace_id"])
            for item in logs.get("logs", [])
            if item.get("trace_id")
        ]
        return self.tempo.query_traces(service, start_time, end_time, trace_ids)


def _profile_error_result(source: str, service: str, error: str | None) -> dict:
    payload = {
        "source": source,
        "service": service,
        "profile_name": None,
        "empty": True,
        "error": error or "Observability profile failed to load.",
    }
    if source == "prometheus":
        payload.update({"queries": [], "metrics": []})
    elif source == "loki":
        payload.update({"logs": [], "loki_selector": None, "trace_id_fields": []})
    elif source == "tempo":
        payload.update({"traces": [], "trace_ids": [], "trace_id_source": None})
    return payload


def get_provider(settings: Settings | None = None) -> ObservabilityProvider:
    config = settings or Settings.from_env()
    if config.use_fake_tools:
        raise ObservabilityProviderError(
            "Observability provider is not used when USE_FAKE_TOOLS=true."
        )
    if config.observability_backend == "file":
        return FileObservabilityProvider.from_settings(config)
    if config.observability_backend == "prometheus_loki_tempo":
        return PrometheusLokiTempoProvider(config)
    if config.observability_backend == "fake":
        raise ObservabilityProviderError(
            "OBSERVABILITY_BACKEND=fake requires USE_FAKE_TOOLS=true."
        )
    raise ObservabilityProviderError(
        f"Unsupported OBSERVABILITY_BACKEND: {config.observability_backend}"
    )
