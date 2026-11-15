from __future__ import annotations

import json

import pytest

from models import (
    AgentResult,
    Agents,
    FullQualifiedName,
    Gherkin,
    Skill,
    State,
    Task,
)
from promptproviders.fixer import FixerPromptProvider


def make_provider(
    user_template: str = ("{current_gherkin}\n{testrunner_results}\n{skills}"),
) -> FixerPromptProvider:
    return FixerPromptProvider(
        system_template="system prompt",
        user_template=user_template,
        final_prompt="final prompt",
    )


def make_gherkin(
    *,
    name: str = "get returns product",
    fqn: str = "repositories.products::ProductRepository",
    test_fqn: str = "repositories.products::test_get_returns_product",
    given: list[str] | None = None,
    when: list[str] | None = None,
    then: list[str] | None = None,
) -> Gherkin:
    return Gherkin(
        name=name,
        fqn=FullQualifiedName(fqn),
        test_fqn=FullQualifiedName(test_fqn),
        given=given if given is not None else ["the product exists"],
        when=when if when is not None else ["the product is requested"],
        then=then if then is not None else ["the product is returned"],
    )


def make_skill(
    *,
    name: str = "pytest",
    description: str = "Pytest testing conventions",
    content: str = "Use pytest fixtures and assertions.",
) -> Skill:
    return Skill(
        name=name,
        description=description,
        content=content,
    )


def make_state(
    *,
    goal: str = "Read a product by its primary key",
    constitution: str = "Use simple architecture",
    current_gherkin: Gherkin | None = None,
) -> State:
    task = Task(
        task_id="001_products_repository",
        goal=goal,
        fqns=[],
        interfaces=[],
        gherkins=[],
        constitution=constitution,
    )
    return State(
        task=task,
        current_gherkin=current_gherkin,
    )


def make_agent_runner_result(response: dict | None = None) -> AgentResult:
    return AgentResult(
        response=response if response is not None else {},
        messages=[],
        metrics=[],
    )


def test_system_returns_system_template() -> None:
    provider = make_provider()

    assert provider.system == "system prompt"


def test_final_user_returns_final_prompt() -> None:
    provider = make_provider()

    assert provider.final_user == "final prompt"


def test_format_user() -> None:
    provider = make_provider()
    state = make_state(current_gherkin=make_gherkin())
    state.agent_results[Agents.TESTER].append(
        make_agent_runner_result(
            {
                "status": "failed",
                "output": "AssertionError",
            }
        )
    )
    skills = [make_skill()]

    result = provider.format_user(state, skills)

    assert "## Scenario: get returns product" in result
    assert "### FQN: repositories.products::ProductRepository" in result
    assert "### Test FQN: repositories.products::test_get_returns_product" in result
    assert "```gherkin" in result
    assert "Given the product exists" in result
    assert "When the product is requested" in result
    assert "Then the product is returned" in result
    assert '"status": "failed"' in result
    assert '"output": "AssertionError"' in result
    assert "pytest" in result
    assert "Pytest testing conventions" in result
    assert "Use pytest fixtures and assertions." in result
    assert "Read a product by its primary key" not in result
    assert "Use simple architecture" not in result


def test_format_user_without_current_gherkin() -> None:
    provider = make_provider()
    state = make_state()

    result = provider.format_user(state, [])

    assert "_(none)_" in result
    assert "## Scenario:" not in result
    assert "### FQN:" not in result
    assert "### Test FQN:" not in result


def test_format_user_without_tester_results() -> None:
    provider = make_provider()
    state = make_state()

    result = provider.format_user(state, [])

    assert "_(none)_" in result


def test_format_user_uses_latest_tester_result() -> None:
    provider = make_provider()
    state = make_state()

    state.agent_results[Agents.TESTER].extend(
        [
            make_agent_runner_result({"status": "first"}),
            make_agent_runner_result({"status": "latest"}),
        ]
    )

    result = provider.format_user(state, [])

    assert '"status": "latest"' in result
    assert '"status": "first"' not in result


def test_format_user_ignores_results_from_other_agents() -> None:
    provider = make_provider()
    state = make_state()

    state.agent_results[Agents.RESEARCHER].append(
        make_agent_runner_result({"status": "researcher result"})
    )

    result = provider.format_user(state, [])

    assert "researcher result" not in result
    assert "_(none)_" in result


def test_format_user_serializes_tester_result_as_json() -> None:
    provider = make_provider()
    state = make_state()
    response = {
        "status": "failed",
        "summary": "Тест завершился с ошибкой",
        "details": {
            "exception": "AssertionError",
            "line": 42,
        },
    }
    state.agent_results[Agents.TESTER].append(make_agent_runner_result(response))

    result = provider.format_user(state, [])
    expected = json.dumps(
        response,
        ensure_ascii=False,
        indent=2,
    )

    assert expected in result
    assert "Тест завершился с ошибкой" in result


def test_format_user_with_empty_tester_response() -> None:
    provider = make_provider()
    state = make_state()
    state.agent_results[Agents.TESTER].append(make_agent_runner_result({}))

    result = provider.format_user(state, [])

    assert "_(none)_" in result


def test_format_user_with_multiple_gherkin_steps() -> None:
    provider = make_provider()
    state = make_state(
        current_gherkin=make_gherkin(
            given=[
                "the database is initialized",
                "the product exists",
            ],
            when=[
                "the product is requested",
                "the result is inspected",
            ],
            then=[
                "the product is returned",
                "the result contains five keys",
            ],
        ),
    )

    result = provider.format_user(state, [])

    assert "Given the database is initialized" in result
    assert "Given the product exists" in result
    assert "When the product is requested" in result
    assert "When the result is inspected" in result
    assert "Then the product is returned" in result
    assert "Then the result contains five keys" in result


def test_format_user_with_empty_gherkin_steps() -> None:
    provider = make_provider()
    state = make_state(
        current_gherkin=make_gherkin(
            given=[],
            when=[],
            then=[],
        ),
    )

    result = provider.format_user(state, [])

    assert "## Scenario: get returns product" in result
    assert "### Gherkin" in result
    assert "```gherkin\n\n```" in result


def test_format_user_with_multiple_skills() -> None:
    provider = make_provider()
    state = make_state()
    skills = [
        make_skill(
            name="pytest",
            description="Testing framework",
            content="Use fixtures.",
        ),
        make_skill(
            name="python",
            description="Python conventions",
            content="Use type annotations.",
        ),
    ]

    result = provider.format_user(state, skills)

    assert "pytest" in result
    assert "Testing framework" in result
    assert "Use fixtures." in result
    assert "python" in result
    assert "Python conventions" in result
    assert "Use type annotations." in result


def test_format_user_without_skills() -> None:
    provider = make_provider()
    state = make_state()

    result = provider.format_user(state, [])

    assert "_(none)_" in result


def test_format_user_does_not_include_other_task_fields() -> None:
    provider = make_provider()
    state = make_state(
        goal="This goal must not be included",
        constitution="These rules must not be included",
    )

    result = provider.format_user(state, [])

    assert "This goal must not be included" not in result
    assert "These rules must not be included" not in result


def test_format_user_does_not_include_target_file_paths() -> None:
    provider = make_provider()
    state = make_state(current_gherkin=make_gherkin())

    result = provider.format_user(state, [])

    assert "target_file" not in result
    assert "target_test_file" not in result
    assert "repositories.products::ProductRepository" in result
    assert "repositories.products::test_get_returns_product" in result


def test_parse_final_response() -> None:
    provider = make_provider()
    response = json.dumps(
        {
            "status": "success",
            "diagnosis": "implementation_error",
            "summary": "Implementation fixed",
        }
    )

    result = provider.parse_final_response(response)

    assert result == {
        "status": "success",
        "diagnosis": "implementation_error",
        "summary": "Implementation fixed",
    }


def test_parse_final_response_with_unicode() -> None:
    provider = make_provider()
    response = '{"status": "success", "summary": "Ошибка исправлена"}'

    result = provider.parse_final_response(response)

    assert result["summary"] == "Ошибка исправлена"


def test_parse_final_response_with_invalid_json() -> None:
    provider = make_provider()

    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("{invalid json}")


def test_format_user_with_unknown_template_placeholder() -> None:
    provider = make_provider(user_template="{unknown}")

    with pytest.raises(KeyError, match="unknown"):
        provider.format_user(make_state(), [])
