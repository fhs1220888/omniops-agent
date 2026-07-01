"""Skill registry."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.skills.loader import load_skills
from app.skills.schemas import SkillDocument


class SkillRegistry:
    def __init__(self, skills_dir: Path | str | None = None) -> None:
        self.settings = Settings.from_env()
        self.skills_dir = str(skills_dir or self.settings.skills_dir)
        self._skills: list[SkillDocument] | None = None

    def load(self) -> list[SkillDocument]:
        if self._skills is None:
            self._skills = load_skills(self.skills_dir)
        return self._skills

    def get(self, skill_id: str) -> SkillDocument | None:
        for skill in self.load():
            if skill.id == skill_id:
                return skill
        return None

    def status(self) -> dict:
        skills = self.load()
        return {
            "skills_enabled": self.settings.skills_enabled,
            "skill_count": len(skills),
            "skills_dir": self.skills_dir,
            "skills": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "path": skill.path,
                }
                for skill in skills
            ],
        }
