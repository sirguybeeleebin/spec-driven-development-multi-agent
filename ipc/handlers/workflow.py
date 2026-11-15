from typing import Protocol


class WorkflowRunner(Protocol):
    def run(
        self,
        *,
        constitution: str,
        graph: dict,
        tasks: list[dict],
    ) -> dict: ...


class WorkflowHandler:
    def __init__(self, *, workflow_runner: WorkflowRunner) -> None:
        self.workflow_runner = workflow_runner

    def handle(self, command: dict) -> dict:
        return self.workflow_runner.run(
            constitution=command["constitution"],
            graph=command["graph"],
            tasks=command["tasks"],
        )