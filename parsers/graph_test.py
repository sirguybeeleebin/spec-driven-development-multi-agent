# tests/parsers/test_graph.py

from __future__ import annotations

import pytest

from models import Edge, Graph, Node
from parsers.graph import parse_graph


def make_graph(body: str) -> str:
    return f"""\
```mermaid
{body}
```
"""


def test_parse_graph() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A
B
C
A --> B
B --> C"""
        )
    )

    assert graph == Graph(
        nodes=[
            Node(task_id="A"),
            Node(task_id="B"),
            Node(task_id="C"),
        ],
        edges=[
            Edge(
                source=Node(task_id="A"),
                target=Node(task_id="B"),
            ),
            Edge(
                source=Node(task_id="B"),
                target=Node(task_id="C"),
            ),
        ],
    )


def test_parse_graph_without_explicit_node_declarations() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph LR
A --> B
B --> C"""
        )
    )

    assert [node.task_id for node in graph.nodes] == ["A", "B", "C"]
    assert len(graph.edges) == 2


def test_parse_graph_with_isolated_nodes() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A
B
C
A --> B"""
        )
    )

    assert [node.task_id for node in graph.nodes] == ["A", "B", "C"]
    assert len(graph.edges) == 1


@pytest.mark.parametrize(
    "direction",
    ["LR", "RL", "TD", "TB", "BT", "lr", "td"],
)
def test_parse_graph_directions(direction: str) -> None:
    graph = parse_graph(
        make_graph(
            f"""\
graph {direction}
A
B
A --> B"""
        )
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_parse_graph_strips_whitespace() -> None:
    graph = parse_graph(
        make_graph(
            """\
    graph TD

    A
    B

    A --> B
    """
        )
    )

    assert [node.task_id for node in graph.nodes] == ["A", "B"]
    assert len(graph.edges) == 1


def test_parse_graph_reuses_nodes_in_edges() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
B --> C
A --> C"""
        )
    )

    assert len(graph.nodes) == 3

    assert graph.edges[0].source is graph.nodes[0]
    assert graph.edges[0].target is graph.nodes[1]
    assert graph.edges[1].source is graph.nodes[1]
    assert graph.edges[1].target is graph.nodes[2]
    assert graph.edges[2].source is graph.nodes[0]
    assert graph.edges[2].target is graph.nodes[2]


def test_parse_graph_chained_edges() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B --> C --> D"""
        )
    )

    assert [node.task_id for node in graph.nodes] == [
        "A",
        "B",
        "C",
        "D",
    ]

    assert [(edge.source.task_id, edge.target.task_id) for edge in graph.edges] == [
        ("A", "B"),
        ("B", "C"),
        ("C", "D"),
    ]


def test_parse_graph_multiple_edges() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
A --> C
B --> D
C --> D"""
        )
    )

    assert len(graph.nodes) == 4
    assert [(edge.source.task_id, edge.target.task_id) for edge in graph.edges] == [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "D"),
    ]


def test_parse_graph_without_mermaid_fence() -> None:
    with pytest.raises(
        ValueError,
        match="missing .* block",
    ):
        parse_graph("graph TD\nA --> B")


def test_parse_graph_without_directive() -> None:
    with pytest.raises(
        ValueError,
        match="missing 'graph <direction>' directive",
    ):
        parse_graph(make_graph("A --> B"))


def test_parse_graph_with_duplicate_directive() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate graph directive",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
graph LR
A --> B"""
            )
        )


def test_parse_graph_with_invalid_directive() -> None:
    with pytest.raises(
        ValueError,
        match="unrecognised mermaid line",
    ):
        parse_graph(
            make_graph(
                """\
graph XX
A --> B"""
            )
        )


def test_parse_graph_with_no_tasks() -> None:
    with pytest.raises(
        ValueError,
        match="no tasks declared",
    ):
        parse_graph(make_graph("graph TD"))


def test_parse_graph_with_duplicate_node() -> None:
    with pytest.raises(
        ValueError,
        match="graph: duplicate node 'A'",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A
A"""
            )
        )


def test_parse_graph_with_duplicate_edge() -> None:
    with pytest.raises(
        ValueError,
        match="graph: duplicate edge 'A' --> 'B'",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A --> B
A --> B"""
            )
        )


def test_parse_graph_with_self_loop() -> None:
    with pytest.raises(
        ValueError,
        match="graph: self-loop at 'A'",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A --> A"""
            )
        )


@pytest.mark.parametrize(
    "line",
    [
        "A-B",
        "A -> B",
        "A --> B;",
        "A --> B C",
        "A B",
        "A.B",
        "A/B",
        "A[Node]",
        "A{Node}",
    ],
)
def test_parse_graph_with_unrecognised_line(line: str) -> None:
    with pytest.raises(
        ValueError,
        match="unrecognised mermaid line",
    ):
        parse_graph(
            make_graph(
                f"""\
graph TD
{line}"""
            )
        )


def test_parse_graph_with_cycle() -> None:
    with pytest.raises(
        ValueError,
        match="graph: cycle detected",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A --> B
B --> C
C --> A"""
            )
        )


def test_parse_graph_with_self_referencing_cycle() -> None:
    with pytest.raises(
        ValueError,
        match="graph: self-loop",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A --> A"""
            )
        )


def test_parse_graph_with_disconnected_cycle() -> None:
    with pytest.raises(
        ValueError,
        match="graph: cycle detected",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
A --> B
C --> D
D --> C"""
            )
        )


def test_parse_graph_with_diamond_dag() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
A --> C
B --> D
C --> D"""
        )
    )

    assert len(graph.nodes) == 4
    assert len(graph.edges) == 4


def test_parse_graph_with_diamond_dag_does_not_detect_cycle() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
A --> C
B --> D
C --> D
D --> E"""
        )
    )

    assert len(graph.nodes) == 5
    assert len(graph.edges) == 5


def test_parse_graph_with_multiple_independent_components() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
C --> D
E"""
        )
    )

    assert [node.task_id for node in graph.nodes] == [
        "A",
        "B",
        "C",
        "D",
        "E",
    ]
    assert len(graph.edges) == 2


def test_parse_graph_preserves_node_order() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
C --> A
B --> C
D"""
        )
    )

    assert [node.task_id for node in graph.nodes] == [
        "C",
        "A",
        "B",
        "D",
    ]


def test_parse_graph_preserves_edge_order() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
A --> B
C --> D
B --> C"""
        )
    )

    assert [(edge.source.task_id, edge.target.task_id) for edge in graph.edges] == [
        ("A", "B"),
        ("C", "D"),
        ("B", "C"),
    ]


def test_parse_graph_accepts_underscores_and_digits() -> None:
    graph = parse_graph(
        make_graph(
            """\
graph TD
task_1 --> task_2
task_2 --> task_3"""
        )
    )

    assert [node.task_id for node in graph.nodes] == [
        "task_1",
        "task_2",
        "task_3",
    ]


def test_parse_graph_rejects_hyphen_in_node_name() -> None:
    with pytest.raises(
        ValueError,
        match="unrecognised mermaid line",
    ):
        parse_graph(
            make_graph(
                """\
graph TD
task-1"""
            )
        )
