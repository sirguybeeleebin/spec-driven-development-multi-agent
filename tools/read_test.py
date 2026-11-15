from pathlib import Path

import pytest

from tools.read import ReadTool


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(workspace: Path) -> ReadTool:
    return ReadTool(root=workspace)


def test_init_resolves_root(tmp_path: Path) -> None:
    tool = ReadTool(root=tmp_path / ".")

    assert tool._root == tmp_path.resolve()


def test_get_openai_schema(tool: ReadTool) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": "read",
            "description": (
                "Read a file from the workspace. Returns the full content."
            ),
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


def test_execute_reads_file(tool: ReadTool, workspace: Path) -> None:
    path = workspace / "example.txt"
    path.write_text("Hello, world!", encoding="utf-8")

    result = tool.execute({"path": "example.txt"})

    assert result == {
        "ok": True,
        "path": "example.txt",
        "content": "Hello, world!",
    }


def test_execute_reads_nested_file(tool: ReadTool, workspace: Path) -> None:
    directory = workspace / "nested" / "directory"
    directory.mkdir(parents=True)
    (directory / "example.txt").write_text("Nested content", encoding="utf-8")

    result = tool.execute({"path": "nested/directory/example.txt"})

    assert result == {
        "ok": True,
        "path": "nested/directory/example.txt",
        "content": "Nested content",
    }


def test_execute_reads_utf8_file(tool: ReadTool, workspace: Path) -> None:
    path = workspace / "example.txt"
    path.write_text("Привет, мир! 你好!", encoding="utf-8")

    result = tool.execute({"path": "example.txt"})

    assert result["content"] == "Привет, мир! 你好!"


def test_execute_reads_empty_file(tool: ReadTool, workspace: Path) -> None:
    (workspace / "empty.txt").write_text("", encoding="utf-8")

    result = tool.execute({"path": "empty.txt"})

    assert result == {
        "ok": True,
        "path": "empty.txt",
        "content": "",
    }


def test_execute_propagates_file_not_found(
    tool: ReadTool,
) -> None:
    with pytest.raises(FileNotFoundError):
        tool.execute({"path": "missing.txt"})


def test_execute_propagates_is_a_directory(
    tool: ReadTool,
    workspace: Path,
) -> None:
    (workspace / "directory").mkdir()

    with pytest.raises(IsADirectoryError):
        tool.execute({"path": "directory"})


def test_execute_propagates_invalid_utf8(
    tool: ReadTool,
    workspace: Path,
) -> None:
    (workspace / "invalid.txt").write_bytes(b"\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        tool.execute({"path": "invalid.txt"})
