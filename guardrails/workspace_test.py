from __future__ import annotations

import json

import pytest

from guardrails.workspace import WorkspaceGuardrail


@pytest.fixture
def guardrail() -> WorkspaceGuardrail:
    return WorkspaceGuardrail()


def make_tool_call(
    *,
    name: str = "read_file",
    arguments: dict | None = None,
) -> dict:
    return {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments or {}),
        },
    }


@pytest.mark.parametrize(
    "path",
    [
        "AGENT.md",
        "AGENT.yaml",
        "tasks/task.md",
        "tasks/nested/task.md",
        "skills/python/SKILL.md",
        "skills/nested/python/SKILL.md",
        "workflows/build.md",
        "workflows/nested/build.md",
    ],
)
def test_rejects_operations_on_protected_paths(
    guardrail: WorkspaceGuardrail,
    path: str,
) -> None:
    with pytest.raises(ValueError, match="protected"):
        guardrail.check(
            tool_call=make_tool_call(arguments={"path": path}),
        )


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "pyproject.toml",
        "src/main.py",
        "tests/test_main.py",
        "AGENT.md.backup",
        "my_tasks/task.md",
        "my_skills/SKILL.md",
        "my_workflows/build.md",
    ],
)
def test_allows_operations_on_unprotected_paths(
    guardrail: WorkspaceGuardrail,
    path: str,
) -> None:
    guardrail.check(
        tool_call=make_tool_call(arguments={"path": path}),
    )


@pytest.mark.parametrize(
    "name",
    [
        "bash",
        "load_skill",
        "other_tool",
    ],
)
def test_ignores_tool_without_path_argument(
    guardrail: WorkspaceGuardrail,
    name: str,
) -> None:
    guardrail.check(
        tool_call=make_tool_call(name=name),
    )


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"path": None},
        {"path": 123},
        {"path": ["tasks/task.md"]},
    ],
)
def test_ignores_missing_or_invalid_path(
    guardrail: WorkspaceGuardrail,
    arguments: dict,
) -> None:
    guardrail.check(
        tool_call=make_tool_call(arguments=arguments),
    )


def test_rejects_absolute_path(guardrail: WorkspaceGuardrail) -> None:
    with pytest.raises(ValueError, match="Absolute paths are not allowed"):
        guardrail.check(
            tool_call=make_tool_call(
                arguments={"path": "/workspace/tasks/task.md"},
            ),
        )


def test_rejects_path_with_parent_traversal(
    guardrail: WorkspaceGuardrail,
) -> None:
    with pytest.raises(ValueError, match="protected"):
        guardrail.check(
            tool_call=make_tool_call(
                arguments={"path": "src/../tasks/task.md"},
            ),
        )
