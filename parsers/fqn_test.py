import pytest

from parsers.fqn import FullQualifiedNameParser, FullQualifiedNamesParser


@pytest.fixture
def fqn_parser():
    return FullQualifiedNameParser()


@pytest.fixture
def fqns_parser():
    return FullQualifiedNamesParser()


def test_parse_fqn_parses_row(fqn_parser):
    row = "| 1 | `internal.models.Task` | target |"

    assert fqn_parser.parse(row) == {
        "number": 1,
        "fqn": "internal.models.Task",
        "role": "target",
    }


def test_parse_fqn_strips_whitespace(fqn_parser):
    row = "|  2  |  `internal.builders.task.build_task`  |  dependency  |"

    assert fqn_parser.parse(row) == {
        "number": 2,
        "fqn": "internal.builders.task.build_task",
        "role": "dependency",
    }


def test_parse_fqn_parses_number_as_integer(fqn_parser):
    row = "| 10 | `internal.parsers.FullQualifiedName.parse_fqn` | target |"

    result = fqn_parser.parse(row)

    assert result["number"] == 10
    assert isinstance(result["number"], int)


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (
            "| 1 | `package.module.Class` | target |",
            {
                "number": 1,
                "fqn": "package.module.Class",
                "role": "target",
            },
        ),
        (
            "| 2 | `package.module.function` | dependency |",
            {
                "number": 2,
                "fqn": "package.module.function",
                "role": "dependency",
            },
        ),
    ],
)
def test_parse_fqn_parses_different_fqn_types(fqn_parser, row, expected):
    assert fqn_parser.parse(row) == expected


@pytest.mark.parametrize(
    "role",
    ["target", "dependency"],
)
def test_parse_fqn_accepts_valid_roles(fqn_parser, role):
    row = f"| 1 | `package.module.Class` | {role} |"

    assert fqn_parser.parse(row)["role"] == role


def test_parse_fqn_raises_for_invalid_number(fqn_parser):
    with pytest.raises(ValueError, match="number"):
        fqn_parser.parse("| x | `internal.models.Task` | target |")


def test_parse_fqn_raises_for_invalid_fqn(fqn_parser):
    with pytest.raises(ValueError, match="format"):
        fqn_parser.parse("| 1 | invalid-FullQualifiedName | target |")


def test_parse_fqn_raises_for_invalid_role(fqn_parser):
    with pytest.raises(ValueError, match="role"):
        fqn_parser.parse("| 1 | `internal.models.Task` | Task model |")


def test_parse_fqn_raises_for_missing_columns(fqn_parser):
    with pytest.raises(ValueError, match="Invalid FullQualifiedName row"):
        fqn_parser.parse("| 1 | `internal.models.Task` |")


def test_parse_fqn_raises_for_extra_columns(fqn_parser):
    with pytest.raises(ValueError, match="Invalid FullQualifiedName row"):
        fqn_parser.parse("| 1 | `internal.models.Task` | target | Extra |")


def test_parse_fqns_returns_table_rows(fqns_parser):
    fqns = """\
| № | fqn | Role |
|---|---|---|
| 1 | `internal.models.Task` | target |
"""

    assert fqns_parser.parse(fqns) == [
        "| № | fqn | Role |",
        "|---|---|---|",
        "| 1 | `internal.models.Task` | target |",
    ]


def test_parse_fqns_skips_non_table_lines(fqns_parser):
    fqns = """\
# FullQualifiedNames

Some description.

| № | fqn | Role |
|---|---|---|
| 1 | `internal.models.Task` | target |

Additional text.
"""

    assert fqns_parser.parse(fqns) == [
        "| № | fqn | Role |",
        "|---|---|---|",
        "| 1 | `internal.models.Task` | target |",
    ]


def test_parse_fqns_parses_multiple_rows(fqns_parser):
    fqns = """\
| № | fqn | Role |
|---|---|---|
| 1 | `internal.models.Task` | target |
| 2 | `internal.builders.task.build_task` | dependency |
| 3 | `internal.parsers.FullQualifiedName.parse_fqn` | dependency |
"""

    assert fqns_parser.parse(fqns) == [
        "| № | fqn | Role |",
        "|---|---|---|",
        "| 1 | `internal.models.Task` | target |",
        "| 2 | `internal.builders.task.build_task` | dependency |",
        "| 3 | `internal.parsers.FullQualifiedName.parse_fqn` | dependency |",
    ]


def test_parse_fqns_raises_when_table_is_missing(fqns_parser):
    with pytest.raises(ValueError, match="FullQualifiedNames table"):
        fqns_parser.parse("")


def test_parse_fqns_raises_when_data_rows_are_missing(fqns_parser):
    fqns = """\
| № | fqn | Role |
|---|---|---|
"""

    with pytest.raises(ValueError, match="FullQualifiedNames table"):
        fqns_parser.parse(fqns)


def test_parse_fqns_raises_for_invalid_header(fqns_parser):
    fqns = """\
| № | Name | Role |
|---|---|---|
| 1 | `internal.models.Task` | target |
"""

    with pytest.raises(ValueError, match="header"):
        fqns_parser.parse(fqns)


def test_parse_fqns_raises_for_invalid_role_header(fqns_parser):
    fqns = """\
| № | fqn | Type |
|---|---|---|
| 1 | `internal.models.Task` | target |
"""

    with pytest.raises(ValueError, match="header"):
        fqns_parser.parse(fqns)


def test_parse_fqns_raises_for_invalid_row(fqns_parser):
    fqns = """\
| № | fqn | Role |
|---|---|---|
| 1 | `internal.models.Task` |
"""

    with pytest.raises(ValueError, match="row"):
        fqns_parser.parse(fqns)


def test_parse_fqns_raises_for_extra_columns(fqns_parser):
    fqns = """\
| № | fqn | Role |
|---|---|---|
| 1 | `internal.models.Task` | target | extra |
"""

    with pytest.raises(ValueError, match="row"):
        fqns_parser.parse(fqns)
