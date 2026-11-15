from __future__ import annotations

from dataclasses import dataclass

from models.task import TaskID


@dataclass
class Node:
    task_id: TaskID


@dataclass
class Edge:
    source: Node
    target: Node


@dataclass
class Graph:
    nodes: list[Node]
    edges: list[Edge]
