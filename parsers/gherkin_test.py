import pytest

from parsers.gherkin import GherkinParser, GherkinsParser


@pytest.fixture
def gherkin_parser():
    return GherkinParser()


@pytest.fixture
def gherkins_parser():
    return GherkinsParser()


@pytest.mark.parametrize("gherkin", ["", "   "])
def test_parse_gherkins_raises_for_missing_scenarios(gherkins_parser, gherkin):
    with pytest.raises(ValueError, match="No Gherkin scenarios found"):
        gherkins_parser.parse(gherkin)


def test_parse_gherkins_parses_single_scenario(gherkins_parser):
    gherkins = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    assert gherkins_parser.parse(gherkins) == [gherkins.strip()]


def test_parse_gherkins_parses_multiple_scenarios(gherkins_parser):
    gherkins = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```

## Scenario: Reject empty order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given empty order lines
When checkout is called
Then validation error is raised
```
"""

    scenarios = gherkins_parser.parse(gherkins)

    assert len(scenarios) == 2
    assert scenarios[0].startswith("## Scenario: Create order")
    assert scenarios[1].startswith("## Scenario: Reject empty order")


def test_parse_gherkins_skips_non_scenario_content(gherkins_parser):
    gherkins = """\
Some introduction.

## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    assert gherkins_parser.parse(gherkins) == [gherkins[gherkins.index("## Scenario:") :].strip()]


def test_parse_gherkins_raises_for_invalid_scenario_heading(gherkins_parser):
    gherkins = """\
## Scenario:

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    with pytest.raises(ValueError, match="Invalid Gherkin scenario heading"):
        gherkins_parser.parse(gherkins)


def test_parse_gherkin_parses_scenario(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    assert gherkin_parser.parse(gherkin) == {
        "name": "Create order",
        "fqns": ["services.checkout::CheckoutService"],
        "gherkin": ("Given valid order lines\nWhen checkout is called\nThen order is created"),
    }


@pytest.mark.parametrize(
    "gherkin",
    [
        "",
        "Some text without a scenario heading",
    ],
)
def test_parse_gherkin_raises_for_missing_scenario_heading(
    gherkin_parser,
    gherkin,
):
    with pytest.raises(
        ValueError,
        match="Missing '## Scenario: <name>' heading",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_empty_scenario_name(gherkin_parser):
    gherkin = """\
## Scenario:

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    with pytest.raises(
        ValueError,
        match="Missing '## Scenario: <name>' heading",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_missing_fqns_section(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    with pytest.raises(ValueError, match="Missing '### FQNs' section"):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_empty_fqns_section(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    with pytest.raises(
        ValueError,
        match="FullQualifiedNames section must contain at least one entry",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_parses_multiple_fqns(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`
- `repositories.orders::OrdersRepository`
- `models.order::Order`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```
"""

    result = gherkin_parser.parse(gherkin)

    assert result["fqns"] == [
        "services.checkout::CheckoutService",
        "repositories.orders::OrdersRepository",
        "models.order::Order",
    ]


def test_parse_gherkin_raises_for_missing_gherkin_section(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`
"""

    with pytest.raises(ValueError, match="Missing '### Gherkin' section"):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_missing_code_block(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

Given valid order lines
When checkout is called
Then order is created
"""

    with pytest.raises(
        ValueError,
        match="Scenario must contain exactly one Gherkin code block",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_multiple_code_blocks(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
```

```gherkin
Given another order
When checkout is called
Then another order is created
```
"""

    with pytest.raises(
        ValueError,
        match="Scenario must contain exactly one Gherkin code block",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_for_empty_code_block(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
```
"""

    with pytest.raises(
        ValueError,
        match="Gherkin code block cannot be empty",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_when_scenario_does_not_start_with_given(
    gherkin_parser,
):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
When checkout is called
Then order is created
```
"""

    with pytest.raises(ValueError, match="Scenario must start with Given"):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_without_when(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
Then order is created
```
"""

    with pytest.raises(
        ValueError,
        match="Scenario must contain exactly one When",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_with_multiple_when_steps(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
When checkout is called again
Then order is created
```
"""

    with pytest.raises(
        ValueError,
        match="Scenario must contain exactly one When",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_without_then(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
```
"""

    with pytest.raises(
        ValueError,
        match="Scenario must contain at least one Then",
    ):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_raises_when_when_appears_after_then(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
Then order is created
When checkout is called
```
"""

    with pytest.raises(ValueError, match="When must appear before Then"):
        gherkin_parser.parse(gherkin)


@pytest.mark.parametrize(
    "invalid_step",
    [
        "Given",
        "When",
        "Then",
        "Unknown invalid step",
    ],
)
def test_parse_gherkin_raises_for_invalid_step(gherkin_parser, invalid_step):
    gherkin = f"""\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
{invalid_step}
```
"""

    with pytest.raises(ValueError, match="Invalid Gherkin step"):
        gherkin_parser.parse(gherkin)


def test_parse_gherkin_accepts_and_step(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
When checkout is called
Then order is created
And order is saved
```
"""

    result = gherkin_parser.parse(gherkin)

    assert result["gherkin"] == (
        "Given valid order lines\nWhen checkout is called\nThen order is created\nAnd order is saved"
    )


def test_parse_gherkin_parses_multiple_and_steps(gherkin_parser):
    gherkin = """\
## Scenario: Create order

### FQNs

- `services.checkout::CheckoutService`

### Gherkin

```gherkin
Given valid order lines
And customer exists
When checkout is called
And storage succeeds
Then order is created
And order lines are persisted
```
"""

    result = gherkin_parser.parse(gherkin)

    assert result["gherkin"] == (
        "Given valid order lines\n"
        "And customer exists\n"
        "When checkout is called\n"
        "And storage succeeds\n"
        "Then order is created\n"
        "And order lines are persisted"
    )
