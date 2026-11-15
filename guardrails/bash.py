from __future__ import annotations

import json
import shlex
from pathlib import Path

from models import Tools


class BashGuardrail:
    _WRITE_COMMANDS = {
        "mkdir",
        "touch",
        "cp",
        "mv",
        "install",
        "ln",
        "mktemp",
        "truncate",
        "dd",
        "tee",
        "mknod",
        "mkfifo",
    }

    def check(self, *, tool_call: dict) -> None:
        function = tool_call.get("function", {})
        name = function.get("name")
        arguments = json.loads(function.get("arguments", "{}"))

        if name != Tools.BASH:
            return

        command = arguments.get("command")

        if not isinstance(command, str):
            raise ValueError("Bash tool must provide a command argument")

        lexer = shlex.shlex(
            command,
            posix=True,
            punctuation_chars="|;&()<>",
        )
        lexer.whitespace_split = True
        lexer.commenters = ""

        try:
            tokens = list(lexer)
        except ValueError as exc:
            raise ValueError(f"Invalid bash command: {exc}") from exc

        if any(">" in token for token in tokens):
            raise ValueError("Bash command rejected: output redirection is not allowed")

        for index, token in enumerate(tokens):
            name = Path(token).name

            if name in self._WRITE_COMMANDS:
                raise ValueError(f"Bash command rejected: '{name}' is not allowed")

            if name == "git" and index + 1 < len(tokens):
                if tokens[index + 1] in {"clone", "worktree"}:
                    raise ValueError(f"Bash command rejected: 'git {tokens[index + 1]}' is not allowed")

            if name in {"curl", "wget"}:
                if any(
                    arg
                    in {
                        "-o",
                        "-O",
                        "--output",
                        "--output-document",
                    }
                    or arg.startswith(
                        (
                            "--output=",
                            "--output-document=",
                        )
                    )
                    for arg in tokens[index + 1 :]
                ):
                    raise ValueError(f"Bash command rejected: '{name}' output options are not allowed")

            if name in {"sed", "perl"}:
                if any(
                    arg == "--in-place"
                    or arg.startswith("--in-place=")
                    or (arg.startswith("-") and not arg.startswith("--") and "i" in arg[1:])
                    for arg in tokens[index + 1 :]
                ):
                    raise ValueError(f"Bash command rejected: '{name} -i' is not allowed")
