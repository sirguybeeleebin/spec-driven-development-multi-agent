from __future__ import annotations

import json


class ImplementerPromptProvider:
    def __init__(
        self,
        *,
        system_template: str,
        user_template: str,
        final_prompt: str,
    ) -> None:
        self._system = system_template
        self._user = user_template
        self._final = final_prompt

    @property
    def system(self) -> str:
        return self._system

    def format_user(self, context: dict) -> str:
        none = "_(none)_"

        current_interface = context["current_interface"]
        interfaces = context["interfaces"]
        sequence = context["sequence"]
        skills = context["skills"]

        current_fqn = (
            f"`{current_interface['fqn']['fqn']}` "
            f"(role: `{current_interface['fqn']['role']}`)"
            if current_interface is not None
            else none
        )

        def format_interface(interface: dict) -> str:
            return "\n".join(
                [
                    f"## Interface: `{interface['fqn']['fqn']}`",
                    f"FullQualifiedName Role: `{interface['fqn']['role']}`",
                    f"Language: {interface['language']}",
                    f"```{interface['language']}",
                    interface["content"],
                    "```",
                ]
            )

        current_interface_text = (
            format_interface(current_interface)
            if current_interface is not None
            else none
        )

        interfaces_text = (
            "\n\n".join(format_interface(interface) for interface in interfaces)
            if interfaces
            else none
        )

        sequence_lines = []

        for participant in sequence["participants"]:
            declaration = (
                f"{participant['type']} "
                f"{participant['alias']} as {participant['name']}"
            )

            if participant.get("fqn") is not None:
                declaration += (
                    f" %% `{participant['fqn']['fqn']}` "
                    f"(role: `{participant['fqn']['role']}`)"
                )

            sequence_lines.append(declaration)

        def format_components(
            components: list[dict],
            indent: int = 0,
        ) -> list[str]:
            lines = []
            prefix = "    " * indent

            for component in components:
                component_type = component["type"]

                if component_type == "directive":
                    lines.append(f"{prefix}{component['name']}")

                elif component_type == "message":
                    lines.append(
                        f"{prefix}{component['source']}"
                        f"{component['arrow']}"
                        f"{component['target']}: "
                        f"{component['content']}"
                    )

                elif component_type == "note":
                    participants = " and ".join(component["participants"])
                    lines.append(
                        f"{prefix}Note {component['position']} "
                        f"{participants}: {component['content']}"
                    )

                elif component_type == "fragment":
                    for index, branch in enumerate(component["branches"]):
                        keyword = (
                            component["type"]
                            if index == 0 or component["type"] == "loop"
                            else "else"
                        )
                        lines.append(f"{prefix}{keyword} {branch['condition']}")
                        lines.extend(
                            format_components(
                                branch["components"],
                                indent + 1,
                            )
                        )

                    lines.append(f"{prefix}end")

            return lines

        sequence_lines.extend(format_components(sequence["components"]))
        sequence_text = "```text\n" + "\n".join(sequence_lines) + "\n```"

        skills_catalog = (
            "\n\n".join(
                f"## Skill: {skill['name']}\n\n{skill['description']}"
                for skill in skills
            )
            if skills
            else none
        )

        return self._user.format(
            goal=context["goal"] or none,
            current_fqn=current_fqn,
            current_interface=current_interface_text,
            interfaces=interfaces_text,
            constitution=context["constitution"] or none,
            sequence=sequence_text,
            researcher_results=json.dumps(
                context["researcher_response"],
                ensure_ascii=False,
                indent=2,
            ),
            skills=skills_catalog,
        )

    @property
    def final_user(self) -> str:
        return self._final

    def parse_final_response(self, final_response: str) -> dict:
        return json.loads(final_response)