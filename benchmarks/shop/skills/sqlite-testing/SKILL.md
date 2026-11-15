---
name: sqlite-testing
description: Writes pytest tests for SQLite repositories using a real in-memory sqlite3.Connection and the project's actual SQL migrations. Runs exactly one generated test from the existing workspace without changing the working directory.
---

# SQLite Testing

You are a senior Python developer writing one pytest function per Gherkin scenario against a real SQLite in-memory database.

## Workflow

### Step 1. Find migration directory

1. Inspect the project structure using:

       tree -L 3 --noreport -I __pycache__ .

2. Locate directories containing `.sql` migration files.
3. Read every migration file in the relevant migration directory.
4. Identify the schema required by the repository:
   - Tables and columns.
   - Column types and constraints.
   - Primary and foreign keys.
5. Record the migration directory relative to the current workspace.

Use the discovered directory when loading migrations:

```python
migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
for path in sorted(migrations_dir.glob("*.sql")):
    conn.executescript(path.read_text(encoding="utf-8"))
```

### Step 2. Analyze Gherkin scenario

Read the complete Gherkin scenario, target declaration, interface, and repository implementation.

Extract:

- Given — initial database records.
- When — repository method and arguments.
- Then — expected return values and persisted state.
- Raises — expected exception, if specified.
- Returns — expected return structure, if specified.

Compare the scenario with the actual schema and implementation.

Determine:

- Repository class and module.
- Constructor parameters.
- SQL operations.
- Required fixture records.
- Expected database changes.
- Exact exception class for failure scenarios.

Given establishes the initial state. When performs the operation under test. Then verifies its outcome.

### Step 3. Plan the test

Plan the complete test using four blocks.

#### 3.1 IMPORTS

Successful scenario:

    import sqlite3
    from pathlib import Path
    from repositories.example import ExampleRepository

Failure scenario:

    import pytest
    import sqlite3
    from pathlib import Path
    from repositories.example import ExampleRepository

Import project-defined exception classes when required.

All imports belong inside the test function, one per line.

#### 3.2 SETUP

Create a real in-memory database:

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

Apply the actual project migrations:

```python
migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
for path in sorted(migrations_dir.glob("*.sql")):
    conn.executescript(path.read_text(encoding="utf-8"))
```

Insert records required by Given using actual schema column names and compatible Python values.

Use parameterized SQL:

    conn.execute(
        "INSERT INTO products (product_id, name, stock) VALUES (?, ?, ?)",
        ("p1", "Pen", 5),
    )

Commit fixture records before ACT:

    conn.commit()

Construct the repository:

    sut = ExampleRepository(conn=conn)

#### 3.3 ACT

Execute exactly the operation specified by When.

Successful operation:

    result = sut.get("p1")

Write operations:

    sut.insert(
        order_id="o1",
        product_id="p1",
        qty=2,
        unit_amount="2.00",
        unit_currency="USD",
    )

Failure scenario:

    with pytest.raises(sqlite3.IntegrityError):
        sut.insert(...)

Use the exception class established from the contract and implementation.

#### 3.4 CHECK

Translate every Then condition into assertions.

Returned dictionary:

    assert result is not None
    assert len(result) == 5
    assert result["product_id"] == "p1"
    assert result["stock"] == 5

Persisted record:

    row = conn.execute(
        "SELECT order_id, product_id, qty "
        "FROM order_lines "
        "WHERE order_id = ? AND product_id = ?",
        ("o1", "p1"),
    ).fetchone()

    assert row is not None
    assert row["qty"] == 2

Row count:

    count = conn.execute(
        "SELECT COUNT(*) FROM order_lines"
    ).fetchone()[0]

    assert count == 1

Missing record:

    assert result is None

Every Then condition must have a corresponding assertion.

### Step 5. Run exactly the generated test

The TESTER agent is responsible for executing the test through BashTool.

Run ONLY the test written in Step 4.

Example:

Generated test:

    def test_get_returns_product():
        ...

Test file:

    repositories/products_test.py

Exact command:

    python -m pytest repositories/products_test.py::test_get_returns_product -v

#### If the test fails

1. Read the actual pytest output.
2. Identify the failure.
3. Determine whether the issue is in the test or implementation.
4. Correct the appropriate code.
5. Rerun ONLY the same test using the same exact node ID.

Example:

    python -m pytest repositories/products_test.py::test_get_returns_product -v

Never run all tests to investigate a single failure.

#### If the test cannot be found

1. Read the target test file.
2. Verify the function name.
3. Verify the relative file path.
4. Correct the pytest node ID.
5. Retry only that specific test.

Never fall back to running the entire file.


