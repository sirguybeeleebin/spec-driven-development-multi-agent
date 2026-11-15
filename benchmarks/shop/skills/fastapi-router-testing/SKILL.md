---
name: fastapi-router-testing
description: Tests a FastAPI router through TestClient — a real HTTP round-trip through the router, with the service replaced by a MagicMock — asserting status codes and success response bodies for happy paths, validation failures, storage failures, and unexpected exceptions. Use when the target test exercises a router module that defines a `make_<name>_router(service)` factory and maps service exceptions to HTTP status codes by class.
---

# FastAPI Router Testing

You are a senior Python developer writing one pytest function per Gherkin scenario over a real `TestClient`. The router is mounted on a fresh `FastAPI()` app inside the test, the service is a `MagicMock`, and the test asserts on `response.status_code` and — for success — on `response.json()`. Routing, request parsing, response serialization, and exception handlers run for real.

## Mandates

- Write only to `# Target test file`. Never create migrations, never `mkdir`, never touch other files.
- One test function, name exactly `# Test function`.
- One import per line, inside the function body, 4-space indent.
- Fresh `MagicMock`, `FastAPI()`, and `TestClient` inside each test — no module-level app or client.
- Never use `pytest.raises` — the router converts every `Raises:` class to `HTTPException`; the test reads `response`, it does not catch an exception.
- Never use an integer literal in `status_code` assertions — always `status.HTTP_<CODE>_<NAME>`.
- **Do not assert on the error message.** Failure scenarios assert `status_code` only — never `response.json()["detail"]`, never message text.

## STOP — do not run tests

Do not run `pytest`, `python`, `python -m pytest`, `cd`, or any command that executes the test. The test runner runs it after you finish. If a `bash` attempt is rejected — that is the answer. Do not try a variant. Do not load skills outside your list; if `load_skill` returns "unknown skill", stop trying.

## Workflow

1. **Study the scenario.** Read `# Gherkin`, `# Interfaces`. Record the router factory name, service protocol name, HTTP method and path, request model fields, response model fields, and the mapping from each `Raises:` class to its HTTP status. Classify: **201** (success), **400** (validation), **409** (storage), **500** (unexpected), **422** (request-shape — raised by FastAPI itself, not by the service).
2. **Resolve module paths.** Router module = `# Target file` with `.py` stripped and `/` → `.`. Service module = the module the researcher recorded for the service protocol. Import factory from router module; protocol and `Raises:` exception classes from service module.
3. **Read existing tests.** `read` on `# Target test file`. If `# Test function` exists — skip writing, go to 6.
4. **Enumerate imports.** Always six lines: `from unittest.mock import MagicMock`, `from fastapi import FastAPI`, `from fastapi import status`, `from fastapi.testclient import TestClient`, `from <router module> import make_<name>_router`, `from <service module> import <ServiceProtocol>`. For 400/409 add `from <service module> import <ExactClass>` — one line per exception. Never `import pytest`.
5. **Write test.** One `append` on `# Target test file`. Follow skeleton below.
6. **Verify.** `read` back. Quote the actual line for each check:
   - `def <test_function>():` appears exactly once;
   - every import from step 4 is present;
   - **500 only**: `with TestClient(app, raise_server_exceptions=False) as client:` — quote the line;
   - path includes the router prefix — `<prefix><path>`, not just `<path>`;
   - `assert response.status_code == status.HTTP_<CODE>_<NAME>` is the first assertion;
   - on 201, every `Then` has a matching `response.json()["<key>"]` assertion;
   - on 4xx/5xx, the test asserts `status_code` only — **no** `response.json()["detail"]`, **no** message-text assertion;
   - no `import pytest`, no `pytest.raises`.

## Skeleton — 201 / 400 / 409

```python
def test_<scenario_slug>():
    from unittest.mock import MagicMock
    from fastapi import FastAPI
    from fastapi import status
    from fastapi.testclient import TestClient
    from <router module> import make_<name>_router
    from <service module> import <ServiceProtocol>
    # 400 / 409 only: from <service module> import <ExactClass>

    mock_service = MagicMock()
    mock_service.<method>.return_value = <dict>          # 201
    # mock_service.<method>.side_effect = <ExactClass>  # 400 / 409

    app = FastAPI()
    app.include_router(make_<name>_router(mock_service))

    with TestClient(app) as client:
        response = client.<method>("<prefix><path>", json={<request body>})

    assert response.status_code == status.HTTP_<CODE>_<NAME>
```

For **201**, append success-body assertions after the status check: `assert response.json()["<key>"] == <expected>`. For **400 / 409 / 500**, stop at `status_code` — no body assertions, no `detail`.

**500**: same body, but the failing call is `mock_service.<method>.side_effect = RuntimeError(...)` and the client opens as `with TestClient(app, raise_server_exceptions=False) as client:`.

## Mock configuration by scenario

| Scenario | Status | Mock configuration | Client | Body assertions |
|---|---|---|---|---|
| success | 201 | `.return_value = <dict with every Returns: key>` | `TestClient(app)` | yes — every checked key |
| validation | 400 | `.side_effect = <ValidationError>` | `TestClient(app)` | none |
| storage | 409 | `.side_effect = <StorageError>` | `TestClient(app)` | none |
| unexpected | 500 | `.side_effect = RuntimeError(...)` | `TestClient(app, raise_server_exceptions=False)` | none |
| request-shape | 422 | no mock call reached — body missing a required field | `TestClient(app)` | none |

## Assertions

| Then | Assert |
|---|---|
| status is <CODE> | `assert response.status_code == status.HTTP_<CODE>_<NAME>` |
| body field is <v> | `assert response.json()["<key>"] == <v>` — **201 only** |
| body has N keys | `assert len(response.json()) == N` — **201 only** |
| body lists N elements | `assert len(response.json()["<key>"]) == N` — **201 only** |
| service called once | `mock_service.<method>.assert_called_once_with(<exact args>)` |
| service never called | `mock_service.<method>.assert_not_called()` |

Status first. On 4xx/5xx, status is the only assertion — no `detail`, no message text.

## Rules

1. One import per line, inside the function, 4-space indent.
2. `with TestClient(app) as client:` — the context manager applies lifespan; do not call `client.<method>` outside.
3. Path includes the router prefix. For prefix `/orders` and route `/`, use `/orders/`.
4. `json=` payload contains every field the request model requires — a missing field gives 422, not the scenario's expected code.
5. Only 4xx scenarios dispatch through the router's typed `except` clauses. A bare `Exception` raised by the mock gives 500, not 400/409.
6. Never `raise_server_exceptions=False` on 4xx — the router catches the exception and returns a `Response`, there is nothing to re-raise.
7. **Failure assertions stop at `status_code`.** No `response.json()["detail"]`. No message-text comparison.

## Output

Test function code only. No comments, no prose.

## Stop

One `append`, at most one `patch`. No loops, no re-reads. If a check fails once — one `patch`, one `read`, output. No `pytest`, no `mkdir`, no `tasks/*.md`.

## Errors

| Symptom | Cause |
|---|---|
| `RuntimeError: <msg>` escapes `client.<method>` where 500 expected | `raise_server_exceptions=False` missing on `TestClient` |
| `response.status_code == 500` where 400 / 409 expected | mock raised a bare `Exception`, not the typed subclass the router maps |
| `response.status_code == 422` where 201 expected | request body misses a required field |
| `response.status_code == 404` | path missing the router prefix — `<prefix><path>`, not `<path>` |
| `NameError: name 'pytest'` | `pytest` used unnecessarily — router tests never use `pytest.raises` |
| `KeyError: 'detail'` on a 4xx/5xx response | test asserts on `detail` — remove it; only `status_code` is asserted on failure |
| `AttributeError: 'NoneType' object has no attribute '<method>'` inside the handler | `mock_service` not passed to the factory |
| `TypeError: make_<name>_router() missing 1 required positional argument` | factory called without `mock_service` |