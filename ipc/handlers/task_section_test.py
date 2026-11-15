from unittest.mock import Mock

from ipc.handlers.task_section import TaskSectionHandler


def test_handle_calls_task_section_service() -> None:
    task_section_service = Mock()
    task_section_service.create.return_value = {"status": "success"}

    handler = TaskSectionHandler(
        task_section_service=task_section_service,
    )

    command = {
        "task_id": "task-123",
        "section": "goal",
        "content": "Implement feature",
    }

    result = handler.handle(command)

    task_section_service.create.assert_called_once_with(
        task_id="task-123",
        section="goal",
        content="Implement feature",
    )
    assert result == {"status": "success"}


def test_handle_returns_service_result() -> None:
    expected = {"task_id": "task-123", "status": "created"}

    task_section_service = Mock()
    task_section_service.create.return_value = expected

    handler = TaskSectionHandler(
        task_section_service=task_section_service,
    )

    result = handler.handle(
        {
            "task_id": "task-123",
            "section": "description",
            "content": "Feature description",
        }
    )

    assert result is expected


def test_handle_propagates_service_exception() -> None:
    task_section_service = Mock()
    task_section_service.create.side_effect = ValueError("Invalid section")

    handler = TaskSectionHandler(
        task_section_service=task_section_service,
    )

    command = {
        "task_id": "task-123",
        "section": "invalid",
        "content": "Content",
    }

    try:
        handler.handle(command)
    except ValueError as error:
        assert str(error) == "Invalid section"
    else:
        raise AssertionError("Expected ValueError")
