from __future__ import annotations

from dataclasses import dataclass, field

from models.agent import AgentResult

TaskID = str


class FullQualifiedName:
    """Dotted module path + '::' + symbol name, e.g. 'repositories.products::ProductRepository'."""

    __slots__ = ("_fqn", "_module", "_name")

    def __init__(self, fqn: str) -> None:
        if not isinstance(fqn, str):
            raise TypeError(f"fqn: expected str, got {type(fqn).__name__}")
        if "::" not in fqn:
            raise ValueError(f"fqn: missing '::' separator in {fqn!r}")
        module, name = fqn.rsplit("::", 1)
        module = module.strip()
        name = name.strip()
        if not module:
            raise ValueError(f"fqn: empty module in {fqn!r}")
        if not name:
            raise ValueError(f"fqn: empty name in {fqn!r}")
        self._module = module
        self._name = name
        self._fqn = f"{module}::{name}"

    @property
    def module(self) -> str:
        return self._module

    @property
    def name(self) -> str:
        return self._name

    @property
    def short_name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._fqn

    def __repr__(self) -> str:
        return f"FullQualifiedName({self._fqn!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FullQualifiedName):
            return NotImplemented
        return self._fqn == other._fqn

    def __hash__(self) -> int:
        return hash(self._fqn)


@dataclass
class Interface:
    name: str
    language: str
    content: str
    description: str
    steps: list[str]


@dataclass
class Sequence:
    language: str
    content: str


@dataclass
class Gherkin:
    name: str
    fqn: FullQualifiedName
    test_fqn: FullQualifiedName
    given: list[str]
    when: list[str]
    then: list[str]


@dataclass
class Task:
    task_id: TaskID
    goal: str
    fqns: list[FullQualifiedName]
    interfaces: list[Interface]
    gherkins: list[Gherkin]
    constitution: str
    sequence: Sequence | None = None


@dataclass
class TaskResult:
    task_id: TaskID
    results: list[AgentResult] = field(default_factory=list)
