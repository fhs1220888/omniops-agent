import os

import pytest

from app.observability.tempo_provider import TempoProvider


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_OBSERVABILITY_TESTS") != "true",
    reason="Set RUN_REAL_OBSERVABILITY_TESTS=true to run live observability tests.",
)


def test_tempo_provider_returns_empty_without_trace_ids() -> None:
    provider = TempoProvider(os.getenv("TEMPO_URL", "http://localhost:3200"))

    result = provider.query_traces("order-service", None, None, [])

    assert result["source"] == "tempo"
    assert result["empty"] is True
    assert result["trace_ids"] == []
