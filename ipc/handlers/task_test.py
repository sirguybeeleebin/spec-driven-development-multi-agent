from unittest.mock import Mock

from ipc.handlers.task import TaskHandler


def test_handle_calls_task_service() -> None:
    task_service = Mock()
    task_service.run.return_value = {"status": "success"}

    handler = TaskHandler(task_service=task_service)

    command = {
        "constitution": "Project constitution",
        "task": "Implement feature",
    }

    result = handler.handle(command)

    task_service.run.assert_called_once_with(
        constitution="Project constitution",
        task="Implement feature",
    )
    assert result == {"status": "success"}


def test_handle_returns_service_result() -> None:
    expected = {"task_id": "task-123", "status": "completed"}

    task_service = Mock()
    task_service.run.return_value = expected

    handler = TaskHandler(task_service=task_service)

    result = handler.handle(
        {
            "constitution": "Constitution",
            "task": "Task",
        }
    )

    assert result is expected


def test_handle_propagates_service_exception() -> None:
    task_service = Mock()
    task_service.run.side_effect = ValueError("Invalid task")

    handler = TaskHandler(task_service=task_service)

    command = {
        "constitution": "Constitution",
        "task": "Task",
    }

    try:
        handler.handle(command)
    except ValueError as error:
        assert str(error) == "Invalid task"
    else:
        raise AssertionError("Expected ValueError")
