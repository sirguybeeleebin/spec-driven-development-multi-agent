from __future__ import annotations

import json

import pytest

from models import (
    FullQualifiedName,
    FullQualifiedNameRole,
    Gherkin,
    Interface,
    Skill,
)
from promptproviders.fixer import FixerPromptProvider


@pytest.fixture
def provider() -> FixerPromptProvider:
    return FixerPromptProvider(
        system_template="Fixer system prompt",
        user_template=(
            "Current Gherkin:\n{current_gherkin}\n"
            "Interfaces:\n{interfaces}\n"
            "Tester results:\n{testrunner_results}\n"
            "Skills:\n{skills}"
        ),
        final_prompt="Final user prompt",
    )


def make_gherkin(
    *,
    name: str = "Create user",
    fqns: list[FullQualifiedName] | None = None,
    given: list[str] | None = None,
    when: list[str] | None = None,
    then: list[str] | None = None,
) -> Gherkin:
    return Gherkin(
        name=name,
        FullQualifiedNames=fqns or [],
        given=given or [],
        when=when or [],
        then=then or [],
    )


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
    provider: FixerPromptProvider,
) -> None:
    assert provider.system == "Fixer system prompt"


def test_final_user_returns_final_prompt(
    provider: FixerPromptProvider,
) -> None:
    assert provider.final_user == "Final user prompt"


def test_format_user_uses_none_without_current_gherkin(
    provider: FixerPromptProvider,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "Current Gherkin:\n_(none)_" in result


def test_format_user_formats_gherkin_scenario(
    provider: FixerPromptProvider,
) -> None:
    gherkin = make_gherkin(
        given=["the user is authenticated"],
        when=["the user submits valid data"],
        then=["the user is created"],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "## Scenario: Create user" in result
    assert "### FQNs\n_(none)_" in result
    assert "```gherkin" in result
    assert "Given the user is authenticated" in result
    assert "When the user submits valid data" in result
    assert "Then the user is created" in result


def test_format_user_formats_gherkin_fqns(
    provider: FixerPromptProvider,
) -> None:
    gherkin = make_gherkin(
        fqns=[
            FullQualifiedName(
                fqn="app.services.UserService",
                role=FullQualifiedNameRole.TARGET,
            )
        ]
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "- `app.services.UserService` (role: `target`)" in result


def test_format_user_formats_multiple_gherkin_steps(
    provider: FixerPromptProvider,
) -> None:
    gherkin = make_gherkin(
        given=["first condition", "second condition"],
        when=["first action", "second action"],
        then=["first result", "second result"],
    )

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "Given first condition\nGiven second condition" in result
    assert "When first action\nWhen second action" in result
    assert "Then first result\nThen second result" in result


def test_format_user_formats_empty_gherkin_steps(
    provider: FixerPromptProvider,
) -> None:
    gherkin = make_gherkin()

    result = provider.format_user(
        current_gherkin=gherkin,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "## Scenario: Create user" in result
    assert "### Gherkin\n```gherkin\n\n```" in result


def test_format_user_formats_interface(
    provider: FixerPromptProvider,
) -> None:
    interface = make_interface()

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[interface],
        tester_result={},
        skills=[],
    )

    assert "## Interface: `app.services.UserService`" in result
    assert "FullQualifiedName Role: `target`" in result
    assert "Language: python" in result
    assert "```python" in result
    assert "class UserService: ..." in result


def test_format_user_formats_multiple_interfaces(
    provider: FixerPromptProvider,
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
        tester_result={},
        skills=[],
    )

    assert "## Interface: `app.services.UserService`" in result
    assert "## Interface: `app.repositories.UserRepository`" in result
    assert "class UserService: ..." in result
    assert "class UserRepository(Protocol): ..." in result


def test_format_user_uses_none_for_empty_interfaces(
    provider: FixerPromptProvider,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "Interfaces:\n_(none)_" in result


def test_format_user_formats_tester_result(
    provider: FixerPromptProvider,
) -> None:
    tester_result = {
        "status": "failed",
        "failed_tests": ["test_create_user"],
    }

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result=tester_result,
        skills=[],
    )

    expected = json.dumps(
        tester_result,
        ensure_ascii=False,
        indent=2,
    )

    assert expected in result


def test_format_user_preserves_unicode_in_tester_result(
    provider: FixerPromptProvider,
) -> None:
    tester_result = {"message": "Тест завершился ошибкой"}

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result=tester_result,
        skills=[],
    )

    expected = json.dumps(
        tester_result,
        ensure_ascii=False,
        indent=2,
    )

    assert expected in result
    assert "Тест завершился ошибкой" in result


def test_format_user_uses_none_for_empty_tester_result(
    provider: FixerPromptProvider,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "Tester results:\n_(none)_" in result


def test_format_user_formats_skill(
    provider: FixerPromptProvider,
) -> None:
    skill = Skill(name="python", description="Python development guidelines", content="")

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=[skill],
    )

    assert "## Skill: python" in result
    assert "Python development guidelines" in result


def test_format_user_formats_multiple_skills(
    provider: FixerPromptProvider,
) -> None:
    skills = [
        Skill(name="python", description="Python guidelines", content=""),
        Skill(name="pytest", description="Pytest guidelines", content=""),
    ]

    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=skills,
    )

    assert "## Skill: python\n\nPython guidelines" in result
    assert "## Skill: pytest\n\nPytest guidelines" in result


def test_format_user_uses_none_for_empty_skills(
    provider: FixerPromptProvider,
) -> None:
    result = provider.format_user(
        current_gherkin=None,
        interfaces=[],
        tester_result={},
        skills=[],
    )

    assert "Skills:\n_(none)_" in result


def test_parse_final_response_returns_parsed_json(
    provider: FixerPromptProvider,
) -> None:
    final_response = '{"status": "fixed", "files": ["service.py"]}'

    result = provider.parse_final_response(final_response)

    assert result == {
        "status": "fixed",
        "files": ["service.py"],
    }


def test_parse_final_response_preserves_unicode(
    provider: FixerPromptProvider,
) -> None:
    final_response = '{"summary": "Ошибки исправлены"}'

    result = provider.parse_final_response(final_response)

    assert result == {"summary": "Ошибки исправлены"}


def test_parse_final_response_raises_for_invalid_json(
    provider: FixerPromptProvider,
) -> None:
    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("invalid json")
