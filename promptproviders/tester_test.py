import json

import pytest

from models import FullQualifiedName, Gherkin, Interface, Sequence, Skill, State, Task
from promptproviders.tester import TesterPromptProvider


def make_provider(
    user_template: str = ("{current_gherkin}\n{interfaces}\n{sequence}\n{skills}"),
) -> TesterPromptProvider:
    return TesterPromptProvider(
        system_template="system prompt",
        user_template=user_template,
        final_prompt="final prompt",
    )


def make_interface(
    *,
    name: str = "ProductRepository",
    language: str = "python",
    content: str = "class ProductRepository: ...",
    description: str = "Product repository",
    steps: list[str] | None = None,
) -> Interface:
    return Interface(
        name=name,
        language=language,
        content=content,
        description=description,
        steps=steps if steps is not None else ["Get product by ID"],
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
    content: str = "content",
) -> Skill:
    return Skill(name=name, description=description, content=content)


def make_state(
    *,
    goal: str = "Read a product by its primary key",
    interfaces: list[Interface] | None = None,
    gherkins: list[Gherkin] | None = None,
    constitution: str = "Use simple architecture",
    sequence: Sequence | None = None,
    current_gherkin: Gherkin | None = None,
) -> State:
    task = Task(
        task_id="001_products_repository",
        goal=goal,
        fqns=[],
        interfaces=interfaces if interfaces is not None else [make_interface()],
        gherkins=gherkins if gherkins is not None else [],
        constitution=constitution,
        sequence=sequence,
    )
    return State(
        task=task,
        current_gherkin=current_gherkin,
    )


def test_system_returns_system_template() -> None:
    provider = make_provider()

    assert provider.system == "system prompt"


def test_final_user_returns_final_prompt() -> None:
    provider = make_provider()

    assert provider.final_user == "final prompt"


def test_format_user() -> None:
    provider = make_provider()
    state = make_state(
        sequence=Sequence(
            language="python",
            content="repository.get(product_id)",
        ),
        current_gherkin=make_gherkin(),
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
    assert "## Interface: ProductRepository" in result
    assert "Language: python" in result
    assert "Description: Product repository" in result
    assert "1. Get product by ID" in result
    assert "class ProductRepository: ..." in result
    assert "repository.get(product_id)" in result
    assert "## Skill: pytest" in result
    assert "Pytest testing conventions" in result
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


def test_format_user_without_interfaces() -> None:
    provider = make_provider()
    state = make_state(interfaces=[])

    result = provider.format_user(state, [])

    assert "_(none)_" in result
    assert "## Interface:" not in result


def test_format_user_without_sequence() -> None:
    provider = make_provider()
    state = make_state(sequence=None)

    result = provider.format_user(state, [])

    assert "_(none)_" in result


def test_format_user_without_skills() -> None:
    provider = make_provider()
    state = make_state()

    result = provider.format_user(state, [])

    assert "## Skill:" not in result


def test_format_user_with_multiple_interfaces() -> None:
    provider = make_provider()
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
        ],
    )

    result = provider.format_user(state, [])

    assert "## Interface: ProductRepository" in result
    assert "class ProductRepository: ..." in result
    assert "## Interface: ProductService" in result
    assert "class ProductService: ..." in result


def test_format_user_without_optional_interface_fields() -> None:
    provider = make_provider()
    state = make_state(
        interfaces=[
            make_interface(
                description="",
                steps=[],
            ),
        ],
    )

    result = provider.format_user(state, [])

    assert "## Interface: ProductRepository" in result
    assert "Description:" not in result
    assert "Steps:" not in result
    assert "class ProductRepository: ..." in result


def test_format_user_with_multiple_gherkin_steps() -> None:
    provider = make_provider()
    state = make_state(
        current_gherkin=make_gherkin(
            given=["the database is initialized", "the product exists"],
            when=["the product is requested", "the result is inspected"],
            then=["the product is returned", "the result contains five keys"],
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
        make_skill(name="pytest", description="Testing framework"),
        make_skill(name="python", description="Python conventions"),
    ]

    result = provider.format_user(state, skills)

    assert "## Skill: pytest" in result
    assert "Testing framework" in result
    assert "## Skill: python" in result
    assert "Python conventions" in result


def test_format_user_uses_current_gherkin_instead_of_task_gherkins() -> None:
    provider = make_provider()
    task_gherkin = make_gherkin(name="another scenario")
    current_gherkin = make_gherkin(name="current scenario")
    state = make_state(
        gherkins=[task_gherkin],
        current_gherkin=current_gherkin,
    )

    result = provider.format_user(state, [])

    assert "## Scenario: current scenario" in result
    assert "## Scenario: another scenario" not in result


def test_format_user_does_not_include_other_task_fields() -> None:
    provider = make_provider()
    state = make_state(
        goal="This goal must not be included",
        constitution="These rules must not be included",
    )

    result = provider.format_user(state, [])

    assert "This goal must not be included" not in result
    assert "These rules must not be included" not in result


def test_parse_final_response() -> None:
    provider = make_provider()
    response = json.dumps(
        {
            "status": "success",
            "summary": "Test implemented",
        }
    )

    result = provider.parse_final_response(response)

    assert result == {
        "status": "success",
        "summary": "Test implemented",
    }


def test_parse_final_response_with_unicode() -> None:
    provider = make_provider()
    response = '{"status": "success", "summary": "Тест реализован"}'

    result = provider.parse_final_response(response)

    assert result["summary"] == "Тест реализован"


def test_parse_final_response_with_invalid_json() -> None:
    provider = make_provider()

    with pytest.raises(json.JSONDecodeError):
        provider.parse_final_response("{invalid json}")


def test_format_user_with_unknown_template_placeholder() -> None:
    provider = make_provider(user_template="{unknown}")

    with pytest.raises(KeyError, match="unknown"):
        provider.format_user(make_state(), [])
