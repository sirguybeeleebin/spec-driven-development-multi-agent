# Task

- task_id: 001_products_repository

# Goal

Read a product row by primary key, returning a mapping with exactly five keys or None.

# FullQualifiedNames

| № | FullQualifiedName | Role |
|---:|---|---|
| 1 | `repositories.products::ProductRepository` | target |

# Interfaces

## repositories.products::ProductRepository

### Language

python

### Description

Repository for reading product records from the product store.
Wraps a SQLite connection supplied by the caller.
Provides a read-only lookup operation by product primary key.
Returns a plain dictionary containing exactly five fields when the product exists, or None when it does not.

### Steps

1. Store the supplied SQLite connection on the instance.
2. Expose get.
3. Query the product store by product_id.
4. Return None when no matching product exists.
5. Return a mapping with exactly five keys when a product exists: product_id, name, price_amount, price_currency, stock.

### Returns

The constructor returns None.

get returns a dict with exactly five keys — product_id, name, price_amount, price_currency, stock — or None when the product does not exist.

### Interface

```python
class ProductRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        ...

    def get(self, product_id: str) -> dict | None:
        ...
```

# Gherkins

## Scenario: get returns product

### FQNs

- repositories.products::ProductRepository
- repositories.products::test_get_returns_product

### Gherkin

```gherkin
Given an empty product store with the schema applied
And a product with id "p1", name "Pen", price "2.00" USD, stock 5 is inserted directly
And a ProductRepository wrapping the storage connection
When the product with id "p1" is looked up
Then the result has exactly five keys
And its product_id is "p1"
And its name is "Pen"
And its price_amount is "2.00"
And its price_currency is "USD"
And its stock is 5
```

## Scenario: get missing returns none

### FQNs

- repositories.products::ProductRepository
- repositories.products::test_get_missing_returns_none

### Gherkin

```gherkin
Given an empty product store with the schema applied
And a ProductRepository wrapping the storage connection
When the product with an unknown id is looked up
Then the result is none
``` 