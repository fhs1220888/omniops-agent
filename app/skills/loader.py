"""Load markdown Skills from skills/**/SKILL.md."""

from __future__ import annotations

from pathlib import Path

from app.skills.schemas import SkillDocument


def load_skills(skills_dir: Path | str = "skills") -> list[SkillDocument]:
    root = Path(skills_dir)
    if not root.exists():
        return []
    skills: list[SkillDocument] = []
    for path in sorted(root.glob("*/SKILL.md")):
        content = path.read_text(encoding="utf-8")
        skill_id = path.parent.name
        skills.append(
            SkillDocument(
                id=skill_id,
                name=_heading(content) or skill_id.replace("_", " ").title(),
                path=path.as_posix(),
                content=content,
                purpose=_section(content, "Purpose"),
                metadata={
                    "path": path.as_posix(),
                    "directory": path.parent.name,
                    "filename": path.name,
                },
            )
        )
    return skills


def _heading(content: str) -> str | None:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _section(content: str, heading: str) -> str | None:
    marker = f"## {heading}"
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        collected: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line.startswith("## "):
                break
            collected.append(next_line)
        value = "\n".join(collected).strip()
        return value or None
    return None
