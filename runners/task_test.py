from __future__ import annotations

from unittest.mock import Mock, call

import pytest

from models import AgentTestResultStatus
from runners.task import TaskRunner


@pytest.fixture
def task_fsm() -> Mock:
    fsm = Mock()
    fsm.status = "running"
    fsm.mark_success.side_effect = lambda: setattr(fsm, "status", "success")
    fsm.mark_error.side_effect = lambda: setattr(fsm, "status", "error")
    return fsm


@pytest.fixture
def researcher() -> Mock:
    agent = Mock()
    agent.run.return_value = Mock(response={"research": "result"})
    return agent


@pytest.fixture
def implementer() -> Mock:
    agent = Mock()
    agent.run.return_value = Mock(response={"implementation": "result"})
    return agent


@pytest.fixture
def tester() -> Mock:
    agent = Mock()
    agent.run.return_value = Mock(response={"status": AgentTestResultStatus.PASSED})
    return agent


@pytest.fixture
def fixer() -> Mock:
    agent = Mock()
    agent.run.return_value = Mock(response={"fix": "result"})
    return agent


@pytest.fixture
def skills() -> list[Mock]:
    return [Mock(), Mock()]


@pytest.fixture
def runner(
    task_fsm: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
    fixer: Mock,
    skills: list[Mock],
) -> TaskRunner:
    return TaskRunner(
        task_fsm=task_fsm,
        researcher=researcher,
        implementer=implementer,
        tester=tester,
        fixer=fixer,
        skills=skills,
    )


@pytest.fixture
def task() -> Mock:
    task = Mock()
    task.task_id = "task-123"
    task.goal = "Implement feature"
    task.fqns = [Mock(), Mock()]
    task.interfaces = [Mock(), Mock()]
    task.gherkins = [Mock(), Mock()]
    task.sequence = Mock()
    return task


def test_init(
    runner: TaskRunner,
    task_fsm: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
    fixer: Mock,
    skills: list[Mock],
) -> None:
    assert runner._task_fsm is task_fsm
    assert runner._researcher is researcher
    assert runner._implementer is implementer
    assert runner._tester is tester
    assert runner._fixer is fixer
    assert runner._skills is skills


def test_run_executes_all_agents(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
    fixer: Mock,
    skills: list[Mock],
) -> None:
    result = runner.run(constitution="Constitution", task=task)

    task_fsm.reset.assert_called_once_with()
    task_fsm.mark_running.assert_called_once_with()
    task_fsm.mark_success.assert_called_once_with()
    task_fsm.mark_error.assert_not_called()

    researcher.run.assert_called_once_with(
        task_id=task.task_id,
        goal=task.goal,
        fqns=task.fqns,
        interfaces=task.interfaces,
        skills=skills,
        sequence=task.sequence,
    )

    assert implementer.run.call_count == len(task.interfaces)
    assert tester.run.call_count == len(task.gherkins)
    fixer.run.assert_not_called()

    assert result.task_id == task.task_id
    assert result.status == task_fsm.status
    assert len(result.results) == 1 + len(task.interfaces) + len(task.gherkins)


def test_run_passes_researcher_result_to_implementer(
    runner: TaskRunner,
    task: Mock,
    researcher: Mock,
    implementer: Mock,
) -> None:
    researcher_response = {"research": "details"}
    researcher.run.return_value = Mock(response=researcher_response)

    runner.run(constitution="Constitution", task=task)

    assert implementer.run.call_count == len(task.interfaces)

    for interface, call_args in zip(
        task.interfaces,
        implementer.run.call_args_list,
        strict=True,
    ):
        assert call_args.kwargs == {
            "goal": task.goal,
            "current_fqn": interface.fqn,
            "current_interface": interface,
            "interfaces": task.interfaces,
            "constitution": "Constitution",
            "researcher_response": researcher_response,
            "skills": runner._skills,
            "sequence": task.sequence,
        }


def test_run_passes_optional_sequence_to_agents(
    runner: TaskRunner,
    task: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
) -> None:
    runner.run(constitution="Constitution", task=task)

    assert researcher.run.call_args.kwargs["sequence"] is task.sequence

    for call_args in implementer.run.call_args_list:
        assert call_args.kwargs["sequence"] is task.sequence

    for call_args in tester.run.call_args_list:
        assert call_args.kwargs["sequence"] is task.sequence


def test_run_skips_fixer_when_tester_passes(
    runner: TaskRunner,
    task: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    tester.run.return_value = Mock(response={"status": AgentTestResultStatus.PASSED})

    result = runner.run(constitution="Constitution", task=task)

    fixer.run.assert_not_called()
    assert len(result.results) == (1 + len(task.interfaces) + len(task.gherkins))


def test_run_executes_fixer_when_tester_does_not_pass(
    runner: TaskRunner,
    task: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    tester_response = {
        "status": AgentTestResultStatus.FAILED,
        "errors": ["Test failed"],
    }
    tester.run.return_value = Mock(response=tester_response)

    result = runner.run(constitution="Constitution", task=task)

    assert fixer.run.call_count == len(task.gherkins)

    for gherkin, call_args in zip(
        task.gherkins,
        fixer.run.call_args_list,
        strict=True,
    ):
        assert call_args == call(
            current_gherkin=gherkin,
            interfaces=task.interfaces,
            tester_result=tester_response,
            skills=runner._skills,
            sequence=task.sequence,
        )

    assert len(result.results) == (1 + len(task.interfaces) + len(task.gherkins) * 2)


def test_run_executes_fixer_only_for_failed_gherkin(
    runner: TaskRunner,
    task: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    tester.run.side_effect = [
        Mock(response={"status": AgentTestResultStatus.PASSED}),
        Mock(response={"status": AgentTestResultStatus.FAILED}),
    ]

    runner.run(constitution="Constitution", task=task)

    assert tester.run.call_count == 2
    fixer.run.assert_called_once_with(
        current_gherkin=task.gherkins[1],
        interfaces=task.interfaces,
        tester_result={"status": AgentTestResultStatus.FAILED},
        skills=runner._skills,
        sequence=task.sequence,
    )


def test_run_without_interfaces(
    runner: TaskRunner,
    task: Mock,
    implementer: Mock,
) -> None:
    task.interfaces = []

    runner.run(constitution="Constitution", task=task)

    implementer.run.assert_not_called()


def test_run_without_gherkins(
    runner: TaskRunner,
    task: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    task.gherkins = []

    result = runner.run(constitution="Constitution", task=task)

    tester.run.assert_not_called()
    fixer.run.assert_not_called()
    assert len(result.results) == 1 + len(task.interfaces)


def test_run_without_interfaces_and_gherkins(
    runner: TaskRunner,
    task: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    task.interfaces = []
    task.gherkins = []

    result = runner.run(constitution="Constitution", task=task)

    researcher.run.assert_called_once()
    implementer.run.assert_not_called()
    tester.run.assert_not_called()
    fixer.run.assert_not_called()
    assert len(result.results) == 1


@pytest.mark.parametrize(
    ("agent_name", "expected_calls"),
    [
        ("researcher", (0, 0, 0)),
        ("implementer", (1, 0, 0)),
        ("tester", (1, 1, 0)),
        ("fixer", (1, 1, 1)),
    ],
)
def test_run_returns_partial_results_when_agent_fails(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    researcher: Mock,
    implementer: Mock,
    tester: Mock,
    fixer: Mock,
    agent_name: str,
    expected_calls: tuple[int, int, int],
) -> None:
    task.interfaces = [task.interfaces[0]]
    task.gherkins = [task.gherkins[0]]

    tester.run.return_value = Mock(response={"status": AgentTestResultStatus.FAILED})

    getattr(runner, f"_{agent_name}").run.side_effect = RuntimeError("Agent failed")

    result = runner.run(constitution="Constitution", task=task)

    assert result.status == "error"
    task_fsm.mark_error.assert_called_once_with()
    task_fsm.mark_success.assert_not_called()
    assert result.task_id == task.task_id
    assert len(result.results) == sum(expected_calls)


def test_run_returns_partial_results_when_researcher_fails(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    researcher: Mock,
    implementer: Mock,
) -> None:
    researcher.run.side_effect = RuntimeError("Research failed")

    result = runner.run(constitution="Constitution", task=task)

    assert result.results == []
    assert result.status == "error"
    task_fsm.mark_error.assert_called_once_with()
    implementer.run.assert_not_called()


def test_run_returns_partial_results_when_implementer_fails(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    implementer: Mock,
    tester: Mock,
) -> None:
    implementer.run.side_effect = RuntimeError("Implementation failed")

    result = runner.run(constitution="Constitution", task=task)

    assert len(result.results) == 1
    assert result.status == "error"
    task_fsm.mark_error.assert_called_once_with()
    tester.run.assert_not_called()


def test_run_returns_partial_results_when_tester_fails(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    tester.run.side_effect = RuntimeError("Testing failed")

    result = runner.run(constitution="Constitution", task=task)

    assert len(result.results) == 1 + len(task.interfaces)
    assert result.status == "error"
    task_fsm.mark_error.assert_called_once_with()
    fixer.run.assert_not_called()


def test_run_returns_partial_results_when_fixer_fails(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    tester: Mock,
    fixer: Mock,
) -> None:
    tester.run.return_value = Mock(response={"status": AgentTestResultStatus.FAILED})
    fixer.run.side_effect = RuntimeError("Fixing failed")

    result = runner.run(constitution="Constitution", task=task)

    assert len(result.results) == 1 + len(task.interfaces) + 1
    assert result.status == "error"
    task_fsm.mark_error.assert_called_once_with()


def test_run_resets_and_marks_running_before_execution(
    runner: TaskRunner,
    task: Mock,
    task_fsm: Mock,
    researcher: Mock,
) -> None:
    events = []

    task_fsm.reset.side_effect = lambda: events.append("reset")
    task_fsm.mark_running.side_effect = lambda: events.append("running")
    researcher.run.side_effect = lambda **kwargs: (
        events.append("researcher"),
        Mock(response={}),
    )[1]

    runner.run(constitution="Constitution", task=task)

    assert events[:3] == ["reset", "running", "researcher"]
