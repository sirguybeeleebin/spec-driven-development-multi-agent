# Task

- task_id: 003_order_lines_repository


# Goal

Persist one order line row, letting any storage rejection propagate unchanged.

# Interfaces

## FQN: repositories.order_lines::OrderLineRepository

```python
class OrderLineRepository:
    """Write access to the order_lines table; one line row per operation.

    Description:
        Repository for the order_lines table. Wraps one
        connection. The repository is write-only — it declares
        only the insert operation, no read-back.

    Steps:
        1. Store the connection on the instance.
        2. Expose insert.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Wrap a storage connection.

        Description:
            Store the connection on the instance.

        Steps:
            1. Store the connection on the instance.
            2. Return None.
        """
        ...

    def insert(
        self,
        order_id: str,
        product_id: str,
        qty: int,
        unit_amount: str,
        unit_currency: str,
    ) -> None:
        """Insert one order line row.

        Description:
            Persist one line associated with the given order. Any
            storage rejection propagates unchanged.

        Steps:
            1. Persist one line row with the five fields.
            2. Let any storage rejection propagate unchanged.
            3. Return None.
        """
        ...
```

# Gherkins

## Scenario: insert writes one line

### FQN: repositories.order_lines::OrderLineRepository

### Test FQN: repositories.order_lines::test_insert_writes_one_line

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an order with id "o1" and a product with id "p1" are persisted directly
When a line for order "o1" and product "p1" is inserted with qty 2 and unit "2.00" USD
Then the order_lines table contains one row for (order_id "o1", product_id "p1")
And that row's qty is 2
```

## Scenario: insert duplicate composite key raises

### FQN: repositories.order_lines::OrderLineRepository

### Test FQN: repositories.order_lines_test::test_insert_duplicate_composite_key_raises

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an order with id "o1" and a product with id "p1" are persisted directly
And a line for order "o1" and product "p1" is inserted
When another line for the same order and product is inserted
Then the storage's integrity error is raised
```

## Scenario: insert with unknown reference raises

### FQN: repositories.order_lines::OrderLineRepository

### Test FQN: repositories.order_lines_test::test_insert_with_unknown_reference_raises

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And a product with id "p1" is persisted directly
When a line is inserted for an order id that does not exist
Then the storage's referential integrity error is raised
```