from __future__ import annotations

from pathlib import Path

import pytest

from models import Tools
from tools.append import AppendTool


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(root: Path) -> AppendTool:
    return AppendTool(root=root)


def test_name_returns_append(tool: AppendTool) -> None:
    assert tool.name == Tools.APPEND


def test_get_openai_schema_returns_strict_schema(
    tool: AppendTool,
) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": Tools.APPEND,
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


def test_execute_creates_file_and_parent_directories(
    tool: AppendTool,
    root: Path,
) -> None:
    result = tool.execute(
        {
            "path": "src/nested/example.py",
            "content": "print('hello')\n",
        },
    )

    file_path = root / "src/nested/example.py"

    assert file_path.is_file()
    assert file_path.read_text(encoding="utf-8") == "print('hello')\n"
    assert result == {
        "ok": True,
        "path": "src/nested/example.py",
        "chars": len("print('hello')\n"),
    }


def test_execute_appends_content_to_existing_file(
    tool: AppendTool,
    root: Path,
) -> None:
    file_path = root / "example.py"
    file_path.write_text("first\n", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.py",
            "content": "second\n",
        },
    )

    assert file_path.read_text(encoding="utf-8") == "first\nsecond\n"
    assert result["ok"] is True
    assert result["chars"] == len("second\n")


def test_execute_inserts_newline_when_existing_file_has_no_trailing_newline(
    tool: AppendTool,
    root: Path,
) -> None:
    file_path = root / "example.py"
    file_path.write_text("first", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.py",
            "content": "second",
        },
    )

    assert file_path.read_text(encoding="utf-8") == "first\nsecond"
    assert result["chars"] == len("\nsecond")


def test_execute_does_not_insert_newline_for_empty_file(
    tool: AppendTool,
    root: Path,
) -> None:
    file_path = root / "example.py"
    file_path.touch()

    tool.execute(
        {
            "path": "example.py",
            "content": "content",
        },
    )

    assert file_path.read_text(encoding="utf-8") == "content"


def test_execute_appends_empty_content(
    tool: AppendTool,
    root: Path,
) -> None:
    file_path = root / "example.py"
    file_path.write_text("content\n", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.py",
            "content": "",
        },
    )

    assert file_path.read_text(encoding="utf-8") == "content\n"
    assert result == {
        "ok": True,
        "path": "example.py",
        "chars": 0,
    }


@pytest.mark.parametrize(
    ("path", "content"),
    [
        (1, "content"),
        ("example.py", 1),
        (None, "content"),
        ("example.py", None),
    ],
)
def test_execute_raises_for_invalid_argument_types(
    tool: AppendTool,
    path: object,
    content: object,
) -> None:
    with pytest.raises(TypeError, match="'path' and 'content' must be strings"):
        tool.execute(
            {
                "path": path,
                "content": content,
            },
        )


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "nested/../../outside.txt",
        "/tmp/outside.txt",
    ],
)
def test_execute_rejects_path_outside_workspace(
    tool: AppendTool,
    path: str,
) -> None:
    with pytest.raises(ValueError, match="Path must be workspace-relative"):
        tool.execute(
            {
                "path": path,
                "content": "content",
            },
        )


def test_execute_rejects_symlink_outside_workspace(
    tool: AppendTool,
    root: Path,
    tmp_path: Path,
) -> None:
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")

    link = root / "outside-link.txt"
    link.symlink_to(outside_file)

    with pytest.raises(ValueError, match="Path must be workspace-relative"):
        tool.execute(
            {
                "path": "outside-link.txt",
                "content": "content",
            },
        )

    assert outside_file.read_text(encoding="utf-8") == "outside"
