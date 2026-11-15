# factories/workflow.py

from __future__ import annotations

from pathlib import Path

from config import Config
from factories.task import make_task_runner
from fsms import WorkflowFSM
from models import Task, Workflow
from parsers.graph import parse_graph
from parsers.task import parse_task
from runners import WorkflowRunner


def make_workflow(config: Config, workflow_id: str) -> Workflow:
    workflow_path = Path(config.root) / "workflows" / f"{workflow_id}.md"
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    content = workflow_path.read_text(encoding="utf-8")
    graph = parse_graph(content)

    tasks: list[Task] = []
    for node in graph.nodes:
        task_path = Path(config.root) / "tasks" / f"{node.task_id}.md"
        if not task_path.exists():
            raise FileNotFoundError(
                f"Task file not found for node {node.task_id}: {task_path}"
            )

        task_content = task_path.read_text(encoding="utf-8")
        task = parse_task(task_content, constitution=config.constitution)
        tasks.append(task)

    return Workflow(
        graph=graph,
        tasks=tasks,
    )


def make_workflow_runner(config: Config) -> WorkflowRunner:
    task_runner = make_task_runner(config=config)
    return WorkflowRunner(
        workflow_fsm=WorkflowFSM(),
        task_runner=task_runner,
    )
