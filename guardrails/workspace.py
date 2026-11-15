from __future__ import annotations

import json
import os
from pathlib import Path


class WorkspaceGuardrail:
    PROTECTED_PATHS = {
        "AGENT.md",
        "AGENT.yaml",
        "tasks",
        "workflows",
        "skills",
    }

    def check(self, *, tool_call: dict) -> None:
        arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))

        path = arguments.get("path")
        command = arguments.get("command")

        if isinstance(command, str) and any(protected in command for protected in self.PROTECTED_PATHS):
            raise ValueError("Workspace operation rejected: protected path")

        if not isinstance(path, str):
            return

        if Path(path).is_absolute():
            raise ValueError("Absolute paths are not allowed")

        target = Path(os.path.normpath(path))

        if any(target == Path(protected) or Path(protected) in target.parents for protected in self.PROTECTED_PATHS):
            raise ValueError(f"Workspace operation rejected: '{path}' is protected")
