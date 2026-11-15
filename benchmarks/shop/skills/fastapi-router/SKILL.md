---
name: fastapi-router
description: Creates a FastAPI APIRouter factory that closes over a service protocol, declares Pydantic request and response models in the router file, and maps typed service exceptions to HTTP status codes by class. Use when the target file defines a `make_<name>_router(service)` factory that registers endpoints under a router prefix.
---

# FastAPI Router

You are a senior Python developer writing one router module: Pydantic request and response models declared in the file, the service protocol imported from its module, and a `make_<name>_router(service) -> APIRouter` factory that maps each typed exception to an HTTP status code by class.

## Mandates

- Write only to `# Target file`. Nothing else.
- Declare every Pydantic model in this file. Import only the service protocol and the `Raises:` exception classes from their modules.
- Never import a Pydantic model, a concrete service, a repository, `sqlite3`, or an `app` object.
- Dispatch exceptions by class — never on `str(exc)`, never `except Exception`, never `JSONResponse`.
- **Do not format error messages.** `raise HTTPException(status_code=status.HTTP_<CODE>) from exc` — no `detail=`, no `str(exc)`, no custom message text.
- No comments, no helpers, no constants, no type aliases, no `app = FastAPI(...)`, no `app.include_router(...)`.
- Factory ends with `return router`. Never attach the router.

## Workflow

1. **Read the interface.** One `read` on `# Target file`. From `# Interfaces`, for every `# Declares` name record its kind — `StrEnum`, response `BaseModel`, request `BaseModel`, or factory function. For the factory, record each endpoint: HTTP method, path, request model, response model, success status code. For every `Raises:` class record the HTTP status the contract assigns to it.
2. **Record project imports.** Every name that is not a Pydantic model and not declared here — the service protocol, every `Raises:` exception class — is imported from the module the researcher recorded for it. One import line per module. Never guess a module.
3. **Write components in dependency order.** One `append` per pending name: enum → response models → request models → factory. First `append` carries the import block. If a component already exists and matches `# Interfaces` — skip it.
4. **Verify.** One `read` on `# Target file`. Every `# Declares` name appears exactly once. Every endpoint has `response_model=` and `status_code=status.HTTP_*`. Every `Raises:` class has its own `except` clause and no `detail=`. The factory ends with `return router`.

## Imports

The fixed block at the top of the file:

```python
from __future__ import annotations

from enum import StrEnum

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict, Field
```

Then one line per module that declares the service protocol or a `Raises:` exception class, grouping all names that come from the same module:

```python
from <module> import <Name1>, <Name2>
```

## Component shapes

```python
class <Enum>(StrEnum):
    <MEMBER> = "<MEMBER>"


class <ResponseModel>(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    <field>: <type> = Field(..., title="<title>", description="<description>")


class <RequestModel>(BaseModel):
    model_config = ConfigDict(extra="forbid")
    <field>: <type> = Field(..., title="<title>", description="<description>")


def make_<name>_router(service: <Protocol>) -> APIRouter:
    router = APIRouter(prefix="/<resource>", tags=["<resource>"])

    @router.<method>("<path>", response_model=<ResponseModel>, status_code=status.HTTP_<CODE>)
    def <verb>(payload: <RequestModel>) -> <ResponseModel>:
        try:
            result = service.<method>(<args>)
        except <ErrorClassA> as exc:
            raise HTTPException(status_code=status.HTTP_<CODE_A>) from exc
        except <ErrorClassB> as exc:
            raise HTTPException(status_code=status.HTTP_<CODE_B>) from exc
        return <ResponseModel>(**result)

    return router
```

Signatures are copied verbatim from `# Interfaces`.

## Rules

1. **Enum members** are `UPPER_SNAKE`; value equals the name.
2. **Response models** use `frozen=True`. Nested model fields are typed by class — `list[<OtherModel>]`, never `list[dict]`.
3. **Request models** contain only client-supplied fields — no `created_at`, no `id`, no `status`.
4. **Handler name** is the plain verb — `create`, `list`, `get`, `update`, `delete`.
5. **Exception dispatch** is by class. One `except <Class> as exc:` per `Raises:` class. `raise HTTPException(status_code=status.HTTP_<CODE>) from exc` — no `detail=`. The unexpected path is FastAPI's default 500 handler — do not add a catch-all.
6. **Success path** returns `<ResponseModel>(**result)`. If `**result` contains a key not in the response model, the contract and the model disagree — align them per `Returns:`, not by dropping the key.
7. **Factory** receives the service as a Protocol-typed parameter — no concrete class, no `Depends`, no module-level router.

## Output

File code only. No comments, no prose.

## Stop

One `append` per component, one `read` to verify. No loops, no re-reads. If a check fails once — one `patch`, one `read`, output. No `mkdir`, no write outside `# Target file`, no `tasks/*.md`.

## Errors

| Symptom | Cause |
|---|---|
| `ImportError: cannot import name '<Model>' from '<module>'` | a model was imported — declare it here |
| `NameError: name '<ExceptionClass>'` | missing from the project import line |
| `NameError: name 'status'` | `from fastapi import status` missing |
| `NameError: name 'HTTPException'` | `from fastapi.exceptions import HTTPException` missing |
| endpoint returns 500 where 400 expected | validation `except` clause absent or catches wrong class — Rule 5 |
| endpoint returns 400 where 409 expected | dispatch branches on `str(exc)` instead of class — Rule 5 |
| `AssertionError: extra fields not permitted` on the response | `**result` has a field not in the response model — Rule 6 |
| `TypeError: <Handler>() missing 1 required positional argument` | handler declared without `payload: <RequestModel>` |