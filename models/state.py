from __future__ import annotations

from dataclasses import dataclass

from models.agent import Agents
from models.result import AgentResult
from models.task import Gherkin, Interface, Task


@dataclass
class State:
    constitution: str

    task: Task

    results: dict[Agents, list[AgentResult]]

    current_interface: Interface | None = None
    current_gherkin: Gherkin | None = None
