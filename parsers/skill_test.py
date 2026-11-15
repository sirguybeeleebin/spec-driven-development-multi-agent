from __future__ import annotations

import pytest

from models import Skill
from parsers.skill import parse_skill

SKILL_TEXT = """\
---
name: code-review
description: Reviews code changes.
---

Review the code for bugs and style issues.
"""


def test_parse_skill_with_multiline_description() -> None:
    text = """\
---
name: code-review
description: Reviews code changes
  and checks coding style.
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.description == "Reviews code changes and checks coding style."


def test_parse_skill_with_multiline_name() -> None:
    text = """\
---
name: code-
  review
description: Reviews code.
---

Skill body.
"""

    with pytest.raises(ValueError, match="name must match"):
        parse_skill(text)


def test_parse_skill() -> None:
    skill = parse_skill(SKILL_TEXT)

    assert skill == Skill(
        name="code-review",
        description="Reviews code changes.",
        content="Review the code for bugs and style issues.",
    )


def test_parse_skill_with_additional_metadata() -> None:
    text = """\
---
name: code-review
description: Reviews code.
version: 1
author: Example
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.content == "Skill body."


def test_parse_skill_preserves_body_internal_whitespace() -> None:
    text = """\
---
name: code-review
description: Reviews code.
---

  Skill body.

Second line.
"""

    skill = parse_skill(text)

    assert skill.content == "Skill body.\n\nSecond line."


def test_frontmatter_with_crlf() -> None:
    text = SKILL_TEXT.replace("\n", "\r\n")

    skill = parse_skill(text)

    assert skill.content == "Review the code for bugs and style issues."


def test_parse_skill_with_colon_in_description() -> None:
    text = """\
---
name: code-review
description: Reviews code: quality and correctness.
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.description == "Reviews code: quality and correctness."


def test_parse_skill_ignores_empty_frontmatter_lines() -> None:
    text = """\
---

name: code-review

description: Reviews code.

---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.name == "code-review"
    assert skill.description == "Reviews code."


def test_parse_skill_uses_last_duplicate_metadata_key() -> None:
    text = """\
---
name: first
name: code-review
description: Reviews code.
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.name == "code-review"


def test_parse_skill_preserves_body_surrounding_whitespace() -> None:
    text = """\
---
name: code-review
description: Reviews code.
---

  Skill body.

"""

    skill = parse_skill(text)

    assert skill.content == "Skill body."


def test_parse_skill_preserves_description_internal_whitespace() -> None:
    text = """\
---
name: code-review
description: Reviews   code.
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.description == "Reviews   code."


def test_parse_skill_strips_description_outer_whitespace() -> None:
    text = """\
---
name: code-review
description:    Reviews code.
---

Skill body.
"""

    skill = parse_skill(text)

    assert skill.description == "Reviews code."


def test_missing_frontmatter() -> None:
    with pytest.raises(
        ValueError,
        match="skill: missing frontmatter block",
    ):
        parse_skill("Skill body.")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "name: code-review\ndescription: Reviews code.",
        "---\nname: code-review\ndescription: Reviews code.",
        "---\nname: code-review\ndescription: Reviews code.\n",
        "text\n---\nname: code-review\ndescription: Reviews code.\n---\n",
    ],
)
def test_invalid_frontmatter(text: str) -> None:
    with pytest.raises(
        ValueError,
        match="skill: missing frontmatter block",
    ):
        parse_skill(text)


def test_missing_name() -> None:
    text = """\
---
description: Reviews code.
---

Skill body.
"""

    with pytest.raises(
        ValueError,
        match="skill: frontmatter missing 'name'",
    ):
        parse_skill(text)


def test_missing_description() -> None:
    text = """\
---
name: code-review
---

Skill body.
"""

    with pytest.raises(
        ValueError,
        match="skill: frontmatter missing 'description'",
    ):
        parse_skill(text)


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        "   ",
        "\t",
    ],
)
def test_empty_name(name: str) -> None:
    text = SKILL_TEXT.replace(
        "name: code-review",
        f"name: {name}",
    )

    with pytest.raises(
        ValueError,
        match="skill: empty name",
    ):
        parse_skill(text)


@pytest.mark.parametrize(
    "name",
    [
        "Code-Review",
        "code_review",
        "code.review",
        "code review",
        "code/review",
        "code@review",
        "123 Code",
        "код-ревью",
        "code--review!",
        "code\nreview",
        "code\t-review",
        "code\u0000-review",
    ],
)
def test_invalid_name(name: str) -> None:
    text = SKILL_TEXT.replace(
        "name: code-review",
        f"name: {name}",
    )

    with pytest.raises(
        ValueError,
        match=r"skill: name must match \[a-z0-9-\]\+",
    ):
        parse_skill(text)


@pytest.mark.parametrize(
    "name",
    [
        "a",
        "code",
        "code-review",
        "code-review-123",
        "123",
        "0-1-2",
    ],
)
def test_valid_name(name: str) -> None:
    text = SKILL_TEXT.replace(
        "name: code-review",
        f"name: {name}",
    )

    skill = parse_skill(text)

    assert skill.name == name


def test_name_is_not_normalized() -> None:
    text = SKILL_TEXT.replace(
        "name: code-review",
        "name: code review",
    )

    with pytest.raises(ValueError, match="name must match"):
        parse_skill(text)


def test_empty_description() -> None:
    text = """\
---
name: code-review
description:
---

Skill body.
"""

    with pytest.raises(
        ValueError,
        match=r"skill 'code-review': empty description",
    ):
        parse_skill(text)


@pytest.mark.parametrize(
    "description",
    [
        "",
        " ",
        "   ",
        "\t",
    ],
)
def test_description_with_only_whitespace(description: str) -> None:
    text = f"""\
---
name: code-review
description: {description}
---

Skill body.
"""

    with pytest.raises(
        ValueError,
        match=r"skill 'code-review': empty description",
    ):
        parse_skill(text)


def test_empty_body() -> None:
    text = """\
---
name: code-review
description: Reviews code.
---
"""

    with pytest.raises(
        ValueError,
        match=r"skill 'code-review': empty body after frontmatter",
    ):
        parse_skill(text)


@pytest.mark.parametrize(
    "body",
    [
        "",
        " ",
        "   ",
        "\n",
        "\n \t\n",
    ],
)
def test_body_with_only_whitespace(body: str) -> None:
    text = f"""\
---
name: code-review
description: Reviews code.
---
{body}"""

    with pytest.raises(
        ValueError,
        match=r"skill 'code-review': empty body after frontmatter",
    ):
        parse_skill(text)


def test_frontmatter_must_be_at_start() -> None:
    text = f"\n{SKILL_TEXT}"

    with pytest.raises(
        ValueError,
        match="skill: missing frontmatter block",
    ):
        parse_skill(text)
