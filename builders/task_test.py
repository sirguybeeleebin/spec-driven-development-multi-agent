import pytest

from builders.task import TaskBuilder
from models import (
    FullQualifiedNameRole,
    SequenceArrow,
    SequenceDirective,
    SequenceFragmentType,
    SequenceNotePosition,
    SequenceParticipantType,
)


@pytest.fixture
def builder() -> TaskBuilder:
    return TaskBuilder()


@pytest.fixture
def fqn() -> dict[str, str | int]:
    return {
        "fqn": "app.services.UserService",
        "role": "target",
    }


@pytest.fixture
def interface() -> dict[str, str | list[str]]:
    return {
        "fqn": "app.services.UserService",
        "language": "python",
        "code": "class UserService: ...",
    }


@pytest.fixture
def participant() -> dict[str, object]:
    return {
        "alias": "User",
        "name": "User",
        "type": "participant",
        "fqn": None,
    }


@pytest.fixture
def message() -> dict[str, object]:
    return {
        "type": "message",
        "source": "User",
        "target": "API",
        "arrow": "->",
        "content": "Request",
    }


@pytest.fixture
def note() -> dict[str, object]:
    return {
        "type": "note",
        "position": "over",
        "participants": ["User", "API"],
        "content": "Description",
    }


@pytest.fixture
def directive() -> dict[str, object]:
    return {
        "type": "directive",
        "name": "autonumber",
    }


@pytest.fixture
def branch() -> dict[str, object]:
    return {
        "type": "branch",
        "condition": "authenticated",
        "components": [],
    }


@pytest.fixture
def fragment(
    message: dict[str, object],
) -> dict[str, object]:
    return {
        "type": "fragment",
        "fragment_type": "alt",
        "branches": [
            {
                "condition": "authorized",
                "components": [message],
            }
        ],
    }


@pytest.fixture
def gherkin() -> dict[str, str | list[str]]:
    return {
        "name": "User authentication",
        "FullQualifiedNames": ["app.services.UserService"],
        "given": "User exists",
        "when": "User authenticates",
        "then": "User is authenticated",
    }


def test_build_empty_task(builder: TaskBuilder) -> None:
    task = builder.build()

    assert task.task_id == ""
    assert task.goal == ""
    assert task.fqns == []
    assert task.interfaces == []
    assert task.sequence.participants == []
    assert task.sequence.components == []
    assert task.gherkins == []


def test_add_task_id(builder: TaskBuilder) -> None:
    builder.add_task_id("TASK-123")

    assert builder.build().task_id == "TASK-123"


def test_add_goal(builder: TaskBuilder) -> None:
    builder.add_goal("Implement user authentication")

    assert builder.build().goal == "Implement user authentication"


def test_add_fqn(
    builder: TaskBuilder,
    fqn: dict[str, str | int],
) -> None:
    builder.add_fqn(fqn)

    task = builder.build()

    assert len(task.fqns) == 1
    assert task.fqns[0].fqn == "app.services.UserService"
    assert task.fqns[0].role == FullQualifiedNameRole.TARGET


def test_add_duplicate_fqn(
    builder: TaskBuilder,
    fqn: dict[str, str | int],
) -> None:
    builder.add_fqn(fqn)
    builder.add_fqn(fqn)

    task = builder.build()

    assert len(task.fqns) == 1


def test_add_interface(
    builder: TaskBuilder,
    fqn: dict[str, str | int],
    interface: dict[str, str | list[str]],
) -> None:
    builder.add_fqn(fqn)
    builder.add_interface(interface)

    task = builder.build()

    assert len(task.interfaces) == 1
    assert task.interfaces[0].fqn is task.fqns[0]
    assert task.interfaces[0].language == "python"
    assert task.interfaces[0].content == "class UserService: ..."


def test_add_participant(
    builder: TaskBuilder,
    participant: dict[str, object],
) -> None:
    builder.add_participant(participant)

    task = builder.build()

    assert len(task.sequence.participants) == 1
    assert task.sequence.participants[0].alias == "User"
    assert task.sequence.participants[0].name == "User"
    assert task.sequence.participants[0].type == SequenceParticipantType("participant")
    assert task.sequence.participants[0].fqn is None


def test_add_participant_with_fqn(
    builder: TaskBuilder,
    fqn: dict[str, str | int],
) -> None:
    builder.add_fqn(fqn)
    builder.add_participant(
        {
            "alias": "UserService",
            "name": "UserService",
            "type": "participant",
            "fqn": "app.services.UserService",
        }
    )

    participant = builder.build().sequence.participants[0]

    assert participant.fqn is not None
    assert participant.fqn.fqn == "app.services.UserService"


def test_add_message(
    builder: TaskBuilder,
    message: dict[str, object],
) -> None:
    builder.add_message(message)

    task = builder.build()

    assert len(task.sequence.components) == 1

    result = task.sequence.components[0]

    assert result.source == "User"
    assert result.target == "API"
    assert result.arrow == SequenceArrow("->")
    assert result.content == "Request"


def test_add_note(
    builder: TaskBuilder,
    note: dict[str, object],
) -> None:
    builder.add_note(note)

    task = builder.build()

    assert len(task.sequence.components) == 1

    result = task.sequence.components[0]

    assert result.position == SequenceNotePosition("over")
    assert result.participants == ["User", "API"]
    assert result.content == "Description"


def test_add_fragment(
    builder: TaskBuilder,
    fragment: dict[str, object],
) -> None:
    builder.add_fragment(fragment)

    task = builder.build()

    assert len(task.sequence.components) == 1

    result = task.sequence.components[0]

    assert result.type == SequenceFragmentType("alt")
    assert len(result.branches) == 1
    assert result.branches[0].condition == "authorized"


def test_add_branch(
    builder: TaskBuilder,
    fragment: dict[str, object],
    branch: dict[str, object],
) -> None:
    builder.add_fragment(fragment)
    builder.add_branch(branch)

    task = builder.build()

    result = task.sequence.components[0]

    assert len(result.branches) == 2
    assert result.branches[1].condition == "authenticated"
    assert result.branches[1].components == []


def test_add_branch_preserves_existing_branches(
    builder: TaskBuilder,
    fragment: dict[str, object],
    branch: dict[str, object],
) -> None:
    builder.add_fragment(fragment)
    builder.add_branch(branch)
    builder.add_branch(
        {
            "type": "branch",
            "condition": "fallback",
            "components": [],
        }
    )

    result = builder.build().sequence.components[0]

    assert len(result.branches) == 3
    assert [item.condition for item in result.branches] == [
        "authorized",
        "authenticated",
        "fallback",
    ]


def test_add_fragment_with_message(
    builder: TaskBuilder,
    fragment: dict[str, object],
) -> None:
    builder.add_fragment(fragment)

    result = builder.build().sequence.components[0]

    assert result.branches[0].components[0].source == "User"
    assert result.branches[0].components[0].target == "API"
    assert result.branches[0].components[0].arrow == SequenceArrow("->")


def test_add_fragment_with_note(
    builder: TaskBuilder,
    note: dict[str, object],
) -> None:
    builder.add_fragment(
        {
            "type": "fragment",
            "fragment_type": "loop",
            "branches": [
                {
                    "condition": "retry",
                    "components": [note],
                }
            ],
        }
    )

    result = builder.build().sequence.components[0]

    assert result.type == SequenceFragmentType("loop")
    assert result.branches[0].components[0].position == (SequenceNotePosition("over"))


def test_add_fragment_with_directive(
    builder: TaskBuilder,
    directive: dict[str, object],
) -> None:
    builder.add_fragment(
        {
            "type": "fragment",
            "fragment_type": "alt",
            "branches": [
                {
                    "condition": "authorized",
                    "components": [directive],
                }
            ],
        }
    )

    result = builder.build().sequence.components[0]

    assert result.branches[0].components == [SequenceDirective(name="autonumber")]


def test_add_directive(
    builder: TaskBuilder,
    directive: dict[str, object],
) -> None:
    builder.add_directive(directive)

    task = builder.build()

    assert task.sequence.components == [SequenceDirective(name="autonumber")]


def test_add_gherkin(
    builder: TaskBuilder,
    fqn: dict[str, str | int],
    gherkin: dict[str, str | list[str]],
) -> None:
    builder.add_fqn(fqn)
    builder.add_gherkin(gherkin)

    task = builder.build()

    assert len(task.gherkins) == 1

    result = task.gherkins[0]

    assert result.name == "User authentication"
    assert result.FullQualifiedNames == [task.fqns[0]]
    assert result.given == "User exists"
    assert result.when == "User authenticates"
    assert result.then == "User is authenticated"


def test_build_preserves_component_order(
    builder: TaskBuilder,
    message: dict[str, object],
    note: dict[str, object],
    directive: dict[str, object],
) -> None:
    builder.add_message(message)
    builder.add_note(note)
    builder.add_directive(directive)

    components = builder.build().sequence.components

    assert len(components) == 3
    assert components[0].source == "User"
    assert components[1].content == "Description"
    assert components[2] == SequenceDirective(name="autonumber")
