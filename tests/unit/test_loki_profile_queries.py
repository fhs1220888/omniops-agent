from app.observability.loki_provider import extract_trace_id, loki_selector
from app.observability.profile import load_observability_profile


def test_loki_selector_uses_profile_service_label() -> None:
    profile = load_observability_profile("spring_boot_micrometer")

    assert loki_selector("payment-service", profile) == '{app="payment-service"}'


def test_trace_id_fields_come_from_profile_json() -> None:
    profile = load_observability_profile("spring_boot_micrometer")
    message = '{"traceid": "abc123", "message": "failed"}'

    assert extract_trace_id(message, profile.loki.trace_id_fields) == "abc123"


def test_trace_id_fields_come_from_profile_text() -> None:
    profile = load_observability_profile("generic")
    message = "level=error traceID=def456 message=failed"

    assert extract_trace_id(message, profile.loki.trace_id_fields) == "def456"
