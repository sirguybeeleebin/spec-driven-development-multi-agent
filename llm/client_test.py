from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from llm.client import LLMClient
from models import Message, MetricName, Role, ToolCall


@pytest.fixture
def openai_client() -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = []
    return client


@pytest.fixture
def client(openai_client: MagicMock) -> LLMClient:
    return LLMClient(
        client=openai_client,
        model="test-model",
        opts={"temperature": 0},
    )


def make_chunk(
    *,
    content: str | None = None,
    tool_calls: list | None = None,
    usage=None,
    choices: list | None = None,
) -> SimpleNamespace:
    if choices is None:
        delta = SimpleNamespace(
            content=content,
            tool_calls=tool_calls,
        )
        choices = [
            SimpleNamespace(delta=delta),
        ]

    return SimpleNamespace(
        choices=choices,
        usage=usage,
    )


def make_tool_call_delta(
    *,
    index: int,
    id: str | None = None,
    name: str | None = None,
    arguments: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        index=index,
        id=id,
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        ),
    )


def make_usage(
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
) -> SimpleNamespace:
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


class DummyTool:
    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "dummy",
                "description": "Dummy tool.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        }

    def execute(self, args: dict) -> dict:
        return {"ok": True}


def test_init_stores_configuration(
    openai_client: MagicMock,
) -> None:
    opts = {"temperature": 0.5}
    client = LLMClient(
        client=openai_client,
        model="test-model",
        opts=opts,
    )

    assert client._client is openai_client
    assert client._model == "test-model"
    assert client._opts == opts
    assert client._opts is not opts
    assert client._printed_tool_ids == set()
    assert client._system_prompt_printed is False


def test_complete_sends_messages_and_configuration(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    messages = [
        Message(role=Role.USER, content="Hello"),
    ]

    client.complete(messages, [])

    openai_client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
        stream=True,
        stream_options={"include_usage": True},
        temperature=0,
    )


def test_complete_includes_tool_schemas(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [DummyTool()],
    )

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert kwargs["tools"] == [DummyTool().get_openai_schema()]


def test_complete_omits_tools_when_empty(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    client.complete(
        [Message(role=Role.USER, content="Hello")],
        [],
    )

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert "tools" not in kwargs


def test_complete_returns_assistant_content(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(content="Hello"),
        make_chunk(content=", world!"),
    ]

    reply, metrics = client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    assert reply.role is Role.ASSISTANT
    assert reply.content == "Hello, world!"
    assert reply.tool_calls == []
    assert len(metrics) == 1
    assert metrics[0].name is MetricName.DURATION_SEC


def test_complete_returns_empty_content(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    reply, metrics = client.complete(
        [Message(role=Role.USER, content="Hello")],
        [],
    )

    assert reply.role is Role.ASSISTANT
    assert reply.content == ""
    assert reply.tool_calls == []
    assert len(metrics) == 1
    assert metrics[0].name is MetricName.DURATION_SEC


def test_complete_returns_usage_metrics(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(content="Hello"),
        make_chunk(usage=make_usage(100, 25), choices=[]),
    ]

    _, metrics = client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    assert [metric.name for metric in metrics] == [
        MetricName.DURATION_SEC,
        MetricName.REQUEST_TOKENS,
        MetricName.RESPONSE_TOKENS,
    ]
    assert metrics[1].value == 100.0
    assert metrics[2].value == 25.0


def test_complete_handles_missing_usage_values(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    usage = SimpleNamespace(
        prompt_tokens=None,
        completion_tokens=None,
    )
    openai_client.chat.completions.create.return_value = [
        make_chunk(usage=usage, choices=[]),
    ]

    _, metrics = client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    assert metrics[1].value == 0.0
    assert metrics[2].value == 0.0


def test_complete_serializes_assistant_tool_calls(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    messages = [
        Message(
            role=Role.ASSISTANT,
            content="",
            tool_calls=[
                ToolCall(
                    id="call_123",
                    name="dummy",
                    arguments={"value": 42},
                )
            ],
        )
    ]

    client.complete(messages, [])

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert kwargs["messages"] == [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "dummy",
                        "arguments": '{"value": 42}',
                    },
                }
            ],
        }
    ]


def test_complete_serializes_tool_message(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    message = Message(
        role=Role.TOOL,
        content='{"ok": true}',
        tool_call_id="call_123",
    )

    client.complete([message], [])

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert kwargs["messages"] == [
        {
            "role": "tool",
            "content": '{"ok": true}',
            "tool_call_id": "call_123",
        }
    ]
    assert "[tool] call_123:" in capsys.readouterr().out


def test_complete_prints_tool_message_only_once(
    client: LLMClient,
    capsys: pytest.CaptureFixture[str],
) -> None:
    message = Message(
        role=Role.TOOL,
        content="Tool result",
        tool_call_id="call_123",
    )

    client.complete([message], [])
    client.complete([message], [])

    output = capsys.readouterr().out

    assert output.count("[tool] call_123:") == 1
    assert output.count("Tool result") == 1


def test_complete_parses_streamed_tool_call(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="dummy",
                    arguments='{"value":',
                )
            ]
        ),
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    arguments="42}",
                )
            ]
        ),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [DummyTool()],
    )

    assert reply.content == ""
    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].id == "call_123"
    assert reply.tool_calls[0].name == "dummy"
    assert reply.tool_calls[0].arguments == {"value": 42}


def test_complete_parses_multiple_streamed_tool_calls(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=1,
                    id="call_2",
                    name="second",
                    arguments='{"value": 2}',
                ),
                make_tool_call_delta(
                    index=0,
                    id="call_1",
                    name="first",
                    arguments='{"value": 1}',
                ),
            ]
        ),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run tools")],
        [DummyTool()],
    )

    assert [call.id for call in reply.tool_calls] == [
        "call_1",
        "call_2",
    ]
    assert [call.name for call in reply.tool_calls] == [
        "first",
        "second",
    ]
    assert [call.arguments for call in reply.tool_calls] == [
        {"value": 1},
        {"value": 2},
    ]


@pytest.mark.parametrize(
    "raw_arguments",
    [
        "{invalid",
        "",
    ],
)
def test_complete_handles_invalid_tool_arguments(
    client: LLMClient,
    openai_client: MagicMock,
    raw_arguments: str,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="dummy",
                    arguments=raw_arguments,
                )
            ]
        ),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [],
    )

    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].arguments == {}


def test_complete_generates_id_when_streamed_id_is_missing(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    name="dummy",
                    arguments="{}",
                )
            ]
        ),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [],
    )

    assert reply.tool_calls[0].id.startswith("stream_")
    assert len(reply.tool_calls[0].id) == len("stream_") + 24


def test_complete_parses_xml_tool_call(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    content = (
        "Before call\n"
        "<function=dummy>"
        "<parameter=value>42</parameter>"
        '<parameter=name>"example"</parameter>'
        "</function>\n"
        "After call"
    )
    openai_client.chat.completions.create.return_value = [
        make_chunk(content=content),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [DummyTool()],
    )

    assert reply.content == "Before call\n\nAfter call"
    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].name == "dummy"
    assert reply.tool_calls[0].arguments == {
        "value": 42,
        "name": "example",
    }
    assert reply.tool_calls[0].id.startswith("xml_")


def test_complete_keeps_xml_parameter_as_string_when_not_json(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    content = "<function=dummy><parameter=value>hello world</parameter></function>"
    openai_client.chat.completions.create.return_value = [
        make_chunk(content=content),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [],
    )

    assert reply.tool_calls[0].arguments == {
        "value": "hello world",
    }


def test_complete_does_not_parse_xml_when_streamed_tool_calls_exist(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            content="<function=xml_tool></function>",
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="dummy",
                    arguments="{}",
                )
            ],
        ),
    ]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [],
    )

    assert len(reply.tool_calls) == 1
    assert reply.tool_calls[0].name == "dummy"
    assert "<function=xml_tool>" in reply.content


def test_complete_prints_tool_call_details(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="dummy",
                    arguments='{"value": 42}',
                )
            ],
        ),
    ]

    client.complete(
        [Message(role=Role.USER, content="Run dummy")],
        [],
    )

    output = capsys.readouterr().out

    assert "[llm] tool_call start: dummy" in output
    assert '[llm] tool_call: dummy args={"value": 42}' in output


def test_complete_logs_load_skill_call(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="load_skill",
                    arguments='{"name": "python"}',
                )
            ],
        ),
    ]

    client.complete(
        [Message(role=Role.USER, content="Load skill")],
        [],
    )

    output = capsys.readouterr().out

    assert "[skill] load_skill name=python" in output


def test_complete_logs_bash_skill_load(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    command = "cat skills/python/SKILL.md"
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="bash",
                    arguments=json.dumps({"command": command}),
                )
            ],
        ),
    ]

    client.complete(
        [Message(role=Role.USER, content="Load skill")],
        [],
    )

    output = capsys.readouterr().out

    assert f"[skill] bash load: {command}" in output


def test_complete_does_not_log_bash_skill_load_for_non_string_command(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(
            tool_calls=[
                make_tool_call_delta(
                    index=0,
                    id="call_123",
                    name="bash",
                    arguments='{"command": 123}',
                )
            ],
        ),
    ]

    client.complete(
        [Message(role=Role.USER, content="Run command")],
        [],
    )

    output = capsys.readouterr().out

    assert "[skill] bash load:" not in output


def test_complete_ignores_chunks_without_choices(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(content="Hello"),
        make_chunk(
            choices=[],
            usage=make_usage(),
        ),
    ]

    reply, metrics = client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    assert reply.content == "Hello"
    assert len(metrics) == 3


def test_complete_ignores_chunks_with_none_delta(
    client: LLMClient,
    openai_client: MagicMock,
) -> None:
    chunk = make_chunk(
        choices=[
            SimpleNamespace(delta=None),
        ]
    )
    openai_client.chat.completions.create.return_value = [chunk]

    reply, _ = client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    assert reply.content == ""
    assert reply.tool_calls == []


def test_complete_prints_streamed_content(
    client: LLMClient,
    openai_client: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openai_client.chat.completions.create.return_value = [
        make_chunk(content="Hello"),
        make_chunk(content=" world"),
    ]

    client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    output = capsys.readouterr().out

    assert "[llm] content:" in output
    assert "Hello world" in output


def test_complete_passes_options_to_api(
    openai_client: MagicMock,
) -> None:
    client = LLMClient(
        client=openai_client,
        model="custom-model",
        opts={
            "temperature": 0.7,
            "max_tokens": 100,
        },
    )

    client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert kwargs["model"] == "custom-model"
    assert kwargs["temperature"] == 0.7
    assert kwargs["max_tokens"] == 100
    assert kwargs["stream"] is True
    assert kwargs["stream_options"] == {"include_usage": True}


def test_complete_options_can_override_default_kwargs(
    openai_client: MagicMock,
) -> None:
    client = LLMClient(
        client=openai_client,
        model="custom-model",
        opts={"stream": False},
    )

    client.complete(
        [Message(role=Role.USER, content="Hi")],
        [],
    )

    kwargs = openai_client.chat.completions.create.call_args.kwargs

    assert kwargs["stream"] is False
