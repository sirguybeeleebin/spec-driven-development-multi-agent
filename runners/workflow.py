from __future__ import annotations

from typing import Protocol

from models import TaskResult, TaskStatus, WorkflowStatus


class TaskRunner(Protocol):
    def run(
        self,
        constitution: str,
        task_id: str,
        goal: str,
        fqns: list[dict],
        interfaces: list[dict],
        gherkins: list[dict],
        skills: list[dict],
        sequence: dict | None = None,
    ) -> TaskResult: ...


class WorkflowFSM(Protocol):
    @property
    def status(self) -> WorkflowStatus: ...

    def reset(self) -> None: ...
    def mark_running(self) -> None: ...
    def mark_success(self) -> None: ...
    def mark_error(self) -> None: ...


class WorkflowRunner:
    def __init__(
        self,
        *,
        workflow_fsm: WorkflowFSM,
        task_runner: TaskRunner,
    ) -> None:
        self._workflow_fsm = workflow_fsm
        self._task_runner = task_runner

    def run(
        self,
        constitution: str,
        graph: dict,
        tasks: list[dict],
        skills: list[dict],
    ) -> dict:
        self._workflow_fsm.reset()
        self._workflow_fsm.mark_running()

        results: list[TaskResult] = []
        task_statuses: dict[str, TaskStatus] = {
            task["task_id"]: TaskStatus.IDLE for task in tasks
        }

        try:
            ancestors: dict[str, list[str]] = {
                task["task_id"]: [] for task in tasks
            }

            for edge in graph["edges"]:
                ancestors[edge["target"]["task_id"]].append(
                    edge["source"]["task_id"]
                )

            while True:
                ready_tasks = []

                for task in tasks:
                    task_id = task["task_id"]

                    if task_statuses[task_id] != TaskStatus.IDLE:
                        continue

                    dependencies = ancestors[task_id]

                    deps_ok = all(
                        task_statuses[ancestor_id] is TaskStatus.SUCCESS
                        for ancestor_id in dependencies
                    )

                    deps_failed = any(
                        task_statuses[ancestor_id]
                        in (TaskStatus.ERROR, TaskStatus.HOLD)
                        for ancestor_id in dependencies
                    )

                    if deps_failed:
                        task_statuses[task_id] = TaskStatus.HOLD
                    elif deps_ok:
                        ready_tasks.append(task)

                if not ready_tasks:
                    if all(
                        status
                        in (
                            TaskStatus.SUCCESS,
                            TaskStatus.ERROR,
                            TaskStatus.HOLD,
                        )
                        for status in task_statuses.values()
                    ):
                        break

                    break

                for task in ready_tasks:
                    task_id = task["task_id"]
                    task_statuses[task_id] = TaskStatus.RUNNING

                    result = self._task_runner.run(
                        constitution,
                        task_id,
                        task["goal"],
                        task["fqns"],
                        task["interfaces"],
                        task["gherkins"],
                        skills,
                        task["sequence"],
                    )

                    results.append(result)
                    task_statuses[task_id] = result.status

            if all(
                status is TaskStatus.SUCCESS
                for status in task_statuses.values()
            ):
                self._workflow_fsm.mark_success()
            else:
                self._workflow_fsm.mark_error()

        except Exception:
            self._workflow_fsm.mark_error()

        return {
            "results": results,
            "task_statuses": task_statuses,
            "status": self._workflow_fsm.status,
        }