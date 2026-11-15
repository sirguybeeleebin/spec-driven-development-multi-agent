from __future__ import annotations

import pytest

from models import Skill, Tools
from tools.load_skill import LoadSkillTool


@pytest.fixture
def skills() -> list[Skill]:
    return [
        Skill(
            name="python",
            description="Python skill",
            content="Python skill content",
        ),
        Skill(
            name="testing",
            description="Testing skill",
            content="Testing skill content",
        ),
    ]


@pytest.fixture
def tool(skills: list[Skill]) -> LoadSkillTool:
    return LoadSkillTool(skills=skills)


def test_name_returns_load_skill(tool: LoadSkillTool) -> None:
    assert tool.name == Tools.LOAD_SKILL


def test_get_openai_schema_returns_strict_schema(
    tool: LoadSkillTool,
) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": Tools.LOAD_SKILL,
            "description": (
                "Load the full content of a skill by its name. "
                "Use this tool when you need detailed instructions, "
                "conventions, or reference materials provided by a skill. "
                "Available skill names are listed in the system prompt "
                "under `# Skills`."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Exact name of the skill to load, as listed in the `# Skills` section of the system prompt."
                        ),
                    },
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    }


def test_execute_returns_skill_content(
    tool: LoadSkillTool,
) -> None:
    result = tool.execute({"name": "python"})

    assert result == {
        "ok": True,
        "name": "python",
        "content": "Python skill content",
    }


def test_execute_returns_requested_skill(
    tool: LoadSkillTool,
) -> None:
    result = tool.execute({"name": "testing"})

    assert result == {
        "ok": True,
        "name": "testing",
        "content": "Testing skill content",
    }


def test_execute_raises_for_unknown_skill(
    tool: LoadSkillTool,
) -> None:
    with pytest.raises(ValueError, match="skill not found: unknown"):
        tool.execute({"name": "unknown"})


def test_execute_raises_for_invalid_name_type(
    tool: LoadSkillTool,
) -> None:
    with pytest.raises(TypeError, match="'name' must be a string"):
        tool.execute({"name": 123})


def test_execute_raises_for_missing_name(
    tool: LoadSkillTool,
) -> None:
    with pytest.raises(KeyError, match="name"):
        tool.execute({})


def test_duplicate_skill_names_use_last_skill() -> None:
    tool = LoadSkillTool(
        skills=[
            Skill(name="python", content="First content", description=""),
            Skill(name="python", content="Second content", description=""),
        ],
    )

    result = tool.execute({"name": "python"})

    assert result == {
        "ok": True,
        "name": "python",
        "content": "Second content",
    }


def test_empty_skills() -> None:
    tool = LoadSkillTool(skills=[])

    with pytest.raises(ValueError, match="skill not found: python"):
        tool.execute({"name": "python"})
