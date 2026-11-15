from __future__ import annotations

from enum import StrEnum


class Agents(StrEnum):
    RESEARCHER = "researcher"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    FIXER = "fixer"
    TASK_BUILDER = 'task_builder'


class AgentTestResultStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
