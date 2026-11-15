# factories/task.py

from __future__ import annotations

from pathlib import Path

from config import Config
from factories.agent import make_agent_runner
from fsms import TaskFSM
from models import Agents, Task
from parsers import parse_task
from runners import TaskRunner


def make_task(config: Config, task_id: str) -> Task:
    task_path = Path(config.root) / "tasks" / f"{task_id}.md"
    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")

    content = task_path.read_text(encoding="utf-8")
    return parse_task(content, constitution=config.constitution)


def make_task_runner(
    config: Config,
) -> TaskRunner:
    return TaskRunner(
        task_fsm=TaskFSM(),
        researcher=make_agent_runner(config, Agents.RESEARCHER),
        implementer=make_agent_runner(config, Agents.IMPLEMENTER),
        tester=make_agent_runner(config, Agents.TESTER),
        fixer=make_agent_runner(config, Agents.FIXER),
    )
