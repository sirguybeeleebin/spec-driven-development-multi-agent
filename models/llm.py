from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MetricName(StrEnum):
    DURATION_SEC = "duration_sec"
    REQUEST_TOKENS = "request_tokens"
    RESPONSE_TOKENS = "response_tokens"
