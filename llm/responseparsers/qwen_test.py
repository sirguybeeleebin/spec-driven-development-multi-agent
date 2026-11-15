import json
from uuid import UUID

from llm.responseparsers.qwen import QwenResponseParser


def test_parse_returns_response_without_tool_calls_unchanged() -> None:
    response: dict = {
        "role": "assistant",
        "content": "Generated response",
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result == response


def test_parse_preserves_existing_tool_calls() -> None:
    response: dict = {
        "role": "assistant",
        "content": "Generated response",
        "tool_calls": [
            {
                "id": "call_existing",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": '{"command": "ls"}',
                },
            },
        ],
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result == response


def test_parse_extracts_tool_call() -> None:
    response: dict = {
        "role": "assistant",
        "content": (
            'Before tool call\n<tool_call>{"name": "bash", "arguments": {"command": "ls"}}</tool_call>\nAfter tool call'
        ),
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result["content"] == "Before tool call\n\nAfter tool call"
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["type"] == "function"
    assert result["tool_calls"][0]["function"] == {
        "name": "bash",
        "arguments": '{"command": "ls"}',
    }
    assert result["tool_calls"][0]["id"].startswith("call_")
    assert len(result["tool_calls"][0]["id"]) == 37


def test_parse_extracts_multiple_tool_calls() -> None:
    response: dict = {
        "role": "assistant",
        "content": (
            '<tool_call>{"name": "bash", "arguments": {"command": "ls"}}</tool_call>\n'
            '<tool_call>{"name": "read", "arguments": {"path": "README.md"}}</tool_call>'
        ),
    }

    result = QwenResponseParser().parse(response)

    assert result["content"] is None
    assert len(result["tool_calls"]) == 2
    assert [tool_call["function"]["name"] for tool_call in result["tool_calls"]] == ["bash", "read"]
    assert [json.loads(tool_call["function"]["arguments"]) for tool_call in result["tool_calls"]] == [
        {"command": "ls"},
        {"path": "README.md"},
    ]


def test_parse_extracts_tool_call_with_string_arguments() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash", "arguments": "{\\"command\\": \\"ls\\"}"}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert len(result["tool_calls"]) == 1
    assert json.loads(result["tool_calls"][0]["function"]["arguments"]) == {
        "command": "ls",
    }


def test_parse_preserves_unicode_arguments() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "write", "arguments": {"content": "Привет, мир"}}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result["tool_calls"][0]["function"]["arguments"] == '{"content": "Привет, мир"}'


def test_parse_removes_tool_call_when_no_content_remains() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash"}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result["content"] is None
    assert len(result["tool_calls"]) == 1


def test_parse_ignores_invalid_json() -> None:
    response: dict = {
        "role": "assistant",
        "content": "<tool_call>invalid json</tool_call>\nRegular response",
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result["content"] == "<tool_call>invalid json</tool_call>\nRegular response"
    assert "tool_calls" not in result


def test_parse_ignores_non_dict_json() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>["bash", {}]</tool_call>\nRegular response',
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result["content"] == '<tool_call>["bash", {}]</tool_call>\nRegular response'
    assert "tool_calls" not in result


def test_parse_ignores_tool_call_without_string_name() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": 123, "arguments": {}}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert "tool_calls" not in result


def test_parse_ignores_invalid_string_arguments() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash", "arguments": "invalid json"}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert "tool_calls" not in result


def test_parse_ignores_non_dict_arguments() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash", "arguments": ["ls"]}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert "tool_calls" not in result


def test_parse_ignores_tool_call_with_null_arguments() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash", "arguments": null}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert "tool_calls" not in result


def test_parse_uses_empty_arguments_by_default() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash"}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["function"]["arguments"] == "{}"


def test_parse_skips_invalid_calls_and_keeps_valid_calls() -> None:
    response: dict = {
        "role": "assistant",
        "content": (
            "<tool_call>invalid json</tool_call>\n"
            '<tool_call>{"name": "bash", "arguments": {"command": "ls"}}</tool_call>'
        ),
    }

    result = QwenResponseParser().parse(response)

    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["function"]["name"] == "bash"
    assert result["content"] is None


def test_parse_generates_unique_tool_call_ids() -> None:
    response: dict = {
        "role": "assistant",
        "content": ('<tool_call>{"name": "bash"}</tool_call>\n<tool_call>{"name": "read"}</tool_call>'),
    }

    result = QwenResponseParser().parse(response)

    ids = [tool_call["id"] for tool_call in result["tool_calls"]]

    assert len(ids) == 2
    assert len(set(ids)) == 2


def test_parse_generates_tool_call_id_from_uuid() -> None:
    response: dict = {
        "role": "assistant",
        "content": '<tool_call>{"name": "bash"}</tool_call>',
    }

    result = QwenResponseParser().parse(response)

    tool_call_id = result["tool_calls"][0]["id"]
    assert tool_call_id.startswith("call_")

    parsed_uuid = UUID(tool_call_id.removeprefix("call_"))
    assert parsed_uuid.version == 4


def test_parse_handles_empty_content() -> None:
    response: dict = {
        "role": "assistant",
        "content": None,
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result["content"] is None
    assert "tool_calls" not in result


def test_parse_ignores_content_without_tool_call_tags() -> None:
    response: dict = {
        "role": "assistant",
        "content": "Use <tool> instead of <tool_call>.",
    }

    result = QwenResponseParser().parse(response)

    assert result is response
    assert result["content"] == "Use <tool> instead of <tool_call>."
    assert "tool_calls" not in result
