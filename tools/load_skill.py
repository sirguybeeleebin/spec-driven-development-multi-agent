from __future__ import annotations

from models import Skill


class LoadSkillTool:
    def __init__(self, *, skills: list[Skill]) -> None:
        self._by_name = {skill.name: skill for skill in skills}

    def get_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": (
                    "Load the full content of a skill by name. The "
                    "catalog of skill names is in the system prompt "
                    "under `# Skills`."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Skill name.",
                        },
                    },
                    "required": ["name"],
                },
            },
        }

    def execute(self, args: dict) -> dict:
        name = args["name"]
        skill = self._by_name[name]

        return {
            "ok": True,
            "name": name,
            "content": skill.content,
        }
