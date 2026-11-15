from typing import Protocol

from models import Role


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> tuple[dict, dict]: ...


class TaskSectionRepository(Protocol):
    def get(
        self,
        *,
        task_id: str,
        section: str,
    ) -> dict | None: ...

    def save(
        self,
        *,
        task_id: str,
        section: str,
        content: str,
        history: list[dict],
    ) -> dict: ...


class TaskSectionRunner:
    def __init__(
        self,
        *,
        client: LLMClient,
        task_section_repository: TaskSectionRepository,
    ) -> None:
        self._client = client
        self._task_section_repository = task_section_repository

    def run(
        self,
        *,
        task_id: str,
        section: str,
        content: str,
    ) -> tuple[dict, dict]:
        task_section = self._task_section_repository.get(
            task_id=task_id,
            section=section,
        )

        history = task_section["history"] if task_section else []
        history.append(
            {
                "role": Role.USER,
                "content": content,
            }
        )

        message, metrics = self._client.complete(messages=history)
        history.append(message)

        self._task_section_repository.save(
            task_id=task_id,
            section=section,
            content=message["content"],
            history=history,
        )

        return message, metrics
