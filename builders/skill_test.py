from builders.skill import SkillBuilder
from models import Skill


def test_add_skill() -> None:
    builder = SkillBuilder()

    skill = {
        "name": "Python",
        "description": "Python development",
        "content": "Python best practices",
    }

    builder.add(skill)

    assert builder._skills == [skill]


def test_build_returns_skills() -> None:
    builder = SkillBuilder()

    builder.add(
        {
            "name": "Python",
            "description": "Python development",
            "content": "Python best practices",
        }
    )
    builder.add(
        {
            "name": "Testing",
            "description": "Software testing",
            "content": "Pytest best practices",
        }
    )

    skills = builder.build()

    assert skills == [
        Skill(
            name="Python",
            description="Python development",
            content="Python best practices",
        ),
        Skill(
            name="Testing",
            description="Software testing",
            content="Pytest best practices",
        ),
    ]


def test_build_returns_empty_list() -> None:
    builder = SkillBuilder()

    assert builder.build() == []


def test_build_preserves_order() -> None:
    builder = SkillBuilder()

    builder.add(
        {
            "name": "First",
            "description": "First skill",
            "content": "First content",
        }
    )
    builder.add(
        {
            "name": "Second",
            "description": "Second skill",
            "content": "Second content",
        }
    )

    skills = builder.build()

    assert [skill.name for skill in skills] == ["First", "Second"]
