import pytest

from fsms.agent import AgentFSM
from models import AgentStatus


@pytest.fixture
def fsm() -> AgentFSM:
    return AgentFSM()


def test_initial_status(fsm: AgentFSM) -> None:
    assert fsm.status == AgentStatus.IDLE


def test_reset(fsm: AgentFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    fsm.reset()

    assert fsm.status == AgentStatus.IDLE


def test_mark_running(fsm: AgentFSM) -> None:
    fsm.mark_running()

    assert fsm.status == AgentStatus.RUNNING


def test_mark_running_from_non_idle(fsm: AgentFSM) -> None:
    fsm.mark_running()

    with pytest.raises(ValueError, match="Cannot mark agent as running"):
        fsm.mark_running()


def test_mark_success(fsm: AgentFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    assert fsm.status == AgentStatus.SUCCESS


def test_mark_success_from_non_running(fsm: AgentFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark agent as successful"):
        fsm.mark_success()


def test_mark_error(fsm: AgentFSM) -> None:
    fsm.mark_running()
    fsm.mark_error()

    assert fsm.status == AgentStatus.ERROR


def test_mark_error_from_non_running(fsm: AgentFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark agent as failed"):
        fsm.mark_error()
