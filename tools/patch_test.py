from pathlib import Path

import pytest

from tools.patch import PatchTool


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(workspace: Path) -> PatchTool:
    return PatchTool(root=workspace)


def test_init_resolves_root(tmp_path: Path) -> None:
    tool = PatchTool(root=tmp_path / ".")

    assert tool._root == tmp_path.resolve()


def test_get_openai_schema(tool: PatchTool) -> None:
    assert tool.get_openai_schema() == {
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


def test_execute_replaces_single_occurrence(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("Hello, world!", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "world",
            "replace": "Python",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len("Hello, Python!"),
    }
    assert path.read_text(encoding="utf-8") == "Hello, Python!"


def test_execute_replaces_all_occurrences(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("foo bar foo baz foo", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "foo",
            "replace": "qux",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len("qux bar qux baz qux"),
    }
    assert path.read_text(encoding="utf-8") == "qux bar qux baz qux"


def test_execute_replaces_multiline_content(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("first\nsecond\nthird", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "second\nthird",
            "replace": "updated\ncontent",
        }
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8") == "first\nupdated\ncontent"


def test_execute_replaces_with_empty_string(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("Hello, world!", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "world",
            "replace": "",
        }
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8") == "Hello, !"


def test_execute_replaces_empty_search(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("abc", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "",
            "replace": "-",
        }
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8") == "-a-b-c-"


def test_execute_preserves_utf8(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("Привет, мир!", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "мир",
            "replace": "Python",
        }
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8") == "Привет, Python!"


def test_execute_reads_nested_file(
    tool: PatchTool,
    workspace: Path,
) -> None:
    directory = workspace / "nested" / "directory"
    directory.mkdir(parents=True)
    path = directory / "example.txt"
    path.write_text("old content", encoding="utf-8")

    result = tool.execute(
        {
            "path": "nested/directory/example.txt",
            "search": "old",
            "replace": "new",
        }
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8") == "new content"


def test_execute_returns_original_content_when_search_not_found(
    tool: PatchTool,
    workspace: Path,
) -> None:
    path = workspace / "example.txt"
    path.write_text("original content", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "missing",
            "replace": "replacement",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len("original content"),
    }
    assert path.read_text(encoding="utf-8") == "original content"


def test_execute_propagates_file_not_found(
    tool: PatchTool,
) -> None:
    with pytest.raises(FileNotFoundError):
        tool.execute(
            {
                "path": "missing.txt",
                "search": "old",
                "replace": "new",
            }
        )


def test_execute_propagates_is_a_directory(
    tool: PatchTool,
    workspace: Path,
) -> None:
    (workspace / "directory").mkdir()

    with pytest.raises(IsADirectoryError):
        tool.execute(
            {
                "path": "directory",
                "search": "old",
                "replace": "new",
            }
        )


def test_execute_propagates_invalid_utf8(
    tool: PatchTool,
    workspace: Path,
) -> None:
    (workspace / "invalid.txt").write_bytes(b"\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        tool.execute(
            {
                "path": "invalid.txt",
                "search": "old",
                "replace": "new",
            }
        )
