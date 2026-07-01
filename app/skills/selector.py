"""Deterministic Skill selector."""

from __future__ import annotations

import re

from app.core.config import Settings
from app.skills.registry import SkillRegistry
from app.skills.schemas import SelectedSkill


DEFAULT_SKILLS = ["evidence_sufficiency_review", "rca_report_generation"]
KEYWORDS: dict[str, list[str]] = {
    "redis_timeout_diagnosis": ["redis", "timeout", "pool", "504", "cart"],
    "downstream_timeout_diagnosis": [
        "downstream",
        "payment",
        "payment-service",
        "dependency",
        "504",
    ],
    "mysql_slow_query_diagnosis": ["mysql", "db", "database", "slow query", "index"],
    "application_exception_diagnosis": ["exception", "500", "stack trace", "error"],
    "service_unhealthy_diagnosis": ["unhealthy", "503", "health", "readiness"],
    "latency_spike_diagnosis": ["latency", "p95", "p99", "slow"],
}


class SkillSelector:
    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self.settings = Settings.from_env()
        self.registry = registry or SkillRegistry(self.settings.skills_dir)

    def select(
        self,
        incident: dict,
        evidence_summary: str | None = None,
        top_k: int = 3,
    ) -> list[SelectedSkill]:
        if not self.settings.skills_enabled:
            return []
        text = _normalize(
            " ".join(
                [
                    str(incident.get("title", "")),
                    str(incident.get("service", "")),
                    str(incident.get("symptom", "")),
                    str(incident.get("description", "")),
                    evidence_summary or "",
                ]
            )
        )
        selected: list[SelectedSkill] = []
        for skill_id in DEFAULT_SKILLS:
            skill = self.registry.get(skill_id)
            if skill is not None:
                selected.append(
                    SelectedSkill(
                        id=skill.id,
                        name=skill.name,
                        path=skill.path,
                        reason="Default skill for evidence review and RCA reporting.",
                        content=skill.content,
                        score=1.0,
                    )
                )
        scored = []
        for skill_id, keywords in KEYWORDS.items():
            matches = [keyword for keyword in keywords if keyword in text]
            if not matches:
                continue
            skill = self.registry.get(skill_id)
            if skill is None:
                continue
            scored.append((len(matches), matches, skill))
        scored.sort(key=lambda item: item[0], reverse=True)
        for score, matches, skill in scored[:top_k]:
            selected.append(
                SelectedSkill(
                    id=skill.id,
                    name=skill.name,
                    path=skill.path,
                    reason=f"Matched keywords: {', '.join(matches)}",
                    content=skill.content,
                    score=float(score),
                )
            )
        return _dedupe(selected)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _dedupe(skills: list[SelectedSkill]) -> list[SelectedSkill]:
    seen = set()
    result = []
    for skill in skills:
        if skill.id in seen:
            continue
        seen.add(skill.id)
        result.append(skill)
    return result
