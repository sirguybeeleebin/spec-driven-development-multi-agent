import re


_FQN = re.compile(r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*")


def parse_full_qualified_names(fqns: str) -> list[str]:
    rows = [
        line
        for line in fqns.splitlines()
        if line.strip().startswith("|")
    ]

    if len(rows) < 3:
        raise ValueError(
            "FullQualifiedNames table must contain a header and at least one row"
        )

    if not all(
        len(row.strip().strip("|").split("|")) == 3
        for row in rows
    ):
        raise ValueError("Invalid FullQualifiedNames table row")

    header = rows[0].strip().strip("|").split("|")

    if header[1].strip() != "fqn":
        raise ValueError("Invalid FullQualifiedNames table header")

    if header[2].strip() != "Role":
        raise ValueError("Invalid FullQualifiedNames table header")

    return rows


def parse_full_qualified_name(row: str) -> dict[str, str | int]:
    columns = [
        column.strip().strip("`")
        for column in row.strip().strip("|").split("|")
    ]

    if len(columns) != 3:
        raise ValueError(f"Invalid FullQualifiedName row: {row}")

    number, fqn, role = columns

    if not number.isdigit():
        raise ValueError(f"Invalid FullQualifiedName number: {number}")

    if not _FQN.fullmatch(fqn):
        raise ValueError(f"Invalid FullQualifiedName format: {fqn}")

    if role not in {"target", "dependency"}:
        raise ValueError(f"Invalid FullQualifiedName role: {role}")

    return {
        "number": int(number),
        "fqn": fqn,
        "role": role,
    }