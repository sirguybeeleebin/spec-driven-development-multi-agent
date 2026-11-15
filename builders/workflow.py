from models import Edge, Graph, Node, Task, Workflow


class WorkflowBuilder:
    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._nodes: list[Node] = []
        self._edges: list[Edge] = []

    def add_task(self, task: Task) -> None:
        self._tasks.append(task)

    def add_node(self, node: Node) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: Edge) -> None:
        self._edges.append(edge)

    def build(self) -> Workflow:
        return Workflow(
            graph=Graph(
                nodes=self._nodes,
                edges=self._edges,
            ),
            tasks=self._tasks,
        )
