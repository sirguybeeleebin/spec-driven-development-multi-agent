from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

import tools.bash as bash_module
from models import Tools
from tools.bash import (
    HEAD_LINES,
    MAX_LINES,
    TAIL_LINES,
    TIMEOUT_SEC,
    BashTool,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(root: Path) -> BashTool:
    return BashTool(root=root)


def make_process_result(
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> Mock:
    return Mock(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_name_returns_bash(tool: BashTool) -> None:
    assert tool.name == Tools.BASH


def test_get_openai_schema_returns_strict_schema(
    tool: BashTool,
) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": Tools.BASH,
            "description": (
                "Execute terminal commands in the project workspace. "
                "Use this tool to inspect project files, explore the codebase, "
                "check command output, run tests, and verify implementation results. "
                "Supports command pipelines and chaining."
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "Shell command to execute from the project root directory. "
                            "Use workspace-relative paths. "
                            "The command can inspect files, search code, "
                            "check project configuration, or run tests."
                        ),
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        },
    }


def test_execute_runs_command_from_root(
    tool: BashTool,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock(
        return_value=make_process_result(
            stdout="hello\n",
        ),
    )
    monkeypatch.setattr(bash_module.subprocess, "run", run)

    result = tool.execute({"command": "echo hello"})

    run.assert_called_once_with(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            "-c",
            "echo hello",
        ],
        cwd=root.resolve(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TIMEOUT_SEC,
        shell=False,
    )

    assert result == {
        "ok": True,
        "exit_code": 0,
        "output": "hello",
        "error": "",
        "line_count": 1,
        "truncated": 0,
    }


def test_execute_returns_error_for_nonzero_exit_code(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bash_module.subprocess,
        "run",
        Mock(
            return_value=make_process_result(
                returncode=2,
                stdout="output\n",
                stderr="command failed\n",
            ),
        ),
    )

    result = tool.execute({"command": "false"})

    assert result == {
        "ok": False,
        "exit_code": 2,
        "output": "output",
        "error": "command failed\n",
        "line_count": 1,
        "truncated": 0,
    }


def test_execute_returns_empty_output_and_error(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bash_module.subprocess,
        "run",
        Mock(
            return_value=make_process_result(
                stdout=None,
                stderr=None,
            ),
        ),
    )

    result = tool.execute({"command": "true"})

    assert result == {
        "ok": True,
        "exit_code": 0,
        "output": "",
        "error": "",
        "line_count": 0,
        "truncated": 0,
    }


def test_execute_does_not_truncate_output_within_limit(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = [f"line {i}" for i in range(MAX_LINES)]

    monkeypatch.setattr(
        bash_module.subprocess,
        "run",
        Mock(
            return_value=make_process_result(
                stdout="\n".join(lines),
            ),
        ),
    )

    result = tool.execute({"command": "cat file.txt"})

    assert result["output"] == "\n".join(lines)
    assert result["line_count"] == MAX_LINES
    assert result["truncated"] == 0


def test_execute_truncates_output_over_limit(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = [f"line {i}" for i in range(MAX_LINES + 20)]

    monkeypatch.setattr(
        bash_module.subprocess,
        "run",
        Mock(
            return_value=make_process_result(
                stdout="\n".join(lines),
            ),
        ),
    )

    result = tool.execute({"command": "cat file.txt"})

    expected = "\n".join(
        [
            *lines[:HEAD_LINES],
            f"... [{20} lines truncated] ...",
            *lines[-TAIL_LINES:],
        ]
    )

    assert result["output"] == expected
    assert result["line_count"] == MAX_LINES + 20
    assert result["truncated"] == 20


def test_execute_truncates_stderr(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = "x" * (MAX_LINES * 200 + 100)

    monkeypatch.setattr(
        bash_module.subprocess,
        "run",
        Mock(
            return_value=make_process_result(
                stderr=error,
            ),
        ),
    )

    result = tool.execute({"command": "command"})

    assert result["error"] == error[: MAX_LINES * 200]
    assert len(result["error"]) == MAX_LINES * 200


def test_execute_raises_for_invalid_command_type(
    tool: BashTool,
) -> None:
    with pytest.raises(TypeError, match="'command' must be a string"):
        tool.execute({"command": 123})


def test_execute_propagates_timeout(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock(
        side_effect=subprocess.TimeoutExpired(
            cmd="sleep",
            timeout=TIMEOUT_SEC,
        ),
    )
    monkeypatch.setattr(bash_module.subprocess, "run", run)

    with pytest.raises(subprocess.TimeoutExpired):
        tool.execute({"command": "sleep 60"})


def test_execute_propagates_subprocess_error(
    tool: BashTool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = Mock(
        side_effect=OSError("failed to start process"),
    )
    monkeypatch.setattr(bash_module.subprocess, "run", run)

    with pytest.raises(OSError, match="failed to start process"):
        tool.execute({"command": "some-command"})
