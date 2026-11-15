from typing import Protocol


class TaskSectionRunner(Protocol):
    def run(
            self,
            *,
            task_id: str,
            section: str,
            content: str,
        ) -> tuple[dict, dict]: ...


class TaskSectionHandler:
    def __init__(
        self,
        *,
        runner: TaskSectionRunner,
    ) -> None:
        self._runner = runner

    def handle(self, command: dict) -> dict:
        return self._runner.create(
            task_id=command["task_id"],
            section=command["section"],
            content=command["content"],
        )
