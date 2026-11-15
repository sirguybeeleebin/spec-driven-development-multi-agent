from models import WorkflowStatus


class WorkflowFSM:
    def __init__(self) -> None:
        self._status = WorkflowStatus.IDLE

    @property
    def status(self) -> WorkflowStatus:
        return self._status

    def reset(self) -> None:
        self._status = WorkflowStatus.IDLE

    def mark_running(self) -> None:
        if self._status != WorkflowStatus.IDLE:
            raise ValueError(f"Cannot mark workflow as running from {self._status}")
        self._status = WorkflowStatus.RUNNING

    def mark_success(self) -> None:
        if self._status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot mark workflow as successful from {self._status}")
        self._status = WorkflowStatus.SUCCESS

    def mark_error(self) -> None:
        if self._status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot mark workflow as failed from {self._status}")
        self._status = WorkflowStatus.ERROR
