from __future__ import annotations

import subprocess
from pathlib import Path

MAX_LINES = 60
HEAD_LINES = 15
TAIL_LINES = 45
TIMEOUT_SEC = 30.0


class BashTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def get_openai_schema(self) -> dict:
        return {
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

    def execute(self, args: dict) -> dict:
        command = args["command"]

        result = subprocess.run(
            [
                "/bin/bash",
                "--noprofile",
                "--norc",
                "-c",
                command,
            ],
            cwd=str(self._root),
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
