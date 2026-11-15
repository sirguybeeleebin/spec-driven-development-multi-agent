import pytest

from parsers.interface import InterfaceParser, InterfacesParser


@pytest.fixture
def interfaces_parser():
    return InterfacesParser()


@pytest.fixture
def interface_parser():
    return InterfaceParser()


def test_parse_interfaces_raises_for_missing_code_blocks(interfaces_parser):
    with pytest.raises(ValueError, match="No interface code blocks found"):
        interfaces_parser.parse("No interface code blocks")


def test_parse_interfaces_raises_for_invalid_code_block(interfaces_parser):
    interfaces = """
```python
def checkout():
    pass
```
```
"""

    with pytest.raises(ValueError, match="Invalid interface code block"):
        interfaces_parser.parse(interfaces)


def test_parse_interfaces_parses_single_code_block(interfaces_parser):
    interfaces = """
```python
def checkout():
    return True
```
"""

    assert interfaces_parser.parse(interfaces) == [
        {
            "language": "python",
            "code": "def checkout():\n    return True",
        }
    ]


def test_parse_interfaces_parses_multiple_code_blocks(interfaces_parser):
    interfaces = """
```python
def checkout():
    return True
```

```sql
SELECT * FROM orders;
```
"""

    assert interfaces_parser.parse(interfaces) == [
        {
            "language": "python",
            "code": "def checkout():\n    return True",
        },
        {
            "language": "sql",
            "code": "SELECT * FROM orders;",
        },
    ]


def test_parse_interfaces_strips_code_block_whitespace(interfaces_parser):
    interfaces = """
```python

def checkout():
    return True

```
"""

    assert interfaces_parser.parse(interfaces) == [
        {
            "language": "python",
            "code": "def checkout():\n    return True",
        }
    ]


def test_parse_interface_parses_interface(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Creates and persists an order.

### Steps

1. Validate order lines.
2. Persist the order.
3. Return the created order.

### Returns

A dictionary containing the created order.

### Interface

```python
class CheckoutService:
    def checkout(self, lines: list[dict]) -> dict:
        ...
```
"""

    assert interface_parser.parse(interface) == {
        "fqn": "services.checkout::CheckoutService",
        "language": "python",
        "description": "Creates and persists an order.",
        "steps": [
            "Validate order lines.",
            "Persist the order.",
            "Return the created order.",
        ],
        "returns": "A dictionary containing the created order.",
        "code": ("class CheckoutService:\n    def checkout(self, lines: list[dict]) -> dict:\n        ..."),
    }


def test_parse_interface_raises_for_missing_fqn(interface_parser):
    interface = """
### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Missing or empty FullQualifiedName"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_empty_fqn(interface_parser):
    interface = """
##

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Missing or empty FullQualifiedName"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_duplicate_fqn(interface_parser):
    interface = """
## services.checkout::CheckoutService

## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Duplicate FullQualifiedName"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_missing_language(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Missing or empty Language"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_empty_language(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Missing or empty Language"):
        interface_parser.parse(interface)


@pytest.mark.parametrize(
    "section",
    [
        "Description",
        "Steps",
        "Returns",
    ],
)
def test_parse_interface_raises_for_missing_section(
    interface_parser,
    section,
):
    sections = {
        "Description": "Description.",
        "Steps": "1. Validate input.",
        "Returns": "Result.",
    }
    sections.pop(section)

    interface = f"""
## services.checkout::CheckoutService

### Language

python

### Description

{sections.get("Description", "")}

### Steps

{sections.get("Steps", "")}

### Returns

{sections.get("Returns", "")}

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match=f"Missing or empty {section}"):
        interface_parser.parse(interface)


@pytest.mark.parametrize(
    "section",
    [
        "Description",
        "Steps",
        "Returns",
    ],
)
def test_parse_interface_raises_for_empty_section(
    interface_parser,
    section,
):
    sections = {
        "Description": "Description.",
        "Steps": "1. Validate input.",
        "Returns": "Result.",
    }
    sections[section] = ""

    interface = f"""
## services.checkout::CheckoutService

### Language

python

### Description

{sections["Description"]}

### Steps

{sections["Steps"]}

### Returns

{sections["Returns"]}

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match=f"Missing or empty {section}"):
        interface_parser.parse(interface)


@pytest.mark.parametrize(
    "section",
    [
        "Description",
        "Steps",
        "Returns",
        "Interface",
    ],
)
def test_parse_interface_raises_for_duplicate_section(
    interface_parser,
    section,
):
    interface = f"""
## services.checkout::CheckoutService

### Language

python

### {section}

Content.

### {section}

Duplicate content.

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match=f"Duplicate {section}"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_missing_interface_section(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.
"""

    with pytest.raises(ValueError, match="Missing or empty Interface"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_missing_code_block(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface
"""

    with pytest.raises(ValueError, match="Missing or empty code block"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_empty_code_block(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
```
"""

    with pytest.raises(ValueError, match="Missing or empty code block"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_unclosed_code_block(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
"""

    with pytest.raises(ValueError, match="Invalid interface code block"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_multiple_code_blocks(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```

```python
def another():
    ...
```
"""

    with pytest.raises(ValueError, match="Invalid interface code block"):
        interface_parser.parse(interface)


@pytest.mark.parametrize(
    "invalid_step",
    [
        "Validate input.",
        "1.",
        "one. Validate input.",
        "- Validate input.",
        "1 Validate input.",
    ],
)
def test_parse_interface_raises_for_invalid_step(
    interface_parser,
    invalid_step,
):
    interface = f"""
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

{invalid_step}

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Invalid interface step"):
        interface_parser.parse(interface)


def test_parse_interface_raises_for_steps_without_entries(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps


### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    with pytest.raises(ValueError, match="Missing or empty Steps"):
        interface_parser.parse(interface)


def test_parse_interface_parses_steps_with_blank_lines(interface_parser):
    interface = """
## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

2. Persist order.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```
"""

    result = interface_parser.parse(interface)

    assert result["steps"] == [
        "Validate input.",
        "Persist order.",
    ]


def test_parse_interface_ignores_content_outside_sections(interface_parser):
    interface = """
Some introductory text.

## services.checkout::CheckoutService

### Language

python

### Description

Description.

### Steps

1. Validate input.

### Returns

Result.

### Interface

```python
def checkout():
    ...
```

Some trailing text.
"""

    result = interface_parser.parse(interface)

    assert result["fqn"] == "services.checkout::CheckoutService"
    assert result["code"] == "def checkout():\n    ..."
