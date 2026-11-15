import pytest

from parsers.task_id import TaskIdParser


@pytest.fixture
def parser():
    return TaskIdParser()


@pytest.mark.parametrize(
    "task_id",
    [
        "001",
        "004_checkout_service",
        "create-task",
        "task_123",
        "Task123",
        "123_task-name",
    ],
)
def test_parse_task_id_returns_task_id(parser, task_id):
    task = f"# Task\n- task_id: {task_id}"

    assert parser.parse(task) == task_id


def test_parse_task_id_strips_outer_whitespace(parser):
    task = """
# Task
- task_id: 004_checkout_service

    """

    assert parser.parse(task) == "004_checkout_service"


def test_parse_task_id_accepts_whitespace_around_value(parser):
    task = "# Task\n- task_id:   004_checkout_service   "

    assert parser.parse(task) == "004_checkout_service"


def test_parse_task_id_accepts_whitespace_after_heading(parser):
    task = "# Task   \n- task_id: 004_checkout_service"

    assert parser.parse(task) == "004_checkout_service"


@pytest.mark.parametrize(
    "task",
    [
        "",
        "Some task",
        "# Task",
        "# Task\n",
        "# Task\n- task_id:",
        "# Task\n- task_id:   ",
        "Task\n- task_id: 001",
        "## Task\n- task_id: 001",
        "# task\n- task_id: 001",
        "# Task\n task_id: 001",
        "# Task\ntask_id: 001",
        "# Task\n- task-id: 001",
        "# Task\n- task_id: 001\n- task_id: 002",
        "# Task\n- task_id: 001\nAdditional content",
    ],
)
def test_parse_task_id_raises_for_invalid_task(parser, task):
    with pytest.raises(ValueError, match="missing or invalid task_id"):
        parser.parse(task)


@pytest.mark.parametrize(
    "task_id",
    [
        "task.id",
        "task/id",
        "task id",
        "task@id",
        "task:id",
        "task.id-123",
        "task_id!",
    ],
)
def test_parse_task_id_raises_for_invalid_task_id_characters(parser, task_id):
    task = f"# Task\n- task_id: {task_id}"

    with pytest.raises(ValueError, match="missing or invalid task_id"):
        parser.parse(task)


def test_parse_task_id_requires_exactly_one_task_id_field(parser):
    task = """\
# Task
- task_id: 001
- task_id: 002
"""

    with pytest.raises(ValueError, match="missing or invalid task_id"):
        parser.parse(task)
