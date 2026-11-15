from models import AgentStatus


class AgentFSM:
    def __init__(self) -> None:
        self._status = AgentStatus.IDLE

    @property
    def status(self) -> AgentStatus:
        return self._status

    def reset(self) -> None:
        self._status = AgentStatus.IDLE

    def mark_running(self) -> None:
        if self._status != AgentStatus.IDLE:
            raise ValueError(f"Cannot mark agent as running from {self._status}")
        self._status = AgentStatus.RUNNING

    def mark_success(self) -> None:
        if self._status != AgentStatus.RUNNING:
            raise ValueError(f"Cannot mark agent as successful from {self._status}")
        self._status = AgentStatus.SUCCESS

    def mark_error(self) -> None:
        if self._status != AgentStatus.RUNNING:
            raise ValueError(f"Cannot mark agent as failed from {self._status}")
        self._status = AgentStatus.ERROR
