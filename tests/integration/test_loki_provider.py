import os

import pytest

from app.observability.loki_provider import LokiProvider


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_OBSERVABILITY_TESTS") != "true",
    reason="Set RUN_REAL_OBSERVABILITY_TESTS=true to run live observability tests.",
)


def test_loki_provider_queries_live_backend() -> None:
    provider = LokiProvider(os.getenv("LOKI_URL", "http://localhost:3100"))

    result = provider.query_logs("order-service", None, None)

    assert result["source"] == "loki"
    assert "logs" in result
