from __future__ import annotations

from typing import Protocol

from models import (
    Task,
    TaskID,
    TaskResult,
    TaskStatus,
    Workflow,
    WorkflowResult,
)


class TaskRunner(Protocol):
    def run(self, task: Task) -> TaskResult: ...


class WorkflowFSM(Protocol):
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

    def run(self, workflow: Workflow) -> WorkflowResult:
        self._workflow_fsm.reset()
        self._workflow_fsm.mark_running()

        try:
            print(
                f"[WorkflowRunner] Starting workflow with {len(workflow.tasks)} tasks"
            )

            results: list[TaskResult] = []
            statuses: dict[TaskID, TaskStatus] = {
                task.task_id: TaskStatus.IDLE for task in workflow.tasks
            }

            ancestors: dict[TaskID, list[TaskID]] = {
                task.task_id: [] for task in workflow.tasks
            }

            for edge in workflow.graph.edges:
                ancestors[edge.target.task_id].append(edge.source.task_id)

            print(f"[WorkflowRunner] Loaded dependencies: {ancestors}")

            while True:
                ready_tasks = []

                for task in workflow.tasks:
                    tid = task.task_id
                    status = statuses[tid]

                    if status != TaskStatus.IDLE:
                        continue

                    deps_ok = all(
                        statuses[aid] is TaskStatus.SUCCESS for aid in ancestors[tid]
                    )

                    deps_failed = any(
                        statuses[aid] in (TaskStatus.ERROR, TaskStatus.HOLD)
                        for aid in ancestors[tid]
                    )

                    if deps_failed:
                        statuses[tid] = TaskStatus.HOLD
                        print(
                            f"[WorkflowRunner] Task {tid} is on hold "
                            f"because one or more dependencies failed"
                        )
                    elif deps_ok:
                        ready_tasks.append(task)
                        print(f"[WorkflowRunner] Task {tid} is ready to run")
                    else:
                        print(
                            f"[WorkflowRunner] Task {tid} is waiting for dependencies: "
                            f"{ancestors[tid]}"
                        )

                if not ready_tasks:
                    if all(
                        status
                        in (
                            TaskStatus.SUCCESS,
                            TaskStatus.ERROR,
                            TaskStatus.HOLD,
                        )
                        for status in statuses.values()
                    ):
                        print("[WorkflowRunner] All tasks have reached a final state")
                        break

                    print(
                        "[WorkflowRunner] No tasks are ready, but some tasks "
                        "are still unfinished"
                    )
                    break

                for task in ready_tasks:
                    tid = task.task_id
                    statuses[tid] = TaskStatus.RUNNING

                    print(f"[WorkflowRunner] Running task {tid}")

                    result = self._task_runner.run(task)
                    statuses[tid] = TaskStatus.SUCCESS
                    results.append(result)
                    print(f"[WorkflowRunner] Task {tid} completed successfully")

            print("[WorkflowRunner] Workflow finished")
            print(f"[WorkflowRunner] Results: {len(results)}")
            print(f"[WorkflowRunner] Final statuses: {statuses}")

            workflow_result = WorkflowResult(
                results=results,
                statuses=statuses,
            )

            if all(status == TaskStatus.SUCCESS for status in statuses.values()):
                self._workflow_fsm.mark_success()
            else:
                self._workflow_fsm.mark_error()

            return workflow_result
        except Exception:
            self._workflow_fsm.mark_error()
            raise
