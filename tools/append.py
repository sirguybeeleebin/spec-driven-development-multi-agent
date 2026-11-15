from __future__ import annotations

from pathlib import Path

from models import Tools


class AppendTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    @property
    def name(self) -> str:
        return Tools.APPEND

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Append a content block to a workspace file. "
                    "Creates the file and parent directories if they do not exist. "
                    "Use this tool to add new content to existing files or create "
                    "files incrementally. Each call appends one block. "
                    "Automatically inserts a newline between consecutive blocks "
                    "when the existing file does not end with one."
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
                        "content": {
                            "type": "string",
                            "description": (
                                "Text content to append to the target file. "
                                "Preserve the required file formatting and syntax."
                            ),
                        },
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, args: dict[str, object]) -> dict[str, object]:
        path = args["path"]
        content = args["content"]

        if not isinstance(path, str) or not isinstance(content, str):
            raise TypeError("'path' and 'content' must be strings")

        candidate = (self._root / path).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError("Path must be workspace-relative")

        candidate.parent.mkdir(parents=True, exist_ok=True)

        if candidate.is_file():
            existing = candidate.read_text(encoding="utf-8")
            if existing and not existing.endswith("\n"):
                content = "\n" + content

        with candidate.open("a", encoding="utf-8") as file:
            file.write(content)

        return {
            "ok": True,
            "path": path,
            "chars": len(content),
        }
