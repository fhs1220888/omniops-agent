"""Observability provider factory."""

from __future__ import annotations

from app.core.config import Settings
from app.observability.base import ObservabilityProvider
from app.observability.file_provider import FileObservabilityProvider
from app.observability.loki_provider import LokiProvider
from app.observability.normalizers import ObservabilityProviderError
from app.observability.prometheus_provider import PrometheusProvider
from app.observability.tempo_provider import TempoProvider


class PrometheusLokiTempoProvider:
    def __init__(self, settings: Settings) -> None:
        self.prometheus = PrometheusProvider(settings.prometheus_url)
        self.loki = LokiProvider(settings.loki_url)
        self.tempo = TempoProvider(settings.tempo_url)

    def query_logs(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        return self.loki.query_logs(service, start_time, end_time)

    def query_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        return self.prometheus.query_metrics(service, start_time, end_time)

    def query_traces(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:
        logs = self.loki.query_logs(service, start_time, end_time)
        trace_ids = [
            str(item["trace_id"])
            for item in logs.get("logs", [])
            if item.get("trace_id")
        ]
        return self.tempo.query_traces(service, start_time, end_time, trace_ids)


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
