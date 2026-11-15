from __future__ import annotations

import os
from pathlib import Path

from models import State, ToolCall


class WorkspaceGuardrail:
    PROTECTED_PATHS = {
        "AGENT.md",
        "AGENT.yaml",
        "tasks",
        "workflows",
        "skills",
    }

    def check(
        self,
        *,
        state: State,
        tool_call: ToolCall,
    ) -> None:
        path = tool_call.arguments.get("path")
        command = tool_call.arguments.get("command")

        if isinstance(command, str) and any(
            protected in command for protected in self.PROTECTED_PATHS
        ):
            raise ValueError("Workspace operation rejected: protected path")

        if not isinstance(path, str):
            return

        if Path(path).is_absolute():
            raise ValueError("Absolute paths are not allowed")

        target = Path(os.path.normpath(path))

        if any(
            target == Path(protected) or Path(protected) in target.parents
            for protected in self.PROTECTED_PATHS
        ):
            raise ValueError(f"Workspace operation rejected: '{path}' is protected")
