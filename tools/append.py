from __future__ import annotations

from pathlib import Path


class AppendTool:
    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "append",
                "description": (
                    "Append content to a file. Creates the file if it "
                    "does not exist. One call writes one block. The "
                    "path must be workspace-relative. If the file "
                    "already exists and does not end with a newline, "
                    "a newline is inserted before the new content so "
                    "blocks never concatenate on one line."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Workspace-relative file path.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to append.",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        }

    def execute(self, args: dict) -> dict:
        path = args["path"]
        content = args["content"]

        candidate = (self._root / path).resolve()
        candidate.parent.mkdir(parents=True, exist_ok=True)

        if candidate.suffix == ".py" and candidate.name != "__init__.py":
            init_file = candidate.parent / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")

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
