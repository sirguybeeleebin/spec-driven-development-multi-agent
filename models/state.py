from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from models.agent import AgentResult, Agents
from models.task import Gherkin, Interface, Task


@dataclass
class State:
    task: Task

    current_interface: Interface | None = None
    current_gherkin: Gherkin | None = None
    current_target_file: Path | None = None
    current_target_test_file: Path | None = None

    agent_results: dict[Agents, list[AgentResult]] = field(
        default_factory=lambda: {agent: [] for agent in Agents}
    )
