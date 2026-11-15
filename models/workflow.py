# models/workflow.py

from __future__ import annotations

from dataclasses import dataclass

from models.graph import Graph
from models.task import Task


@dataclass
class Workflow:
    graph: Graph
    tasks: list[Task]
