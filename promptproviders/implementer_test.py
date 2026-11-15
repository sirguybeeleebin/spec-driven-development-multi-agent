from __future__ import annotations

import json

import pytest

from models import (
    AgentResult,
    Agents,
    FullQualifiedName,
    Interface,
    Sequence,
    Skill,
    State,
    Task,
)
from promptproviders.implementer import ImplementerPromptProvider


def make_agent_runner_result(response: dict | None = None) -> AgentResult:
    return AgentResult(
        response=response or {},
        messages=[],
        metrics=[],
    )


def make_interface(
    name: str = "ProductRepository",
    *,
    language: str = "python",
    content: str = "class ProductRepository: ...",
    description: str = "Reads products from the database.",
    steps: list[str] | None = None,
) -> Interface:
    return Interface(
        name=name,
        language=language,
        content=content,
        description=description,
        steps=steps or [],
    )


def make_skill(
    name: str = "pytest",
    *,
    description: str = "Pytest testing guidelines.",
    content: str = "Use fixtures and parametrization.",
) -> Skill:
    return Skill(
        name=name,
        description=description,
        content=content,
    )


def make_state(
    *,
    fqns: list[FullQualifiedName] | None = None,
    interfaces: list[Interface] | None = None,
    sequence: Sequence | None = None,
    constitution: str = "Follow project rules.",
    researcher_response: dict | None = None,
    current_fqn: FullQualifiedName | None = None,
) -> State:
    task = Task(
        task_id="001",
        goal="Implement product repository.",
        fqns=fqns or [],
        interfaces=interfaces or [],
        gherkins=[],
        constitution=constitution,
        sequence=sequence,
    )
    state = State(task=task)

    if researcher_response is not None:
        state.agent_results[Agents.RESEARCHER].append(
            make_agent_runner_result(researcher_response)
        )

    if current_fqn is not None:
        state.current_fqn = current_fqn

    return state


def make_provider(
    user_template: str,
    *,
    system_template: str = "Implementer system prompt.",
    final_prompt: str = "Return JSON.",
) -> ImplementerPromptProvider:
    return ImplementerPromptProvider(
        system_template=system_template,
        user_template=user_template,
        final_prompt=final_prompt,
    )


def test_init_and_properties() -> None:
    provider = make_provider(
        user_template="User: {goal}",
        system_template="System prompt.",
        final_prompt="Final prompt.",
    )

    assert provider.system == "System prompt."
    assert provider.final_user == "Final prompt."


def test_format_user_with_all_task_data() -> None:
    provider = make_provider(
        user_template=(
            "{goal}\n"
            "{current_fqn}\n"
            "{interfaces}\n"
            "{constitution}\n"
            "{sequence}\n"
            "{researcher_results}\n"
            "{skills}"
        )
    )
    state = make_state(
        fqns=[
            FullQualifiedName("repositories.products::ProductRepository"),
            FullQualifiedName("services.products::ProductService"),
        ],
        interfaces=[
            make_interface(
                steps=[
                    "Get a product by ID",
                    "Return None if missing",
                ]
            )
        ],
        sequence=Sequence(
            language="mermaid",
            content="A --> B",
        ),
        researcher_response={
            "summary": "Research completed.",
            "findings": ["Finding 1", "Finding 2"],
        },
        current_fqn=FullQualifiedName("repositories.products::ProductRepository"),
    )
    skills = [make_skill()]

    result = provider.format_user(state, skills)

    assert "Implement product repository." in result
    assert "repositories.products::ProductRepository" in result
    assert "## Interface: repositories.products::ProductRepository" in result
    assert "Language: python" in result
    assert "Description: Reads products from the database." in result
    assert "1. Get a product by ID" in result
    assert "2. Return None if missing" in result
    assert "class ProductRepository: ..." in result
    assert "Follow project rules." in result
    assert "```mermaid\nA --> B\n```" in result
    assert '"summary": "Research completed."' in result
    assert '"Finding 1"' in result
    assert "## Skill: pytest" in result
    assert "Pytest testing guidelines." in result


def test_format_user_without_optional_data() -> None:
    provider = make_provider(
        user_template=(
            "{goal}\n"
            "{current_fqn}\n"
            "{interfaces}\n"
            "{constitution}\n"
            "{sequence}\n"
            "{researcher_results}\n"
            "{skills}"
        )
    )
    state = make_state(constitution="")

    result = provider.format_user(state, [])

    assert "Implement product repository." in result
    assert result.count("_(none)_") == 5
    assert "{}" in result


def test_format_user_without_current_fqn() -> None:
    provider = make_provider(user_template="{current_fqn}")
    state = make_state()

    result = provider.format_user(state, [])

    assert result == "_(none)_"


def test_format_user_with_interface_without_description_and_steps() -> None:
    provider = make_provider(user_template="{interfaces}")
    state = make_state(
        interfaces=[
            make_interface(
                description="",
                steps=[],
            )
        ]
    )

    result = provider.format_user(state, [])

    assert "## Interface: ProductRepository" in result
    assert "Language: python" in result
    assert "class ProductRepository: ..." in result
    assert "Description:" not in result
    assert "Steps:" not in result


def test_format_user_with_multiple_interfaces() -> None:
    provider = make_provider(user_template="{interfaces}")
    state = make_state(
        interfaces=[
            make_interface(
                name="ProductRepository",
                content="class ProductRepository: ...",
            ),
            make_interface(
                name="ProductService",
                content="class ProductService: ...",
            ),
        ]
    )

    result = provider.format_user(state, [])

    assert "## Interface: ProductRepository" in result
    assert "## Interface: ProductService" in result
    assert "class ProductRepository: ..." in result
    assert "class ProductService: ..." in result


def test_format_user_uses_interface_name_when_fqn_is_missing() -> None:
    provider = make_provider(user_template="{interfaces}")
    state = make_state(
        interfaces=[make_interface(name="ProductRepository")],
    )

    result = provider.format_user(state, [])

    assert "## Interface: ProductRepository" in result


def test_format_user_uses_fqn_for_matching_interface() -> None:
    provider = make_provider(user_template="{interfaces}")
    state = make_state(
        fqns=[
            FullQualifiedName("repositories.products::ProductRepository"),
        ],
        interfaces=[make_interface()],
    )

    result = provider.format_user(state, [])

    assert "## Interface: repositories.products::ProductRepository" in result


def test_format_user_with_empty_researcher_results() -> None:
    provider = make_provider(user_template="{researcher_results}")
    state = make_state()

    result = provider.format_user(state, [])

    assert result == "{}"


def test_format_user_with_researcher_results() -> None:
    provider = make_provider(user_template="{researcher_results}")
    state = make_state(
        researcher_response={
            "summary": "Found relevant modules.",
            "files": ["repositories/products.py"],
        }
    )

    result = provider.format_user(state, [])

    assert json.loads(result) == {
        "summary": "Found relevant modules.",
        "files": ["repositories/products.py"],
    }


def test_format_user_serializes_researcher_results_as_unicode() -> None:
    provider = make_provider(user_template="{researcher_results}")
    state = make_state(researcher_response={"summary": "Исследование завершено."})

    result = provider.format_user(state, [])

    assert "Исследование завершено." in result
    assert "\\u" not in result


def test_format_user_with_multiple_skills() -> None:
    provider = make_provider(user_template="{skills}")
    state = make_state()
    skills = [
        make_skill(name="pytest"),
        make_skill(
            name="ruff",
            description="Python linting guidelines.",
        ),
    ]

    result = provider.format_user(state, skills)

    assert "## Skill: pytest" in result
    assert "Pytest testing guidelines." in result
    assert "## Skill: ruff" in result
    assert "Python linting guidelines." in result


def test_format_user_without_skills() -> None:
    provider = make_provider(user_template="{skills}")
    state = make_state()

    result = provider.format_user(state, [])

    assert result == "_(none)_"


def test_format_user_with_sequence() -> None:
    provider = make_provider(user_template="{sequence}")
    state = make_state(
        sequence=Sequence(
            language="plantuml",
            content="@startuml\nA -> B\n@enduml",
        )
    )

    result = provider.format_user(state, [])

    assert result == ("```plantuml\n@startuml\nA -> B\n@enduml\n```")


def test_format_user_without_sequence() -> None:
    provider = make_provider(user_template="{sequence}")
    state = make_state()

    result = provider.format_user(state, [])

    assert result == "_(none)_"


def test_format_user_with_empty_goal() -> None:
    provider = make_provider(user_template="{goal}")
    state = make_state()
    state.task.goal = ""

    result = provider.format_user(state, [])

    assert result == "_(none)_"


def test_format_user_with_empty_constitution() -> None:
    provider = make_provider(user_template="{constitution}")
    state = make_state(constitution="")

    result = provider.format_user(state, [])

    assert result == "_(none)_"


def test_format_user_raises_for_unknown_template_placeholder() -> None:
    provider = make_provider(user_template="{unknown}")
    state = make_state()

    with pytest.raises(KeyError, match="unknown"):
        provider.format_user(state, [])
