import pytest

from fsms.task import TaskFSM
from models import TaskStatus


@pytest.fixture
def fsm() -> TaskFSM:
    return TaskFSM()


def test_initial_status(fsm: TaskFSM) -> None:
    assert fsm.status == TaskStatus.IDLE


def test_reset(fsm: TaskFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    fsm.reset()

    assert fsm.status == TaskStatus.IDLE


def test_mark_running(fsm: TaskFSM) -> None:
    fsm.mark_running()

    assert fsm.status == TaskStatus.RUNNING


def test_mark_running_from_non_idle(fsm: TaskFSM) -> None:
    fsm.mark_running()

    with pytest.raises(ValueError, match="Cannot mark task as running"):
        fsm.mark_running()


def test_mark_success(fsm: TaskFSM) -> None:
    fsm.mark_running()
    fsm.mark_success()

    assert fsm.status == TaskStatus.SUCCESS


def test_mark_success_from_non_running(fsm: TaskFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark task as successful"):
        fsm.mark_success()


def test_mark_error(fsm: TaskFSM) -> None:
    fsm.mark_running()
    fsm.mark_error()

    assert fsm.status == TaskStatus.ERROR


def test_mark_error_from_non_running(fsm: TaskFSM) -> None:
    with pytest.raises(ValueError, match="Cannot mark task as failed"):
        fsm.mark_error()


def test_mark_hold_from_idle(fsm: TaskFSM) -> None:
    fsm.mark_hold()

    assert fsm.status == TaskStatus.HOLD


def test_mark_hold_from_running(fsm: TaskFSM) -> None:
    fsm.mark_running()
    fsm.mark_hold()

    assert fsm.status == TaskStatus.HOLD


@pytest.mark.parametrize(
    ("prepare", "status"),
    [
        (lambda fsm: (fsm.mark_running(), fsm.mark_success()), TaskStatus.SUCCESS),
        (lambda fsm: (fsm.mark_running(), fsm.mark_error()), TaskStatus.ERROR),
        (lambda fsm: fsm.mark_hold(), TaskStatus.HOLD),
    ],
)
def test_mark_hold_from_invalid_status(prepare, status: TaskStatus) -> None:
    fsm = TaskFSM()
    prepare(fsm)

    assert fsm.status == status

    with pytest.raises(ValueError, match="Cannot put task on hold"):
        fsm.mark_hold()
