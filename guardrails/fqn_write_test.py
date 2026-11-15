from pathlib import Path
from types import SimpleNamespace

import pytest

from guardrails.fqn_write import FQNWriteGuardrail
from models import ToolCall


@pytest.fixture
def guardrail() -> FQNWriteGuardrail:
    return FQNWriteGuardrail()


@pytest.fixture
def state() -> SimpleNamespace:
    return SimpleNamespace(
        current_target_file=Path("repositories/products/repository.py")
    )


def test_check_ignores_non_write_tool(
    guardrail: FQNWriteGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = ToolCall(
        id="1",
        name="read_file",
        arguments={"path": "other.py"},
    )

    guardrail.check(state=state, tool_call=tool_call)


def test_check_accepts_target_file(
    guardrail: FQNWriteGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = ToolCall(
        id="1",
        name="append_file",
        arguments={"path": "repositories/products/repository.py"},
    )

    guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize("tool_name", ["append_file", "patch_file"])
def test_check_rejects_different_file(
    guardrail: FQNWriteGuardrail,
    state: SimpleNamespace,
    tool_name: str,
) -> None:
    tool_call = ToolCall(
        id="1",
        name=tool_name,
        arguments={"path": "repositories/products_test.py"},
    )

    with pytest.raises(ValueError, match="Write rejected"):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize("tool_name", ["append_file", "patch_file"])
def test_check_rejects_missing_target_file(
    guardrail: FQNWriteGuardrail,
    tool_name: str,
) -> None:
    state = SimpleNamespace(current_target_file=None)
    tool_call = ToolCall(
        id="1",
        name=tool_name,
        arguments={"path": "repositories/products/repository.py"},
    )

    with pytest.raises(ValueError, match="Current target file is not set"):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize("arguments", [{}, {"path": None}, {"path": 123}])
def test_check_rejects_invalid_path(
    guardrail: FQNWriteGuardrail,
    state: SimpleNamespace,
    arguments: dict,
) -> None:
    tool_call = ToolCall(
        id="1",
        name="append_file",
        arguments=arguments,
    )

    with pytest.raises(ValueError, match="Write tool must provide a path argument"):
        guardrail.check(state=state, tool_call=tool_call)
