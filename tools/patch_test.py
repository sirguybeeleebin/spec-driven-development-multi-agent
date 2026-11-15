from __future__ import annotations

from pathlib import Path

import pytest

from models import Tools
from tools.patch import PatchTool


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def tool(root: Path) -> PatchTool:
    return PatchTool(root=root)


def test_name_returns_patch(tool: PatchTool) -> None:
    assert tool.name == Tools.PATCH


def test_get_openai_schema_returns_strict_schema(
    tool: PatchTool,
) -> None:
    assert tool.get_openai_schema() == {
        "type": "function",
        "function": {
            "name": Tools.PATCH,
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


def test_execute_replaces_all_occurrences(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("foo bar foo", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "foo",
            "replace": "baz",
        },
    )

    assert path.read_text(encoding="utf-8") == "baz bar baz"
    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len("baz bar baz"),
    }


def test_execute_replaces_multiline_text(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("first\nold\nlast\n", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "old\nlast",
            "replace": "new\ncontent",
        },
    )

    assert path.read_text(encoding="utf-8") == "first\nnew\ncontent\n"
    assert result["chars"] == len("first\nnew\ncontent\n")


def test_execute_removes_matched_text(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("before REMOVE after", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "REMOVE ",
            "replace": "",
        },
    )

    assert path.read_text(encoding="utf-8") == "before after"
    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len("before after"),
    }


def test_execute_does_not_modify_file_when_search_not_found(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    original = "original content"
    path.write_text(original, encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "search": "missing",
            "replace": "replacement",
        },
    )

    assert path.read_text(encoding="utf-8") == original
    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": len(original),
    }


def test_execute_matching_is_case_sensitive(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("Foo foo FOO", encoding="utf-8")

    tool.execute(
        {
            "path": "example.txt",
            "search": "foo",
            "replace": "bar",
        },
    )

    assert path.read_text(encoding="utf-8") == "Foo bar FOO"


def test_execute_preserves_utf8_content(
    tool: PatchTool,
    root: Path,
) -> None:
    path = root / "example.txt"
    path.write_text("Привет, мир!", encoding="utf-8")

    tool.execute(
        {
            "path": "example.txt",
            "search": "мир",
            "replace": "Python",
        },
    )

    assert path.read_text(encoding="utf-8") == "Привет, Python!"


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            {"path": 123, "search": "a", "replace": "b"},
            "'path' must be a string",
        ),
        (
            {"path": "file.txt", "search": 123, "replace": "b"},
            "'search' must be a string",
        ),
        (
            {"path": "file.txt", "search": "a", "replace": 123},
            "'replace' must be a string",
        ),
    ],
)
def test_execute_raises_for_invalid_argument_types(
    tool: PatchTool,
    args: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        tool.execute(args)


def test_execute_raises_for_empty_search(
    tool: PatchTool,
) -> None:
    with pytest.raises(ValueError, match="search must not be empty"):
        tool.execute(
            {
                "path": "example.txt",
                "search": "",
                "replace": "replacement",
            },
        )


def test_execute_raises_for_path_outside_workspace(
    tool: PatchTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute(
            {
                "path": "../outside.txt",
                "search": "content",
                "replace": "changed",
            },
        )


def test_execute_raises_for_absolute_path_outside_workspace(
    tool: PatchTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute(
            {
                "path": str(outside_file),
                "search": "content",
                "replace": "changed",
            },
        )


def test_execute_raises_for_missing_file(
    tool: PatchTool,
) -> None:
    with pytest.raises(FileNotFoundError):
        tool.execute(
            {
                "path": "missing.txt",
                "search": "content",
                "replace": "changed",
            },
        )


def test_execute_rejects_symlink_outside_workspace(
    tool: PatchTool,
    root: Path,
) -> None:
    outside_file = root.parent / "outside.txt"
    outside_file.write_text("content", encoding="utf-8")

    symlink = root / "outside-link.txt"
    symlink.symlink_to(outside_file)

    with pytest.raises(ValueError, match="path must be inside workspace"):
        tool.execute(
            {
                "path": "outside-link.txt",
                "search": "content",
                "replace": "changed",
            },
        )

    assert outside_file.read_text(encoding="utf-8") == "content"


def test_execute_raises_for_missing_arguments(
    tool: PatchTool,
) -> None:
    with pytest.raises(KeyError, match="path"):
        tool.execute({})

    with pytest.raises(KeyError, match="search"):
        tool.execute({"path": "example.txt"})

    with pytest.raises(KeyError, match="replace"):
        tool.execute(
            {
                "path": "example.txt",
                "search": "text",
            },
        )
