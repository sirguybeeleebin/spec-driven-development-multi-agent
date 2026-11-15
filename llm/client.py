from __future__ import annotations

from time import perf_counter
from typing import Protocol

from openai import OpenAI


class ResponseParser(Protocol):
    def parse(self, response: dict) -> dict: ...


class LLMClient:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
        opts: dict,
        response_parsers: list[ResponseParser],
    ) -> None:
        self._client = client
        self._model = model
        self._opts = opts
        self._response_parsers = response_parsers

    def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> tuple[dict, dict]:
        started_at = perf_counter()

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else "none",
            parallel_tool_calls=True,
            **self._opts,
        )

        metrics = {
            "duration_sec": perf_counter() - started_at,
            "request_tokens": response.usage.prompt_tokens if response.usage else 0,
            "response_tokens": response.usage.completion_tokens if response.usage else 0,
        }

        assistant_message = response.choices[0].message.model_dump(
            exclude_none=True,
        )

        for parser in self._response_parsers:
            assistant_message = parser.parse(assistant_message)

        return assistant_message, metrics
