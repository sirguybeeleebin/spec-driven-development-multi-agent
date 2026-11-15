from __future__ import annotations

import json

import pytest

from models import (
    FullQualifiedName,
    FullQualifiedNameRole,
    Interface,
    Sequence,
    SequenceArrow,
    SequenceBranch,
    SequenceDirective,
    SequenceFragment,
    SequenceFragmentType,
    SequenceMessage,
    SequenceNote,
    SequenceNotePosition,
    SequenceParticipant,
    SequenceParticipantType,
    Skill,
)
from promptproviders.implementer import ImplementerPromptProvider


@pytest.fixture
def provider() -> ImplementerPromptProvider:
    return ImplementerPromptProvider(
        system_template="Implementer system prompt",
        user_template=(
            "Goal: {goal}\n"
            "Current FQN: {current_fqn}\n"
            "Current interface:\n{current_interface}\n"
            "Interfaces:\n{interfaces}\n"
            "Constitution: {constitution}\n"
            "Sequence:\n{sequence}\n"
            "Researcher results:\n{researcher_results}\n"
            "Skills:\n{skills}"
        ),
        final_prompt="Final user prompt",
    )


@pytest.fixture
def sequence() -> Sequence:
    return Sequence(participants=[], components=[])


def make_interface(
    *,
    fqn: str = "app.services.UserService",
    role: FullQualifiedNameRole = FullQualifiedNameRole.TARGET,
    language: str = "python",
    content: str = "class UserService: ...",
) -> Interface:
    return Interface(
        fqn=FullQualifiedName(fqn=fqn, role=role),
        language=language,
        content=content,
    )


def test_system_returns_system_template(
    provider: ImplementerPromptProvider,
) -> None:
    assert provider.system == "Implementer system prompt"


def test_final_user_returns_final_prompt(
    provider: ImplementerPromptProvider,
) -> None:
    assert provider.final_user == "Final user prompt"


def test_format_user_formats_goal(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement user service",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Goal: Implement user service" in result


def test_format_user_uses_none_for_empty_goal(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Goal: _(none)_" in result


def test_format_user_formats_current_fqn(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    interface = make_interface()

    result = provider.format_user(
        goal="Implement feature",
        current_interface=interface,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Current FQN: `app.services.UserService` (role: `target`)" in result


def test_format_user_uses_none_without_current_interface(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Current FQN: _(none)_" in result
    assert "Current interface:\n_(none)_" in result


def test_format_user_formats_current_interface(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    interface = make_interface()

    result = provider.format_user(
        goal="Implement feature",
        current_interface=interface,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "## Interface: `app.services.UserService`" in result
    assert "FullQualifiedName Role: `target`" in result
    assert "Language: python" in result
    assert "```python" in result
    assert "class UserService: ..." in result


def test_format_user_formats_interfaces(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    interface = make_interface(
        fqn="app.repositories.UserRepository",
        role=FullQualifiedNameRole.DEPENDENCY,
        content="class UserRepository(Protocol): ...",
    )

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[interface],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "## Interface: `app.repositories.UserRepository`" in result
    assert "FullQualifiedName Role: `dependency`" in result
    assert "class UserRepository(Protocol): ..." in result


def test_format_user_uses_none_for_empty_interfaces(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Interfaces:\n_(none)_" in result


def test_format_user_formats_constitution(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Use Python 3.12 and pytest",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Constitution: Use Python 3.12 and pytest" in result


def test_format_user_uses_none_for_empty_constitution(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Constitution: _(none)_" in result


def test_format_user_formats_sequence_participants(
    provider: ImplementerPromptProvider,
) -> None:
    participant = SequenceParticipant(
        alias="U",
        name="User",
        type=SequenceParticipantType.PARTICIPANT,
    )
    sequence = Sequence(participants=[participant], components=[])

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "participant U as User" in result
    assert "```text" in result


def test_format_user_formats_sequence_participant_fqn(
    provider: ImplementerPromptProvider,
) -> None:
    participant = SequenceParticipant(
        alias="S",
        name="UserService",
        type=SequenceParticipantType.PARTICIPANT,
        fqn=FullQualifiedName(
            fqn="app.services.UserService",
            role=FullQualifiedNameRole.TARGET,
        ),
    )
    sequence = Sequence(participants=[participant], components=[])

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "participant S as UserService %% `app.services.UserService` (role: `target`)" in result


def test_format_user_formats_sequence_directive(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [SequenceDirective(name="autonumber")]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "autonumber" in result


def test_format_user_formats_sequence_message(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceMessage(
            source="User",
            arrow=SequenceArrow.SYNC,
            target="API",
            content="Create user",
        )
    ]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "User->>API: Create user" in result


def test_format_user_formats_sequence_note(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceNote(
            participants=["User", "API"],
            position=SequenceNotePosition.OVER,
            content="Request validation",
        )
    ]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Note over User and API: Request validation" in result


def test_format_user_formats_sequence_fragment(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    message = SequenceMessage(
        source="API",
        arrow=SequenceArrow.ASYNC,
        target="Database",
        content="Save user",
    )
    fragment = SequenceFragment(
        type=SequenceFragmentType.ALT,
        branches=[
            SequenceBranch(
                condition="user is valid",
                components=[message],
            )
        ],
    )
    sequence.components = [fragment]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "alt user is valid" in result
    assert "    API->Database: Save user" in result
    assert "end" in result


def test_format_user_formats_fragment_else_branch(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    fragment = SequenceFragment(
        type=SequenceFragmentType.ALT,
        branches=[
            SequenceBranch(condition="user is valid", components=[]),
            SequenceBranch(condition="user is invalid", components=[]),
        ],
    )
    sequence.components = [fragment]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "alt user is valid" in result
    assert "else user is invalid" in result
    assert result.count("end") == 1


def test_format_user_formats_loop_fragment_branches(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    fragment = SequenceFragment(
        type=SequenceFragmentType.LOOP,
        branches=[
            SequenceBranch(condition="first iteration", components=[]),
            SequenceBranch(condition="next iteration", components=[]),
        ],
    )
    sequence.components = [fragment]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "loop first iteration" in result
    assert "loop next iteration" in result
    assert "else" not in result
    assert result.count("end") == 1


def test_format_user_formats_nested_sequence_fragments(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    message = SequenceMessage(
        source="API",
        arrow=SequenceArrow.SYNC,
        target="Database",
        content="Get user",
    )
    inner_fragment = SequenceFragment(
        type=SequenceFragmentType.LOOP,
        branches=[
            SequenceBranch(
                condition="user exists",
                components=[message],
            )
        ],
    )
    outer_fragment = SequenceFragment(
        type=SequenceFragmentType.ALT,
        branches=[
            SequenceBranch(
                condition="request is valid",
                components=[inner_fragment],
            )
        ],
    )
    sequence.components = [outer_fragment]

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "alt request is valid" in result
    assert "    loop user exists" in result
    assert "        API->>Database: Get user" in result
    assert result.count("end") == 2


def test_format_user_formats_researcher_response(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    researcher_response = {
        "summary": "Research completed",
        "findings": ["Finding 1", "Finding 2"],
    }

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response=researcher_response,
        skills=[],
    )

    expected = json.dumps(
        researcher_response,
        ensure_ascii=False,
        indent=2,
    )

    assert expected in result


def test_format_user_preserves_unicode_in_researcher_response(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    researcher_response = {"summary": "Исследование завершено"}

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response=researcher_response,
        skills=[],
    )

    expected = json.dumps(
        researcher_response,
        ensure_ascii=False,
        indent=2,
    )

    assert expected in result


def test_format_user_formats_skills(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    skill = Skill(
        name="python",
        description="Python development guidelines",
        content="Python skill content",
    )

    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[skill],
    )

    assert "## Skill: python" in result
    assert "Python development guidelines" in result


def test_format_user_uses_none_for_empty_skills(
    provider: ImplementerPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        goal="Implement feature",
        current_interface=None,
        interfaces=[],
        constitution="Project rules",
        sequence=sequence,
        researcher_response={},
        skills=[],
    )

    assert "Skills:\n_(none)_" in result


def test_parse_final_response_returns_parsed_json(
    provider: ImplementerPromptProvider,
) -> None:
    final_response = '{"summary": "Implementation completed", "files": ["service.py"]}'

    result = provider.parse_final_response(final_response)

    assert result == {
        "summary": "Implementation completed",
        "files": ["service.py"],
    }


def test_parse_final_response_preserves_unicode(
    provider: ImplementerPromptProvider,
) -> None:
    final_response = '{"summary": "Реализация завершена"}'

    result = provider.parse_final_response(final_response)

    assert result == {"summary": "Реализация завершена"}


def test_parse_final_response_raises_for_invalid_json(
    provider: ImplementerPromptProvider,
) -> None:
    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("invalid json")
