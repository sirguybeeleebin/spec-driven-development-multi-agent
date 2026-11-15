from models import AgentStatus


class AgentFSM:
    def __init__(self) -> None:
        self.status = AgentStatus.IDLE

    def reset(self) -> None:
        self.status = AgentStatus.IDLE

    def mark_running(self) -> None:
        if self.status != AgentStatus.IDLE:
            raise ValueError(f"Cannot mark agent as running from {self.status}")
        self.status = AgentStatus.RUNNING

    def mark_success(self) -> None:
        if self.status != AgentStatus.RUNNING:
            raise ValueError(f"Cannot mark agent as successful from {self.status}")
        self.status = AgentStatus.SUCCESS

    def mark_error(self) -> None:
        if self.status != AgentStatus.RUNNING:
            raise ValueError(f"Cannot mark agent as failed from {self.status}")
        self.status = AgentStatus.ERROR
