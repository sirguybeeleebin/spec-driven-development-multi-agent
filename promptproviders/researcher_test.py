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
from promptproviders.researcher import ResearcherPromptProvider


@pytest.fixture
def provider() -> ResearcherPromptProvider:
    return ResearcherPromptProvider(
        system_template="Researcher system prompt",
        user_template=(
            "Task: {task_id}\n"
            "Goal: {goal}\n"
            "FQNs:\n{fqns}\n"
            "Interfaces:\n{interfaces}\n"
            "Sequence:\n{sequence}\n"
            "Skills:\n{skills}"
        ),
        final_prompt="Final user prompt",
    )


def make_sequence(
    *,
    participants: list[SequenceParticipant] | None = None,
    components: list | None = None,
) -> Sequence:
    return Sequence(
        participants=participants or [],
        components=components or [],
    )


def test_system_returns_system_template(
    provider: ResearcherPromptProvider,
) -> None:
    assert provider.system == "Researcher system prompt"


def test_final_user_returns_final_prompt(
    provider: ResearcherPromptProvider,
) -> None:
    assert provider.final_user == "Final user prompt"


def test_format_user_formats_task_and_goal(
    provider: ResearcherPromptProvider,
) -> None:
    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "Task: TASK-123" in result
    assert "Goal: Implement feature" in result


def test_format_user_uses_none_for_empty_goal(
    provider: ResearcherPromptProvider,
) -> None:
    result = provider.format_user(
        task_id="TASK-123",
        goal="",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "Goal: _(none)_" in result


def test_format_user_formats_fqns(
    provider: ResearcherPromptProvider,
) -> None:
    fqn = FullQualifiedName(
        fqn="app.services.UserService",
        role=FullQualifiedNameRole.TARGET,
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[fqn],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "- `app.services.UserService` (role: `target`)" in result


def test_format_user_uses_none_for_empty_fqns(
    provider: ResearcherPromptProvider,
) -> None:
    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "FQNs:\n_(none)_" in result


def test_format_user_formats_interfaces(
    provider: ResearcherPromptProvider,
) -> None:
    interface = Interface(
        fqn=FullQualifiedName(
            fqn="app.services.UserService",
            role=FullQualifiedNameRole.TARGET,
        ),
        language="python",
        content="class UserService:\n    def get(self) -> User: ...",
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[interface],
        sequence=make_sequence(),
        skills=[],
    )

    assert "### Interface: `app.services.UserService`" in result
    assert "FullQualifiedName Role: `target`" in result
    assert "Language: python" in result
    assert "```python" in result
    assert "class UserService:" in result


def test_format_user_uses_none_for_empty_interfaces(
    provider: ResearcherPromptProvider,
) -> None:
    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "Interfaces:\n_(none)_" in result


def test_format_user_formats_sequence_participants(
    provider: ResearcherPromptProvider,
) -> None:
    participant = SequenceParticipant(
        alias="U",
        name="User",
        type=SequenceParticipantType.PARTICIPANT,
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(participants=[participant]),
        skills=[],
    )

    assert "participant U as User" in result
    assert "```text" in result


def test_format_user_formats_sequence_participant_fqn(
    provider: ResearcherPromptProvider,
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

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(participants=[participant]),
        skills=[],
    )

    assert "participant S as UserService %% `app.services.UserService` (role: `target`)" in result


def test_format_user_formats_sequence_directive(
    provider: ResearcherPromptProvider,
) -> None:
    directive = SequenceDirective(name="autonumber")

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[directive]),
        skills=[],
    )

    assert "autonumber" in result


def test_format_user_formats_sequence_message(
    provider: ResearcherPromptProvider,
) -> None:
    message = SequenceMessage(
        source="User",
        arrow=SequenceArrow.SYNC,
        target="API",
        content="Create user",
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[message]),
        skills=[],
    )

    assert "User->>API: Create user" in result


def test_format_user_formats_sequence_note(
    provider: ResearcherPromptProvider,
) -> None:
    note = SequenceNote(
        participants=["User", "API"],
        position=SequenceNotePosition.OVER,
        content="Request validation",
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[note]),
        skills=[],
    )

    assert "Note over User and API: Request validation" in result


def test_format_user_formats_sequence_fragment(
    provider: ResearcherPromptProvider,
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
            ),
        ],
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[fragment]),
        skills=[],
    )

    assert "alt user is valid" in result
    assert "    API->Database: Save user" in result
    assert "end" in result


def test_format_user_formats_multiple_fragment_branches(
    provider: ResearcherPromptProvider,
) -> None:
    fragment = SequenceFragment(
        type=SequenceFragmentType.ALT,
        branches=[
            SequenceBranch(
                condition="user is valid",
                components=[],
            ),
            SequenceBranch(
                condition="user is invalid",
                components=[],
            ),
        ],
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[fragment]),
        skills=[],
    )

    assert "alt user is valid" in result
    assert "else user is invalid" in result
    assert result.count("end") == 1


def test_format_user_formats_nested_sequence_fragments(
    provider: ResearcherPromptProvider,
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
            ),
        ],
    )

    outer_fragment = SequenceFragment(
        type=SequenceFragmentType.ALT,
        branches=[
            SequenceBranch(
                condition="request is valid",
                components=[inner_fragment],
            ),
        ],
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(components=[outer_fragment]),
        skills=[],
    )

    assert "alt request is valid" in result
    assert "    loop user exists" in result
    assert "        API->>Database: Get user" in result
    assert result.count("end") == 2


def test_format_user_formats_skills(
    provider: ResearcherPromptProvider,
) -> None:
    skill = Skill(
        name="python",
        description="Python development guidelines",
        content="Python skill content",
    )

    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[skill],
    )

    assert "### Skill: python" in result
    assert "Python development guidelines" in result


def test_format_user_uses_none_for_empty_skills(
    provider: ResearcherPromptProvider,
) -> None:
    result = provider.format_user(
        task_id="TASK-123",
        goal="Implement feature",
        fqns=[],
        interfaces=[],
        sequence=make_sequence(),
        skills=[],
    )

    assert "Skills:\n_(none)_" in result


def test_parse_final_response_returns_parsed_json(
    provider: ResearcherPromptProvider,
) -> None:
    final_response = '{"summary": "Research completed", "findings": ["Finding 1"]}'

    result = provider.parse_final_response(final_response)

    assert result == {
        "summary": "Research completed",
        "findings": ["Finding 1"],
    }


def test_parse_final_response_preserves_unicode(
    provider: ResearcherPromptProvider,
) -> None:
    final_response = '{"summary": "Исследование завершено"}'

    result = provider.parse_final_response(final_response)

    assert result == {"summary": "Исследование завершено"}


def test_parse_final_response_raises_for_invalid_json(
    provider: ResearcherPromptProvider,
) -> None:
    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("invalid json")
