from __future__ import annotations

import json


class TesterPromptProvider:
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

        current_gherkin = context["current_gherkin"]
        interfaces = context["interfaces"]
        sequence = context["sequence"]
        skills = context["skills"]

        if current_gherkin is None:
            gherkin = none
        else:
            fqns = (
                "\n".join(
                    f"- `{fqn['fqn']}` (role: `{fqn['role']}`)"
                    for fqn in current_gherkin["FullQualifiedNames"]
                )
                if current_gherkin["FullQualifiedNames"]
                else none
            )

            steps = "\n".join(
                [
                    *(f"Given {step}" for step in current_gherkin["given"]),
                    *(f"When {step}" for step in current_gherkin["when"]),
                    *(f"Then {step}" for step in current_gherkin["then"]),
                ]
            )

            gherkin = (
                f"## Scenario: {current_gherkin['name']}\n\n"
                f"### FQNs\n{fqns}\n\n"
                f"### Gherkin\n```gherkin\n{steps}\n```"
            )

        interface_parts = []

        for interface in interfaces:
            interface_parts.append(
                "\n".join(
                    [
                        f"## Interface: `{interface['fqn']['fqn']}`",
                        f"FullQualifiedName Role: `{interface['fqn']['role']}`",
                        f"Language: {interface['language']}",
                        f"```{interface['language']}",
                        interface["content"],
                        "```",
                    ]
                )
            )

        interfaces_text = "\n\n".join(interface_parts) if interface_parts else none

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
            current_gherkin=gherkin,
            interfaces=interfaces_text,
            sequence=sequence_text,
            skills=skills_catalog,
        )

    @property
    def final_user(self) -> str:
        return self._final

    def parse_final_response(self, final_response: str) -> dict:
        return json.loads(final_response)