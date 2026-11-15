import json
from pathlib import Path


class TaskSectionRepository:
    def __init__(self, *, root: Path) -> None:
        self._root = root / "task_sections"

    def get(
        self,
        *,
        task_id: str,
        section: str,
    ) -> dict | None:
        path = self._root / task_id / f"{section}.json"

        if not path.exists():
            return None

        return json.loads(path.read_text(encoding="utf-8"))

    def save(
        self,
        *,
        task_id: str,
        section: str,
        content: str,
        history: list[dict],
    ) -> dict:
        task_section = {
            "task_id": task_id,
            "section": section,
            "content": content,
            "history": history,
        }

        path = self._root / task_id / f"{section}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(task_section, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return task_section