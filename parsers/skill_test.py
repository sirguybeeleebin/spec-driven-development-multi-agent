import pytest

from parsers.skill import SkillParser


@pytest.fixture
def parser():
    return SkillParser()


def test_parse_skill_parses_valid_skill(parser):
    skill = """\
---
name: sqlite-implementing
description: Implements a repository over sqlite3.Connection.
---

# SQLite Repository

You are a senior Python developer.
"""

    assert parser.parse(skill) == {
        "name": "sqlite-implementing",
        "description": "Implements a repository over sqlite3.Connection.",
        "content": "# SQLite Repository\n\nYou are a senior Python developer.",
    }


def test_parse_skill_parses_multiline_description(parser):
    skill = """\
---
name: create-task
description: Creates a task
 from the provided requirements.
---

Content
"""

    result = parser.parse(skill)

    assert result["description"] == ("Creates a task from the provided requirements.")


def test_parse_skill_strips_metadata_whitespace(parser):
    skill = """\
---
name:   create-task
description:   Creates a task.
---

Content
"""

    result = parser.parse(skill)

    assert result["name"] == "create-task"
    assert result["description"] == "Creates a task."


def test_parse_skill_strips_content_whitespace(parser):
    skill = """\
---
name: create-task
description: Creates a task.
---


 Content

"""

    assert parser.parse(skill)["content"] == "Content"


def test_parse_skill_preserves_multiline_content(parser):
    skill = """\
---
name: create-task
description: Creates a task.
---

# Title

First paragraph.

Second paragraph.
"""

    assert parser.parse(skill)["content"] == ("# Title\n\nFirst paragraph.\n\nSecond paragraph.")


def test_parse_skill_accepts_additional_metadata(parser):
    skill = """\
---
name: create-task
description: Creates a task.
version: 1.0
author: developer
---

Content
"""

    assert parser.parse(skill) == {
        "name": "create-task",
        "description": "Creates a task.",
        "content": "Content",
    }


@pytest.mark.parametrize(
    "frontmatter",
    [
        "",
        "description: Creates a task.",
        "name: create-task",
        "name: create-task\ndescription:",
        "name: create-task\ndescription:   ",
    ],
)
def test_parse_skill_raises_for_missing_or_empty_required_metadata(
    parser,
    frontmatter,
):
    skill = f"---\n{frontmatter}\n---\n\nContent"

    with pytest.raises(ValueError, match="missing or empty"):
        parser.parse(skill)


@pytest.mark.parametrize(
    "frontmatter",
    [
        "123: value",
        "_name: value",
        "-name: value",
        "name!: value",
        ": value",
    ],
)
def test_parse_skill_raises_for_invalid_frontmatter_key(
    parser,
    frontmatter,
):
    skill = f"""\
---
name: create-task
description: Creates a task.
{frontmatter}
---

Content
"""

    with pytest.raises(ValueError, match="invalid frontmatter key"):
        parser.parse(skill)


def test_parse_skill_raises_for_duplicate_frontmatter_key(parser):
    skill = """\
---
name: create-task
description: Creates a task.
version: 1
version: 2
---

Content
"""

    with pytest.raises(ValueError, match="duplicate frontmatter key"):
        parser.parse(skill)


def test_parse_skill_raises_for_duplicate_description_key(parser):
    skill = """\
---
name: create-task
description: Creates a task.
description: Another description.
---

Content
"""

    with pytest.raises(ValueError, match="duplicate frontmatter key"):
        parser.parse(skill)


def test_parse_skill_raises_for_invalid_frontmatter_line(parser):
    skill = """\
---
name: create-task
description: Creates a task.
invalid line
---

Content
"""

    with pytest.raises(ValueError, match="invalid frontmatter line"):
        parser.parse(skill)


def test_parse_skill_accepts_indented_continuation_line(parser):
    skill = """\
---
name: create-task
description: Creates a task
 with additional details.
---

Content
"""

    assert parser.parse(skill)["description"] == ("Creates a task with additional details.")


def test_parse_skill_rejects_tab_indented_continuation_line(parser):
    skill = "---\nname: create-task\ndescription: Creates a task\n\twith details\n---\n\nContent"

    with pytest.raises(ValueError, match="invalid frontmatter line"):
        parser.parse(skill)


@pytest.mark.parametrize(
    "name",
    [
        "Create-task",
        "create_task",
        "create task",
        "create--task",
        "-create-task",
        "create-task-",
        "create.task",
        "create-task-1!",
    ],
)
def test_parse_skill_raises_for_invalid_name_format(parser, name):
    skill = f"""\
---
name: {name}
description: Creates a task.
---

Content
"""

    with pytest.raises(ValueError, match="invalid name format"):
        parser.parse(skill)


@pytest.mark.parametrize(
    "name",
    [
        "task",
        "create-task",
        "create-task-1",
        "task123",
        "123-task",
    ],
)
def test_parse_skill_accepts_valid_name_format(parser, name):
    skill = f"""\
---
name: {name}
description: Creates a task.
---

Content
"""

    assert parser.parse(skill)["name"] == name


@pytest.mark.parametrize(
    "content",
    [
        "",
        "   ",
        "\n\n",
    ],
)
def test_parse_skill_raises_for_empty_content(parser, content):
    skill = f"""\
---
name: create-task
description: Creates a task.
---

{content}"""

    with pytest.raises(ValueError, match="content cannot be empty"):
        parser.parse(skill)


def test_parse_skill_ignores_empty_frontmatter_lines(parser):
    skill = """\
---
name: create-task

description: Creates a task.

---

Content
"""

    assert parser.parse(skill) == {
        "name": "create-task",
        "description": "Creates a task.",
        "content": "Content",
    }


@pytest.mark.parametrize(
    "skill",
    [
        "",
        "Content without frontmatter",
        "---\nname: create-task\n",
        "---\nname: create-task\n---",
    ],
)
def test_parse_skill_raises_for_missing_frontmatter_block(parser, skill):
    with pytest.raises(ValueError, match="missing frontmatter block"):
        parser.parse(skill)
