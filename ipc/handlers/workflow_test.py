from unittest.mock import Mock

from ipc.handlers.workflow import WorkflowHandler


def test_handle_calls_workflow_service() -> None:
    workflow_service = Mock()
    workflow_service.run.return_value = {"status": "success"}

    handler = WorkflowHandler(workflow_service=workflow_service)

    command = {
        "constitution": "Project constitution",
        "graph": "Task graph",
        "tasks": ["Task 1", "Task 2"],
    }

    result = handler.handle(command)

    workflow_service.run.assert_called_once_with(
        constitution="Project constitution",
        graph="Task graph",
        tasks=["Task 1", "Task 2"],
    )
    assert result == {"status": "success"}


def test_handle_returns_service_result() -> None:
    expected = {"status": "completed", "tasks_num": 2}

    workflow_service = Mock()
    workflow_service.run.return_value = expected

    handler = WorkflowHandler(workflow_service=workflow_service)

    result = handler.handle(
        {
            "constitution": "Constitution",
            "graph": "Graph",
            "tasks": ["Task 1", "Task 2"],
        }
    )

    assert result is expected


def test_handle_propagates_service_exception() -> None:
    workflow_service = Mock()
    workflow_service.run.side_effect = ValueError("Invalid workflow")

    handler = WorkflowHandler(workflow_service=workflow_service)

    command = {
        "constitution": "Constitution",
        "graph": "Graph",
        "tasks": ["Task 1"],
    }

    try:
        handler.handle(command)
    except ValueError as error:
        assert str(error) == "Invalid workflow"
    else:
        raise AssertionError("Expected ValueError")
