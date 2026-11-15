from __future__ import annotations

from typing import Protocol

from models import AgentTestResultStatus


class Agent(Protocol):
    def run(self, context: dict, skills: list[dict]) -> dict: ...


class TaskFSM(Protocol):
    @property
    def status(self): ...

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

    def run(
        self,
        *,
        constitution: str,
        task_id: str,
        goal: str,
        fqns: list[dict],
        interfaces: list[dict],
        gherkins: list[dict],
        skills: list[dict],
        sequence: dict | None = None,
    ) -> dict:
        self._task_fsm.reset()
        self._task_fsm.mark_running()

        results: list[dict] = []

        try:
            researcher_result = self._researcher.run(
                {
                    "task_id": task_id,
                    "goal": goal,
                    "fqns": fqns,
                    "interfaces": interfaces,
                    "sequence": sequence,
                },
                skills,
            )
            results.append(researcher_result)

            for interface in interfaces:
                implementer_result = self._implementer.run(
                    {
                        "goal": goal,
                        "current_fqn": interface["fqn"],
                        "current_interface": interface,
                        "interfaces": interfaces,
                        "constitution": constitution,
                        "researcher_response": researcher_result["response"],
                        "sequence": sequence,
                    },
                    skills,
                )
                results.append(implementer_result)

            for gherkin in gherkins:
                tester_result = self._tester.run(
                    {
                        "current_gherkin": gherkin,
                        "interfaces": interfaces,
                        "sequence": sequence,
                    },
                    skills,
                )
                results.append(tester_result)

                if tester_result["response"].get("status") == AgentTestResultStatus.PASSED:
                    continue

                fixer_result = self._fixer.run(
                    {
                        "current_gherkin": gherkin,
                        "interfaces": interfaces,
                        "tester_result": tester_result["response"],
                        "sequence": sequence,
                    },
                    skills,
                )
                results.append(fixer_result)

            self._task_fsm.mark_success()

        except Exception:
            self._task_fsm.mark_error()

        return {
            "task_id": task_id,
            "results": results,
            "status": self._task_fsm.status,
        }