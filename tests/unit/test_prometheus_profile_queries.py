from app.observability.profile import load_observability_profile
from app.observability.prometheus_provider import prometheus_queries


def test_prometheus_queries_use_demo_profile_names() -> None:
    profile = load_observability_profile("demo_order_service")

    queries = dict(prometheus_queries("order-service", profile))

    assert "order_service_requests_total" in queries["request_rate"]
    assert "order_service_request_duration_seconds_bucket" in queries["p95_latency_ms"]
    assert 'service="order-service"' in queries["request_rate"]
    assert 'status_code=~"5.."' in queries["error_rate_percent"]
    assert "[5m]" in queries["request_rate"]


def test_prometheus_queries_use_spring_boot_profile_names() -> None:
    profile = load_observability_profile("spring_boot_micrometer")

    queries = dict(prometheus_queries("payment-service", profile))

    assert "http_server_requests_seconds_count" in queries["request_rate"]
    assert "http_server_requests_seconds_bucket" in queries["p95_latency_ms"]
    assert 'application="payment-service"' in queries["request_rate"]
    assert 'status=~"5.."' in queries["error_rate_percent"]
