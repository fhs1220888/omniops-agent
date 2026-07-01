from app.skills.registry import SkillRegistry


def test_skill_registry_status() -> None:
    registry = SkillRegistry("skills")

    status = registry.status()

    assert status["skill_count"] >= 8
    assert status["skills_dir"] == "skills"
    assert any(item["id"] == "redis_timeout_diagnosis" for item in status["skills"])


def test_skill_registry_get() -> None:
    skill = SkillRegistry("skills").get("redis_timeout_diagnosis")

    assert skill is not None
    assert skill.name == "Redis Timeout Diagnosis Skill"
    assert skill.path == "skills/redis_timeout_diagnosis/SKILL.md"
