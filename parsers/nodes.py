import re


_MERMAID_FENCE = re.compile(
    r"```mermaid\s*\n(.*?)\n```",
    re.DOTALL,
)
_DIRECTIVE = re.compile(
    r"^graph\s+(?:LR|RL|TD|TB|BT)$",
    re.IGNORECASE,
)
_NODE = re.compile(r"^\w+$")


def parse_nodes(graph: str) -> list[dict[str, str]]:
    fence = _MERMAID_FENCE.search(graph)

    if fence is None:
        raise ValueError("Missing ```mermaid``` block")

    lines = [
        line.strip()
        for line in fence.group(1).splitlines()
        if line.strip()
    ]

    if not lines or not _DIRECTIVE.fullmatch(lines[0]):
        raise ValueError("Missing or invalid graph directive")

    nodes = {}

    for line in lines[1:]:
        if "-->" in line:
            parts = [part.strip() for part in line.split("-->")]

            if len(parts) < 2 or any(
                not _NODE.fullmatch(part)
                for part in parts
            ):
                raise ValueError(f"Invalid graph edge: {line}")

            for part in parts:
                nodes.setdefault(part, {"task_id": part})

            continue

        if not _NODE.fullmatch(line):
            raise ValueError(f"Invalid graph node: {line}")

        nodes.setdefault(line, {"task_id": line})

    if not nodes:
        raise ValueError("Graph must contain at least one node")

    return list(nodes.values())