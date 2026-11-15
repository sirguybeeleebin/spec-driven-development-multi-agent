import pytest

from parsers.sequence import (
    SequenceBranchParser,
    SequenceDirectiveParser,
    SequenceFragmentParser,
    SequenceMessageParser,
    SequenceNoteParser,
    SequenceParticipantParser,
)


class TestSequenceParticipantParser:
    @pytest.fixture
    def parser(self) -> SequenceParticipantParser:
        return SequenceParticipantParser()

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            (
                "participant User",
                {
                    "alias": "User",
                    "name": "User",
                    "type": "participant",
                    "fqn": None,
                },
            ),
            (
                "actor Client",
                {
                    "alias": "Client",
                    "name": "Client",
                    "type": "actor",
                    "fqn": None,
                },
            ),
            (
                "participant API as Backend API",
                {
                    "alias": "API",
                    "name": "Backend API",
                    "type": "participant",
                    "fqn": None,
                },
            ),
            (
                "actor DB as Database",
                {
                    "alias": "DB",
                    "name": "Database",
                    "type": "actor",
                    "fqn": None,
                },
            ),
        ],
    )
    def test_parse_valid_participant(
        self,
        parser: SequenceParticipantParser,
        line: str,
        expected: dict[str, object],
    ) -> None:
        assert parser.parse(line) == expected

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "User",
            "participant",
            "actor",
            "participant User as",
            "participant User extra",
        ],
    )
    def test_parse_invalid_participant(
        self,
        parser: SequenceParticipantParser,
        line: str,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid participant"):
            parser.parse(line)


class TestSequenceMessageParser:
    @pytest.fixture
    def parser(self) -> SequenceMessageParser:
        return SequenceMessageParser()

    @pytest.fixture
    def participant_aliases(self) -> set[str]:
        return {"User", "API"}

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            (
                "User -> API: Request",
                {
                    "type": "message",
                    "source": "User",
                    "target": "API",
                    "arrow": "->",
                    "content": "Request",
                },
            ),
            (
                "API --> User: Response",
                {
                    "type": "message",
                    "source": "API",
                    "target": "User",
                    "arrow": "-->",
                    "content": "Response",
                },
            ),
            (
                "User ->> API: Async request",
                {
                    "type": "message",
                    "source": "User",
                    "target": "API",
                    "arrow": "->>",
                    "content": "Async request",
                },
            ),
            (
                "API -->> User: Async response",
                {
                    "type": "message",
                    "source": "API",
                    "target": "User",
                    "arrow": "-->>",
                    "content": "Async response",
                },
            ),
            (
                " User -> API: Request ",
                {
                    "type": "message",
                    "source": "User",
                    "target": "API",
                    "arrow": "->",
                    "content": "Request",
                },
            ),
        ],
    )
    def test_parse_valid_message(
        self,
        parser: SequenceMessageParser,
        participant_aliases: set[str],
        line: str,
        expected: dict[str, object],
    ) -> None:
        assert parser.parse(line, participant_aliases) == expected

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "User API: Request",
            "User -> API",
            "User -> : Request",
            "-> API: Request",
            "User <-> API: Request",
        ],
    )
    def test_parse_invalid_message(
        self,
        parser: SequenceMessageParser,
        participant_aliases: set[str],
        line: str,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid message"):
            parser.parse(line, participant_aliases)

    def test_parse_unknown_source(
        self,
        parser: SequenceMessageParser,
        participant_aliases: set[str],
    ) -> None:
        with pytest.raises(ValueError, match="Unknown message source"):
            parser.parse("Unknown -> API: Request", participant_aliases)

    def test_parse_unknown_target(
        self,
        parser: SequenceMessageParser,
        participant_aliases: set[str],
    ) -> None:
        with pytest.raises(ValueError, match="Unknown message target"):
            parser.parse("User -> Unknown: Request", participant_aliases)


class TestSequenceNoteParser:
    @pytest.fixture
    def parser(self) -> SequenceNoteParser:
        return SequenceNoteParser()

    @pytest.fixture
    def participant_aliases(self) -> set[str]:
        return {"User", "API", "DB"}

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            (
                "Note left of User: User note",
                {
                    "type": "note",
                    "position": "left of",
                    "participants": ["User"],
                    "content": "User note",
                },
            ),
            (
                "Note right of API: API note",
                {
                    "type": "note",
                    "position": "right of",
                    "participants": ["API"],
                    "content": "API note",
                },
            ),
            (
                "Note over User: Shared note",
                {
                    "type": "note",
                    "position": "over",
                    "participants": ["User"],
                    "content": "Shared note",
                },
            ),
            (
                "Note over User, API: Shared note",
                {
                    "type": "note",
                    "position": "over",
                    "participants": ["User", "API"],
                    "content": "Shared note",
                },
            ),
            (
                "Note over User, API, DB: Shared note",
                {
                    "type": "note",
                    "position": "over",
                    "participants": ["User", "API", "DB"],
                    "content": "Shared note",
                },
            ),
        ],
    )
    def test_parse_valid_note(
        self,
        parser: SequenceNoteParser,
        participant_aliases: set[str],
        line: str,
        expected: dict[str, object],
    ) -> None:
        assert parser.parse(line, participant_aliases) == expected

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "Note User: Text",
            "Note above User: Text",
            "Note left of User",
            "Note over User:",
        ],
    )
    def test_parse_invalid_note(
        self,
        parser: SequenceNoteParser,
        participant_aliases: set[str],
        line: str,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid note"):
            parser.parse(line, participant_aliases)

    def test_parse_unknown_participant(
        self,
        parser: SequenceNoteParser,
        participant_aliases: set[str],
    ) -> None:
        with pytest.raises(ValueError, match="Unknown participant in note"):
            parser.parse("Note over User, Unknown: Text", participant_aliases)


class TestSequenceFragmentParser:
    @pytest.fixture
    def parser(self) -> SequenceFragmentParser:
        return SequenceFragmentParser()

    @pytest.mark.parametrize(
        ("line", "fragment_type", "condition"),
        [
            ("alt authenticated", "alt", "authenticated"),
            ("loop retry", "loop", "retry"),
            ("alt user is authorized", "alt", "user is authorized"),
            (" loop 3 times ", "loop", "3 times"),
        ],
    )
    def test_parse_valid_fragment(
        self,
        parser: SequenceFragmentParser,
        line: str,
        fragment_type: str,
        condition: str,
    ) -> None:
        assert parser.parse(line) == {
            "type": "fragment",
            "fragment_type": fragment_type,
            "branches": [
                {
                    "condition": condition,
                    "components": [],
                }
            ],
        }

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "alt",
            "loop",
            "par condition",
            "alt ",
        ],
    )
    def test_parse_invalid_fragment(
        self,
        parser: SequenceFragmentParser,
        line: str,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid fragment"):
            parser.parse(line)


class TestSequenceBranchParser:
    @pytest.fixture
    def parser(self) -> SequenceBranchParser:
        return SequenceBranchParser()

    @pytest.mark.parametrize(
        ("line", "condition"),
        [
            ("else authenticated", "authenticated"),
            ("else user is authorized", "user is authorized"),
            (" else  fallback ", "fallback"),
        ],
    )
    def test_parse_valid_branch(
        self,
        parser: SequenceBranchParser,
        line: str,
        condition: str,
    ) -> None:
        assert parser.parse(line) == {
            "type": "branch",
            "condition": condition,
            "components": [],
        }

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "alt authenticated",
            "else",
            "else ",
        ],
    )
    def test_parse_invalid_branch(
        self,
        parser: SequenceBranchParser,
        line: str,
    ) -> None:
        with pytest.raises(ValueError):
            parser.parse(line)


class TestSequenceDirectiveParser:
    @pytest.fixture
    def parser(self) -> SequenceDirectiveParser:
        return SequenceDirectiveParser()

    @pytest.mark.parametrize(
        "line",
        [
            "autonumber",
            " autonumber ",
        ],
    )
    def test_parse_valid_directive(
        self,
        parser: SequenceDirectiveParser,
        line: str,
    ) -> None:
        assert parser.parse(line) == {
            "type": "directive",
            "name": "autonumber",
        }

    @pytest.mark.parametrize(
        "line",
        [
            "",
            "activate",
            "autonumber 1",
            "autoNumber",
        ],
    )
    def test_parse_invalid_directive(
        self,
        parser: SequenceDirectiveParser,
        line: str,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid directive"):
            parser.parse(line)
