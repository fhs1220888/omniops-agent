import os

import pytest

from app.observability.prometheus_provider import PrometheusProvider


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_OBSERVABILITY_TESTS") != "true",
    reason="Set RUN_REAL_OBSERVABILITY_TESTS=true to run live observability tests.",
)


def test_prometheus_provider_queries_live_backend() -> None:
    provider = PrometheusProvider(os.getenv("PROMETHEUS_URL", "http://localhost:9090"))

    result = provider.query_metrics("order-service", None, None)

    assert result["source"] == "prometheus"
    assert "metrics" in result
    assert "queries" in result
