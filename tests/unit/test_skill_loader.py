from pathlib import Path

from app.skills.loader import load_skills


REQUIRED_SECTIONS = [
    "## Purpose",
    "## When To Use",
    "## Required Evidence",
    "## Reasoning Steps",
    "## Guardrails",
]


def test_skill_loader_loads_all_skills() -> None:
    skills = load_skills("skills")

    assert len(skills) >= 8
    assert {skill.id for skill in skills} >= {
        "redis_timeout_diagnosis",
        "downstream_timeout_diagnosis",
        "mysql_slow_query_diagnosis",
        "application_exception_diagnosis",
        "service_unhealthy_diagnosis",
        "latency_spike_diagnosis",
        "evidence_sufficiency_review",
        "rca_report_generation",
    }


def test_skill_markdown_contains_required_sections() -> None:
    for path in Path("skills").glob("*/SKILL.md"):
        content = path.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in content, f"{path} missing {section}"
