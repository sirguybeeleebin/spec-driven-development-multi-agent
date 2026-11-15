import re


_MERMAID_FENCE = re.compile(
    r"```mermaid\s*\n(.*?)\n```",
    re.DOTALL,
)
_DIRECTIVE = re.compile(r"^graph\s+(?:LR|RL|TD|TB|BT)$", re.IGNORECASE)
_NODE = re.compile(r"^\w+$")


def parse_edges(graph: str) -> list[dict[str, str]]:
    fence = _MERMAID_FENCE.search(graph)

    if fence is None:
        raise ValueError("Missing ```mermaid``` block")

    edges = []

    for raw_line in fence.group(1).splitlines():
        line = raw_line.strip()

        if not line or _DIRECTIVE.fullmatch(line):
            continue

        if "-->" not in line:
            raise ValueError(f"Invalid graph edge: {line}")

        parts = [part.strip() for part in line.split("-->")]

        if len(parts) < 2 or any(not _NODE.fullmatch(part) for part in parts):
            raise ValueError(f"Invalid graph edge: {line}")

        edges.extend(
            {"source": source, "target": target}
            for source, target in zip(parts, parts[1:], strict=False)
        )

    return edges