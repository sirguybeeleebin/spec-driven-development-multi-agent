from __future__ import annotations

from types import SimpleNamespace

import pytest

from guardrails.bash import BashGuardrail
from models import ToolCall, Tools


@pytest.fixture
def guardrail() -> BashGuardrail:
    return BashGuardrail()


@pytest.fixture
def state() -> SimpleNamespace:
    return SimpleNamespace()


def make_tool_call(
    command: str | None = None,
    *,
    name: Tools = Tools.BASH,
    arguments: dict | None = None,
) -> ToolCall:
    return ToolCall(
        id="1",
        name=name,
        arguments=arguments if arguments is not None else {"command": command},
    )


def test_check_ignores_non_bash_tool(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = make_tool_call(
        "mkdir new_directory",
        name=Tools.APPEND,
    )

    guardrail.check(state=state, tool_call=tool_call)


def test_check_rejects_missing_command(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = make_tool_call(arguments={})

    with pytest.raises(
        ValueError,
        match="Bash tool must provide a command argument",
    ):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize("command", [None, 123, [], {}])
def test_check_rejects_invalid_command(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: object,
) -> None:
    tool_call = make_tool_call(arguments={"command": command})

    with pytest.raises(
        ValueError,
        match="Bash tool must provide a command argument",
    ):
        guardrail.check(state=state, tool_call=tool_call)


def test_check_rejects_invalid_syntax(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = make_tool_call("cat 'file.txt")

    with pytest.raises(ValueError, match="Invalid bash command"):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    "command",
    [
        "mkdir new_directory",
        "touch new_file.txt",
        "cp source.txt destination.txt",
        "mv source.txt destination.txt",
        "install source.txt destination.txt",
        "ln -s source.txt link.txt",
        "mktemp",
        "truncate -s 0 file.txt",
        "dd if=/dev/zero of=file.txt",
        "tee file.txt",
        "mknod file.txt",
        "mkfifo pipe",
    ],
)
def test_check_rejects_write_commands(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
) -> None:
    tool_call = make_tool_call(command)

    with pytest.raises(ValueError, match="Bash command rejected"):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    "command",
    [
        "echo hello > file.txt",
        "echo hello >> file.txt",
        "cat < input.txt > output.txt",
        "command 2> error.log",
        "command &> output.log",
    ],
)
def test_check_rejects_output_redirection(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
) -> None:
    tool_call = make_tool_call(command)

    with pytest.raises(
        ValueError,
        match="output redirection is not allowed",
    ):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    ("command", "git_command"),
    [
        ("git clone https://example.com/repo.git", "clone"),
        ("git worktree add ../worktree", "worktree"),
    ],
)
def test_check_rejects_git_write_commands(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
    git_command: str,
) -> None:
    tool_call = make_tool_call(command)

    with pytest.raises(
        ValueError,
        match=f"git {git_command}",
    ):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    ("command", "executable"),
    [
        ("curl -o file.txt https://example.com/file", "curl"),
        ("curl -O https://example.com/file", "curl"),
        ("curl --output file.txt https://example.com/file", "curl"),
        ("curl --output=file.txt https://example.com/file", "curl"),
        ("wget -o file.txt https://example.com/file", "wget"),
        ("wget -O file.txt https://example.com/file", "wget"),
        ("wget --output-document=file.txt https://example.com/file", "wget"),
    ],
)
def test_check_rejects_download_output_options(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
    executable: str,
) -> None:
    tool_call = make_tool_call(command)

    with pytest.raises(
        ValueError,
        match=f"{executable}.*output options",
    ):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    "command",
    [
        "sed -i 's/foo/bar/' file.txt",
        "sed -i.bak 's/foo/bar/' file.txt",
        "perl -i -pe 's/foo/bar/' file.txt",
        "perl -pi -e 's/foo/bar/' file.txt",
    ],
)
def test_check_rejects_in_place_modification(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
) -> None:
    tool_call = make_tool_call(command)

    with pytest.raises(ValueError, match="-i"):
        guardrail.check(state=state, tool_call=tool_call)


@pytest.mark.parametrize(
    "command",
    [
        "ls -la",
        "cat README.md",
        "head -n 20 file.py",
        "tail -n 20 file.py",
        "grep -R 'class' .",
        "find . -name '*.py'",
        "git status",
        "git diff",
        "pytest -v",
        "python -m pytest",
        "poetry run pytest -v",
        "ruff check .",
    ],
)
def test_check_accepts_read_and_test_commands(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
    command: str,
) -> None:
    tool_call = make_tool_call(command)

    guardrail.check(state=state, tool_call=tool_call)


def test_check_accepts_pipeline(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = make_tool_call("find . -name '*.py' | grep test")

    guardrail.check(state=state, tool_call=tool_call)


def test_check_accepts_command_chaining(
    guardrail: BashGuardrail,
    state: SimpleNamespace,
) -> None:
    tool_call = make_tool_call("git status && pytest -v")

    guardrail.check(state=state, tool_call=tool_call)
