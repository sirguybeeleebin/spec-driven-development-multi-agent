from models import WorkflowStatus


class WorkflowFSM:
    def __init__(self) -> None:
        self.status = WorkflowStatus.IDLE

    def reset(self) -> None:
        self.status = WorkflowStatus.IDLE

    def mark_running(self) -> None:
        if self.status != WorkflowStatus.IDLE:
            raise ValueError(f"Cannot mark workflow as running from {self.status}")
        self.status = WorkflowStatus.RUNNING

    def mark_success(self) -> None:
        if self.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot mark workflow as successful from {self.status}")
        self.status = WorkflowStatus.SUCCESS

    def mark_error(self) -> None:
        if self.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot mark workflow as failed from {self.status}")
        self.status = WorkflowStatus.ERROR
