from builders.workflow import WorkflowBuilder
from models import Edge, Graph, Node, Sequence, Task, Workflow


def make_task(task_id: str) -> Task:
    return Task(
        task_id=task_id,
        goal="Test task",
        fqns=[],
        interfaces=[],
        sequence=Sequence(participants=[], components=[]),
        gherkins=[],
    )


def test_add_task() -> None:
    builder = WorkflowBuilder()
    task = make_task("task_1")

    builder.add_task(task)

    assert builder._tasks == [task]


def test_add_node() -> None:
    builder = WorkflowBuilder()
    node = Node(task_id="task_1")

    builder.add_node(node)

    assert builder._nodes == [node]


def test_add_edge() -> None:
    builder = WorkflowBuilder()
    source = Node(task_id="task_1")
    target = Node(task_id="task_2")
    edge = Edge(source=source, target=target)

    builder.add_edge(edge)

    assert builder._edges == [edge]


def test_build_returns_workflow() -> None:
    builder = WorkflowBuilder()
    task = make_task("task_1")
    node_1 = Node(task_id="task_1")
    node_2 = Node(task_id="task_2")
    edge = Edge(source=node_1, target=node_2)

    builder.add_task(task)
    builder.add_node(node_1)
    builder.add_node(node_2)
    builder.add_edge(edge)

    result = builder.build()

    assert result == Workflow(
        graph=Graph(
            nodes=[node_1, node_2],
            edges=[edge],
        ),
        tasks=[task],
    )


def test_build_returns_empty_workflow() -> None:
    builder = WorkflowBuilder()

    result = builder.build()

    assert result == Workflow(
        graph=Graph(nodes=[], edges=[]),
        tasks=[],
    )
