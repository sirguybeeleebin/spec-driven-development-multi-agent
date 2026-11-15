from llm.responseparsers.openai import OpenAIResponseParser


def test_parse_returns_response_unchanged() -> None:
    response: dict = {
        "role": "assistant",
        "content": "Generated response",
    }

    result = OpenAIResponseParser().parse(response)

    assert result == response
    assert result is response


def test_parse_preserves_tool_calls() -> None:
    response: dict = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": '{"command": "ls"}',
                },
            },
        ],
    }

    result = OpenAIResponseParser().parse(response)

    assert result == response
    assert result is response


def test_parse_preserves_additional_response_fields() -> None:
    response: dict = {
        "role": "assistant",
        "content": "Generated response",
        "refusal": "Request refused",
    }

    result = OpenAIResponseParser().parse(response)

    assert result == response
    assert result is response
