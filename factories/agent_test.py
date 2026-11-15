from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from factories import agent as agent_factory
from models import Agents, Skill, Tools


@pytest.fixture
def config(tmp_path):
    config = MagicMock()
    config.root = tmp_path
    config.agent_configs = {
        Agents.RESEARCHER: {
            "provider": {
                "base_url": "http://localhost:8080/v1",
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.2,
                "max_tokens": 1000,
            },
            "skills": [],
            "tools": [],
            "max_iterations": 10,
        },
        Agents.IMPLEMENTER: {
            "provider": {
                "base_url": "http://localhost:8080/v1",
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.2,
            },
            "skills": [],
            "tools": [],
            "max_iterations": 12,
        },
        Agents.TESTER: {
            "provider": {
                "base_url": "http://localhost:8080/v1",
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.2,
            },
            "skills": [],
            "tools": [],
        },
        Agents.FIXER: {
            "provider": {
                "base_url": "http://localhost:8080/v1",
                "api_key": "test-key",
                "model": "test-model",
                "temperature": 0.2,
            },
            "skills": [],
            "tools": [],
        },
    }
    return config


@pytest.fixture
def mocks():
    with (
        patch.object(agent_factory, "AgentRunner") as agent_runner,
        patch.object(agent_factory, "AgentFSM") as agent_fsm,
        patch.object(agent_factory, "parse_skill") as parse_skill,
        patch.object(agent_factory, "OpenAI") as openai,
        patch.object(agent_factory, "LLMClient") as llm_client,
        patch.object(agent_factory, "FQNWriteGuardrail") as fqn_guardrail,
        patch.object(agent_factory, "BashGuardrail") as bash_guardrail,
        patch.object(agent_factory, "WorkspaceGuardrail") as workspace_guardrail,
    ):
        agent_runner.return_value = MagicMock(name="agent_runner")
        agent_fsm.return_value = MagicMock(name="agent_fsm")
        parse_skill.return_value = MagicMock(spec=Skill)

        yield {
            "agent_runner": agent_runner,
            "agent_fsm": agent_fsm,
            "parse_skill": parse_skill,
            "openai": openai,
            "llm_client": llm_client,
            "fqn_guardrail": fqn_guardrail,
            "bash_guardrail": bash_guardrail,
            "workspace_guardrail": workspace_guardrail,
        }


@pytest.mark.parametrize(
    ("agent", "provider_class", "system", "user", "final"),
    [
        (
            Agents.RESEARCHER,
            agent_factory.ResearcherPromptProvider,
            agent_factory.RESEARCHER_SYSTEM,
            agent_factory.RESEARCHER_USER_TEMPLATE,
            agent_factory.RESEARCHER_FINAL,
        ),
        (
            Agents.IMPLEMENTER,
            agent_factory.ImplementerPromptProvider,
            agent_factory.IMPLEMENTER_SYSTEM,
            agent_factory.IMPLEMENTER_USER_TEMPLATE,
            agent_factory.IMPLEMENTER_FINAL,
        ),
        (
            Agents.TESTER,
            agent_factory.TesterPromptProvider,
            agent_factory.TESTER_SYSTEM,
            agent_factory.TESTER_USER_TEMPLATE,
            agent_factory.TESTER_FINAL,
        ),
        (
            Agents.FIXER,
            agent_factory.FixerPromptProvider,
            agent_factory.FIXER_SYSTEM,
            agent_factory.FIXER_USER_TEMPLATE,
            agent_factory.FIXER_FINAL,
        ),
    ],
)
def test_make_agent_runner_selects_prompt_provider(
    config,
    mocks,
    agent,
    provider_class,
    system,
    user,
    final,
):
    with patch.object(agent_factory, provider_class.__name__) as provider:
        result = agent_factory.make_agent_runner(config, agent)

    provider.assert_called_once_with(
        system_template=system,
        user_template=user,
        final_prompt=final,
    )

    mocks["agent_fsm"].assert_called_once_with()

    mocks["agent_runner"].assert_called_once_with(
        llm=mocks["llm_client"].return_value,
        agent_fsm=mocks["agent_fsm"].return_value,
        guardrails=[
            mocks["fqn_guardrail"].return_value,
            mocks["bash_guardrail"].return_value,
            mocks["workspace_guardrail"].return_value,
        ],
        prompt_provider=provider.return_value,
        skills=[],
        tools=[],
        max_iterations=config.agent_configs[agent].get("max_iterations", 15),
    )

    assert result is mocks["agent_runner"].return_value


def test_rejects_unsupported_agent(config):
    with pytest.raises(ValueError, match="unsupported agent"):
        agent_factory.make_agent_runner(config, "unknown")


def test_loads_and_parses_skills(config, mocks, tmp_path):
    skill_dir = tmp_path / "skills" / "python"
    skill_dir.mkdir(parents=True)

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Python skill", encoding="utf-8")

    parsed_skill = MagicMock(spec=Skill)
    mocks["parse_skill"].return_value = parsed_skill

    config.agent_configs[Agents.RESEARCHER]["skills"] = ["python"]

    result = agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["parse_skill"].assert_called_once_with("# Python skill")

    runner_kwargs = mocks["agent_runner"].call_args.kwargs
    assert runner_kwargs["skills"] == [parsed_skill]

    assert result is mocks["agent_runner"].return_value


def test_raises_when_skill_file_does_not_exist(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["skills"] = ["missing_skill"]

    with pytest.raises(
        FileNotFoundError,
        match="Skill file not found",
    ):
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["llm_client"].assert_not_called()
    mocks["agent_runner"].assert_not_called()
    mocks["agent_fsm"].assert_not_called()


@pytest.mark.parametrize(
    ("tool_name", "tool_class"),
    [
        (Tools.LOAD_SKILL, agent_factory.LoadSkillTool),
        (Tools.APPEND, agent_factory.AppendTool),
        (Tools.PATCH, agent_factory.PatchTool),
        (Tools.READ, agent_factory.ReadTool),
        (Tools.BASH, agent_factory.BashTool),
    ],
)
def test_creates_configured_tool(
    config,
    mocks,
    tool_name,
    tool_class,
):
    config.agent_configs[Agents.RESEARCHER]["tools"] = [tool_name]

    with patch.object(
        agent_factory,
        tool_class.__name__,
    ) as tool_mock:
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["tools"] == [tool_mock.return_value]

    if tool_name == Tools.LOAD_SKILL:
        tool_mock.assert_called_once_with(skills=[])
    else:
        tool_mock.assert_called_once_with(root=config.root)


def test_creates_multiple_tools_in_configured_order(config, mocks):
    tool_names = [
        Tools.READ,
        Tools.APPEND,
        Tools.BASH,
    ]

    config.agent_configs[Agents.RESEARCHER]["tools"] = tool_names

    with (
        patch.object(agent_factory, "ReadTool") as read_tool,
        patch.object(agent_factory, "AppendTool") as append_tool,
        patch.object(agent_factory, "BashTool") as bash_tool,
    ):
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["tools"] == [
        read_tool.return_value,
        append_tool.return_value,
        bash_tool.return_value,
    ]


def test_rejects_unknown_tool(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["tools"] = ["unknown_tool"]

    with pytest.raises(ValueError, match="unknown tool"):
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["agent_runner"].assert_not_called()
    mocks["llm_client"].assert_not_called()


def test_uses_default_max_iterations(config, mocks):
    del config.agent_configs[Agents.RESEARCHER]["max_iterations"]

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["max_iterations"] == 15


def test_converts_max_iterations_to_int(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["max_iterations"] = "25"

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["max_iterations"] == 25


def test_creates_openai_client(config, mocks):
    provider_cfg = config.agent_configs[Agents.RESEARCHER]["provider"]

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["openai"].assert_called_once_with(
        base_url=provider_cfg["base_url"],
        api_key=provider_cfg["api_key"],
    )


def test_uses_none_as_default_api_key(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["provider"]["api_key"] = ""

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["openai"].assert_called_once_with(
        base_url="http://localhost:8080/v1",
        api_key="none",
    )


def test_creates_llm_client(config, mocks):
    provider_cfg = config.agent_configs[Agents.RESEARCHER]["provider"]

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["llm_client"].assert_called_once_with(
        client=mocks["openai"].return_value,
        model=provider_cfg["model"],
        opts={
            "temperature": 0.2,
            "max_tokens": 1000,
        },
    )


def test_omits_max_tokens_when_not_configured(config, mocks):
    provider_cfg = config.agent_configs[Agents.IMPLEMENTER]["provider"]

    agent_factory.make_agent_runner(config, Agents.IMPLEMENTER)

    mocks["llm_client"].assert_called_once_with(
        client=mocks["openai"].return_value,
        model=provider_cfg["model"],
        opts={"temperature": 0.2},
    )


def test_converts_provider_options_to_expected_types(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["provider"].update(
        {
            "temperature": "0.7",
            "max_tokens": "2000",
        }
    )

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["llm_client"].assert_called_once_with(
        client=mocks["openai"].return_value,
        model="test-model",
        opts={
            "temperature": 0.7,
            "max_tokens": 2000,
        },
    )


def test_passes_guardrails_to_agent(config, mocks):
    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    mocks["fqn_guardrail"].assert_called_once_with()
    mocks["bash_guardrail"].assert_called_once_with()
    mocks["workspace_guardrail"].assert_called_once_with()

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["guardrails"] == [
        mocks["fqn_guardrail"].return_value,
        mocks["bash_guardrail"].return_value,
        mocks["workspace_guardrail"].return_value,
    ]


def test_passes_skills_and_tools_to_agent(config, mocks):
    skill = MagicMock(spec=Skill)
    tool = MagicMock()

    mocks["parse_skill"].return_value = skill

    skill_dir = config.root / "skills" / "python"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Python", encoding="utf-8")

    config.agent_configs[Agents.RESEARCHER]["skills"] = ["python"]

    with patch.object(agent_factory, "ReadTool", return_value=tool):
        config.agent_configs[Agents.RESEARCHER]["tools"] = [Tools.READ]
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    runner_kwargs = mocks["agent_runner"].call_args.kwargs

    assert runner_kwargs["skills"] == [skill]
    assert runner_kwargs["tools"] == [tool]


def test_does_not_modify_original_agent_config(config, mocks):
    original_config = config.agent_configs[Agents.RESEARCHER].copy()

    agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    assert config.agent_configs[Agents.RESEARCHER] == original_config


def test_passes_root_to_configured_tool(config, mocks):
    config.agent_configs[Agents.RESEARCHER]["tools"] = [Tools.APPEND]

    with patch.object(agent_factory, "AppendTool") as append_tool:
        agent_factory.make_agent_runner(config, Agents.RESEARCHER)

    append_tool.assert_called_once_with(root=Path(config.root))
