from models import Edge, Graph, Node


class GraphBuilder:
    def __init__(self) -> None:
        self._nodes: list[dict] = []
        self._edges: list[dict] = []

    def add_node(self, node: dict) -> None:
        self._nodes.append(node)

    def add_edge(self, edge: dict) -> None:
        self._edges.append(edge)

    def build(self) -> Graph:
        nodes_by_id = {node["task_id"]: Node(task_id=node["task_id"]) for node in self._nodes}

        return Graph(
            nodes=list(nodes_by_id.values()),
            edges=[
                Edge(
                    source=nodes_by_id[edge["source"]],
                    target=nodes_by_id[edge["target"]],
                )
                for edge in self._edges
            ],
        )
