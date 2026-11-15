import re


def parse_goal(goal: str) -> str:
    match = re.match(r"\A# Goal\s*\n(.+)\Z", goal, re.DOTALL)

    if match is None:
        raise ValueError("Missing '# Goal' heading or goal content")

    content = match.group(1).strip()

    if not content:
        raise ValueError("Goal cannot be empty")

    return content