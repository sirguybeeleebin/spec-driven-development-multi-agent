from __future__ import annotations

from pathlib import Path

from models import Tools


class PatchTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    @property
    def name(self) -> str:
        return Tools.PATCH

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Replace exact text in a workspace file. "
                    "Use this tool to update existing code, configuration, "
                    "documentation, or other file content by matching a specific "
                    "text fragment and replacing all its occurrences."
                ),
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Path to the target file relative to the workspace root. "
                                "For example: 'src/main.py' or 'tests/test_main.py'."
                            ),
                        },
                        "search": {
                            "type": "string",
                            "description": (
                                "Exact text fragment to find in the file. "
                                "Matching is case-sensitive and includes whitespace "
                                "and line breaks. All occurrences are replaced."
                            ),
                        },
                        "replace": {
                            "type": "string",
                            "description": (
                                "Text that replaces every occurrence of the search fragment. "
                                "Can contain multiple lines or be an empty string "
                                "to remove the matched text."
                            ),
                        },
                    },
                    "required": ["path", "search", "replace"],
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, args: dict[str, object]) -> dict[str, object]:
        path = args["path"]
        search = args["search"]
        replace = args["replace"]

        if not isinstance(path, str):
            raise TypeError("'path' must be a string")
        if not isinstance(search, str):
            raise TypeError("'search' must be a string")
        if not isinstance(replace, str):
            raise TypeError("'replace' must be a string")
        if not search:
            raise ValueError("search must not be empty")

        candidate = (self._root / path).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError("path must be inside workspace")

        original = candidate.read_text(encoding="utf-8")
        updated = original.replace(search, replace)

        if updated != original:
            candidate.write_text(updated, encoding="utf-8")

        return {
            "ok": True,
            "path": path,
            "chars": len(updated),
        }
