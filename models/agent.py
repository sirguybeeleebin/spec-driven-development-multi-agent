from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from models.llm import Message, Metric


class Agents(StrEnum):
    RESEARCHER = "researcher"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    FIXER = "fixer"


class AgentTestResultStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class AgentResult:
    response: dict
    messages: list[Message]
    metrics: list[list[Metric]]
