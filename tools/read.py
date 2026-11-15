from __future__ import annotations

from pathlib import Path


class ReadTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "read",
                "description": ("Read a file from the workspace. Returns the full content."),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Workspace-relative file path.",
                        },
                    },
                    "required": ["path"],
                },
            },
        }

    def execute(self, args: dict) -> dict:
        path = args["path"]
        candidate = (self._root / path).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError("path must be inside workspace")

        content = candidate.read_text(encoding="utf-8")

        return {
            "ok": True,
            "path": path,
            "content": content,
        }
