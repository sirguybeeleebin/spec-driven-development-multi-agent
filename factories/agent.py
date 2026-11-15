from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import Config
from fsms import AgentFSM
from guardrails import BashGuardrail, FQNWriteGuardrail, WorkspaceGuardrail
from llm import LLMClient
from models import Agents, Skill, Tools
from parsers import parse_skill
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
from runners import AgentRunner
from tools import (
    AppendTool,
    BashTool,
    LoadSkillTool,
    PatchTool,
    ReadTool,
)

AgentConfig = Mapping[str, Any]


def make_agent_runner(
    config: Config,
    agent: Agents,
) -> AgentRunner:
    if not isinstance(agent, Agents):
        raise ValueError(f"unsupported agent: {agent!r}")

    agent_cfg = dict(config.agent_configs[agent])
    root = Path(config.root)
    agent_cfg["root"] = root

    raw_skill_names = list(agent_cfg.get("skills", []))
    skills: list[Skill] = []

    for skill_name in raw_skill_names:
        skill_path = root / "skills" / skill_name / "SKILL.md"

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        skills.append(parse_skill(content))

    if agent is Agents.RESEARCHER:
        prompt_provider = ResearcherPromptProvider(
            system_template=RESEARCHER_SYSTEM,
            user_template=RESEARCHER_USER_TEMPLATE,
            final_prompt=RESEARCHER_FINAL,
        )
    elif agent is Agents.IMPLEMENTER:
        prompt_provider = ImplementerPromptProvider(
            system_template=IMPLEMENTER_SYSTEM,
            user_template=IMPLEMENTER_USER_TEMPLATE,
            final_prompt=IMPLEMENTER_FINAL,
        )
    elif agent is Agents.TESTER:
        prompt_provider = TesterPromptProvider(
            system_template=TESTER_SYSTEM,
            user_template=TESTER_USER_TEMPLATE,
            final_prompt=TESTER_FINAL,
        )
    elif agent is Agents.FIXER:
        prompt_provider = FixerPromptProvider(
            system_template=FIXER_SYSTEM,
            user_template=FIXER_USER_TEMPLATE,
            final_prompt=FIXER_FINAL,
        )
    else:
        raise ValueError(f"unsupported agent: {agent!r}")

    tools = []

    for tool_name in agent_cfg.get("tools", []):
        if tool_name == Tools.LOAD_SKILL:
            tools.append(LoadSkillTool(skills=skills))
        elif tool_name == Tools.APPEND:
            tools.append(AppendTool(root=root))
        elif tool_name == Tools.PATCH:
            tools.append(PatchTool(root=root))
        elif tool_name == Tools.READ:
            tools.append(ReadTool(root=root))
        elif tool_name == Tools.BASH:
            tools.append(BashTool(root=root))
        else:
            raise ValueError(f"unknown tool: {tool_name!r}")

    provider_cfg = agent_cfg["provider"]
    opts = {
        "temperature": float(provider_cfg["temperature"]),
    }

    if "max_tokens" in provider_cfg:
        opts["max_tokens"] = int(provider_cfg["max_tokens"])

    llm = LLMClient(
        client=OpenAI(
            base_url=provider_cfg["base_url"],
            api_key=provider_cfg["api_key"] or "none",
        ),
        model=provider_cfg["model"],
        opts=opts,
    )

    return AgentRunner(
        llm=llm,
        agent_fsm=AgentFSM(),
        guardrails=[
            FQNWriteGuardrail(),
            BashGuardrail(),
            WorkspaceGuardrail(),
        ],
        prompt_provider=prompt_provider,
        skills=skills,
        tools=tools,
        max_iterations=int(agent_cfg.get("max_iterations", 15)),
    )
