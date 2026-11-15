from __future__ import annotations

from pathlib import Path

from models import State, ToolCall


class FQNWriteGuardrail:
    def check(
        self,
        *,
        state: State,
        tool_call: ToolCall,
    ) -> None:
        if tool_call.name not in {"append_file", "patch_file"}:
            return

        target_file = state.current_target_file

        if target_file is None:
            raise ValueError("Current target file is not set")

        path = tool_call.arguments.get("path")

        if not isinstance(path, str):
            raise ValueError("Write tool must provide a path argument")

        if Path(path) != target_file:
            raise ValueError(f"Write rejected: expected '{target_file}', got '{path}'")
