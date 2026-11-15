from __future__ import annotations

from unittest.mock import Mock, call

import pytest

from models import (
    AgentResult,
    AgentTestResultStatus,
    FullQualifiedName,
    Gherkin,
    Interface,
    State,
    Task,
)
from runners.task import TaskRunner


def make_agent_runner_result(response: dict | None = None) -> AgentResult:
    return AgentResult(
        response=response or {},
        messages=[],
        metrics=[],
    )


def make_interface(name: str) -> Interface:
    return Interface(
        name=name,
        language="python",
        content=f"class {name}: pass",
        description=f"{name} description",
        steps=[],
    )


def make_gherkin(name: str) -> Gherkin:
    return Gherkin(
        name=name,
        fqn=FullQualifiedName(f"services::{name}"),
        test_fqn=FullQualifiedName(f"tests::{name}"),
        given=[],
        when=[],
        then=[],
    )


def make_task(
    interfaces: list[Interface] | None = None,
    gherkins: list[Gherkin] | None = None,
) -> Task:
    return Task(
        task_id="task-1",
        goal="Implement the requested functionality",
        fqns=[],
        interfaces=interfaces or [],
        gherkins=gherkins or [],
        constitution="",
    )


@pytest.fixture
def agents() -> dict[str, Mock]:
    return {
        "researcher": Mock(),
        "implementer": Mock(),
        "tester": Mock(),
        "fixer": Mock(),
    }


@pytest.fixture
def task_fsm() -> Mock:
    return Mock()


@pytest.fixture
def runner(
    agents: dict[str, Mock],
    task_fsm: Mock,
) -> TaskRunner:
    return TaskRunner(
        task_fsm=task_fsm,
        researcher=agents["researcher"],
        implementer=agents["implementer"],
        tester=agents["tester"],
        fixer=agents["fixer"],
    )


def test_runs_researcher_once_and_implementer_for_each_interface(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    interfaces = [
        make_interface("UserRepository"),
        make_interface("UserService"),
        make_interface("UserRouter"),
    ]

    runner.run(make_task(interfaces=interfaces))

    agents["researcher"].run.assert_called_once()
    assert agents["implementer"].run.call_count == len(interfaces)


def test_passes_same_state_to_all_agents(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    captured_states: list[State] = []

    def capture_state(*, state: State) -> AgentResult:
        captured_states.append(state)
        return make_agent_runner_result({"status": AgentTestResultStatus.PASSED})

    for agent in agents.values():
        agent.run.side_effect = capture_state

    runner.run(
        make_task(
            interfaces=[
                make_interface("UserRepository"),
                make_interface("UserService"),
            ],
            gherkins=[make_gherkin("first")],
        )
    )

    assert captured_states
    assert all(state is captured_states[0] for state in captured_states)


def test_runs_implementer_for_each_interface(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    interfaces = [
        make_interface("UserRepository"),
        make_interface("UserService"),
        make_interface("UserRouter"),
    ]

    runner.run(make_task(interfaces=interfaces))

    assert agents["implementer"].run.call_count == len(interfaces)


def test_sets_current_interface_before_each_implementation(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    interfaces = [
        make_interface("UserRepository"),
        make_interface("UserService"),
        make_interface("UserRouter"),
    ]
    captured_interfaces: list[Interface | None] = []

    def capture_state(*, state: State) -> AgentResult:
        captured_interfaces.append(state.current_interface)
        return make_agent_runner_result()

    agents["implementer"].run.side_effect = capture_state

    runner.run(make_task(interfaces=interfaces))

    assert captured_interfaces == interfaces


def test_passes_current_interface_to_implementer(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    interface = make_interface("UserRepository")
    captured_interfaces: list[Interface | None] = []

    def capture_state(*, state: State) -> AgentResult:
        captured_interfaces.append(state.current_interface)
        return make_agent_runner_result()

    agents["implementer"].run.side_effect = capture_state

    runner.run(make_task(interfaces=[interface]))

    assert captured_interfaces == [interface]


def test_resets_current_interface_after_implementation(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    agents["implementer"].run.return_value = make_agent_runner_result()

    runner.run(
        make_task(
            interfaces=[
                make_interface("UserRepository"),
                make_interface("UserService"),
            ]
        )
    )

    state = agents["implementer"].run.call_args.kwargs["state"]

    assert state.current_interface is None


def test_runs_tester_for_each_gherkin(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    gherkins = [
        make_gherkin("first"),
        make_gherkin("second"),
        make_gherkin("third"),
    ]
    agents["tester"].run.return_value = make_agent_runner_result(
        {"status": AgentTestResultStatus.PASSED}
    )

    runner.run(make_task(gherkins=gherkins))

    assert agents["tester"].run.call_count == len(gherkins)


def test_runs_fixer_when_test_fails(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    agents["tester"].run.return_value = make_agent_runner_result(
        {"status": AgentTestResultStatus.FAILED}
    )

    runner.run(make_task(gherkins=[make_gherkin("first")]))

    agents["fixer"].run.assert_called_once()


def test_does_not_run_fixer_when_test_passes(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    agents["tester"].run.return_value = make_agent_runner_result(
        {"status": AgentTestResultStatus.PASSED}
    )

    runner.run(make_task(gherkins=[make_gherkin("first")]))

    agents["fixer"].run.assert_not_called()


def test_runs_fixer_only_for_failed_gherkin(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    agents["tester"].run.side_effect = [
        make_agent_runner_result({"status": AgentTestResultStatus.PASSED}),
        make_agent_runner_result({"status": AgentTestResultStatus.FAILED}),
        make_agent_runner_result({"status": AgentTestResultStatus.PASSED}),
    ]

    runner.run(
        make_task(
            gherkins=[
                make_gherkin("first"),
                make_gherkin("second"),
                make_gherkin("third"),
            ]
        )
    )

    agents["fixer"].run.assert_called_once()


def test_sets_current_gherkin_before_each_test(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    gherkins = [
        make_gherkin("first"),
        make_gherkin("second"),
    ]
    captured_gherkins: list[Gherkin | None] = []

    def capture_state(*, state: State) -> AgentResult:
        captured_gherkins.append(state.current_gherkin)
        return make_agent_runner_result({"status": AgentTestResultStatus.PASSED})

    agents["tester"].run.side_effect = capture_state

    runner.run(make_task(gherkins=gherkins))

    assert captured_gherkins == gherkins


def test_passes_current_gherkin_to_fixer(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    gherkin = make_gherkin("first")
    captured_gherkins: list[Gherkin | None] = []

    def capture_state(*, state: State) -> AgentResult:
        captured_gherkins.append(state.current_gherkin)
        return make_agent_runner_result()

    agents["tester"].run.side_effect = capture_state
    agents["fixer"].run.side_effect = capture_state

    runner.run(make_task(gherkins=[gherkin]))

    assert captured_gherkins == [gherkin, gherkin]


def test_resets_current_gherkin_after_run(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    agents["tester"].run.return_value = make_agent_runner_result(
        {"status": AgentTestResultStatus.PASSED}
    )

    runner.run(make_task(gherkins=[make_gherkin("first")]))

    state = agents["tester"].run.call_args.kwargs["state"]

    assert state.current_gherkin is None


def test_returns_results_from_all_agents_in_execution_order(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    researcher_result = make_agent_runner_result({"agent": "researcher"})
    implementer_results = [
        make_agent_runner_result({"agent": "implementer-1"}),
        make_agent_runner_result({"agent": "implementer-2"}),
    ]
    tester_result = make_agent_runner_result({"agent": "tester"})
    fixer_result = make_agent_runner_result({"agent": "fixer"})

    agents["researcher"].run.return_value = researcher_result
    agents["implementer"].run.side_effect = implementer_results
    agents["tester"].run.return_value = tester_result
    agents["fixer"].run.return_value = fixer_result

    result = runner.run(
        make_task(
            interfaces=[
                make_interface("UserRepository"),
                make_interface("UserService"),
            ],
            gherkins=[make_gherkin("first")],
        )
    )

    assert result.task_id == "task-1"
    assert result.results == [
        researcher_result,
        *implementer_results,
        tester_result,
        fixer_result,
    ]


def test_runs_implementations_before_tests(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    events = []

    agents["researcher"].run.side_effect = lambda **kwargs: (
        events.append("researcher") or make_agent_runner_result()
    )
    agents["implementer"].run.side_effect = lambda **kwargs: (
        events.append("implementer") or make_agent_runner_result()
    )
    agents["tester"].run.side_effect = lambda **kwargs: (
        events.append("tester")
        or make_agent_runner_result({"status": AgentTestResultStatus.PASSED})
    )

    runner.run(
        make_task(
            interfaces=[
                make_interface("UserRepository"),
                make_interface("UserService"),
            ],
            gherkins=[make_gherkin("first")],
        )
    )

    assert events == [
        "researcher",
        "implementer",
        "implementer",
        "tester",
    ]


def test_empty_interfaces(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    runner.run(make_task())

    agents["researcher"].run.assert_called_once()
    agents["implementer"].run.assert_not_called()


def test_empty_gherkins(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    result = runner.run(make_task(interfaces=[make_interface("UserRepository")]))

    agents["researcher"].run.assert_called_once()
    agents["implementer"].run.assert_called_once()
    agents["tester"].run.assert_not_called()
    agents["fixer"].run.assert_not_called()

    assert len(result.results) == 2


def test_propagates_agent_exception(
    runner: TaskRunner,
    agents: dict[str, Mock],
) -> None:
    error = RuntimeError("Research failed")
    agents["researcher"].run.side_effect = error

    with pytest.raises(RuntimeError, match="Research failed"):
        runner.run(make_task())


def test_resets_and_marks_task_running_before_execution(
    runner: TaskRunner,
    task_fsm: Mock,
) -> None:
    runner.run(make_task())

    assert task_fsm.method_calls[:3] == [
        call.reset(),
        call.mark_running(),
        call.mark_success(),
    ]


def test_marks_task_error_when_agent_execution_fails(
    runner: TaskRunner,
    agents: dict[str, Mock],
    task_fsm: Mock,
) -> None:
    agents["researcher"].run.side_effect = RuntimeError("Research failed")

    with pytest.raises(RuntimeError, match="Research failed"):
        runner.run(make_task())

    task_fsm.reset.assert_called_once()
    task_fsm.mark_running.assert_called_once()
    task_fsm.mark_error.assert_called_once()
    task_fsm.mark_success.assert_not_called()
