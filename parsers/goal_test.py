import pytest

from parsers.goal import GoalParser


@pytest.fixture
def parser():
    return GoalParser()


def test_parse_removes_heading(parser):
    assert parser.parse("# Goal\nCreate a task") == "Create a task"


def test_parse_strips_leading_and_trailing_whitespace(parser):
    assert parser.parse("# Goal\n  Create a task\n  ") == "Create a task"


def test_parse_removes_heading_only_once(parser):
    assert parser.parse("# Goal\n# Goal\nCreate a task") == ("# Goal\nCreate a task")


def test_parse_preserves_content(parser):
    goal = "# Goal\nCreate a task.\nValidate its fields.\nReturn the result."

    assert parser.parse(goal) == ("Create a task.\nValidate its fields.\nReturn the result.")


@pytest.mark.parametrize(
    "goal",
    [
        "",
        "# Goal",
        "# Goal\n",
    ],
)
def test_parse_raises_for_missing_content(parser, goal):
    with pytest.raises(
        ValueError,
        match="Missing '# Goal' heading or goal content",
    ):
        parser.parse(goal)


def test_parse_raises_for_whitespace_content(parser):
    with pytest.raises(ValueError, match="Goal cannot be empty"):
        parser.parse("# Goal\n   ")


@pytest.mark.parametrize(
    "goal",
    [
        "# goal\nCreate a task",
        "Description\n# Goal\nCreate a task",
        "Goal\nCreate a task",
        "## Goal\nCreate a task",
        " # Goal\nCreate a task",
    ],
)
def test_parse_raises_for_invalid_heading(parser, goal):
    with pytest.raises(
        ValueError,
        match="Missing '# Goal' heading or goal content",
    ):
        parser.parse(goal)


@pytest.mark.parametrize(
    "goal",
    [
        "# Goal\nCreate a task",
        "# Goal   \nCreate a task",
        "# Goal\t\nCreate a task",
    ],
)
def test_parse_removes_heading_with_whitespace(parser, goal):
    assert parser.parse(goal) == "Create a task"


def test_parse_preserves_internal_whitespace(parser):
    goal = "# Goal\nCreate a task.\n\nValidate its fields.\n  Return the result."

    assert parser.parse(goal) == ("Create a task.\n\nValidate its fields.\n  Return the result.")
