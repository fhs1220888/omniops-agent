from pathlib import Path

import pytest

from app.observability.profile import (
    ObservabilityProfileError,
    list_observability_profiles,
    load_observability_profile,
)


def test_load_demo_order_service_profile() -> None:
    profile = load_observability_profile("demo_order_service")

    assert profile.name == "demo_order_service"
    assert profile.prometheus.request_count_metric == "order_service_requests_total"
    assert profile.prometheus.status_label == "status_code"
    assert profile.loki.service_label == "service"


def test_load_generic_profile() -> None:
    profile = load_observability_profile("generic")

    assert profile.name == "generic"
    assert profile.prometheus.request_count_metric == "http_requests_total"
    assert profile.loki.trace_id_fields == ["trace_id", "traceId", "traceID"]


def test_load_profile_from_path() -> None:
    path = Path("config/observability_profiles/spring_boot_micrometer.yaml")

    profile = load_observability_profile(str(path))

    assert profile.name == "spring_boot_micrometer"
    assert profile.prometheus.service_label == "application"


def test_missing_profile_has_clear_error() -> None:
    with pytest.raises(ObservabilityProfileError, match="Observability profile not found"):
        load_observability_profile("does_not_exist")


def test_list_observability_profiles() -> None:
    profiles = list_observability_profiles()
    names = {item["name"] for item in profiles}

    assert {
        "demo_order_service",
        "generic",
        "spring_boot_micrometer",
        "fastapi_prometheus",
    } <= names
