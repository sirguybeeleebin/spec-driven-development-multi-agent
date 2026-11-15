import re


_TASK_ID = re.compile(
    r"\A# Task\s*\n\s*-\s*task_id:\s*([a-zA-Z0-9_-]+)\s*\Z"
)


def parse_task_id(task: str) -> str:
    match = _TASK_ID.match(task.strip())

    if match is None:
        raise ValueError("Task: missing or invalid task_id")

    return match.group(1)