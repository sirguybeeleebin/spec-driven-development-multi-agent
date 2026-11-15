from typing import Protocol


class TaskRunner(Protocol):
    def run(
        self,
        *,
        constitution: str,
        task_id: str,
        goal: str,
        fqns: list[dict],
        interfaces: list[dict],
        gherkins: list[dict],
        sequence: dict | None = None,
    ) -> dict: ...


class TaskHandler:
    def __init__(self, *, task_runner: TaskRunner) -> None:
        self.task_runner = task_runner

    def handle(self, command: dict) -> dict:
        return self.task_runner.run(
            constitution=command["constitution"],
            task_id=command["task_id"],
            goal=command["goal"],
            fqns=command["fqns"],
            interfaces=command["interfaces"],
            gherkins=command["gherkins"],
            sequence=command.get("sequence"),
        )