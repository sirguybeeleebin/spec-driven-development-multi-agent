---
name: testing-with-mocks
description: Tests a service class whose Protocol-typed collaborators are injected through __init__. Uses MagicMock test doubles to verify orchestration, validation, collaborator calls, and result assembly. Use when the target test exercises a service class that consumes Protocol-typed collaborators through __init__.
---

# Testing with Mocks

You are a senior Python developer writing one pytest function per Gherkin scenario using mocked collaborators.

## Workflow

### Step 1. Analyze the scenario

Read the complete Gherkin scenario, target interface, and implementation.

Extract:
- Given — initial state and input data.
- When — service method being executed.
- Then — expected results and collaborator interactions.
- Raises — expected exception, when applicable.
- Returns — expected return structure, when applicable.

Identify:
- SUT class and module.
- Constructor parameters and their types.
- Method signature.
- Every collaborator method called by the SUT.
- Exact arguments and argument style (positional or keyword).
- Order of collaborator calls.
- Validation conditions.
- Exception handling and exception chaining.
- Values produced internally by the SUT.

The implementation is the source of truth for call order and argument style.

### Step 2. Plan imports

Determine the complete set of imports required by the test.

For a successful scenario:

    from unittest.mock import MagicMock
    from <sut module> import <SutClass>

For a failure scenario, additionally include:

    import pytest

For project-defined exceptions, import the exact exception class from its actual module.

Include additional imports according to the assertions:
- `ANY` — for internally generated arguments in mock call assertions.
- `call` — for ordered call sequences.
- `Decimal` — for decimal values.
- `uuid` — when UUID values are explicitly constructed in the test.
- Other standard-library or project imports required by the scenario.

All imports are placed inside the test function, one import per line, with four-space indentation.

Complete the import plan before writing the test.

### Step 3. Analyze collaborator execution

For each constructor parameter, inspect how the SUT uses it during the scenario.

Classify collaborators according to execution order:

- Before — called before the expected result or exception.
- At — called at the operation that produces the expected result or exception.
- After — called after the operation that produces the expected result or exception.

Record the exact method name, arguments, and expected return value for every call.

For each Before collaborator, determine the concrete return value required by the SUT.

Typical values include:
- `int`
- `str`
- `True` / `False`
- `None`
- `[]`
- `[{...}]`
- Dictionaries with the exact keys accessed by the implementation.

For an exception scenario, identify the collaborator whose method produces the exception and determine whether the SUT propagates or wraps it.

### Step 4. Plan MagicMock configuration

Create one `MagicMock()` for every constructor parameter.

Use the constructor parameter name as the variable name.

Example:

    repository = MagicMock()
    payment_gateway = MagicMock()
    event_publisher = MagicMock()

Configure method return values according to the implementation:

    repository.get_by_id.return_value = {
        "id": "o1",
        "status": "pending",
    }

    payment_gateway.charge.return_value = {
        "transaction_id": "tx1",
        "status": "success",
    }

    event_publisher.publish.return_value = None

For exception scenarios, configure the relevant method with `side_effect`:

    repository.get_by_id.return_value = None

Or, for a storage rejection:

    repository.insert.side_effect = StorageError("storage failure")

Use the exact exception class declared by the contract.

### Step 5. Plan the Arrange section

Prepare:
1. All MagicMock instances.
2. Concrete return values for methods used by the scenario.
3. Input arguments.
4. Expected values.
5. Any additional data required by the Given conditions.

Construct the SUT using keyword arguments matching its constructor:

    sut = CheckoutService(
        repository=repository,
        payment_gateway=payment_gateway,
        event_publisher=event_publisher,
    )

### Step 6. Write the test

Read the target test file and identify the required test function name.

Write one function with exactly that name.

Follow this structure:

1. Imports.
2. MagicMock construction.
3. Mock configuration.
4. SUT construction.
5. When — one SUT method call.
6. Then — result assertions.
7. Collaborator interaction assertions.

### Step 7. Assert results and interactions

Translate every Then condition into assertions.

For returned dictionaries:

    assert result is not None
    assert result["status"] == "success"
    assert result["transaction_id"] == "tx1"

For collaborator calls:

    repository.get_by_id.assert_called_once_with("o1")
    payment_gateway.charge.assert_called_once_with(
        order_id="o1",
        amount=Decimal("10.00"),
    )

For collaborators that execute after an expected failure:

    event_publisher.publish.assert_not_called()

For ordered calls:

    from unittest.mock import call

    assert repository.method.call_args_list == [
        call("o1"),
        call("o2"),
    ]

For internally generated values:

    assert result["transaction_id"] is not None
    assert isinstance(result["transaction_id"], str)

For wrapped exceptions:

    with pytest.raises(ServiceError) as exc_info:
        sut.execute("o1")

    assert exc_info.value.__cause__ is not None

For directly propagated exceptions, assert the exact exception class around the SUT call.

### Step 8. Verify the test

Read the resulting test function and verify:

1. The function name matches `# Test function`.
2. Every planned import is present inside the function.
3. Every constructor parameter has a corresponding MagicMock.
4. The SUT receives all constructor arguments by keyword.
5. Mock return values match the values consumed by the implementation.
6. The When operation matches the Gherkin scenario.
7. Every Then condition has a corresponding assertion.
8. Every collaborator called before the expected outcome has the correct call assertion.
9. Collaborators after the expected failure have the appropriate interaction assertion.
10. Exception assertions match the exact class from the contract.
11. Internally generated values are checked by type and presence.
12. The test function appears exactly once.

## Test Structure

### Successful scenario

    def test_<scenario>():
        from unittest.mock import MagicMock
        from services.checkout import CheckoutService

        repository = MagicMock()
        payment_gateway = MagicMock()

        repository.get_by_id.return_value = {
            "id": "o1",
            "status": "pending",
        }

        payment_gateway.charge.return_value = {
            "transaction_id": "tx1",
            "status": "success",
        }

        sut = CheckoutService(
            repository=repository,
            payment_gateway=payment_gateway,
        )

        result = sut.checkout("o1")

        assert result is not None
        assert result["status"] == "success"
        assert result["transaction_id"] == "tx1"

        repository.get_by_id.assert_called_once_with("o1")
        payment_gateway.charge.assert_called_once_with(
            order_id="o1",
        )

### Failure scenario

    def test_<scenario>():
        import pytest
        from unittest.mock import MagicMock
        from services.checkout import CheckoutService, CheckoutError

        repository = MagicMock()
        payment_gateway = MagicMock()

        repository.get_by_id.return_value = None

        sut = CheckoutService(
            repository=repository,
            payment_gateway=payment_gateway,
        )

        with pytest.raises(CheckoutError):
            sut.checkout("unknown")

        repository.get_by_id.assert_called_once_with("unknown")
        payment_gateway.charge.assert_not_called()

## Output

Emit the executable Python test function only.
