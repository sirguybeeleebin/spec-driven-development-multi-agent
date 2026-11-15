# Task

- task_id: 003_order_lines_repository

# Goal

Persist one order line row, letting any storage rejection propagate unchanged.

# FullQualifiedNames

| № | FullQualifiedName | Role |
|---:|---|---|
| 1 | `repositories.order_lines::OrderLineRepository` | target |

# Interfaces

## repositories.order_lines::OrderLineRepository

### Language

python

### Description

Repository for the order_lines table.
Wraps a SQLite connection supplied by the caller.
The repository is write-only — it declares only the insert operation, with no read-back.
Persists one order line associated with the supplied order and product.
Any storage rejection, including duplicate composite keys and foreign key violations, propagates unchanged.

### Steps

1. Store the supplied SQLite connection on the instance.
2. Expose insert.
3. Persist one order line with the supplied order_id, product_id, qty, unit_amount, and unit_currency.
4. Let any storage rejection propagate unchanged.

### Returns

The constructor returns None.

insert returns None after successfully persisting one order line row. Any storage exception propagates unchanged.

### Interface

```python
class OrderLineRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        ...

    def insert(
        self,
        order_id: str,
        product_id: str,
        qty: int,
        unit_amount: str,
        unit_currency: str,
    ) -> None:
        ...
```

# Gherkins

## Scenario: insert writes one line

### FQNs

- repositories.order_lines::OrderLineRepository
- repositories.order_lines::test_insert_writes_one_line

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an order with id "o1" and a product with id "p1" are persisted directly
And an OrderLineRepository wrapping the storage connection
When a line for order "o1" and product "p1" is inserted with qty 2 and unit "2.00" USD
Then the order_lines table contains one row for (order_id "o1", product_id "p1")
And that row's qty is 2
```

## Scenario: insert duplicate composite key raises

### FQNs

- repositories.order_lines::OrderLineRepository
- repositories.order_lines::test_insert_duplicate_composite_key_raises

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an order with id "o1" and a product with id "p1" are persisted directly
And an OrderLineRepository wrapping the storage connection
And a line for order "o1" and product "p1" is inserted
When another line for the same order and product is inserted
Then the storage's integrity error is raised unchanged
```

## Scenario: insert with unknown reference raises

### FQNs

- repositories.order_lines::OrderLineRepository
- repositories.order_lines::test_insert_with_unknown_reference_raises

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And a product with id "p1" is persisted directly
And an OrderLineRepository wrapping the storage connection
When a line is inserted for an order id that does not exist
Then the storage's referential integrity error is raised unchanged
```