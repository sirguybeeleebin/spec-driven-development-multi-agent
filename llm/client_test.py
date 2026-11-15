from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import llm.client as llm_module
from llm.client import LLMClient


@pytest.fixture
def client() -> Mock:
    return Mock()


@pytest.fixture
def response_parsers() -> list[Mock]:
    return []


@pytest.fixture
def llm_client(
    client: Mock,
    response_parsers: list[Mock],
) -> LLMClient:
    return LLMClient(
        client=client,
        model="test-model",
        opts={"temperature": 0.2},
        response_parsers=response_parsers,
    )


def make_response(
    *,
    message: dict[str, object] | None = None,
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
) -> Mock:
    response = Mock()

    response.choices = [
        SimpleNamespace(
            message=Mock(
                model_dump=Mock(
                    return_value=message
                    or {
                        "role": "assistant",
                        "content": "Hello",
                    },
                ),
            ),
        ),
    ]

    response.usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    return response


def test_complete_calls_openai_with_tools(
    llm_client: LLMClient,
    client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "example",
            },
        },
    ]

    client.chat.completions.create.return_value = make_response()

    monkeypatch.setattr(
        llm_module,
        "perf_counter",
        Mock(side_effect=[10.0, 12.5]),
    )

    messages = [
        {
            "role": "user",
            "content": "Hello",
        },
    ]

    result, metrics = llm_client.complete(
        messages,
        tools=tools,
    )

    client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        parallel_tool_calls=True,
        temperature=0.2,
    )

    assert result == {
        "role": "assistant",
        "content": "Hello",
    }

    assert metrics == {
        "duration_sec": 2.5,
        "request_tokens": 10,
        "response_tokens": 5,
    }


def test_complete_without_tools_disables_tool_choice(
    llm_client: LLMClient,
    client: Mock,
) -> None:
    client.chat.completions.create.return_value = make_response()

    messages = [
        {
            "role": "user",
            "content": "Hello",
        },
    ]

    result, metrics = llm_client.complete(messages)

    client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=messages,
        tools=None,
        tool_choice="none",
        parallel_tool_calls=True,
        temperature=0.2,
    )

    assert result["content"] == "Hello"
    assert metrics["request_tokens"] == 10
    assert metrics["response_tokens"] == 5


def test_complete_handles_missing_usage(
    llm_client: LLMClient,
    client: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response()
    response.usage = None

    client.chat.completions.create.return_value = response

    monkeypatch.setattr(
        llm_module,
        "perf_counter",
        Mock(side_effect=[1.0, 3.0]),
    )

    _, metrics = llm_client.complete([])

    assert metrics == {
        "duration_sec": 2.0,
        "request_tokens": 0,
        "response_tokens": 0,
    }


def test_complete_applies_response_parsers_in_order(
    client: Mock,
) -> None:
    first_parser = Mock()
    second_parser = Mock()

    first_result = {
        "role": "assistant",
        "content": "Parsed by first",
    }

    second_result = {
        "role": "assistant",
        "content": "Parsed by second",
    }

    first_parser.parse.return_value = first_result
    second_parser.parse.return_value = second_result

    llm_client = LLMClient(
        client=client,
        model="test-model",
        opts={},
        response_parsers=[
            first_parser,
            second_parser,
        ],
    )

    client.chat.completions.create.return_value = make_response()

    result, _ = llm_client.complete([])

    first_parser.parse.assert_called_once_with(
        {
            "role": "assistant",
            "content": "Hello",
        },
    )

    second_parser.parse.assert_called_once_with(first_result)

    assert result == second_result


def test_complete_returns_assistant_message_without_none_fields(
    llm_client: LLMClient,
    client: Mock,
) -> None:
    response = make_response(
        message={
            "role": "assistant",
            "content": "Hello",
        },
    )

    client.chat.completions.create.return_value = response

    result, _ = llm_client.complete([])

    response.choices[0].message.model_dump.assert_called_once_with(
        exclude_none=True,
    )

    assert result == {
        "role": "assistant",
        "content": "Hello",
    }


def test_complete_passes_opts_to_openai(
    client: Mock,
) -> None:
    llm_client = LLMClient(
        client=client,
        model="custom-model",
        opts={
            "temperature": 0.7,
            "max_tokens": 100,
        },
        response_parsers=[],
    )

    client.chat.completions.create.return_value = make_response()

    llm_client.complete([])

    client.chat.completions.create.assert_called_once_with(
        model="custom-model",
        messages=[],
        tools=None,
        tool_choice="none",
        parallel_tool_calls=True,
        temperature=0.7,
        max_tokens=100,
    )
