from unittest.mock import MagicMock, call, patch

import pytest

from factories import workflow as workflow_factory
from models import Task


@pytest.fixture
def config(tmp_path):
    config = MagicMock()
    config.root = tmp_path
    config.constitution = "Test constitution"
    return config


@pytest.fixture
def workflow_file(config):
    workflows_dir = config.root / "workflows"
    workflows_dir.mkdir()

    path = workflows_dir / "example.md"
    path.write_text("# Example workflow", encoding="utf-8")

    return path


@pytest.fixture
def tasks_dir(config):
    path = config.root / "tasks"
    path.mkdir()
    return path


@pytest.fixture
def graph():
    graph = MagicMock()
    graph.nodes = []
    return graph


def test_make_workflow_parses_graph(config, workflow_file, graph):
    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ) as parse_graph,
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        result = workflow_factory.make_workflow(config, "example")

    parse_graph.assert_called_once_with("# Example workflow")

    workflow.assert_called_once_with(
        graph=graph,
        tasks=[],
    )

    assert result is workflow.return_value


def test_make_workflow_reads_file_as_utf8(config, workflow_file, graph):
    workflow_file.write_text(
        "# Рабочий процесс",
        encoding="utf-8",
    )

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ) as parse_graph,
        patch.object(workflow_factory, "Workflow"),
    ):
        workflow_factory.make_workflow(config, "example")

    parse_graph.assert_called_once_with("# Рабочий процесс")


def test_make_workflow_raises_when_workflow_file_missing(config):
    expected_path = config.root / "workflows" / "missing.md"

    with (
        patch.object(workflow_factory, "parse_graph") as parse_graph,
        patch.object(workflow_factory, "Workflow") as workflow,
    ):
        with pytest.raises(
            FileNotFoundError,
            match="Workflow file not found",
        ) as exc_info:
            workflow_factory.make_workflow(config, "missing")

    assert str(expected_path) in str(exc_info.value)

    parse_graph.assert_not_called()
    workflow.assert_not_called()


def test_make_workflow_propagates_graph_parser_exception(
    config,
    workflow_file,
):
    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            side_effect=ValueError("Invalid graph"),
        ),
        patch.object(workflow_factory, "Workflow") as workflow,
    ):
        with pytest.raises(
            ValueError,
            match="Invalid graph",
        ):
            workflow_factory.make_workflow(config, "example")

    workflow.assert_not_called()


def test_make_workflow_loads_single_task(config, workflow_file, tasks_dir):
    (tasks_dir / "task1.md").write_text(
        "# Task 1",
        encoding="utf-8",
    )

    node = MagicMock()
    node.task_id = "task1"

    graph = MagicMock()
    graph.nodes = [node]

    parsed_task = MagicMock(spec=Task)

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
            return_value=parsed_task,
        ) as parse_task,
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        result = workflow_factory.make_workflow(config, "example")

    parse_task.assert_called_once_with(
        "# Task 1",
        constitution=config.constitution,
    )

    workflow.assert_called_once_with(
        graph=graph,
        tasks=[parsed_task],
    )

    assert result is workflow.return_value


def test_make_workflow_loads_multiple_tasks(config, workflow_file, tasks_dir):
    task_ids = ["task1", "task2", "task3"]

    nodes = []

    for task_id in task_ids:
        (tasks_dir / f"{task_id}.md").write_text(
            f"# {task_id}",
            encoding="utf-8",
        )

        node = MagicMock()
        node.task_id = task_id
        nodes.append(node)

    graph = MagicMock()
    graph.nodes = nodes

    parsed_tasks = [
        MagicMock(spec=Task, name=f"parsed_{task_id}") for task_id in task_ids
    ]

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
            side_effect=parsed_tasks,
        ) as parse_task,
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        result = workflow_factory.make_workflow(config, "example")

    assert parse_task.call_args_list == [
        call("# task1", constitution=config.constitution),
        call("# task2", constitution=config.constitution),
        call("# task3", constitution=config.constitution),
    ]

    workflow.assert_called_once_with(
        graph=graph,
        tasks=parsed_tasks,
    )

    assert result is workflow.return_value


def test_make_workflow_raises_when_task_file_missing(
    config,
    workflow_file,
    tasks_dir,
):
    node = MagicMock()
    node.task_id = "missing_task"

    graph = MagicMock()
    graph.nodes = [node]

    expected_path = tasks_dir / "missing_task.md"

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
        ) as parse_task,
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        with pytest.raises(
            FileNotFoundError,
            match="Task file not found for node missing_task",
        ) as exc_info:
            workflow_factory.make_workflow(config, "example")

    assert str(expected_path) in str(exc_info.value)

    parse_task.assert_not_called()
    workflow.assert_not_called()


def test_make_workflow_raises_if_later_task_is_missing(
    config,
    workflow_file,
    tasks_dir,
):
    (tasks_dir / "task1.md").write_text(
        "# Task 1",
        encoding="utf-8",
    )

    node1 = MagicMock()
    node1.task_id = "task1"

    node2 = MagicMock()
    node2.task_id = "task2"

    graph = MagicMock()
    graph.nodes = [node1, node2]

    parsed_task = MagicMock(spec=Task)

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
            return_value=parsed_task,
        ) as parse_task,
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        with pytest.raises(
            FileNotFoundError,
            match="Task file not found for node task2",
        ):
            workflow_factory.make_workflow(config, "example")

    parse_task.assert_called_once_with(
        "# Task 1",
        constitution=config.constitution,
    )

    workflow.assert_not_called()


def test_make_workflow_passes_constitution_to_every_task(
    config,
    workflow_file,
    tasks_dir,
):
    task_ids = ["task1", "task2"]
    nodes = []

    for task_id in task_ids:
        (tasks_dir / f"{task_id}.md").write_text(
            f"Content of {task_id}",
            encoding="utf-8",
        )

        node = MagicMock()
        node.task_id = task_id
        nodes.append(node)

    graph = MagicMock()
    graph.nodes = nodes

    config.constitution = "Custom constitution"

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
            return_value=MagicMock(spec=Task),
        ) as parse_task,
        patch.object(workflow_factory, "Workflow"),
    ):
        workflow_factory.make_workflow(config, "example")

    assert parse_task.call_args_list == [
        call("Content of task1", constitution="Custom constitution"),
        call("Content of task2", constitution="Custom constitution"),
    ]


def test_make_workflow_propagates_task_parser_exception(
    config,
    workflow_file,
    tasks_dir,
):
    (tasks_dir / "task1.md").write_text(
        "# Invalid task",
        encoding="utf-8",
    )

    node = MagicMock()
    node.task_id = "task1"

    graph = MagicMock()
    graph.nodes = [node]

    with (
        patch.object(
            workflow_factory,
            "parse_graph",
            return_value=graph,
        ),
        patch.object(
            workflow_factory,
            "parse_task",
            side_effect=ValueError("Invalid task format"),
        ),
        patch.object(
            workflow_factory,
            "Workflow",
        ) as workflow,
    ):
        with pytest.raises(
            ValueError,
            match="Invalid task format",
        ):
            workflow_factory.make_workflow(config, "example")

    workflow.assert_not_called()


def test_make_workflow_runner_creates_task_runner(config):
    expected_task_runner = MagicMock(name="task_runner")

    with (
        patch.object(
            workflow_factory,
            "make_task_runner",
            return_value=expected_task_runner,
        ) as make_task_runner,
        patch.object(workflow_factory, "WorkflowFSM") as workflow_fsm,
        patch.object(
            workflow_factory,
            "WorkflowRunner",
        ) as workflow_runner,
    ):
        result = workflow_factory.make_workflow_runner(config)

    make_task_runner.assert_called_once_with(config=config)
    workflow_fsm.assert_called_once_with()

    workflow_runner.assert_called_once_with(
        workflow_fsm=workflow_fsm.return_value,
        task_runner=expected_task_runner,
    )

    assert result is workflow_runner.return_value


def test_make_workflow_runner_propagates_task_runner_exception(config):
    with (
        patch.object(
            workflow_factory,
            "make_task_runner",
            side_effect=RuntimeError("Task runner failed"),
        ) as make_task_runner,
        patch.object(workflow_factory, "WorkflowFSM") as workflow_fsm,
        patch.object(
            workflow_factory,
            "WorkflowRunner",
        ) as workflow_runner,
    ):
        with pytest.raises(
            RuntimeError,
            match="Task runner failed",
        ):
            workflow_factory.make_workflow_runner(config)

    make_task_runner.assert_called_once_with(config=config)
    workflow_fsm.assert_not_called()
    workflow_runner.assert_not_called()


def test_make_workflow_runner_returns_workflow_runner(config):
    expected_runner = MagicMock(name="workflow_runner")

    with (
        patch.object(workflow_factory, "make_task_runner"),
        patch.object(workflow_factory, "WorkflowFSM"),
        patch.object(
            workflow_factory,
            "WorkflowRunner",
            return_value=expected_runner,
        ),
    ):
        result = workflow_factory.make_workflow_runner(config)

    assert result is expected_runner
