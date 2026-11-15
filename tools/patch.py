from __future__ import annotations

from pathlib import Path


class PatchTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "patch",
                "description": (
                    "Replace all occurrences of one exact substring in a file. "
                    "The search string must match the file byte-for-byte. "
                    "The path must be workspace-relative."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Workspace-relative file path.",
                        },
                        "search": {
                            "type": "string",
                            "description": "Exact text to replace.",
                        },
                        "replace": {
                            "type": "string",
                            "description": "Text to put in its place.",
                        },
                    },
                    "required": ["path", "search", "replace"],
                },
            },
        }

    def execute(self, args: dict) -> dict:
        path = args["path"]
        search = args["search"]
        replace = args["replace"]

        candidate = self._root / path
        original = candidate.read_text(encoding="utf-8")
        updated = original.replace(search, replace)
        candidate.write_text(updated, encoding="utf-8")

        return {
            "ok": True,
            "path": path,
            "chars": len(updated),
        }
