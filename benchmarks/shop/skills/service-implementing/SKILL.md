---
name: service-implementing
description: Implements a service-layer class that receives collaborator protocols through `__init__`, validates inputs, sequences collaborator calls, and returns a result dict. Use when the target implements a business operation that coordinates two or more collaborators and produces a result the caller returns.
---

# Service Implementing

You are a senior Python developer writing one file that declares collaborator protocols, an exception hierarchy, and a service class.
You write code with using only interfaces from task AND DONT USE IMPORTS
You write file sequentially working on each collaborator independantly and using `append` tool

## Mandates

- Write only to `# Target file`. Nothing else.
- Declare every `# Declares` name here. Do not import a name that must be declared — Rule 3.
- Every persist call is wrapped in `try/except Exception as exc: raise <StorageError>(...) from exc`. No bare `execute` escapes to the caller.
- Method body phases in strict order: **validate → produce → persist → assemble**.
- No comments, no helpers, no constants, no type aliases, no `if __name__ == "__main__"`, no `print`.
- No `try/except` around validate, produce, or assemble — only around persist.

## Workflow

1. **Read the interface.** One `read` on `# Target file`. From `# Interfaces`, for every `# Declares` name record its kind — **exception base** (nothing extends it), **exception subclass**, **protocol**, or **service class**. For each method record `Steps:`, `Returns:`, `Raises:` verbatim.
2. **Read the sequence.** From `# Sequence`, every arrow from service → collaborator records: callee, method, arguments, phase (`validate` / `produce` / `persist` / `assemble`). Every `Note over S` is a service step without a collaborator call. If `# Sequence` is `_(none)_`, the service does only validation and assembly.
3. **Write components in dependency order. sequentially** One `append` per pending name: exception base → exception subclasses → protocols → service. First `append` carries the import block.
4. **Write the service method.** Phases in order:
   - **validate** — one `if <invalid>: raise <ValidationError>("<reason>")` per `Raise X when Y` in `Steps:`. Include any collaborator lookup the validation needs (`self._<collab>.<get>(...)`).
   - **produce** — one assignment per internally generated value: `<value> = datetime.now(timezone.utc).isoformat()` or whatever `Steps:` names.
   - **persist** — one `self._<collab>.<method>(<args>)` per `# Sequence` arrow, in diagram order, each wrapped in `try: … except Exception as exc: raise <StorageError>("<reason>") from exc`. A `loop` becomes `for …: try/except`. An `alt` becomes `if …: try/except`.
   - **assemble** — `return { ... }` with exactly one key per `Returns:` key, in `Returns:` order.
5. **Verify.** One `read` on `# Target file`. Every `# Declares` name appears exactly once. Every persist call is inside `try/except ... from exc`. Every `Returns:` key appears in the return dict. Every validate `if` is above the first persist.

## Imports

`from __future__ import annotations` always. `from datetime import datetime, timezone` only when a body calls `datetime.now(...)`. `from typing import Protocol` only when `# Declares` contains a protocol. Import from `<path>` only for `Raises:` classes the researcher marked `import from <path>`. Everything else in `# Declares` is declared here.

## Component shapes

```python
class <Base>(Exception): ...

class <Sub>(<Base>): ...

class <Collaborator>(Protocol):
    def <method>(self, <args>) -> <ret>: ...

class <Service>:
    def __init__(self, <collab_a>: <ProtoA>, <collab_b>: <ProtoB>) -> None:
        self._<collab_a> = <collab_a>
        self._<collab_b> = <collab_b>

    def <method>(self, <args>) -> dict:
        # validate → produce → persist → assemble
        ...
```

Signatures are copied verbatim from `# Interfaces`. Protocol method bodies are `...`. Exception class bodies are `...`.

## Rules

1. Catch the specific `<StorageError>`, not `<Base>`. If `Raises:` names both, catch the subclass.
2. Do not configure anything for a collaborator the SUT never reaches on this path.
3. Every `# Raises:` class that is not in `# Declares` is either imported from `<path>` or declared here — never both.
4. `datetime.now(timezone.utc).isoformat()` is the default for `created_at` when `Steps:` says "timestamp". Never call `datetime.now()` without `tz=timezone.utc`.

## Output

File code only. No comments, no prose.

## Stop

One `append` per component, one `read` to verify. No loops, no re-reads. If a check fails once — one `patch`, one `read`, output. No `mkdir`, no write outside `# Target file`, no `tasks/*.md`.

## Errors

| Symptom | Cause |
|---|---|
| `ImportError: cannot import name '<Name>' from partially initialized module` | a `# Declares` name is imported from its own module — declare it here |
| `NameError: name '<Collaborator>'` in `__init__` | protocol declared after the service — reorder appends |
| `NameError: name '<ValidationError>'` in a method | exception declared after the service — reorder appends |
| `sqlite3.IntegrityError` escapes to the caller | persist call not wrapped — add `try/except Exception as exc: raise <StorageError>(...) from exc` |
| `DID NOT RAISE <ValidationError>` | validate phase runs after persist — move `if <invalid>: raise` above the first persist |
| `KeyError: '<key>'` from the caller | return dict misses a `Returns:` key |
| `AttributeError: 'NoneType' object has no attribute '<method>'` | collaborator passed as `None` — the composition root passes real instances |
| `TypeError: <Service>() missing 1 required positional argument` | a `# Interfaces` collaborator was omitted from `__init__` |