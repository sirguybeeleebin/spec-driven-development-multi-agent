from models import TaskStatus


class TaskFSM:
    def __init__(self) -> None:
        self.status = TaskStatus.IDLE

    def reset(self) -> None:
        self.status = TaskStatus.IDLE

    def mark_running(self) -> None:
        if self.status != TaskStatus.IDLE:
            raise ValueError(f"Cannot mark task as running from {self.status}")
        self.status = TaskStatus.RUNNING

    def mark_success(self) -> None:
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot mark task as successful from {self.status}")
        self.status = TaskStatus.SUCCESS

    def mark_error(self) -> None:
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot mark task as failed from {self.status}")
        self.status = TaskStatus.ERROR

    def mark_hold(self) -> None:
        if self.status not in {TaskStatus.IDLE, TaskStatus.RUNNING}:
            raise ValueError(f"Cannot put task on hold from {self.status}")
        self.status = TaskStatus.HOLD
