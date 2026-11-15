from __future__ import annotations

from pathlib import Path

import pytest

from tools.read import ReadTool


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(root: Path) -> ReadTool:
    return ReadTool(root=root)


def test_get_openai_schema_returns_schema(
    tool: ReadTool,
) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read a file from the workspace. Returns the full content.",
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


def test_execute_reads_file_content(
    tool: ReadTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("Hello, world!", encoding="utf-8")

    result = tool.execute({"path": "example.txt"})

    assert result == {
        "ok": True,
        "path": "example.txt",
        "content": "Hello, world!",
    }


def test_execute_reads_utf8_content(
    tool: ReadTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("Привет, мир! 🌍", encoding="utf-8")

    result = tool.execute({"path": "example.txt"})

    assert result["content"] == "Привет, мир! 🌍"


def test_execute_reads_empty_file(
    tool: ReadTool,
    root: Path,
) -> None:
    path = root / "empty.txt"
    path.write_text("", encoding="utf-8")

    result = tool.execute({"path": "empty.txt"})

    assert result == {
        "ok": True,
        "path": "empty.txt",
        "content": "",
    }


def test_execute_reads_file_in_subdirectory(
    tool: ReadTool,
    root: Path,
) -> None:
    path = root / "src" / "module.py"
    path.parent.mkdir(parents=True)
    path.write_text("print('hello')", encoding="utf-8")

    result = tool.execute({"path": "src/module.py"})

    assert result == {
        "ok": True,
        "path": "src/module.py",
        "content": "print('hello')",
    }


def test_execute_raises_for_path_outside_workspace(
    tool: ReadTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute({"path": "../outside.txt"})


def test_execute_raises_for_absolute_path_outside_workspace(
    tool: ReadTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute({"path": str(outside_file)})


def test_execute_rejects_symlink_outside_workspace(
    tool: ReadTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")

    symlink = root / "outside-link.txt"
    symlink.symlink_to(outside_file)

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute({"path": "outside-link.txt"})

    assert outside_file.read_text(encoding="utf-8") == "secret"


def test_execute_raises_for_missing_file(
    tool: ReadTool,
) -> None:
    with pytest.raises(FileNotFoundError):
        tool.execute({"path": "missing.txt"})


def test_execute_raises_for_missing_path_argument(
    tool: ReadTool,
) -> None:
    with pytest.raises(KeyError, match="path"):
        tool.execute({})


def test_execute_returns_original_relative_path(
    tool: ReadTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("content", encoding="utf-8")

    result = tool.execute({"path": "./example.txt"})

    assert result["path"] == "./example.txt"
    assert result["content"] == "content"
