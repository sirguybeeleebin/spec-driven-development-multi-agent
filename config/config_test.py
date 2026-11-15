from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from config.config import Config, make_config
from models import Agents


@pytest.fixture
def root(tmp_path):
    return tmp_path


@pytest.fixture
def config_file(root):
    path = root / "AGENT.yaml"
    path.write_text(
        """
agents:
  researcher:
    max_iterations: 10
    tools:
      - read
  implementer:
    max_iterations: 15
    tools:
      - bash
""",
        encoding="utf-8",
    )
    return path


def test_make_config_loads_yaml(root, config_file):
    result = make_config(root)

    assert isinstance(result, Config)
    assert result.agent_configs == {
        Agents.RESEARCHER: {
            "max_iterations": 10,
            "tools": ["read"],
        },
        Agents.IMPLEMENTER: {
            "max_iterations": 15,
            "tools": ["bash"],
        },
    }


def test_make_config_resolves_root(root, config_file):
    result = make_config(root)

    assert result.root == root.resolve()


def test_make_config_raises_when_yaml_missing(root):
    with pytest.raises(FileNotFoundError, match="config not found"):
        make_config(root)


def test_make_config_loads_empty_yaml(root):
    (root / "AGENT.yaml").write_text("", encoding="utf-8")

    result = make_config(root)

    assert result.agent_configs == {}
    assert result.constitution == ""
    assert result.skills == []


def test_make_config_loads_null_yaml(root):
    (root / "AGENT.yaml").write_text("null", encoding="utf-8")

    result = make_config(root)

    assert result.agent_configs == {}


def test_make_config_raises_on_invalid_yaml(root):
    (root / "AGENT.yaml").write_text(
        "invalid: [yaml",
        encoding="utf-8",
    )

    with pytest.raises(yaml.YAMLError):
        make_config(root)


def test_make_config_loads_constitution(root, config_file):
    constitution = "# Project Constitution\n\nFollow these rules."

    (root / "AGENT.md").write_text(
        constitution,
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.constitution == constitution


def test_make_config_uses_empty_constitution_when_missing(root, config_file):
    result = make_config(root)

    assert result.constitution == ""


def test_make_config_reads_constitution_as_utf8(root, config_file):
    constitution = "# Конституция проекта"

    (root / "AGENT.md").write_text(
        constitution,
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.constitution == constitution


def test_make_config_loads_single_skill_as_string(root, config_file):
    skill_dir = root / "skills" / "python"
    skill_dir.mkdir(parents=True)

    skill_content = "# Python Skill\n\nUse Python best practices."

    (skill_dir / "SKILL.md").write_text(
        skill_content,
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.skills == [skill_content]


def test_make_config_loads_multiple_skills(root, config_file):
    skill_contents = {
        "python": "# Python Skill",
        "testing": "# Testing Skill",
        "git": "# Git Skill",
    }

    for name, content in skill_contents.items():
        skill_dir = root / "skills" / name
        skill_dir.mkdir(parents=True)

        (skill_dir / "SKILL.md").write_text(
            content,
            encoding="utf-8",
        )

    result = make_config(root)

    assert result.skills == [
        "# Git Skill",
        "# Python Skill",
        "# Testing Skill",
    ]


def test_make_config_loads_skills_in_sorted_order(root, config_file):
    for name in ["zebra", "alpha", "middle"]:
        skill_dir = root / "skills" / name
        skill_dir.mkdir(parents=True)

        (skill_dir / "SKILL.md").write_text(
            f"# {name}",
            encoding="utf-8",
        )

    result = make_config(root)

    assert result.skills == [
        "# alpha",
        "# middle",
        "# zebra",
    ]


def test_make_config_loads_skill_as_utf8(root, config_file):
    skill_dir = root / "skills" / "python"
    skill_dir.mkdir(parents=True)

    content = "# Программирование на Python"

    (skill_dir / "SKILL.md").write_text(
        content,
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.skills == [content]


def test_make_config_ignores_non_skill_files(root, config_file):
    skill_dir = root / "skills" / "python"
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(
        "# Python",
        encoding="utf-8",
    )

    (skill_dir / "README.md").write_text(
        "# Readme",
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.skills == ["# Python"]


def test_make_config_ignores_root_level_skill_file(root, config_file):
    skills_dir = root / "skills"
    skills_dir.mkdir()

    (skills_dir / "SKILL.md").write_text(
        "# Root Skill",
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.skills == []


def test_make_config_handles_missing_skills_directory(root, config_file):
    result = make_config(root)

    assert result.skills == []


def test_make_config_preserves_skill_content(root, config_file):
    skill_dir = root / "skills" / "python"
    skill_dir.mkdir(parents=True)

    content = (
        "---\n"
        "name: python\n"
        "description: Python development\n"
        "---\n\n"
        "# Instructions\n\n"
        "- Follow PEP 8\n"
        "- Write tests\n"
    )

    (skill_dir / "SKILL.md").write_text(
        content,
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.skills[0] == content


def test_make_config_propagates_skill_read_error(root, config_file):
    skill_dir = root / "skills" / "python"
    skill_dir.mkdir(parents=True)

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Python", encoding="utf-8")

    with patch.object(
        Path,
        "read_text",
        side_effect=PermissionError("Permission denied"),
    ):
        with pytest.raises(PermissionError, match="Permission denied"):
            make_config(root)


def test_config_is_frozen(root):
    config = Config(
        root=root,
        agent_configs={},
        constitution="",
        skills=[],
    )

    with pytest.raises(AttributeError):
        config.root = Path("/another/path")


def test_config_stores_all_fields(root):
    agent_configs = {
        Agents.RESEARCHER: {"max_iterations": 10},
    }
    skills = ["# Python Skill", "# Testing Skill"]

    result = Config(
        root=root,
        agent_configs=agent_configs,
        constitution="Test constitution",
        skills=skills,
    )

    assert result.root == root
    assert result.agent_configs == agent_configs
    assert result.constitution == "Test constitution"
    assert result.skills == skills


def test_make_config_loads_all_agents(root):
    (root / "AGENT.yaml").write_text(
        """
agents:
  researcher: {}
  implementer: {}
  tester: {}
  fixer: {}
""",
        encoding="utf-8",
    )

    result = make_config(root)

    assert set(result.agent_configs) == set(Agents)


def test_make_config_raises_on_unknown_agent(root):
    (root / "AGENT.yaml").write_text(
        """
agents:
  unknown:
    max_iterations: 10
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        make_config(root)


def test_make_config_loads_empty_agents(root):
    (root / "AGENT.yaml").write_text(
        "agents: {}",
        encoding="utf-8",
    )

    result = make_config(root)

    assert result.agent_configs == {}
