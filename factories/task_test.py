from unittest.mock import MagicMock, call, patch

import pytest

from factories import task as task_factory
from models import Agents, Task


@pytest.fixture
def config(tmp_path):
    config = MagicMock()
    config.root = tmp_path
    config.constitution = "Test constitution"
    return config


def test_make_task_reads_task_file(config, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    task_file = tasks_dir / "example.md"
    task_file.write_text("# Example task", encoding="utf-8")

    parsed_task = MagicMock(spec=Task)

    with patch.object(
        task_factory,
        "parse_task",
        return_value=parsed_task,
    ) as parse_task:
        result = task_factory.make_task(config, "example")

    parse_task.assert_called_once_with(
        "# Example task",
        constitution=config.constitution,
    )

    assert result is parsed_task


def test_make_task_uses_utf8_encoding(config, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    task_file = tasks_dir / "example.md"
    task_file.write_text("Пример задачи", encoding="utf-8")

    with patch.object(
        task_factory,
        "parse_task",
        return_value=MagicMock(spec=Task),
    ):
        result = task_factory.make_task(config, "example")

    assert result is not None


def test_make_task_raises_when_file_does_not_exist(config, tmp_path):
    task_id = "missing"
    expected_path = tmp_path / "tasks" / "missing.md"

    with patch.object(task_factory, "parse_task") as parse_task:
        with pytest.raises(
            FileNotFoundError,
            match="Task file not found",
        ) as exc_info:
            task_factory.make_task(config, task_id)

    assert str(expected_path) in str(exc_info.value)
    parse_task.assert_not_called()


def test_make_task_passes_constitution_to_parser(config, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    (tasks_dir / "example.md").write_text(
        "Task content",
        encoding="utf-8",
    )

    config.constitution = "Custom constitution"

    with patch.object(
        task_factory,
        "parse_task",
        return_value=MagicMock(spec=Task),
    ) as parse_task:
        task_factory.make_task(config, "example")

    parse_task.assert_called_once_with(
        "Task content",
        constitution="Custom constitution",
    )


def test_make_task_returns_parser_result(config, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    (tasks_dir / "example.md").write_text(
        "Task content",
        encoding="utf-8",
    )

    expected_task = MagicMock(spec=Task)

    with patch.object(
        task_factory,
        "parse_task",
        return_value=expected_task,
    ):
        result = task_factory.make_task(config, "example")

    assert result is expected_task


def test_make_task_propagates_parser_exception(config, tmp_path):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()

    (tasks_dir / "example.md").write_text(
        "Invalid task",
        encoding="utf-8",
    )

    with patch.object(
        task_factory,
        "parse_task",
        side_effect=ValueError("Invalid task format"),
    ):
        with pytest.raises(
            ValueError,
            match="Invalid task format",
        ):
            task_factory.make_task(config, "example")


def test_make_task_runner_creates_all_agent_runners(config):
    researcher = MagicMock(name="researcher")
    implementer = MagicMock(name="implementer")
    tester = MagicMock(name="tester")
    fixer = MagicMock(name="fixer")

    expected_runners = [
        researcher,
        implementer,
        tester,
        fixer,
    ]

    with (
        patch.object(
            task_factory,
            "make_agent_runner",
            side_effect=expected_runners,
        ) as make_agent_runner,
        patch.object(task_factory, "TaskFSM") as task_fsm,
        patch.object(task_factory, "TaskRunner") as task_runner,
    ):
        result = task_factory.make_task_runner(config)

    assert make_agent_runner.call_args_list == [
        call(config, Agents.RESEARCHER),
        call(config, Agents.IMPLEMENTER),
        call(config, Agents.TESTER),
        call(config, Agents.FIXER),
    ]

    task_fsm.assert_called_once_with()

    task_runner.assert_called_once_with(
        task_fsm=task_fsm.return_value,
        researcher=researcher,
        implementer=implementer,
        tester=tester,
        fixer=fixer,
    )

    assert result is task_runner.return_value


@pytest.mark.parametrize(
    ("agent", "expected_position"),
    [
        (Agents.RESEARCHER, 0),
        (Agents.IMPLEMENTER, 1),
        (Agents.TESTER, 2),
        (Agents.FIXER, 3),
    ],
)
def test_make_task_runner_creates_agents_in_correct_order(
    config,
    agent,
    expected_position,
):
    with (
        patch.object(
            task_factory,
            "make_agent_runner",
        ) as make_agent_runner,
        patch.object(task_factory, "TaskFSM"),
        patch.object(task_factory, "TaskRunner"),
    ):
        task_factory.make_task_runner(config)

    assert make_agent_runner.call_args_list[expected_position] == call(config, agent)


def test_make_task_runner_propagates_agent_creation_exception(config):
    with (
        patch.object(
            task_factory,
            "make_agent_runner",
            side_effect=RuntimeError("Agent creation failed"),
        ) as make_agent_runner,
        patch.object(task_factory, "TaskFSM") as task_fsm,
        patch.object(task_factory, "TaskRunner") as task_runner,
    ):
        with pytest.raises(
            RuntimeError,
            match="Agent creation failed",
        ):
            task_factory.make_task_runner(config)

    make_agent_runner.assert_called_once_with(
        config,
        Agents.RESEARCHER,
    )
    task_fsm.assert_called_once_with()
    task_runner.assert_not_called()


def test_make_task_runner_does_not_create_runner_if_agent_fails(config):
    with (
        patch.object(
            task_factory,
            "make_agent_runner",
            side_effect=[
                MagicMock(name="researcher"),
                MagicMock(name="implementer"),
                RuntimeError("Tester creation failed"),
            ],
        ) as make_agent_runner,
        patch.object(task_factory, "TaskFSM") as task_fsm,
        patch.object(task_factory, "TaskRunner") as task_runner,
    ):
        with pytest.raises(
            RuntimeError,
            match="Tester creation failed",
        ):
            task_factory.make_task_runner(config)

    assert make_agent_runner.call_count == 3
    task_fsm.assert_called_once_with()
    task_runner.assert_not_called()


def test_make_task_runner_returns_task_runner_instance(config):
    expected_runner = MagicMock()

    with (
        patch.object(task_factory, "make_agent_runner"),
        patch.object(task_factory, "TaskFSM"),
        patch.object(
            task_factory,
            "TaskRunner",
            return_value=expected_runner,
        ),
    ):
        result = task_factory.make_task_runner(config)

    assert result is expected_runner
