from __future__ import annotations

import subprocess
from pathlib import Path

from models import Tools

MAX_LINES = 60
HEAD_LINES = 15
TAIL_LINES = 45
TIMEOUT_SEC = 30.0


class BashTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    @property
    def name(self) -> str:
        return Tools.BASH

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
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

    def execute(self, args: dict[str, object]) -> dict[str, object]:
        command = args["command"]

        if not isinstance(command, str):
            raise TypeError("'command' must be a string")

        result = subprocess.run(
            [
                "/bin/bash",
                "--noprofile",
                "--norc",
                "-c",
                command,
            ],
            cwd=self._root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT_SEC,
            shell=False,
        )

        output = result.stdout or ""
        error = result.stderr or ""
        lines = output.splitlines()
        total = len(lines)

        if total <= MAX_LINES:
            formatted_output = "\n".join(lines)
            truncated = 0
        else:
            truncated = total - MAX_LINES
            formatted_output = "\n".join(
                [
                    *lines[:HEAD_LINES],
                    f"... [{truncated} lines truncated] ...",
                    *lines[-TAIL_LINES:],
                ]
            )

        return {
            "ok": result.returncode == 0,
            "exit_code": result.returncode,
            "output": formatted_output,
            "error": error[: MAX_LINES * 200],
            "line_count": total,
            "truncated": truncated,
        }
