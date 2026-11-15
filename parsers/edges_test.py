import pytest

from parsers.edges import EdgesParser


@pytest.fixture
def parser():
    return EdgesParser()


def test_parse_returns_empty_list_without_edges(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "```",
        ]
    )

    assert parser.parse(graph) == []


def test_parse_parses_single_edge(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "A --> B",
            "```",
        ]
    )

    assert parser.parse(graph) == [{"source": "A", "target": "B"}]


def test_parse_parses_multiple_edges(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "A --> B",
            "B --> C",
            "C --> D",
            "```",
        ]
    )

    assert parser.parse(graph) == [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
        {"source": "C", "target": "D"},
    ]


def test_parse_parses_chained_edges(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "A --> B --> C --> D",
            "```",
        ]
    )

    assert parser.parse(graph) == [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "C"},
        {"source": "C", "target": "D"},
    ]


def test_parse_parses_edges_with_numeric_prefixes(parser):
    graph = """\
```mermaid
graph LR
001_products_repository --> 003_order_lines_repository
002_orders_repository --> 003_order_lines_repository
003_order_lines_repository --> 004_checkout_service
004_checkout_service --> 005_orders_router
005_orders_router --> 006_main
```
"""

    assert parser.parse(graph) == [
        {
            "source": "001_products_repository",
            "target": "003_order_lines_repository",
        },
        {
            "source": "002_orders_repository",
            "target": "003_order_lines_repository",
        },
        {
            "source": "003_order_lines_repository",
            "target": "004_checkout_service",
        },
        {
            "source": "004_checkout_service",
            "target": "005_orders_router",
        },
        {
            "source": "005_orders_router",
            "target": "006_main",
        },
    ]


def test_parse_strips_whitespace(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "  A  -->  B  ",
            "```",
        ]
    )

    assert parser.parse(graph) == [{"source": "A", "target": "B"}]


@pytest.mark.parametrize(
    "directive",
    ["graph LR", "graph RL", "graph TD", "graph TB", "graph BT"],
)
def test_parse_ignores_graph_directive(parser, directive):
    graph = "\n".join(
        [
            "```mermaid",
            directive,
            "A --> B",
            "```",
        ]
    )

    assert parser.parse(graph) == [{"source": "A", "target": "B"}]


@pytest.mark.parametrize(
    "line",
    [
        "A",
        "B",
        "invalid",
        "A --- B",
        "A -->",
        "--> B",
        "A --> B -->",
        "A --> B --> invalid node",
        "A --> B C",
        "A --> task-name",
    ],
)
def test_parse_rejects_invalid_lines(parser, line):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            line,
            "```",
        ]
    )

    with pytest.raises(ValueError, match="Invalid graph edge"):
        parser.parse(graph)


def test_parse_uses_first_mermaid_block(parser):
    graph = "\n".join(
        [
            "```mermaid",
            "graph TD",
            "A --> B",
            "```",
            "",
            "```mermaid",
            "graph TD",
            "C --> D",
            "```",
        ]
    )

    assert parser.parse(graph) == [{"source": "A", "target": "B"}]


def test_parse_raises_when_mermaid_block_is_missing(parser):
    with pytest.raises(ValueError, match="Missing"):
        parser.parse("graph TD\nA --> B")
