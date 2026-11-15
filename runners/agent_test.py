from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from models import Message, Role, State, ToolCall
from runners.agent import AgentRunner


class FakeLLM:
    def __init__(self, replies: list[Message]) -> None:
        self._replies = iter(replies)
        self.calls = []

    def complete(
        self,
        messages: list[Message],
        tools: list,
    ) -> tuple[Message, list]:
        self.calls.append((list(messages), list(tools)))
        return next(self._replies), []


class FakeTool:
    def __init__(
        self,
        name: str = "test_tool",
        result: dict | None = None,
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self.result = result or {"ok": True}
        self.error = error
        self.calls = []

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {"name": self.name},
        }

    def execute(self, args: dict) -> dict:
        self.calls.append(args)

        if self.error:
            raise self.error

        return self.result


class FakePromptProvider:
    system = "System prompt"
    final_user = "Return final response"

    def __init__(self) -> None:
        self.format_user_calls = []
        self.parse_final_response_calls = []

    def format_user(self, state: State, skills: list) -> str:
        self.format_user_calls.append((state, skills))
        return "User prompt"

    def parse_final_response(self, final_response: str) -> dict:
        self.parse_final_response_calls.append(final_response)
        return {"result": final_response}


def make_message(
    *,
    role: Role = Role.ASSISTANT,
    content: str = "",
    tool_calls: list[ToolCall] | None = None,
    tool_call_id: str | None = None,
) -> Message:
    return Message(
        role=role,
        content=content,
        tool_calls=tool_calls or [],
        tool_call_id=tool_call_id,
    )


def make_tool_call(
    *,
    id: str = "call_1",
    name: str = "test_tool",
    arguments: dict | None = None,
) -> ToolCall:
    return ToolCall(
        id=id,
        name=name,
        arguments=arguments or {},
    )


def make_agent_runner(
    *,
    replies: list[Message],
    tools: list | None = None,
    guardrails: list | None = None,
    max_iterations: int = 5,
) -> tuple[AgentRunner, FakeLLM, FakePromptProvider]:
    llm = FakeLLM(replies)
    agent_fsm = Mock()
    prompt_provider = FakePromptProvider()

    agent = AgentRunner(
        llm=llm,
        agent_fsm=agent_fsm,
        guardrails=guardrails or [],
        prompt_provider=prompt_provider,
        skills=[],
        tools=tools or [],
        max_iterations=max_iterations,
    )

    return agent, llm, prompt_provider


def make_state() -> State:
    return Mock()


def test_builds_initial_session() -> None:
    main_reply = make_message(content="Finished")
    final_reply = make_message(content='{"result": "done"}')

    agent, llm, prompt_provider = make_agent_runner(
        replies=[main_reply, final_reply],
    )
    state = make_state()

    agent.run(state=state)

    assert llm.calls[0][0] == [
        make_message(role=Role.SYSTEM, content="System prompt"),
        make_message(role=Role.USER, content="User prompt"),
    ]
    assert prompt_provider.format_user_calls == [(state, [])]


def test_calls_llm_with_configured_tools() -> None:
    tool = FakeTool()
    main_reply = make_message(content="Finished")
    final_reply = make_message(content="Done")

    agent, llm, _ = make_agent_runner(
        replies=[main_reply, final_reply],
        tools=[tool],
    )

    agent.run(state=make_state())

    assert llm.calls[0][1] == [tool]


def test_executes_tool_and_appends_result() -> None:
    tool_call = make_tool_call(arguments={"value": 42})
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")
    tool = FakeTool(result={"ok": True, "value": 42})

    agent, llm, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
        max_iterations=1,
    )

    result = agent.run(state=make_state())

    assert tool.calls == [{"value": 42}]
    assert llm.calls[1][0][-2:] == [
        make_message(
            role=Role.TOOL,
            content='{"ok": true, "value": 42}',
            tool_call_id="call_1",
        ),
        make_message(
            role=Role.USER,
            content="Return final response",
        ),
    ]
    assert result.response == {"result": "Done"}


def test_executes_multiple_tool_calls() -> None:
    first_call = make_tool_call(
        id="call_1",
        name="first_tool",
        arguments={"value": 1},
    )
    second_call = make_tool_call(
        id="call_2",
        name="second_tool",
        arguments={"value": 2},
    )

    first_tool = FakeTool("first_tool", {"result": 1})
    second_tool = FakeTool("second_tool", {"result": 2})

    assistant_reply = make_message(
        tool_calls=[first_call, second_call],
    )
    final_reply = make_message(content="Done")

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[first_tool, second_tool],
        max_iterations=1,
    )

    result = agent.run(state=make_state())

    assert first_tool.calls == [{"value": 1}]
    assert second_tool.calls == [{"value": 2}]

    tool_messages = [
        message for message in result.messages if message.role == Role.TOOL
    ]

    assert len(tool_messages) == 2
    assert json.loads(tool_messages[0].content) == {"result": 1}
    assert json.loads(tool_messages[1].content) == {"result": 2}


def test_runs_guardrails_before_tool_execution() -> None:
    tool_call = make_tool_call(arguments={"value": 42})
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")

    tool = FakeTool()
    guardrail = Mock()
    state = make_state()

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
        guardrails=[guardrail],
        max_iterations=1,
    )

    agent.run(state=state)

    guardrail.check.assert_called_once_with(
        state=state,
        tool_call=tool_call,
    )
    assert tool.calls == [{"value": 42}]


def test_runs_all_guardrails_before_tool_execution() -> None:
    tool_call = make_tool_call()
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")

    tool = FakeTool()
    first_guardrail = Mock()
    second_guardrail = Mock()
    state = make_state()

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
        guardrails=[first_guardrail, second_guardrail],
        max_iterations=1,
    )

    agent.run(state=state)

    first_guardrail.check.assert_called_once_with(
        state=state,
        tool_call=tool_call,
    )
    second_guardrail.check.assert_called_once_with(
        state=state,
        tool_call=tool_call,
    )
    assert tool.calls == [{}]


def test_does_not_execute_tool_when_guardrail_rejects_call() -> None:
    tool_call = make_tool_call()
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")

    tool = FakeTool()
    guardrail = Mock()
    guardrail.check.side_effect = ValueError("Write rejected")

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
        guardrails=[guardrail],
        max_iterations=1,
    )

    result = agent.run(state=make_state())

    assert tool.calls == []

    tool_message = next(
        message for message in result.messages if message.role == Role.TOOL
    )
    tool_result = json.loads(tool_message.content)

    assert tool_result["ok"] is False
    assert tool_result["error"] == "ValueError"
    assert tool_result["message"] == "Write rejected"


def test_stops_running_guardrails_after_first_rejection() -> None:
    tool_call = make_tool_call()
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")

    first_guardrail = Mock()
    first_guardrail.check.side_effect = ValueError("Rejected")
    second_guardrail = Mock()

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[FakeTool()],
        guardrails=[first_guardrail, second_guardrail],
        max_iterations=1,
    )

    agent.run(state=make_state())

    first_guardrail.check.assert_called_once()
    second_guardrail.check.assert_not_called()


def test_returns_tool_error_when_execution_fails() -> None:
    tool_call = make_tool_call()
    assistant_reply = make_message(tool_calls=[tool_call])
    final_reply = make_message(content="Done")

    tool = FakeTool(error=RuntimeError("Execution failed"))

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
        max_iterations=1,
    )

    result = agent.run(state=make_state())

    tool_message = next(
        message for message in result.messages if message.role == Role.TOOL
    )
    tool_result = json.loads(tool_message.content)

    assert tool_result["ok"] is False
    assert tool_result["error"] == "RuntimeError"
    assert tool_result["message"] == "Execution failed"


def test_stops_when_llm_returns_no_tool_calls() -> None:
    assistant_reply = make_message(content="Finished")
    final_reply = make_message(content="Done")

    agent, llm, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
    )

    result = agent.run(state=make_state())

    assert len(llm.calls) == 2
    assert result.response == {"result": "Done"}


def test_stops_after_max_iterations() -> None:
    tool_call = make_tool_call()
    replies = [
        make_message(tool_calls=[tool_call]),
        make_message(tool_calls=[tool_call]),
        make_message(content="Done"),
    ]

    tool = FakeTool()

    agent, llm, _ = make_agent_runner(
        replies=replies,
        tools=[tool],
        max_iterations=2,
    )

    result = agent.run(state=make_state())

    assert len(llm.calls) == 3
    assert len(tool.calls) == 2
    assert result.response == {"result": "Done"}


def test_calls_finalizer_exactly_once_without_tools() -> None:
    assistant_reply = make_message(content="Finished")
    final_reply = make_message(content="Done")

    tool = FakeTool()

    agent, llm, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
    )

    agent.run(state=make_state())

    assert len(llm.calls) == 2
    assert llm.calls[1][1] == []
    assert llm.calls[1][0][-1] == make_message(
        role=Role.USER,
        content="Return final response",
    )


def test_finalizer_does_not_execute_tool_calls() -> None:
    assistant_reply = make_message(content="Finished")
    final_tool_call = make_tool_call()
    final_reply = make_message(
        content="Done",
        tool_calls=[final_tool_call],
    )

    tool = FakeTool()

    agent, llm, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
        tools=[tool],
    )

    result = agent.run(state=make_state())

    assert tool.calls == []
    assert len(llm.calls) == 2
    assert result.response == {"result": "Done"}


def test_aggregates_metrics_from_all_llm_calls() -> None:
    first_metrics = [object()]
    final_metrics = [object()]

    class MetricsLLM:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages: list, tools: list) -> tuple:
            self.calls += 1

            if self.calls == 1:
                return make_message(content="Finished"), first_metrics

            return make_message(content="Done"), final_metrics

    llm = MetricsLLM()

    agent = AgentRunner(
        llm=llm,
        agent_fsm=Mock(),
        guardrails=[],
        prompt_provider=FakePromptProvider(),
        skills=[],
        tools=[],
        max_iterations=5,
    )

    result = agent.run(state=make_state())

    assert result.metrics == [first_metrics, final_metrics]


def test_parses_final_response() -> None:
    main_reply = make_message(content="Finished")
    final_reply = make_message(content='{"status": "passed"}')

    agent, _, prompt_provider = make_agent_runner(
        replies=[main_reply, final_reply],
    )

    result = agent.run(state=make_state())

    assert prompt_provider.parse_final_response_calls == ['{"status": "passed"}']
    assert result.response == {"result": '{"status": "passed"}'}


def test_returns_complete_message_session() -> None:
    assistant_reply = make_message(content="Finished")
    final_reply = make_message(content="Done")

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply, final_reply],
    )

    result = agent.run(state=make_state())

    assert result.messages == [
        make_message(role=Role.SYSTEM, content="System prompt"),
        make_message(role=Role.USER, content="User prompt"),
        assistant_reply,
        make_message(
            role=Role.USER,
            content="Return final response",
        ),
        final_reply,
    ]


def test_unknown_tool_raises_key_error() -> None:
    tool_call = make_tool_call(name="unknown_tool")
    assistant_reply = make_message(tool_calls=[tool_call])

    agent, _, _ = make_agent_runner(
        replies=[assistant_reply],
        tools=[],
    )

    with pytest.raises(KeyError, match="unknown_tool"):
        agent.run(state=make_state())


def test_zero_max_iterations_still_calls_finalizer() -> None:
    final_reply = make_message(content="Done")

    agent, llm, _ = make_agent_runner(
        replies=[final_reply],
        max_iterations=0,
    )

    result = agent.run(state=make_state())

    assert len(llm.calls) == 1
    assert llm.calls[0][1] == []
    assert result.response == {"result": "Done"}


def test_resets_and_marks_agent_running_before_execution() -> None:
    agent_fsm = Mock()
    llm = FakeLLM(
        [
            make_message(content="Finished"),
            make_message(content="Done"),
        ]
    )

    agent = AgentRunner(
        llm=llm,
        agent_fsm=agent_fsm,
        guardrails=[],
        prompt_provider=FakePromptProvider(),
        skills=[],
        tools=[],
        max_iterations=5,
    )

    agent.run(state=make_state())

    assert [call.args for call in agent_fsm.method_calls] == [
        (),
        (),
        (),
    ]
    assert [call[0] for call in agent_fsm.method_calls] == [
        "reset",
        "mark_running",
        "mark_success",
    ]


def test_marks_agent_error_when_execution_fails() -> None:
    agent_fsm = Mock()
    llm = FakeLLM([])

    agent = AgentRunner(
        llm=llm,
        agent_fsm=agent_fsm,
        guardrails=[],
        prompt_provider=FakePromptProvider(),
        skills=[],
        tools=[],
        max_iterations=5,
    )

    with pytest.raises(StopIteration):
        agent.run(state=make_state())

    agent_fsm.reset.assert_called_once()
    agent_fsm.mark_running.assert_called_once()
    agent_fsm.mark_error.assert_called_once()
    agent_fsm.mark_success.assert_not_called()
