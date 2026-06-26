import pytest

from app.core.config import Settings
from app.observability.factory import PrometheusLokiTempoProvider, get_provider
from app.observability.file_provider import FileObservabilityProvider
from app.observability.normalizers import ObservabilityProviderError


def test_factory_returns_file_provider_for_file_backend(tmp_path) -> None:
    data_file = tmp_path / "observability.json"
    data_file.write_text('{"logs": [], "metrics": [], "traces": []}', encoding="utf-8")
    settings = Settings(
        use_fake_tools=False,
        observability_backend="file",
        observability_data_file=str(data_file),
    )

    provider = get_provider(settings)

    assert isinstance(provider, FileObservabilityProvider)


def test_factory_returns_live_provider_for_prometheus_loki_tempo_backend() -> None:
    settings = Settings(
        use_fake_tools=False,
        observability_backend="prometheus_loki_tempo",
        prometheus_url="http://prometheus:9090",
        loki_url="http://loki:3100",
        tempo_url="http://tempo:3200",
    )

    provider = get_provider(settings)

    assert isinstance(provider, PrometheusLokiTempoProvider)


def test_factory_rejects_fake_backend_when_fake_tools_disabled() -> None:
    settings = Settings(use_fake_tools=False, observability_backend="fake")

    with pytest.raises(ObservabilityProviderError):
        get_provider(settings)


def test_factory_rejects_provider_access_when_fake_tools_enabled() -> None:
    settings = Settings(use_fake_tools=True, observability_backend="file")

    with pytest.raises(ObservabilityProviderError):
        get_provider(settings)
