from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.bash import (
    HEAD_LINES,
    MAX_LINES,
    TAIL_LINES,
    TIMEOUT_SEC,
    BashTool,
)


@pytest.fixture
def tool(tmp_path: Path) -> BashTool:
    return BashTool(root=tmp_path)


def test_init_resolves_root(tmp_path: Path) -> None:
    tool = BashTool(root=tmp_path / ".")

    assert tool._root == tmp_path.resolve()


def test_get_openai_schema(tool: BashTool) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Execute read-only terminal commands and run tests "
                "in the target project root directory. "
                "This tool is intended ONLY for inspecting project files "
                "and executing tests. "
                "Do NOT create, modify, or delete files or directories. "
                "Do NOT use file-writing commands, output redirection, "
                "or commands that modify the project. "
                "The working directory is ALREADY set to the project root — "
                "always use relative paths "
                "and do NOT use 'cd' with absolute paths or '..'. "
                "Supports pipelines and chaining."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "Read-only terminal command or test command "
                            "relative to the project root."
                        ),
                    },
                },
                "required": ["command"],
            },
        },
    }


def test_execute_success(tool: BashTool) -> None:
    result = tool.execute({"command": "printf 'Hello, world!' "})

    assert result == {
        "ok": True,
        "exit_code": 0,
        "output": "Hello, world!",
        "error": "",
        "line_count": 1,
        "truncated": 0,
    }


def test_execute_runs_in_workspace_root(
    tool: BashTool,
    tmp_path: Path,
) -> None:
    result = tool.execute({"command": "pwd"})

    assert result["output"] == str(tmp_path.resolve())


def test_execute_returns_nonzero_exit_code(tool: BashTool) -> None:
    result = tool.execute({"command": "exit 7"})

    assert result["ok"] is False
    assert result["exit_code"] == 7


def test_execute_returns_stdout_and_stderr(tool: BashTool) -> None:
    result = tool.execute({"command": "printf 'stdout'; printf 'stderr' >&2; exit 1"})

    assert result["ok"] is False
    assert result["exit_code"] == 1
    assert result["output"] == "stdout"
    assert result["error"] == "stderr"


def test_execute_returns_empty_output(tool: BashTool) -> None:
    result = tool.execute({"command": "true"})

    assert result == {
        "ok": True,
        "exit_code": 0,
        "output": "",
        "error": "",
        "line_count": 0,
        "truncated": 0,
    }


def test_execute_counts_output_lines(tool: BashTool) -> None:
    result = tool.execute({"command": "printf 'first\\nsecond\\nthird\\n'"})

    assert result["output"] == "first\nsecond\nthird"
    assert result["line_count"] == 3
    assert result["truncated"] == 0


def test_execute_truncates_output(tool: BashTool) -> None:
    result = tool.execute(
        {"command": ("for i in $(seq 1 80); do printf 'line %s\\n' \"$i\"; done")}
    )

    expected_lines = [
        *(f"line {i}" for i in range(1, HEAD_LINES + 1)),
        "... [20 lines truncated] ...",
        *(f"line {i}" for i in range(81 - TAIL_LINES, 81)),
    ]

    assert result["output"] == "\n".join(expected_lines)
    assert result["line_count"] == 80
    assert result["truncated"] == 20


def test_execute_does_not_truncate_at_max_lines(tool: BashTool) -> None:
    result = tool.execute(
        {
            "command": (
                f"for i in $(seq 1 {MAX_LINES}); do printf 'line %s\\n' \"$i\"; done"
            )
        }
    )

    assert result["line_count"] == MAX_LINES
    assert result["truncated"] == 0
    assert result["output"].splitlines() == [
        f"line {i}" for i in range(1, MAX_LINES + 1)
    ]


def test_execute_truncates_stderr(tool: BashTool) -> None:
    error_limit = MAX_LINES * 200
    result = tool.execute(
        {"command": (f"head -c {error_limit + 100} /dev/zero | tr '\\0' 'x' >&2")}
    )

    assert len(result["error"]) == error_limit
    assert result["error"] == "x" * error_limit


def test_execute_supports_pipelines(tool: BashTool) -> None:
    result = tool.execute({"command": "printf 'one\\ntwo\\n' | grep two"})

    assert result["ok"] is True
    assert result["output"] == "two"


def test_execute_supports_command_chaining(tool: BashTool) -> None:
    result = tool.execute({"command": "printf 'first'; printf 'second'"})

    assert result["ok"] is True
    assert result["output"] == "firstsecond"


@patch("tools.bash.subprocess.run")
def test_execute_passes_expected_arguments(
    mock_run: object,
    tool: BashTool,
    tmp_path: Path,
) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = ""
    mock_run.return_value.stderr = ""

    tool.execute({"command": "pytest -v"})

    mock_run.assert_called_once_with(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            "-c",
            "pytest -v",
        ],
        cwd=str(tmp_path.resolve()),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=TIMEOUT_SEC,
        shell=False,
    )


@patch("tools.bash.subprocess.run")
def test_execute_propagates_timeout(
    mock_run: object,
    tool: BashTool,
) -> None:
    mock_run.side_effect = subprocess.TimeoutExpired(
        cmd="sleep 60",
        timeout=TIMEOUT_SEC,
    )

    with pytest.raises(subprocess.TimeoutExpired):
        tool.execute({"command": "sleep 60"})


@patch("tools.bash.subprocess.run")
def test_execute_propagates_os_error(
    mock_run: object,
    tool: BashTool,
) -> None:
    mock_run.side_effect = OSError("Execution failed")

    with pytest.raises(OSError, match="Execution failed"):
        tool.execute({"command": "some-command"})
