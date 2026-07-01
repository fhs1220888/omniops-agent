from app.skills.selector import SkillSelector


def _ids(selected) -> list[str]:
    return [item.id for item in selected]


def test_redis_incident_selects_redis_skill() -> None:
    selected = SkillSelector().select(
        {
            "title": "Redis timeout during checkout",
            "service": "order-service",
            "symptom": "Checkout returns 504",
        },
        "Logs contain redis_timeout and metrics show 504 spike.",
    )

    ids = _ids(selected)
    assert "redis_timeout_diagnosis" in ids
    assert "evidence_sufficiency_review" in ids
    assert "rca_report_generation" in ids


def test_mysql_incident_selects_mysql_skill() -> None:
    selected = SkillSelector().select(
        {
            "title": "Database slow query",
            "service": "order-service",
            "symptom": "mysql checkout_order_lookup missing index",
        }
    )

    assert "mysql_slow_query_diagnosis" in _ids(selected)


def test_application_exception_selects_exception_skill() -> None:
    selected = SkillSelector().select(
        {
            "title": "Application exception spike",
            "service": "order-service",
            "symptom": "Checkout returns HTTP 500 errors",
        }
    )

    assert "application_exception_diagnosis" in _ids(selected)
