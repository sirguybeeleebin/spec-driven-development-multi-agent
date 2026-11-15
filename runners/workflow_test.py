from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from models import Task, TaskResult, TaskStatus, Workflow, WorkflowResult
from runners.workflow import WorkflowRunner


def make_task(task_id: str) -> Task:
    return Mock(spec=Task, task_id=task_id)


def make_edge(source: str, target: str) -> SimpleNamespace:
    return SimpleNamespace(
        source=SimpleNamespace(task_id=source),
        target=SimpleNamespace(task_id=target),
    )


def make_workflow(
    task_ids: list[str],
    edges: list[SimpleNamespace] | None = None,
) -> Workflow:
    return Workflow(
        graph=SimpleNamespace(edges=edges or []),
        tasks=[make_task(task_id) for task_id in task_ids],
    )


def make_task_result(task_id: str) -> TaskResult:
    return TaskResult(task_id=task_id, results=[])


@pytest.fixture
def task_runner() -> Mock:
    return Mock()


@pytest.fixture
def workflow_fsm() -> Mock:
    return Mock()


@pytest.fixture
def runner(
    task_runner: Mock,
    workflow_fsm: Mock,
) -> WorkflowRunner:
    return WorkflowRunner(
        workflow_fsm=workflow_fsm,
        task_runner=task_runner,
    )


def test_runs_all_independent_tasks(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(["task-1", "task-2", "task-3"])
    task_runner.run.side_effect = [
        make_task_result("task-1"),
        make_task_result("task-2"),
        make_task_result("task-3"),
    ]

    result = runner.run(workflow)

    assert task_runner.run.call_count == 3
    assert [item.args[0].task_id for item in task_runner.run.call_args_list] == [
        "task-1",
        "task-2",
        "task-3",
    ]
    assert [item.task_id for item in result.results] == [
        "task-1",
        "task-2",
        "task-3",
    ]
    assert result.statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.SUCCESS,
        "task-3": TaskStatus.SUCCESS,
    }


def test_runs_dependent_tasks_in_order(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3"],
        [
            make_edge("task-1", "task-2"),
            make_edge("task-2", "task-3"),
        ],
    )
    task_runner.run.side_effect = [
        make_task_result("task-1"),
        make_task_result("task-2"),
        make_task_result("task-3"),
    ]

    result = runner.run(workflow)

    assert [item.task_id for item in result.results] == [
        "task-1",
        "task-2",
        "task-3",
    ]
    assert [item.args[0].task_id for item in task_runner.run.call_args_list] == [
        "task-1",
        "task-2",
        "task-3",
    ]
    assert all(status is TaskStatus.SUCCESS for status in result.statuses.values())


def test_runs_task_only_after_all_dependencies_succeed(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3"],
        [
            make_edge("task-1", "task-3"),
            make_edge("task-2", "task-3"),
        ],
    )
    task_runner.run.side_effect = [
        make_task_result("task-1"),
        make_task_result("task-2"),
        make_task_result("task-3"),
    ]

    result = runner.run(workflow)

    assert [item.task_id for item in result.results] == [
        "task-1",
        "task-2",
        "task-3",
    ]
    assert task_runner.run.call_count == 3
    assert result.statuses["task-3"] is TaskStatus.SUCCESS


def test_runs_independent_tasks_in_same_ready_batch(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3"],
        [make_edge("task-1", "task-3")],
    )
    task_runner.run.side_effect = [
        make_task_result("task-1"),
        make_task_result("task-2"),
        make_task_result("task-3"),
    ]

    runner.run(workflow)

    assert [item.args[0].task_id for item in task_runner.run.call_args_list] == [
        "task-1",
        "task-2",
        "task-3",
    ]


def test_propagates_task_error(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(["task-1"])
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(workflow)

    assert task_runner.run.call_count == 1
    assert task_runner.run.call_args.args[0].task_id == "task-1"


def test_propagates_error_before_running_dependent_task(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2"],
        [make_edge("task-1", "task-2")],
    )
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(workflow)

    assert task_runner.run.call_count == 1
    assert task_runner.run.call_args.args[0].task_id == "task-1"


def test_propagates_error_before_running_transitive_dependents(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3", "task-4"],
        [
            make_edge("task-1", "task-2"),
            make_edge("task-2", "task-3"),
            make_edge("task-3", "task-4"),
        ],
    )
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(workflow)

    assert task_runner.run.call_count == 1
    assert task_runner.run.call_args.args[0].task_id == "task-1"


def test_propagates_error_without_running_unrelated_branch(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3", "task-4"],
        [
            make_edge("task-1", "task-2"),
            make_edge("task-3", "task-4"),
        ],
    )
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(workflow)

    assert task_runner.run.call_count == 1
    assert task_runner.run.call_args.args[0].task_id == "task-1"


def test_propagates_error_when_another_dependency_is_successful(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2", "task-3"],
        [
            make_edge("task-1", "task-3"),
            make_edge("task-2", "task-3"),
        ],
    )
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(workflow)

    assert task_runner.run.call_count == 1
    assert task_runner.run.call_args.args[0].task_id == "task-1"


def test_returns_task_results_in_execution_order(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(["task-1", "task-2"])
    first_result = make_task_result("task-1")
    second_result = make_task_result("task-2")
    task_runner.run.side_effect = [first_result, second_result]

    result = runner.run(workflow)

    assert isinstance(result, WorkflowResult)
    assert result.results == [first_result, second_result]
    assert result.statuses == {
        "task-1": TaskStatus.SUCCESS,
        "task-2": TaskStatus.SUCCESS,
    }


def test_passes_original_task_objects_to_task_runner(
    runner: WorkflowRunner,
    task_runner: Mock,
) -> None:
    workflow = make_workflow(["task-1", "task-2"])

    runner.run(workflow)

    assert task_runner.run.call_args_list == [
        call(workflow.tasks[0]),
        call(workflow.tasks[1]),
    ]


def test_empty_workflow(
    runner: WorkflowRunner,
    task_runner: Mock,
    workflow_fsm: Mock,
) -> None:
    result = runner.run(make_workflow([]))

    task_runner.run.assert_not_called()
    assert isinstance(result, WorkflowResult)
    assert result.results == []
    assert result.statuses == {}

    workflow_fsm.mark_error.assert_not_called()
    workflow_fsm.mark_success.assert_called_once()


def test_stops_when_workflow_has_cycle(
    runner: WorkflowRunner,
    task_runner: Mock,
    workflow_fsm: Mock,
) -> None:
    workflow = make_workflow(
        ["task-1", "task-2"],
        [
            make_edge("task-1", "task-2"),
            make_edge("task-2", "task-1"),
        ],
    )

    result = runner.run(workflow)

    task_runner.run.assert_not_called()
    assert result.results == []
    assert result.statuses == {
        "task-1": TaskStatus.IDLE,
        "task-2": TaskStatus.IDLE,
    }

    workflow_fsm.mark_error.assert_called_once()
    workflow_fsm.mark_success.assert_not_called()


def test_resets_and_marks_workflow_running_before_execution(
    runner: WorkflowRunner,
    workflow_fsm: Mock,
) -> None:
    runner.run(make_workflow(["task-1"]))

    assert workflow_fsm.method_calls == [
        call.reset(),
        call.mark_running(),
        call.mark_success(),
    ]


def test_marks_workflow_success_when_all_tasks_succeed(
    runner: WorkflowRunner,
    workflow_fsm: Mock,
) -> None:
    runner.run(make_workflow(["task-1", "task-2"]))

    workflow_fsm.reset.assert_called_once()
    workflow_fsm.mark_running.assert_called_once()
    workflow_fsm.mark_success.assert_called_once()
    workflow_fsm.mark_error.assert_not_called()


def test_marks_workflow_error_when_task_execution_fails(
    runner: WorkflowRunner,
    task_runner: Mock,
    workflow_fsm: Mock,
) -> None:
    task_runner.run.side_effect = RuntimeError("Task failed")

    with pytest.raises(RuntimeError, match="Task failed"):
        runner.run(make_workflow(["task-1"]))

    workflow_fsm.reset.assert_called_once()
    workflow_fsm.mark_running.assert_called_once()
    workflow_fsm.mark_error.assert_called_once()
    workflow_fsm.mark_success.assert_not_called()
