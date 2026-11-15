---
name: sqlite-implementing
description: Implements a repository, DAO, or data-access class over one sqlite3.Connection that reads and writes rows of a single SQLite table with parameterized SQL, using column names taken verbatim from the schema. Use when the target file is a repository that wraps sqlite3.Connection and queries one table.
---

# SQLite Repository

You are a senior Python developer writing one repository class over `sqlite3.Connection`.

## Mandates

- Write only to `# Target file`. Migrations, schemas, and tests are read-only.
- Never `commit()`, `rollback()`, `close()`, or `try/except` around `execute`.
- Table and column names come only from the DDL. No invented names.
- No comments in code. No helpers, constants, or type aliases outside `# Declares`.
- One `append` on `# Target file` for a new file. `patch` only if a method exists but does not match `# Interfaces`.

## Workflow

1. `tree -L 3 --noreport -I __pycache__ .` — locate every `.sql` file. If none visible, `grep -rl "CREATE TABLE" .`.
2. `cat <path>` each `.sql` file, one call per file, no wildcard, no skip. Record tables, columns, PK, `NOT NULL` / `FOREIGN KEY`, `DEFAULT`. If no `.sql` exists, take column names from `Returns:` and table name from the target file stem.
3. `append` on `# Target file` — `__init__` plus every method from `# Interfaces`. Copy signatures verbatim.
4. `read` back — `__init__` stores `self._conn = conn` and sets `self._conn.row_factory = sqlite3.Row`; every `SELECT` lists columns explicitly, never `SELECT *`; every `?` has a matching tuple element; body follows `Steps:` in order.

## Imports

Exactly two lines at the top of the file:

```python
from __future__ import annotations

import sqlite3
```

Add `from datetime import datetime, timezone`, `import uuid`, or `import json` only when a method body uses that name. No `TYPE_CHECKING`, no `Connection` alias, no project imports.

## Query shapes

- Read one: `stmt = "SELECT <cols> FROM <t> WHERE <pk> = ?"`; `row = self._conn.execute(stmt, (<key>,)).fetchone()`; `if row is None: return None`; `return dict(row)`.
- Read all: `rows = self._conn.execute("SELECT <cols> FROM <t>").fetchall()`; `return [dict(row) for row in rows]`.
- Insert: `self._conn.execute("INSERT INTO <t> (<cols>) VALUES (?, ?, ...)", (<v1>, <v2>, ...))`.
- Update: `self._conn.execute("UPDATE <t> SET <c1> = ? WHERE <pk> = ?", (<v1>, <pk>))`.
- Delete: `self._conn.execute("DELETE FROM <t> WHERE <pk> = ?", (<pk>,))`.

"Persist" in `Steps:` means one `execute`. It never means `commit()`.

## Output

File code only. No comments, no prose.

## Stop

Do not run tests, `mkdir`, `touch`, or any write outside `# Target file`. No `pytest`, no `python -m`. Do not read `tasks/*.md` — the task is in the prompt. One `read` to verify, then output.