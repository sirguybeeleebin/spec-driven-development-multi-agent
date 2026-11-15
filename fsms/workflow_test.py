import pytest

from fsms.workflow import WorkflowFSM
from models import WorkflowStatus


@pytest.fixture
def fsm() -> WorkflowFSM:
    return WorkflowFSM()


def test_initial_status(fsm: WorkflowFSM) -> None:
    assert fsm.status == WorkflowStatus.IDLE


def test_reset(fsm: WorkflowFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    fsm.reset()

    assert fsm.status == WorkflowStatus.IDLE


def test_mark_running(fsm: WorkflowFSM) -> None:
    fsm.mark_running()

    assert fsm.status == WorkflowStatus.RUNNING


@pytest.mark.parametrize(
    "status",
    [WorkflowStatus.RUNNING, WorkflowStatus.SUCCESS, WorkflowStatus.ERROR],
)
def test_mark_running_from_invalid_status(status: WorkflowStatus) -> None:
    fsm = WorkflowFSM()
    fsm.status = status

    with pytest.raises(ValueError, match="Cannot mark workflow as running"):
        fsm.mark_running()


def test_mark_success(fsm: WorkflowFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    assert fsm.status == WorkflowStatus.SUCCESS


def test_mark_success_from_non_running(fsm: WorkflowFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark workflow as successful"):
        fsm.mark_success()


def test_mark_error(fsm: WorkflowFSM) -> None:
    fsm.mark_running()
    fsm.mark_error()

    assert fsm.status == WorkflowStatus.ERROR


def test_mark_error_from_non_running(fsm: WorkflowFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark workflow as failed"):
        fsm.mark_error()
