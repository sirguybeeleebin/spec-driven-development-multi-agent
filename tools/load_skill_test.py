import pytest

from models import Skill
from tools.load_skill import LoadSkillTool


@pytest.fixture
def skills() -> list[Skill]:
    return [
        Skill(
            name="python",
            description="Python programming skill.",
            content="# Python\nPython skill content.",
        ),
        Skill(
            name="testing",
            description="Testing skill.",
            content="# Testing\nTesting skill content.",
        ),
    ]


@pytest.fixture
def tool(skills: list[Skill]) -> LoadSkillTool:
    return LoadSkillTool(skills=skills)


def test_init_builds_skill_index(skills: list[Skill]) -> None:
    tool = LoadSkillTool(skills=skills)

    assert tool._by_name == {
        "python": skills[0],
        "testing": skills[1],
    }


def test_init_with_empty_skills() -> None:
    tool = LoadSkillTool(skills=[])

    assert tool._by_name == {}


def test_get_openai_schema(tool: LoadSkillTool) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "Load the full content of a skill by name. The "
                "catalog of skill names is in the system prompt "
                "under `# Skills`."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name.",
                    },
                },
                "required": ["name"],
            },
        },
    }


def test_execute_loads_skill(tool: LoadSkillTool) -> None:
    result = tool.execute({"name": "python"})

    assert result == {
        "ok": True,
        "name": "python",
        "content": "# Python\nPython skill content.",
    }


def test_execute_loads_another_skill(tool: LoadSkillTool) -> None:
    result = tool.execute({"name": "testing"})

    assert result == {
        "ok": True,
        "name": "testing",
        "content": "# Testing\nTesting skill content.",
    }


def test_execute_preserves_multiline_content() -> None:
    content = "# Python\n\n## Functions\n\n- map\n- filter\n"
    tool = LoadSkillTool(
        skills=[
            Skill(
                name="python",
                description="Python programming skill.",
                content=content,
            )
        ],
    )

    result = tool.execute({"name": "python"})

    assert result["content"] == content


def test_execute_loads_empty_content() -> None:
    tool = LoadSkillTool(
        skills=[
            Skill(
                name="empty",
                description="Empty skill.",
                content="",
            )
        ],
    )

    result = tool.execute({"name": "empty"})

    assert result == {
        "ok": True,
        "name": "empty",
        "content": "",
    }


def test_execute_raises_key_error_for_unknown_skill(
    tool: LoadSkillTool,
) -> None:
    with pytest.raises(KeyError, match="unknown"):
        tool.execute({"name": "unknown"})


def test_init_uses_last_skill_with_duplicate_name() -> None:
    skills = [
        Skill(
            name="python",
            description="First description.",
            content="First content",
        ),
        Skill(
            name="python",
            description="Second description.",
            content="Second content",
        ),
    ]
    tool = LoadSkillTool(skills=skills)

    result = tool.execute({"name": "python"})

    assert result["content"] == "Second content"
