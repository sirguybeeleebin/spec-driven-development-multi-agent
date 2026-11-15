from builders.graph import GraphBuilder
from models import Edge, Graph, Node


def test_add_node() -> None:
    builder = GraphBuilder()

    node = {"task_id": "task-1"}

    builder.add_node(node)

    assert builder._nodes == [node]


def test_add_edge() -> None:
    builder = GraphBuilder()

    edge = {"source": "task-1", "target": "task-2"}

    builder.add_edge(edge)

    assert builder._edges == [edge]


def test_build_creates_graph() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})
    builder.add_node({"task_id": "task-2"})
    builder.add_edge(
        {
            "source": "task-1",
            "target": "task-2",
        }
    )

    graph = builder.build()

    assert isinstance(graph, Graph)
    assert graph.nodes == [
        Node(task_id="task-1"),
        Node(task_id="task-2"),
    ]
    assert graph.edges == [
        Edge(
            source=graph.nodes[0],
            target=graph.nodes[1],
        ),
    ]


def test_build_creates_graph_without_edges() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})

    graph = builder.build()

    assert graph.nodes == [Node(task_id="task-1")]
    assert graph.edges == []


def test_build_creates_empty_graph() -> None:
    builder = GraphBuilder()

    graph = builder.build()

    assert graph.nodes == []
    assert graph.edges == []


def test_build_uses_unique_nodes_by_task_id() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})
    builder.add_node({"task_id": "task-1"})
    builder.add_node({"task_id": "task-2"})

    graph = builder.build()

    assert graph.nodes == [
        Node(task_id="task-1"),
        Node(task_id="task-2"),
    ]


def test_build_preserves_edge_references() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})
    builder.add_node({"task_id": "task-2"})
    builder.add_edge(
        {
            "source": "task-1",
            "target": "task-2",
        }
    )

    graph = builder.build()

    assert graph.edges[0].source is graph.nodes[0]
    assert graph.edges[0].target is graph.nodes[1]


def test_build_raises_key_error_for_unknown_source() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})
    builder.add_edge(
        {
            "source": "unknown",
            "target": "task-1",
        }
    )

    try:
        builder.build()
    except KeyError as error:
        assert error.args == ("unknown",)
    else:
        raise AssertionError("Expected KeyError")


def test_build_raises_key_error_for_unknown_target() -> None:
    builder = GraphBuilder()

    builder.add_node({"task_id": "task-1"})
    builder.add_edge(
        {
            "source": "task-1",
            "target": "unknown",
        }
    )

    try:
        builder.build()
    except KeyError as error:
        assert error.args == ("unknown",)
    else:
        raise AssertionError("Expected KeyError")
