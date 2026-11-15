from __future__ import annotations

import pytest

from models import FullQualifiedName, Gherkin, Interface, Sequence, Task
from parsers.task import parse_task

CONSTITUTION = "Project constitution"

INTERFACES = """\
## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    Description:
        Creates an order from order lines.
    Steps:
        1. Validate order lines.
        2. Persist the order.
```

## FQN: repositories.products::ProductRepository

```python
class ProductRepository:
    def get(self, product_id: str) -> dict | None:
        ...
```
"""

GHERKINS = """\
## Scenario: creates an order

### FQN: services.checkout::CheckoutService

### Test FQN: services.checkout::test_creates_an_order

### Gherkin

```gherkin
Given valid order lines
And a customer identifier
When checkout is called
Then an order is persisted
And the order is returned
```

## Scenario: returns a product

### FQN: repositories.products::ProductRepository

### Test FQN: repositories.products::test_returns_a_product

### Gherkin

```gherkin
Given a product identifier
When the product is requested
Then the product is returned
```
"""


SEQUENCE = """\
sequenceDiagram
    participant C as Caller
    participant S as CheckoutService
    C->>S: checkout()
    S-->>C: order
"""


def make_task_text(
    *,
    task_section: str = "- task_id: test_task",
    goal: str = "Implement the requested behavior.",
    interfaces: str = INTERFACES,
    gherkins: str = GHERKINS,
    sequence: str | None = None,
) -> str:
    sections = [
        "# Task\n" + task_section,
        "# Goal\n" + goal,
        "# Interfaces\n" + interfaces,
        "# Gherkins\n" + gherkins,
    ]

    if sequence is not None:
        sections.append("# Sequence\n```mermaid\n" + sequence + "\n```")

    return "\n\n".join(sections)


def make_gherkin(
    *,
    name: str = "executes checkout",
    fqn: str = "services.checkout::CheckoutService",
    test_fqn: str = "services.checkout::test_executes_checkout",
    steps: str = (
        "Given a checkout service\nWhen checkout is called\nThen checkout is executed"
    ),
) -> str:
    return (
        f"## Scenario: {name}\n\n"
        f"### FQN: {fqn}\n\n"
        f"### Test FQN: {test_fqn}\n\n"
        f"### Gherkin\n\n"
        f"```gherkin\n{steps}\n```"
    )


def test_parse_task() -> None:
    task = parse_task(
        make_task_text(sequence=SEQUENCE),
        constitution=CONSTITUTION,
    )

    assert isinstance(task, Task)
    assert task.task_id == "test_task"
    assert task.goal == "Implement the requested behavior."
    assert task.constitution == CONSTITUTION
    assert task.fqns == [
        FullQualifiedName("services.checkout::CheckoutService"),
        FullQualifiedName("repositories.products::ProductRepository"),
    ]
    assert task.interfaces == [
        Interface(
            name="CheckoutService",
            language="python",
            content=(
                "class CheckoutService:\n"
                "    Description:\n"
                "        Creates an order from order lines.\n"
                "    Steps:\n"
                "        1. Validate order lines.\n"
                "        2. Persist the order."
            ),
            description="Creates an order from order lines.",
            steps=[
                "Validate order lines.",
                "Persist the order.",
            ],
        ),
        Interface(
            name="ProductRepository",
            language="python",
            content=(
                "class ProductRepository:\n"
                "    def get(self, product_id: str) -> dict | None:\n"
                "        ..."
            ),
            description="",
            steps=[],
        ),
    ]
    assert task.gherkins == [
        Gherkin(
            name="creates an order",
            fqn=FullQualifiedName("services.checkout::CheckoutService"),
            test_fqn=FullQualifiedName("services.checkout::test_creates_an_order"),
            given=[
                "valid order lines",
                "a customer identifier",
            ],
            when=["checkout is called"],
            then=[
                "an order is persisted",
                "the order is returned",
            ],
        ),
        Gherkin(
            name="returns a product",
            fqn=FullQualifiedName("repositories.products::ProductRepository"),
            test_fqn=FullQualifiedName("repositories.products::test_returns_a_product"),
            given=["a product identifier"],
            when=["the product is requested"],
            then=["the product is returned"],
        ),
    ]
    assert task.sequence == Sequence(
        language="mermaid",
        content=SEQUENCE.strip(),
    )


def test_parse_task_without_sequence() -> None:
    task = parse_task(make_task_text(), constitution=CONSTITUTION)

    assert task.sequence is None


def test_parse_task_with_plantuml_sequence() -> None:
    sequence = """\
@startuml
actor Caller
Caller -> Service: execute
Service --> Caller: result
@enduml
"""

    text = make_task_text()
    text += f"\n\n# Sequence\n```plantuml\n{sequence}\n```"

    task = parse_task(text, constitution=CONSTITUTION)

    assert task.sequence == Sequence(
        language="plantuml",
        content=sequence.strip(),
    )


def test_parse_task_preserves_interface_language_and_content() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

```typescript
export class CheckoutService {
    checkout(): void {}
}
```
"""
    gherkins = make_gherkin()

    task = parse_task(
        make_task_text(interfaces=interfaces, gherkins=gherkins),
        constitution=CONSTITUTION,
    )

    assert task.interfaces[0].language == "typescript"
    assert task.interfaces[0].content == (
        "export class CheckoutService {\n    checkout(): void {}\n}"
    )


def test_parse_task_matches_gherkin_to_explicit_fqn() -> None:
    interfaces = """\
## FQN: repositories.products::ProductRepository

```python
class ProductRepository:
    ...
```

## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    ...
```
"""
    gherkins = "\n\n".join(
        [
            make_gherkin(
                name="executes checkout",
                fqn="services.checkout::CheckoutService",
                test_fqn="services.checkout::test_executes_checkout",
            ),
            make_gherkin(
                name="gets a product",
                fqn="repositories.products::ProductRepository",
                test_fqn="repositories.products::test_gets_a_product",
            ),
        ]
    )

    task = parse_task(
        make_task_text(interfaces=interfaces, gherkins=gherkins),
        constitution=CONSTITUTION,
    )

    assert task.gherkins[0].fqn == FullQualifiedName(
        "services.checkout::CheckoutService"
    )
    assert task.gherkins[1].fqn == FullQualifiedName(
        "repositories.products::ProductRepository"
    )


def test_parse_task_rejects_empty_constitution() -> None:
    with pytest.raises(ValueError, match="constitution is empty"):
        parse_task(make_task_text(), constitution="")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "# Task\n- task_id: test_task\n# Goal\nGoal",
        "# Task\n- task_id: test_task\n# Goal\nGoal\n# Interfaces\n",
        "# Task\n- task_id: test_task\n# Goal\nGoal\n# Gherkins\n",
    ],
)
def test_parse_task_rejects_missing_required_sections(text: str) -> None:
    with pytest.raises(ValueError, match="missing '#"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_missing_task_id() -> None:
    text = make_task_text(task_section="- target_file: app.py")

    with pytest.raises(ValueError, match="missing 'task_id'"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_task_id() -> None:
    text = make_task_text(task_section="- task_id:    ")

    with pytest.raises(ValueError, match="empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_goal() -> None:
    text = make_task_text(goal="  ")

    with pytest.raises(ValueError, match="goal is empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_no_interfaces() -> None:
    text = make_task_text(interfaces="")

    with pytest.raises(ValueError, match="no interfaces declared"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_interface_fqn() -> None:
    interfaces = """\
## FQN:

```python
class CheckoutService:
    ...
```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="FQN is empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_invalid_interface_fqn() -> None:
    interfaces = """\
## FQN: CheckoutService

```python
class CheckoutService:
    ...
```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="missing '::' separator"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_duplicate_fqn() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    ...
```

## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    ...
```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="duplicate entry"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_duplicate_short_name() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    ...
```

## FQN: services.legacy::CheckoutService

```python
class CheckoutService:
    ...
```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="short name"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_interface_without_fence() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

No code block.
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="expected exactly one fenced block"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_interface_with_multiple_fences() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

```python
class CheckoutService:
    ...
```

```text
additional block
```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="expected exactly one fenced block"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_interface_content() -> None:
    interfaces = """\
## FQN: services.checkout::CheckoutService

```python

```
"""

    text = make_task_text(interfaces=interfaces)

    with pytest.raises(ValueError, match="content is empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_no_gherkins() -> None:
    text = make_task_text(gherkins="")

    with pytest.raises(ValueError, match="no gherkins declared"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_gherkin_name() -> None:
    gherkins = make_gherkin(name="")

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="gherkin: empty name"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_duplicate_gherkin_name() -> None:
    gherkin = make_gherkin()

    text = make_task_text(gherkins=f"{gherkin}\n\n{gherkin}")

    with pytest.raises(ValueError, match="duplicate name"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_gherkin_with_unknown_target() -> None:
    gherkins = make_gherkin(
        fqn="services.unknown::UnknownService",
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="is not declared"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_gherkin_fqn() -> None:
    gherkins = make_gherkin(fqn="")

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="FQN is empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_invalid_gherkin_fqn() -> None:
    gherkins = make_gherkin(fqn="CheckoutService")

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="missing '::' separator"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_empty_test_fqn() -> None:
    gherkins = make_gherkin(test_fqn="")

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="Test FQN is empty"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_invalid_test_fqn() -> None:
    gherkins = make_gherkin(test_fqn="test_executes_checkout")

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="missing '::' separator"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_duplicate_test_fqn() -> None:
    first = make_gherkin(
        name="first scenario",
        test_fqn="services.checkout::test_checkout",
    )
    second = make_gherkin(
        name="second scenario",
        test_fqn="services.checkout::test_checkout",
    )

    text = make_task_text(gherkins=f"{first}\n\n{second}")

    with pytest.raises(ValueError, match="duplicate Test FQN"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_missing_gherkin_fqn() -> None:
    gherkins = """\
## Scenario: executes checkout

### Test FQN: services.checkout::test_executes_checkout

### Gherkin

```gherkin
Given a checkout service
When checkout is called
Then checkout is executed
```
"""

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one FQN"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_multiple_gherkin_fqns() -> None:
    gherkins = make_gherkin().replace(
        "### Test FQN:",
        "### FQN: services.checkout::CheckoutService\n\n### Test FQN:",
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one FQN"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_missing_test_fqn() -> None:
    gherkins = """\
## Scenario: executes checkout

### FQN: services.checkout::CheckoutService

### Gherkin

```gherkin
Given a checkout service
When checkout is called
Then checkout is executed
```
"""

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one Test FQN"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_multiple_test_fqns() -> None:
    gherkins = make_gherkin().replace(
        "### Gherkin",
        "### Test FQN: services.checkout::test_another\n\n### Gherkin",
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one Test FQN"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_missing_gherkin_heading() -> None:
    gherkins = """\
## Scenario: executes checkout

### FQN: services.checkout::CheckoutService

### Test FQN: services.checkout::test_executes_checkout

```gherkin
Given a checkout service
When checkout is called
Then checkout is executed
```
"""

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_multiple_gherkin_headings() -> None:
    gherkins = make_gherkin().replace(
        "### Gherkin",
        "### Gherkin\n\n### Gherkin",
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="expected exactly one"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_missing_gherkin_fence() -> None:
    gherkins = """\
## Scenario: executes checkout

### FQN: services.checkout::CheckoutService

### Test FQN: services.checkout::test_executes_checkout

### Gherkin

Given a checkout service.
"""

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="missing ```gherkin``` block"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_gherkin_line_without_keyword() -> None:
    gherkins = make_gherkin(
        steps=(
            "Given a checkout service\ncheckout is called\nThen checkout is executed"
        )
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="line without keyword"):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_gherkin_and_without_preceding_keyword() -> None:
    gherkins = make_gherkin(
        steps=(
            "And a checkout service\nWhen checkout is called\nThen checkout is executed"
        )
    )

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match="'And' without preceding keyword"):
        parse_task(text, constitution=CONSTITUTION)


@pytest.mark.parametrize(
    ("steps", "error"),
    [
        (
            "When checkout is called\nThen checkout is executed",
            "has no Given step",
        ),
        (
            "Given a checkout service\nThen checkout is executed",
            "has no When step",
        ),
        (
            "Given a checkout service\nWhen checkout is called",
            "has no Then step",
        ),
    ],
)
def test_parse_task_rejects_gherkin_missing_required_step(
    steps: str,
    error: str,
) -> None:
    gherkins = make_gherkin(steps=steps)

    text = make_task_text(gherkins=gherkins)

    with pytest.raises(ValueError, match=error):
        parse_task(text, constitution=CONSTITUTION)


def test_parse_task_rejects_sequence_without_supported_fence() -> None:
    text = make_task_text()
    text += "\n\n# Sequence\nUnsupported sequence format."

    with pytest.raises(
        ValueError,
        match="no ```mermaid``` or ```plantuml``` block",
    ):
        parse_task(text, constitution=CONSTITUTION)


@pytest.mark.parametrize("language", ["mermaid", "plantuml"])
def test_parse_task_rejects_empty_sequence(language: str) -> None:
    text = make_task_text()
    text += f"\n\n# Sequence\n```{language}\n\n```"

    with pytest.raises(ValueError, match="sequence: .* content is empty"):
        parse_task(text, constitution=CONSTITUTION)
