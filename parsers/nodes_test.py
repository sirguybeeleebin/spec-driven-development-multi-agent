import pytest

from parsers.nodes import NodesParser


@pytest.fixture
def parser():
    return NodesParser()


def test_parse_nodes_parses_single_node(parser):
    graph = """\
```mermaid
graph TD
task_1
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
    ]


def test_parse_nodes_parses_multiple_nodes(parser):
    graph = """\
```mermaid
graph TD
task_1
task_2
task_3
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
        {"task_id": "task_3"},
    ]


def test_parse_nodes_parses_nodes_from_edges(parser):
    graph = """\
```mermaid
graph TD
task_1 --> task_2
task_2 --> task_3
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
        {"task_id": "task_3"},
    ]


def test_parse_nodes_parses_chained_edges(parser):
    graph = """\
```mermaid
graph TD
task_1 --> task_2 --> task_3
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
        {"task_id": "task_3"},
    ]


def test_parse_nodes_parses_nodes_with_numeric_prefixes(parser):
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
        {"task_id": "001_products_repository"},
        {"task_id": "003_order_lines_repository"},
        {"task_id": "002_orders_repository"},
        {"task_id": "004_checkout_service"},
        {"task_id": "005_orders_router"},
        {"task_id": "006_main"},
    ]


def test_parse_nodes_does_not_duplicate_nodes(parser):
    graph = """\
```mermaid
graph TD
task_1
task_1
task_1 --> task_2
task_2 --> task_1
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
    ]


def test_parse_nodes_preserves_node_order(parser):
    graph = """\
```mermaid
graph TD
task_3 --> task_1
task_2 --> task_3
task_4
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_3"},
        {"task_id": "task_1"},
        {"task_id": "task_2"},
        {"task_id": "task_4"},
    ]


def test_parse_nodes_strips_whitespace(parser):
    graph = """\
```mermaid
graph TD
task_1
 task_2
task_1 --> task_2
```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
    ]


@pytest.mark.parametrize(
    "directive",
    [
        "graph LR",
        "graph RL",
        "graph TD",
        "graph TB",
        "graph BT",
        "GRAPH TD",
    ],
)
def test_parse_nodes_accepts_graph_directives(parser, directive):
    graph = f"""\
```mermaid
{directive}
task_1
```
"""

    assert parser.parse(graph) == [{"task_id": "task_1"}]


def test_parse_nodes_ignores_empty_lines(parser):
    graph = """\
```mermaid
graph TD

task_1

task_2

```
"""

    assert parser.parse(graph) == [
        {"task_id": "task_1"},
        {"task_id": "task_2"},
    ]


def test_parse_nodes_uses_first_mermaid_block(parser):
    graph = """\
```mermaid
graph TD
task_1
```

```mermaid
graph TD
task_2
```
"""

    assert parser.parse(graph) == [{"task_id": "task_1"}]


def test_parse_nodes_raises_without_mermaid_block(parser):
    with pytest.raises(ValueError, match="Missing"):
        parser.parse("graph TD\ntask_1")


@pytest.mark.parametrize(
    "graph",
    [
        "```mermaid\ntask_1\n```",
        "```mermaid\nflowchart TD\ntask_1\n```",
        "```mermaid\ninvalid directive\ntask_1\n```",
        "```mermaid\ngraph\n task_1\n```",
    ],
)
def test_parse_nodes_raises_for_missing_or_invalid_directive(parser, graph):
    with pytest.raises(ValueError, match="directive"):
        parser.parse(graph)


@pytest.mark.parametrize(
    "graph",
    [
        "```python\ngraph TD\ntask_1\n```",
        "```\ngraph TD\ntask_1\n```",
    ],
)
def test_parse_nodes_raises_for_non_mermaid_code_block(parser, graph):
    with pytest.raises(ValueError, match="Missing"):
        parser.parse(graph)


@pytest.mark.parametrize(
    "node",
    [
        "task-name",
        "task.name",
        "task name",
        "task[1]",
        "task()",
        "task!",
    ],
)
def test_parse_nodes_raises_for_invalid_node(parser, node):
    graph = f"""\
```mermaid
graph TD
{node}
```
"""

    with pytest.raises(ValueError, match="Invalid graph node"):
        parser.parse(graph)


@pytest.mark.parametrize(
    "node",
    [
        "1task",
        "001",
        "001_task",
        "123_task_name",
    ],
)
def test_parse_nodes_accepts_nodes_starting_with_digits(parser, node):
    graph = f"""\
```mermaid
graph TD
{node}
```
"""

    assert parser.parse(graph) == [{"task_id": node}]


@pytest.mark.parametrize(
    "edge",
    [
        "task_1 -->",
        "--> task_2",
        "task_1 --> --> task_2",
        "task_1 --> task-2",
        "task_1 --> task_2 -->",
    ],
)
def test_parse_nodes_raises_for_invalid_edge(parser, edge):
    graph = f"""\
```mermaid
graph TD
{edge}
```
"""

    with pytest.raises(ValueError, match="Invalid graph edge"):
        parser.parse(graph)


def test_parse_nodes_raises_for_graph_without_nodes(parser):
    graph = """\
```mermaid
graph TD
```
"""

    with pytest.raises(ValueError, match="at least one node"):
        parser.parse(graph)


def test_parse_nodes_raises_for_graph_with_only_empty_lines(parser):
    graph = """\
```mermaid
graph TD


```
"""

    with pytest.raises(ValueError, match="at least one node"):
        parser.parse(graph)
