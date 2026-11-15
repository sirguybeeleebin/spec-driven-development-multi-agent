import re


def parse_sequence_participant(line: str) -> dict[str, object]:
    match = re.fullmatch(
        r"(actor|participant)\s+(\w+)(?:\s+as\s+(.+))?",
        line.strip(),
    )

    if match is None:
        raise ValueError(f"Invalid participant: {line}")

    participant_type, alias, name = match.groups()

    return {
        "alias": alias,
        "name": (name or alias).strip(),
        "type": participant_type,
        "fqn": None,
    }


def parse_sequence_message(
    line: str,
    participant_aliases: set[str],
) -> dict[str, object]:
    match = re.fullmatch(
        r"(\w+)\s*(-->>|->>|-->|->)\s*(\w+)\s*:\s*(.+)",
        line.strip(),
    )

    if match is None:
        raise ValueError(f"Invalid message: {line}")

    source, arrow, target, content = match.groups()

    if source not in participant_aliases:
        raise ValueError(f"Unknown message source: {source}")

    if target not in participant_aliases:
        raise ValueError(f"Unknown message target: {target}")

    return {
        "type": "message",
        "source": source,
        "target": target,
        "arrow": arrow,
        "content": content.strip(),
    }


def parse_sequence_note(
    line: str,
    participant_aliases: set[str],
) -> dict[str, object]:
    match = re.fullmatch(
        r"Note\s+(left of|right of|over)\s+([\w,\s]+):\s*(.+)",
        line.strip(),
    )

    if match is None:
        raise ValueError(f"Invalid note: {line}")

    position, raw_participants, content = match.groups()
    participants = [
        alias.strip()
        for alias in raw_participants.split(",")
    ]

    if any(alias not in participant_aliases for alias in participants):
        raise ValueError(f"Unknown participant in note: {line}")

    return {
        "type": "note",
        "position": position,
        "participants": participants,
        "content": content.strip(),
    }


def parse_sequence_fragment(line: str) -> dict[str, object]:
    match = re.fullmatch(r"(alt|loop)\s+(.+)", line.strip())

    if match is None:
        raise ValueError(f"Invalid fragment: {line}")

    fragment_type, condition = match.groups()

    return {
        "type": "fragment",
        "fragment_type": fragment_type,
        "branches": [
            {
                "condition": condition.strip(),
                "components": [],
            }
        ],
    }


def parse_sequence_branch(line: str) -> dict[str, object]:
    stripped_line = line.strip()

    if not stripped_line.startswith("else"):
        raise ValueError(f"Invalid branch: {line}")

    condition = stripped_line.removeprefix("else").strip()

    if not condition:
        raise ValueError("Empty else condition")

    return {
        "type": "branch",
        "condition": condition,
        "components": [],
    }


def parse_sequence_directive(line: str) -> dict[str, object]:
    if line.strip() != "autonumber":
        raise ValueError(f"Invalid directive: {line}")

    return {
        "type": "directive",
        "name": "autonumber",
    }