from pathlib import Path

import pytest

from tools.append import AppendTool


@pytest.fixture
def tool(tmp_path: Path) -> AppendTool:
    return AppendTool(root=tmp_path)


def test_init_resolves_root(tmp_path: Path) -> None:
    tool = AppendTool(root=tmp_path / ".")

    assert tool._root == tmp_path.resolve()


def test_get_openai_schema(tool: AppendTool) -> None:
    assert tool.get_openai_schema() == {
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


def test_execute_creates_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    result = tool.execute(
        {
            "path": "example.txt",
            "content": "Hello, world!",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": 13,
    }
    assert (tmp_path / "example.txt").read_text(encoding="utf-8") == ("Hello, world!")


def test_execute_appends_to_existing_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("First block\n", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "content": "Second block\n",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": 13,
    }
    assert path.read_text(encoding="utf-8") == ("First block\nSecond block\n")


def test_execute_inserts_newline_before_appending(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("First block", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "content": "Second block",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": 13,
    }
    assert path.read_text(encoding="utf-8") == ("First block\nSecond block")


def test_execute_does_not_insert_newline_for_empty_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "content": "First block",
        }
    )

    assert result["chars"] == len("First block")
    assert path.read_text(encoding="utf-8") == "First block"


def test_execute_appends_to_file_ending_with_newline(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("First block\n", encoding="utf-8")

    tool.execute(
        {
            "path": "example.txt",
            "content": "Second block",
        }
    )

    assert path.read_text(encoding="utf-8") == ("First block\nSecond block")


def test_execute_appends_empty_content(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("Existing content", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "content": "",
        }
    )

    assert result == {
        "ok": True,
        "path": "example.txt",
        "chars": 1,
    }
    assert path.read_text(encoding="utf-8") == "Existing content\n"


def test_execute_creates_nested_directories(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    result = tool.execute(
        {
            "path": "nested/deep/example.txt",
            "content": "Nested content",
        }
    )

    path = tmp_path / "nested" / "deep" / "example.txt"

    assert result["ok"] is True
    assert path.is_file()
    assert path.read_text(encoding="utf-8") == "Nested content"


def test_execute_creates_init_file_for_python_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    result = tool.execute(
        {
            "path": "package/module.py",
            "content": "VALUE = 42\n",
        }
    )

    package = tmp_path / "package"

    assert result["ok"] is True
    assert (package / "__init__.py").is_file()
    assert (package / "__init__.py").read_text(encoding="utf-8") == ""
    assert (package / "module.py").read_text(encoding="utf-8") == ("VALUE = 42\n")


def test_execute_does_not_overwrite_existing_init_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    init_file = package / "__init__.py"
    init_file.write_text("PACKAGE = True\n", encoding="utf-8")

    tool.execute(
        {
            "path": "package/module.py",
            "content": "VALUE = 42\n",
        }
    )

    assert init_file.read_text(encoding="utf-8") == "PACKAGE = True\n"


def test_execute_does_not_create_init_file_for_init_py(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    result = tool.execute(
        {
            "path": "package/__init__.py",
            "content": "PACKAGE = True\n",
        }
    )

    init_file = tmp_path / "package" / "__init__.py"

    assert result["ok"] is True
    assert init_file.read_text(encoding="utf-8") == "PACKAGE = True\n"


def test_execute_does_not_create_init_file_for_non_python_file(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    tool.execute(
        {
            "path": "package/module.txt",
            "content": "Content",
        }
    )

    assert not (tmp_path / "package" / "__init__.py").exists()


def test_execute_preserves_utf8_content(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    content = "Привет, мир! 🌍"

    result = tool.execute(
        {
            "path": "example.txt",
            "content": content,
        }
    )

    assert result["chars"] == len(content)
    assert (tmp_path / "example.txt").read_text(encoding="utf-8") == content


def test_execute_counts_characters_after_newline_insertion(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text("Hello", encoding="utf-8")

    result = tool.execute(
        {
            "path": "example.txt",
            "content": "мир",
        }
    )

    assert result["chars"] == len("\nмир")
    assert path.read_text(encoding="utf-8") == "Hello\nмир"


def test_execute_propagates_file_read_error(
    tool: AppendTool,
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_bytes(b"\xff")

    with pytest.raises(UnicodeDecodeError):
        tool.execute(
            {
                "path": "example.txt",
                "content": "Content",
            }
        )
