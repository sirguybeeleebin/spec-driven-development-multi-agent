from __future__ import annotations

import json

import pytest

from models import (
    FullQualifiedName,
    FullQualifiedNameRole,
    Gherkin,
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
from promptproviders.tester import TesterPromptProvider


@pytest.fixture
def provider() -> TesterPromptProvider:
    return TesterPromptProvider(
        system_template="Tester system prompt",
        user_template=(
            "Current Gherkin:\n{current_gherkin}\nInterfaces:\n{interfaces}\nSequence:\n{sequence}\nSkills:\n{skills}"
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


def test_system_returns_system_template(provider: TesterPromptProvider) -> None:
    assert provider.system == "Tester system prompt"


def test_final_user_returns_final_prompt(provider: TesterPromptProvider) -> None:
    assert provider.final_user == "Final user prompt"


def test_format_user_uses_none_without_current_gherkin(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "Current Gherkin:\n_(none)_" in result


def test_format_user_formats_gherkin_scenario(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    gherkin = Gherkin(
        name="Create user",
        FullQualifiedNames=[],
        given=["the user is authenticated"],
        when=["the user submits valid data"],
        then=["the user is created"],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "## Scenario: Create user" in result
    assert "### FQNs\n_(none)_" in result
    assert "```gherkin" in result
    assert "Given the user is authenticated" in result
    assert "When the user submits valid data" in result
    assert "Then the user is created" in result


def test_format_user_formats_gherkin_fqns(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    gherkin = Gherkin(
        name="Create user",
        FullQualifiedNames=[
            FullQualifiedName(
                fqn="app.services.UserService",
                role=FullQualifiedNameRole.TARGET,
            )
        ],
        given=[],
        when=[],
        then=[],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "- `app.services.UserService` (role: `target`)" in result


def test_format_user_formats_multiple_gherkin_steps(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    gherkin = Gherkin(
        name="Update user",
        FullQualifiedNames=[],
        given=["first condition", "second condition"],
        when=["first action", "second action"],
        then=["first result", "second result"],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "Given first condition\nGiven second condition" in result
    assert "When first action\nWhen second action" in result
    assert "Then first result\nThen second result" in result


def test_format_user_formats_empty_gherkin_steps(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    gherkin = Gherkin(
        name="Empty scenario",
        FullQualifiedNames=[],
        given=[],
        when=[],
        then=[],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "## Scenario: Empty scenario" in result
    assert "### Gherkin\n```gherkin\n\n```" in result


def test_format_user_formats_interfaces(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    interface = make_interface()

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[interface],
        sequence=sequence,
        skills=[],
    )

    assert "## Interface: `app.services.UserService`" in result
    assert "FullQualifiedName Role: `target`" in result
    assert "Language: python" in result
    assert "```python" in result
    assert "class UserService: ..." in result


def test_format_user_formats_multiple_interfaces(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    first = make_interface(
        fqn="app.services.UserService",
        content="class UserService: ...",
    )
    second = make_interface(
        fqn="app.repositories.UserRepository",
        role=FullQualifiedNameRole.DEPENDENCY,
        content="class UserRepository(Protocol): ...",
    )

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[first, second],
        sequence=sequence,
        skills=[],
    )

    assert "## Interface: `app.services.UserService`" in result
    assert "## Interface: `app.repositories.UserRepository`" in result
    assert "class UserService: ..." in result
    assert "class UserRepository(Protocol): ..." in result


def test_format_user_uses_none_for_empty_interfaces(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "Interfaces:\n_(none)_" in result


def test_format_user_formats_sequence_participants(
    provider: TesterPromptProvider,
) -> None:
    sequence = Sequence(
        participants=[
            SequenceParticipant(
                alias="U",
                name="User",
                type=SequenceParticipantType.PARTICIPANT,
            )
        ],
        components=[],
    )

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "participant U as User" in result
    assert "```text" in result


def test_format_user_formats_sequence_participant_fqn(
    provider: TesterPromptProvider,
) -> None:
    sequence = Sequence(
        participants=[
            SequenceParticipant(
                alias="S",
                name="UserService",
                type=SequenceParticipantType.PARTICIPANT,
                fqn=FullQualifiedName(
                    fqn="app.services.UserService",
                    role=FullQualifiedNameRole.TARGET,
                ),
            )
        ],
        components=[],
    )

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert ("participant S as UserService %% `app.services.UserService` (role: `target`)") in result


def test_format_user_formats_sequence_directive(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [SequenceDirective(name="autonumber")]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "autonumber" in result


def test_format_user_formats_sequence_message(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceMessage(
            source="User",
            target="API",
            arrow=SequenceArrow.SYNC,
            content="Create user",
        )
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "User->>API: Create user" in result


def test_format_user_formats_sequence_note(
    provider: TesterPromptProvider,
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
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "Note over User and API: Request validation" in result


def test_format_user_formats_sequence_fragment(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceFragment(
            type=SequenceFragmentType.ALT,
            branches=[
                SequenceBranch(
                    condition="user is valid",
                    components=[
                        SequenceMessage(
                            source="API",
                            target="Database",
                            arrow=SequenceArrow.RETURN_ASYNC,
                            content="Save user",
                        )
                    ],
                )
            ],
        )
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "alt user is valid" in result
    assert "    API-->Database: Save user" in result
    assert "end" in result


def test_format_user_formats_fragment_else_branch(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceFragment(
            type=SequenceFragmentType.ALT,
            branches=[
                SequenceBranch(condition="user is valid", components=[]),
                SequenceBranch(condition="user is invalid", components=[]),
            ],
        )
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "alt user is valid" in result
    assert "else user is invalid" in result
    assert result.count("end") == 1


def test_format_user_formats_loop_fragment_branches(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceFragment(
            type=SequenceFragmentType.LOOP,
            branches=[
                SequenceBranch(condition="first iteration", components=[]),
                SequenceBranch(condition="next iteration", components=[]),
            ],
        )
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "loop first iteration" in result
    assert "loop next iteration" in result
    assert "else" not in result
    assert result.count("end") == 1


def test_format_user_formats_nested_sequence_fragments(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    sequence.components = [
        SequenceFragment(
            type=SequenceFragmentType.ALT,
            branches=[
                SequenceBranch(
                    condition="request is valid",
                    components=[
                        SequenceFragment(
                            type=SequenceFragmentType.ALT,
                            branches=[
                                SequenceBranch(
                                    condition="user exists",
                                    components=[
                                        SequenceMessage(
                                            source="API",
                                            target="Database",
                                            arrow=SequenceArrow.SYNC,
                                            content="Get user",
                                        )
                                    ],
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "alt request is valid" in result
    assert "    alt user exists" in result
    assert "        API->>Database: Get user" in result
    assert result.count("end") == 2


def test_format_user_formats_skills(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    skill = Skill(name="python", description="Python testing guidelines", content="")

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[skill],
    )

    assert "## Skill: python" in result
    assert "Python testing guidelines" in result


def test_format_user_formats_multiple_skills(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    skills = [
        Skill(name="python", description="Python guidelines", content=""),
        Skill(name="pytest", description="Pytest guidelines", content=""),
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=skills,
    )

    assert "## Skill: python\n\nPython guidelines" in result
    assert "## Skill: pytest\n\nPytest guidelines" in result


def test_format_user_uses_none_for_empty_skills(
    provider: TesterPromptProvider,
    sequence: Sequence,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        sequence=sequence,
        skills=[],
    )

    assert "Skills:\n_(none)_" in result


def test_parse_final_response_returns_parsed_json(
    provider: TesterPromptProvider,
) -> None:
    final_response = '{"status": "passed", "tests": ["test_create_user"]}'

    result = provider.parse_final_response(final_response)

    assert result == {
        "status": "passed",
        "tests": ["test_create_user"],
    }


def test_parse_final_response_preserves_unicode(
    provider: TesterPromptProvider,
) -> None:
    final_response = '{"summary": "Все тесты пройдены"}'

    result = provider.parse_final_response(final_response)

    assert result == {"summary": "Все тесты пройдены"}


def test_parse_final_response_raises_for_invalid_json(
    provider: TesterPromptProvider,
) -> None:
    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("invalid json")
