# models/workflow.py

from __future__ import annotations

from dataclasses import dataclass

from models.graph import Graph
from models.status import TaskStatus
from models.task import Task, TaskID, TaskResult


@dataclass
class Workflow:
    graph: Graph
    tasks: list[Task]


@dataclass
class WorkflowResult:
    results: list[TaskResult]
    statuses: dict[TaskID, TaskStatus]
