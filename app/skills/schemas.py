"""Skill schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillDocument(BaseModel):
    id: str
    name: str
    path: str
    content: str
    purpose: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SelectedSkill(BaseModel):
    id: str
    name: str
    path: str
    reason: str
    content: str
    score: float = 0.0
