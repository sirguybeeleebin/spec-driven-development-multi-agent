from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

from agent import Agent
from fsms import AgentFSM, TaskFSM, WorkflowFSM
from guardrails import BashGuardrail, WorkspaceGuardrail
from ipc.handlers import TaskHandler, TaskSectionHandler, WorkflowHandler
from ipc.server import IPCServer
from llm import LLMClient
from llm.responseparsers import OpenAIResponseParser, QwenResponseParser
from models import Agents
from promptproviders import (
    FixerPromptProvider,
    ImplementerPromptProvider,
    ResearcherPromptProvider,
    TesterPromptProvider,
)
from prompts import (
    FIXER_FINAL,
    FIXER_SYSTEM,
    FIXER_USER_TEMPLATE,
    IMPLEMENTER_FINAL,
    IMPLEMENTER_SYSTEM,
    IMPLEMENTER_USER_TEMPLATE,
    RESEARCHER_FINAL,
    RESEARCHER_SYSTEM,
    RESEARCHER_USER_TEMPLATE,
    TESTER_FINAL,
    TESTER_SYSTEM,
    TESTER_USER_TEMPLATE,
)
from repositories import TaskSectionRepository
from runners import TaskRunner, TaskSectionRunner, WorkflowRunner
from tools import AppendTool, BashTool, PatchTool, ReadTool


def run_daemon_app(
    root: Path,
    config: dict,
    skills: list[dict],
    socket_path: Path,
) -> None:
    agents_config = config["agents"]

    llms = {
        agent: LLMClient(
            client=OpenAI(
                base_url=agents_config[agent]["provider"]["base_url"],
                api_key=agents_config[agent]["provider"]["api_key"],
            ),
            model=agents_config[agent]["provider"]["model"],
            opts={
                "temperature": agents_config[agent]["provider"]["temperature"],
            },
            response_parsers=[OpenAIResponseParser(), QwenResponseParser()],
        )
        for agent in (
            Agents.RESEARCHER,
            Agents.IMPLEMENTER,
            Agents.TESTER,
            Agents.FIXER,
            Agents.TASK_BUILDER,
        )
    }

    prompt_providers = {
        Agents.RESEARCHER: ResearcherPromptProvider(
            system_template=RESEARCHER_SYSTEM,
            user_template=RESEARCHER_USER_TEMPLATE,
            final_prompt=RESEARCHER_FINAL,
        ),
        Agents.IMPLEMENTER: ImplementerPromptProvider(
            system_template=IMPLEMENTER_SYSTEM,
            user_template=IMPLEMENTER_USER_TEMPLATE,
            final_prompt=IMPLEMENTER_FINAL,
        ),
        Agents.TESTER: TesterPromptProvider(
            system_template=TESTER_SYSTEM,
            user_template=TESTER_USER_TEMPLATE,
            final_prompt=TESTER_FINAL,
        ),
        Agents.FIXER: FixerPromptProvider(
            system_template=FIXER_SYSTEM,
            user_template=FIXER_USER_TEMPLATE,
            final_prompt=FIXER_FINAL,
        ),
    }

    guardrails = {
        agent: [
            BashGuardrail(),
            WorkspaceGuardrail(),
        ]
        for agent in (
            Agents.RESEARCHER,
            Agents.IMPLEMENTER,
            Agents.TESTER,
            Agents.FIXER,
        )
    }

    agent_fsms = {
        agent: AgentFSM()
        for agent in (
            Agents.RESEARCHER,
            Agents.IMPLEMENTER,
            Agents.TESTER,
            Agents.FIXER,
        )
    }

    tools = {
        tool.name: tool
        for tool in (
            BashTool(root=root),
            ReadTool(root=root),
            PatchTool(root=root),
            AppendTool(root=root),
        )
    }

    agents = {
        agent: Agent(
            llm=llms[agent],
            agent_fsm=agent_fsms[agent],
            prompt_provider=prompt_providers[agent],
            tools=[
                tools[name]
                for name in agents_config[agent]["tools"]
            ],
            guardrails=guardrails[agent],
            max_iterations=agents_config[agent]["max_iterations"],
        )
        for agent in (
            Agents.RESEARCHER,
            Agents.IMPLEMENTER,
            Agents.TESTER,
            Agents.FIXER,
        )
    }

    task_fsm = TaskFSM()
    workflow_fsm = WorkflowFSM()

    task_runner = TaskRunner(
        task_fsm=task_fsm,
        researcher=agents[Agents.RESEARCHER],
        implementer=agents[Agents.IMPLEMENTER],
        tester=agents[Agents.TESTER],
        fixer=agents[Agents.FIXER],
    )

    workflow_runner = WorkflowRunner(
        workflow_fsm=workflow_fsm,
        task_runner=task_runner,
    )

    task_section_repository = TaskSectionRepository(root=root)

    task_section_runner = TaskSectionRunner(
        client=llms[Agents.TASK_BUILDER],
        task_section_repository=task_section_repository,
    )

    task_handler = TaskHandler(
        task_runner=task_runner,
        skills=skills,
    )
    workflow_handler = WorkflowHandler(
        workflow_runner=workflow_runner,
        skills=skills,
    )
    task_section_handler = TaskSectionHandler(runner=task_section_runner)

    executor = ThreadPoolExecutor(max_workers=config["max_workers"])

    server = IPCServer(
        socket_path=socket_path,
        task_handler=task_handler,
        workflow_handler=workflow_handler,
        task_section_handler=task_section_handler,
        executor=executor,
    )

    try:
        server.start()
    finally:
        executor.shutdown(wait=True)