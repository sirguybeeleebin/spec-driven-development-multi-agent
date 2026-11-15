from __future__ import annotations

from typing import Protocol

from models import (
    AgentResult,
    Agents,
    AgentTestResultStatus,
    State,
    Task,
    TaskResult,
)


class Agent(Protocol):
    def run(self, *, state: State) -> AgentResult: ...


class TaskFSM(Protocol):
    def reset(self) -> None: ...
    def mark_running(self) -> None: ...
    def mark_success(self) -> None: ...
    def mark_error(self) -> None: ...
    def mark_hold(self) -> None: ...


class TaskRunner:
    def __init__(
        self,
        *,
        task_fsm: TaskFSM,
        researcher: Agent,
        implementer: Agent,
        tester: Agent,
        fixer: Agent,
    ) -> None:
        self._task_fsm = task_fsm
        self._researcher = researcher
        self._implementer = implementer
        self._tester = tester
        self._fixer = fixer

    def run(self, task: Task) -> TaskResult:
        self._task_fsm.reset()
        self._task_fsm.mark_running()

        try:
            print(f"[TaskRunner] Starting task: {task.task_id}")
            print(f"[TaskRunner] Interfaces: {len(task.interfaces)}")
            print(f"[TaskRunner] Gherkins: {len(task.gherkins)}")

            state = State(task=task)

            print(f"[TaskRunner] Running researcher for {task.task_id}")
            result = self._researcher.run(state=state)
            state.agent_results[Agents.RESEARCHER].append(result)
            print("[TaskRunner] Researcher completed")

            for interface in task.interfaces:
                state.current_interface = interface

                print(
                    f"[TaskRunner] Running implementer for interface: {interface.name}"
                )
                result = self._implementer.run(state=state)
                state.agent_results[Agents.IMPLEMENTER].append(result)
                print(
                    f"[TaskRunner] Implementer completed for interface: {interface.name}"
                )

            state.current_interface = None

            for gherkin in task.gherkins:
                state.current_gherkin = gherkin

                print(f"[TaskRunner] Running tester for gherkin: {gherkin}")
                result = self._tester.run(state=state)
                state.agent_results[Agents.TESTER].append(result)

                status = result.response.get("status")
                print(f"[TaskRunner] Tester status: {status}")

                if status == AgentTestResultStatus.PASSED:
                    print("[TaskRunner] Tests passed")
                    continue

                print("[TaskRunner] Tests failed, running fixer")
                result = self._fixer.run(state=state)
                state.agent_results[Agents.FIXER].append(result)
                print("[TaskRunner] Fixer completed")

            state.current_gherkin = None

            results = [
                result
                for agent_results in state.agent_results.values()
                for result in agent_results
            ]

            print(f"[TaskRunner] Task completed: {task.task_id}")
            print(f"[TaskRunner] Agent results: {len(results)}")

            task_result = TaskResult(
                task_id=task.task_id,
                results=results,
            )

            self._task_fsm.mark_success()

            return task_result
        except Exception:
            self._task_fsm.mark_error()
            raise
