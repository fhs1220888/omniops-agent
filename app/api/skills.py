"""Skill registry APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.skills.registry import SkillRegistry
from app.skills.selector import SkillSelector

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillSelectRequest(BaseModel):
    incident: dict = Field(default_factory=dict)
    evidence_summary: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


@router.get("/status")
def skills_status() -> dict:
    return SkillRegistry().status()


@router.post("/select")
def select_skills(payload: SkillSelectRequest) -> dict:
    selected = SkillSelector().select(
        incident=payload.incident,
        evidence_summary=payload.evidence_summary,
        top_k=payload.top_k,
    )
    return {
        "selected_skills": [skill.model_dump() for skill in selected],
    }


@router.get("/{skill_id}")
def get_skill(skill_id: str) -> dict:
    skill = SkillRegistry().get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.model_dump()
