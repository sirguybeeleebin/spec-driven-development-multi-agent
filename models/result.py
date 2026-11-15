from __future__ import annotations

from dataclasses import dataclass

from models.status import AgentStatus, TaskStatus, WorkflowStatus
from models.task import TaskID


@dataclass
class AgentResult:
    response: dict
    messages: list[dict]
    metrics: list[list[dict]]
    status: AgentStatus


@dataclass
class TaskResult:
    task_id: TaskID
    results: list[AgentResult]
    status: TaskStatus


@dataclass
class WorkflowResult:
    results: list[TaskResult]
    task_statuses: dict[TaskID, TaskStatus]
    status: WorkflowStatus


@dataclass
class TaskSectionResult:
    final: str
    messages: list[dict]
    metrics: list[dict]
