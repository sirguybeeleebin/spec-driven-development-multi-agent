from models import TaskStatus


class TaskFSM:
    def __init__(self) -> None:
        self._status = TaskStatus.IDLE

    @property
    def status(self) -> TaskStatus:
        return self._status

    def reset(self) -> None:
        self._status = TaskStatus.IDLE

    def mark_running(self) -> None:
        if self._status != TaskStatus.IDLE:
            raise ValueError(f"Cannot mark task as running from {self._status}")
        self._status = TaskStatus.RUNNING

    def mark_success(self) -> None:
        if self._status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot mark task as successful from {self._status}")
        self._status = TaskStatus.SUCCESS

    def mark_error(self) -> None:
        if self._status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot mark task as failed from {self._status}")
        self._status = TaskStatus.ERROR

    def mark_hold(self) -> None:
        if self._status not in {TaskStatus.IDLE, TaskStatus.RUNNING}:
            raise ValueError(f"Cannot put task on hold from {self._status}")
        self._status = TaskStatus.HOLD
