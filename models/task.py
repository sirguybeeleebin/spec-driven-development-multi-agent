from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

TaskID = str
Goal = str


class FullQualifiedNameRole(StrEnum):
    TARGET = "target"
    DEPENDENCY = "dependency"


@dataclass
class FullQualifiedName:
    fqn: str
    role: FullQualifiedNameRole


@dataclass
class Interface:
    fqn: FullQualifiedName
    language: str
    content: str


class SequenceParticipantType(StrEnum):
    ACTOR = "actor"
    PARTICIPANT = "participant"


class SequenceArrow(StrEnum):
    SYNC = "->>"
    ASYNC = "->"
    RETURN = "-->>"
    RETURN_ASYNC = "-->"


class SequenceNotePosition(StrEnum):
    LEFT = "left of"
    RIGHT = "right of"
    OVER = "over"


class SequenceFragmentType(StrEnum):
    ALT = "alt"
    LOOP = "loop"


@dataclass
class SequenceParticipant:
    alias: str
    name: str
    type: SequenceParticipantType
    fqn: FullQualifiedName | None = None


@dataclass
class SequenceMessage:
    source: str
    target: str
    arrow: SequenceArrow
    content: str


@dataclass
class SequenceNote:
    position: SequenceNotePosition
    participants: list[str]
    content: str


@dataclass
class SequenceBranch:
    condition: str
    components: list[SequenceComponent]


@dataclass
class SequenceFragment:
    type: SequenceFragmentType
    branches: list[SequenceBranch]


@dataclass
class SequenceDirective:
    name: str


SequenceComponent = SequenceMessage | SequenceNote | SequenceFragment | SequenceDirective


@dataclass
class Sequence:
    participants: list[SequenceParticipant]
    components: list[SequenceComponent]


@dataclass
class Gherkin:
    name: str
    FullQualifiedNames: list[FullQualifiedName]
    given: list[str]
    when: list[str]
    then: list[str]


@dataclass
class Task:
    task_id: TaskID
    goal: Goal
    fqns: list[FullQualifiedName]
    interfaces: list[Interface]
    sequence: Sequence
    gherkins: list[Gherkin]


class TaskSectionAction(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"


class TaskSections(StrEnum):
    TASK = "Task"
    GOAL = "Goal"
    FullQualifiedNameS = "FullQualifiedNames"
    INTERFACES = "Interfaces"
    SEQUENCE = "Sequence"
    GHERKINS = "Gherkins"


class SequenceDiagramSymbol(StrEnum):
    PARTICIPANT = "participant "
    ACTOR = "actor "
    ALT = "alt "
    LOOP = "loop "
    ELSE = "else"
    END = "end"
    AUTONUMBER = "autonumber"
    NOTE = "Note "
    MESSAGE = "->"
