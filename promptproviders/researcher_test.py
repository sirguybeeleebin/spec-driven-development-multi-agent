from __future__ import annotations

import json

from models import (
    FullQualifiedName,
    Interface,
    Sequence,
    Skill,
    State,
    Task,
)
from promptproviders.researcher import ResearcherPromptProvider


def make_state(
    *,
    fqns: list[FullQualifiedName] | None = None,
    interfaces: list[Interface] | None = None,
    sequence: Sequence | None = None,
    constitution: str = "Follow project rules.",
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
    return State(task=task)


def make_provider(
    user_template: str,
    *,
    system_template: str = "Researcher system prompt.",
    final_prompt: str = "Return JSON.",
) -> ResearcherPromptProvider:
    return ResearcherPromptProvider(
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
            "{goal}\n{fqns}\n{interfaces}\n{constitution}\n{sequence}\n{skills}"
        )
    )
    state = make_state(
        fqns=[
            FullQualifiedName("repositories.products::ProductRepository"),
            FullQualifiedName("services.products::ProductService"),
        ],
        interfaces=[
            Interface(
                name="ProductRepository",
                language="python",
                content="class ProductRepository:\n    def get(self, product_id: int): ...",
                description="Reads products from the database.",
                steps=["Get a product by ID", "Return None if missing"],
            )
        ],
        sequence=Sequence(
            language="mermaid",
            content="A --> B",
        ),
    )
    skills = [
        Skill(
            name="pytest",
            description="Pytest testing guidelines.",
            content="Use pytest fixtures and parametrize where appropriate.",
        )
    ]

    result = provider.format_user(state, skills)

    assert "Implement product repository." in result
    assert "- `repositories.products::ProductRepository`" in result
    assert "- `services.products::ProductService`" in result
    assert "## Interface: ProductRepository" in result
    assert "Language: python" in result
    assert "Description: Reads products from the database." in result
    assert "1. Get a product by ID" in result
    assert "2. Return None if missing" in result
    assert "class ProductRepository:" in result
    assert "Follow project rules." in result
    assert "```mermaid\nA --> B\n```" in result
    assert "## Skill: pytest" in result
    assert "Pytest testing guidelines." in result


def test_format_user_without_optional_data() -> None:
    provider = make_provider(
        user_template=(
            "{goal}\n{fqns}\n{interfaces}\n{constitution}\n{sequence}\n{skills}"
        )
    )
    state = make_state(constitution="")

    result = provider.format_user(state, [])

    assert "Implement product repository." in result
    assert result.count("_(none)_") == 5


def test_format_user_with_interface_without_description_and_steps() -> None:
    provider = make_provider(user_template="{interfaces}")
    state = make_state(
        interfaces=[
            Interface(
                name="ProductRepository",
                language="python",
                content="class ProductRepository: ...",
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


def test_parse_final_response() -> None:
    provider = make_provider(user_template="{goal}")
    response = {
        "summary": "Research completed.",
        "findings": ["Finding 1", "Finding 2"],
    }

    result = provider.parse_final_response(json.dumps(response, ensure_ascii=False))

    assert result == response


def test_parse_final_response_with_invalid_json() -> None:
    provider = make_provider(user_template="{goal}")

    try:
        provider.parse_final_response("invalid json")
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("Expected JSONDecodeError")
