
from __future__ import annotations

from models import Tools


class LoadSkillTool:
    def __init__(self, *, skills: list[dict[str, str]]) -> None:
        self._by_name = {
            skill["name"]: skill
            for skill in skills
        }

    @property
    def name(self) -> str:
        return Tools.LOAD_SKILL

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": (
                    "Load the full content of a skill by its name. "
                    "Use this tool when you need detailed instructions, "
                    "conventions, or reference materials provided by a skill. "
                    "Available skill names are listed in the system prompt "
                    "under `# Skills`."
                ),
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": (
                                "Exact name of the skill to load, "
                                "as listed in the `# Skills` section "
                                "of the system prompt."
                            ),
                        },
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, args: dict[str, object]) -> dict[str, object]:
        name = args["name"]

        if not isinstance(name, str):
            raise TypeError("'name' must be a string")

        skill = self._by_name.get(name)

        if skill is None:
            raise ValueError(f"skill not found: {name}")

        return {
            "ok": True,
            "name": name,
            "content": skill["content"],
        }
