from __future__ import annotations

from unittest.mock import Mock, call

import pytest

from models import TaskStatus, WorkflowStatus
from runners.workflow import WorkflowRunner


@pytest.fixture
def workflow_fsm() -> Mock:
    fsm = Mock()
    fsm.status = WorkflowStatus.RUNNING
    fsm.mark_success.side_effect = lambda: setattr(fsm, "status", WorkflowStatus.SUCCESS)
    fsm.mark_error.side_effect = lambda: setattr(fsm, "status", WorkflowStatus.ERROR)
    return fsm


@pytest.fixture
def task_runner() -> Mock:
    return Mock()


@pytest.fixture
def runner(workflow_fsm: Mock, task_runner: Mock) -> WorkflowRunner:
    return WorkflowRunner(
        workflow_fsm=workflow_fsm,
        task_runner=task_runner,
    )


@pytest.fixture
def tasks() -> list[Mock]:
    return [
        Mock(task_id="task-1"),
        Mock(task_id="task-2"),
        Mock(task_id="task-3"),
    ]


@pytest.fixture
def workflow(tasks: list[Mock]) -> Mock:
    workflow = Mock()
    workflow.tasks = tasks
    workflow.graph.edges = []
    return workflow


def make_result(status: TaskStatus) -> Mock:
    return Mock(status=status)


def make_edge(source: Mock, target: Mock) -> Mock:
    edge = Mock()
    edge.source = source
    edge.target = target
    return edge


def test_init(
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    runner = WorkflowRunner(
        workflow_fsm=workflow_fsm,
        task_runner=task_runner,
    )

    assert runner._workflow_fsm is workflow_fsm
    assert runner._task_runner is task_runner


def test_run_executes_all_independent_tasks(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    expected_results = [
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
    ]
    task_runner.run.side_effect = expected_results

    result = runner.run("Constitution", workflow)

    workflow_fsm.reset.assert_called_once_with()
    workflow_fsm.mark_running.assert_called_once_with()
    workflow_fsm.mark_success.assert_called_once_with()
    workflow_fsm.mark_error.assert_not_called()

    assert task_runner.run.call_args_list == [call("Constitution", task) for task in tasks]
    assert result.results == expected_results
    assert result.task_statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.SUCCESS,
        "task-3": TaskStatus.SUCCESS,
    }
    assert result.status == WorkflowStatus.SUCCESS


def test_run_executes_dependent_tasks_in_order(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[1]),
        make_edge(tasks[1], tasks[2]),
    ]
    task_runner.run.side_effect = [
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
    ]

    result = runner.run("Constitution", workflow)

    assert task_runner.run.call_args_list == [
        call("Constitution", tasks[0]),
        call("Constitution", tasks[1]),
        call("Constitution", tasks[2]),
    ]
    assert result.task_statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.SUCCESS,
        "task-3": TaskStatus.SUCCESS,
    }


def test_run_executes_independent_tasks_before_dependent_tasks(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[2]),
        make_edge(tasks[1], tasks[2]),
    ]
    task_runner.run.side_effect = [
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.SUCCESS),
    ]

    runner.run("Constitution", workflow)

    assert task_runner.run.call_args_list == [
        call("Constitution", tasks[0]),
        call("Constitution", tasks[1]),
        call("Constitution", tasks[2]),
    ]


def test_run_marks_workflow_error_when_task_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    task_runner.run.side_effect = [
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.ERROR),
        make_result(TaskStatus.SUCCESS),
    ]

    result = runner.run("Constitution", workflow)

    workflow_fsm.mark_error.assert_called_once_with()
    workflow_fsm.mark_success.assert_not_called()

    assert result.task_statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.ERROR,
        "task-3": TaskStatus.SUCCESS,
    }
    assert result.status == WorkflowStatus.ERROR


def test_run_holds_dependent_tasks_when_dependency_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[1]),
        make_edge(tasks[1], tasks[2]),
    ]
    task_runner.run.return_value = make_result(TaskStatus.ERROR)

    result = runner.run("Constitution", workflow)

    task_runner.run.assert_called_once_with("Constitution", tasks[0])

    assert result.task_statuses == {
        "task-1": TaskStatus.ERROR,
        "task-2": TaskStatus.HOLD,
        "task-3": TaskStatus.HOLD,
    }
    assert result.status == WorkflowStatus.ERROR


def test_run_holds_task_when_any_dependency_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[2]),
        make_edge(tasks[1], tasks[2]),
    ]
    task_runner.run.side_effect = [
        make_result(TaskStatus.SUCCESS),
        make_result(TaskStatus.ERROR),
    ]

    result = runner.run("Constitution", workflow)

    assert task_runner.run.call_args_list == [
        call("Constitution", tasks[0]),
        call("Constitution", tasks[1]),
    ]
    assert result.task_statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.ERROR,
        "task-3": TaskStatus.HOLD,
    }


def test_run_holds_dependent_tasks_when_dependency_is_on_hold(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[1]),
        make_edge(tasks[1], tasks[2]),
    ]
    task_runner.run.return_value = make_result(TaskStatus.HOLD)

    result = runner.run("Constitution", workflow)

    task_runner.run.assert_called_once_with("Constitution", tasks[0])

    assert result.task_statuses == {
        "task-1": TaskStatus.HOLD,
        "task-2": TaskStatus.HOLD,
        "task-3": TaskStatus.HOLD,
    }


def test_run_continues_independent_tasks_when_one_task_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    task_runner: Mock,
) -> None:
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[2]),
    ]
    task_runner.run.side_effect = [
        make_result(TaskStatus.ERROR),
        make_result(TaskStatus.SUCCESS),
    ]

    result = runner.run("Constitution", workflow)

    assert task_runner.run.call_args_list == [
        call("Constitution", tasks[0]),
        call("Constitution", tasks[1]),
    ]
    assert result.task_statuses == {
        "task-1": TaskStatus.ERROR,
        "task-2": TaskStatus.SUCCESS,
        "task-3": TaskStatus.HOLD,
    }


def test_run_returns_error_for_cyclic_dependencies(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    workflow.tasks = tasks[:2]
    workflow.graph.edges = [
        make_edge(tasks[0], tasks[1]),
        make_edge(tasks[1], tasks[0]),
    ]

    result = runner.run("Constitution", workflow)

    task_runner.run.assert_not_called()
    workflow_fsm.mark_error.assert_called_once_with()
    workflow_fsm.mark_success.assert_not_called()

    assert result.task_statuses == {
        "task-1": TaskStatus.IDLE,
        "task-2": TaskStatus.IDLE,
    }
    assert result.status == WorkflowStatus.ERROR


def test_run_returns_success_for_empty_workflow(
    runner: WorkflowRunner,
    workflow: Mock,
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    workflow.tasks = []

    result = runner.run("Constitution", workflow)

    task_runner.run.assert_not_called()
    workflow_fsm.mark_success.assert_called_once_with()
    workflow_fsm.mark_error.assert_not_called()

    assert result.results == []
    assert result.task_statuses == {}
    assert result.status == WorkflowStatus.SUCCESS


def test_run_returns_partial_results_when_task_runner_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    expected_result = make_result(TaskStatus.SUCCESS)
    task_runner.run.side_effect = [
        expected_result,
        RuntimeError("Task execution failed"),
    ]

    result = runner.run("Constitution", workflow)

    assert result.results == [expected_result]
    assert result.task_statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.RUNNING,
        "task-3": TaskStatus.IDLE,
    }
    assert result.status == WorkflowStatus.ERROR

    workflow_fsm.mark_error.assert_called_once_with()
    workflow_fsm.mark_success.assert_not_called()


def test_run_returns_error_when_workflow_graph_fails(
    runner: WorkflowRunner,
    workflow: Mock,
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    workflow.graph.edges = None

    result = runner.run("Constitution", workflow)

    task_runner.run.assert_not_called()
    workflow_fsm.mark_error.assert_called_once_with()
    workflow_fsm.mark_success.assert_not_called()
    assert result.status == WorkflowStatus.ERROR


def test_run_marks_running_before_executing_tasks(
    runner: WorkflowRunner,
    workflow: Mock,
    tasks: list[Mock],
    workflow_fsm: Mock,
    task_runner: Mock,
) -> None:
    events = []

    workflow_fsm.reset.side_effect = lambda: events.append("reset")
    workflow_fsm.mark_running.side_effect = lambda: events.append("running")
    task_runner.run.side_effect = lambda *args: (
        events.append("task"),
        make_result(TaskStatus.SUCCESS),
    )[1]

    runner.run("Constitution", workflow)

    assert events == [
        "reset",
        "running",
        "task",
        "task",
        "task",
    ]
