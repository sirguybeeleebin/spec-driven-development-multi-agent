# Task

- task_id: 002_orders_repository

# Goal

Persist one order header row, letting any storage rejection propagate unchanged.

# FullQualifiedNames

| № | FullQualifiedName | Role |
|---:|---|---|
| 1 | `repositories.orders::OrderRepository` | target |

# Interfaces

## repositories.orders::OrderRepository

### Language

python

### Description

Repository for the orders table.
Wraps a SQLite connection supplied by the caller.
The repository is write-only — it declares only the insert operation, with no read-back.
Persists one order header row with the supplied values.
Any storage rejection, including a duplicate order_id, propagates unchanged.

### Steps

1. Store the supplied SQLite connection on the instance.
2. Expose insert.
3. Persist one order row with the supplied order_id, customer_id, status, and created_at.
4. Let any storage rejection propagate unchanged.

### Returns

The constructor returns None.

insert returns None after successfully persisting one order header row. Any storage exception propagates unchanged.

### Interface

```python
class OrderRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        ...

    def insert(
        self,
        order_id: str,
        customer_id: str,
        status: str,
        created_at: str,
    ) -> None:
        ...
```

# Gherkins

## Scenario: insert writes header row

### FQNs

- repositories.orders::OrderRepository
- repositories.orders::test_insert_writes_header_row

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an OrderRepository wrapping the storage connection
When an order with id "o1", customer "c1", status "PENDING", created at "2024-01-01T00:00:00+00:00" is inserted
Then the orders table contains one row with order_id "o1"
And that row's status is "PENDING"
```

## Scenario: insert duplicate raises

### FQNs

- repositories.orders::OrderRepository
- repositories.orders::test_insert_duplicate_raises

### Gherkin

```gherkin
Given an empty shop store with the schema applied
And an OrderRepository wrapping the storage connection
And an order with id "o1" is inserted
When another order with the same id "o1" is inserted
Then the storage's integrity error is raised unchanged
```