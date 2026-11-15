# models/statuses.py

from __future__ import annotations

from enum import StrEnum


class AgentStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class TaskStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    HOLD = "hold"


class WorkflowStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
